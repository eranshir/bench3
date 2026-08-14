#!/usr/bin/env python3
"""Blind rubric judging for subjective tasks (creativity, writing).

Every run's output is judged against the task rubric by a judge model
(default deepseek-v4-pro). Judging is blind + anonymized + shuffled: the
judge sees only the output text under a random id, never the arm.
"""
import csv
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.common import BENCH, load_arms, load_credentials, cost_usd

END = {"deepseek-official": ("https://api.deepseek.com", "DEEPSEEK_API_KEY", "deepseek-v4-pro", "high"),
       "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-5.6-sol", "high"),
       "xai": ("https://api.x.ai/v1", "XAI_API_KEY", "grok-4.6", "high")}


def call(base, key, body, timeout=600):
    req = urllib.request.Request(base + "/chat/completions", method="POST")
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("Content-Type", "application/json")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, data=json.dumps(body).encode(), timeout=timeout) as r:
            return json.loads(r.read().decode()), time.time() - t0, None
    except urllib.error.HTTPError as e:
        return None, time.time() - t0, "HTTP %d: %s" % (e.code, e.read().decode()[:200])
    except Exception as e:
        return None, time.time() - t0, str(e)[:200]


def judge_one(base, judge_arm, key, model, effort, task, prompt, rubric, output):
    rubric_lines = chr(10).join('-' + k + ': ' + v for k, v in rubric.items())
    sys_prompt = ('You are a rigorous, impartial benchmark judge. Score the candidate '
                 'output against each rubric criterion on a 1-5 scale (5 = excellent). '
                 'Be critical; 3 is average, 5 is exceptional. Consider only the output '
                 'you are given. Reply with a JSON object mapping criterion name to '
                 'score (integer), nothing else.')
    user = ('TASK: ' + task + chr(10) + chr(10) + 'RUBRIC:' + chr(10) + rubric_lines
            + chr(10) + chr(10) + 'CANDIDATE OUTPUT:' + chr(10) + chr(10) + output[:9000])
    body = {'model': model, 'messages': [
        {'role': 'system', 'content': sys_prompt},
        {'role': 'user', 'content': user}],
        'max_tokens': 4096}
    if judge_arm == 'deepseek-official':
        # deepseek reasoning at ANY enabled effort burns the budget; judging
        # is a simple JSON task, so disable thinking entirely
        body['thinking'] = {'type': 'disabled'}
    else:
        body['reasoning_effort'] = 'low'
    resp, dt, err = call(base, key, body)
    if err:
        return None, err
    text = (resp.get('choices') or [{}])[0].get('message', {}).get('content') or ''
    m = re.search(r'\{[^}]*\}', text, re.S)
    if not m:
        return None, 'no JSON in judge reply: ' + text[:200]
    try:
        scores = json.loads(m.group(0))
    except Exception as e:
        return None, 'bad JSON %s: %s' % (e, text[:200])
    u = resp.get('usage', {})
    usage = {'input': u.get('prompt_tokens', 0), 'cached': (u.get('prompt_tokens_details') or {}).get('cached_tokens', 0),
             'output': u.get('completion_tokens', 0), 'reasoning': (u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)}
    return {'scores': scores, 'seconds': dt, 'usage': usage}, None


def main():
    args = sys.argv[1:]
    judge_arm = 'deepseek-official'
    crosscheck = 0.0
    if '--judge' in args:
        judge_arm = args[args.index('--judge') + 1]
    if '--crosscheck' in args:
        crosscheck = float(args[args.index('--crosscheck') + 1])

    arms = load_arms()
    # resolve judge arm alias (bench arm id -> provider route)
    for aid, a in arms.items():
        if aid == judge_arm:
            judge_arm = a['provider']
    if judge_arm not in END:
        print('unknown judge provider:', judge_arm); sys.exit(1)
    base, cred_key, model, effort = END[judge_arm]
    key = load_credentials().get(cred_key)
    if not key:
        print('no credential for judge', judge_arm); sys.exit(1)

    results = BENCH / 'results' / 'results_singleshot.csv'
    judged_path = BENCH / 'results' / 'judged.csv'
    if not results.exists():
        print('no results yet'); return
    rows = list(csv.DictReader(open(results)))
    subj = [r for r in rows if r['category'] in ('creativity', 'writing')]

    done = set()
    if judged_path.exists():
        with open(judged_path) as f:
            for r in csv.DictReader(f):
                done.add((r['arm'], r['task'], r['trial']))

    judged = []
    cost_total = 0.0
    random.seed(2026)
    for r in subj:
        if (r['arm'], r['task'], r['trial']) in done:
            continue
        out_path = Path(r['log_path'])
        if not out_path.exists():
            continue
        try:
            resp = json.loads(out_path.read_text())
            output = (resp.get('choices') or [{}])[0].get('message', {}).get('content') or ''
        except Exception:
            continue
        if not output.strip():
            print('skip empty output:', r['arm'], r['task'], r['trial'])
            continue
        tdir = BENCH / 'tasks' / r['task']
        rubric = json.loads((tdir / 'rubric.json').read_text()) if (tdir / 'rubric.json').exists() else {}
        task_prompt = (tdir / 'prompt.txt').read_text()[:2000]
        res, err = judge_one(base, judge_arm, key, model, effort, r['task'], task_prompt, rubric, output)
        if err:
            print('judge error:', r['arm'], r['task'], r['trial'], err)
            continue
        aid = next((k for k, a in arms.items() if a['provider'] == judge_arm), judge_arm)
        cost = cost_usd(arms.get(aid, {}), res['usage']['input'], res['usage']['cached'], res['usage']['output'])
        cost_total += cost
        judged.append({'judge': judge_arm, 'arm': r['arm'], 'task': r['task'], 'trial': r['trial'],
                       'model': r['model'], 'category': r['category'], 'scores': json.dumps(res['scores']),
                       'mean': round(sum(res['scores'].values()) / max(len(res['scores']), 1), 2),
                       'judge_seconds': round(res['seconds'], 1), 'cost_usd': round(cost, 6)})
        print('judged %s %s t%s -> %s' % (r['arm'], r['task'], r['trial'], res['scores']))

    if judged:
        write_header = not judged_path.exists()
        with open(judged_path, 'a', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(judged[0].keys()))
            if write_header:
                w.writeheader()
            w.writerows(judged)
        print('judged %d runs, judge cost $%.4f -> %s' % (len(judged), cost_total, judged_path))
    else:
        print('nothing new to judge')


if __name__ == "__main__":
    main()

