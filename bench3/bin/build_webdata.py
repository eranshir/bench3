#!/usr/bin/env python3
"""Build webapp/data/results.json from the results CSVs + run artifacts.

The webapp reads this one JSON bundle for all aggregate views, and fetches
per-run detail files (responses, logs, grades, trajectories) lazily.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.common import BENCH, load_arms

RESULTS = BENCH / 'results'
RUNS = BENCH / 'runs'
TASKS = BENCH / 'tasks'
WEB = BENCH / 'webapp'
DATA = WEB / 'data'


def task_meta(cat, name):
    d = TASKS / cat / name
    meta = {'category': cat, 'name': name}
    prompt_file = d / 'PROMPT.txt' if (d / 'PROMPT.txt').exists() else d / 'prompt.txt'
    if prompt_file.exists():
        meta['prompt'] = prompt_file.read_text()[:4000]
    if (d / 'rubric.json').exists():
        meta['rubric'] = json.loads((d / 'rubric.json').read_text())
    if (d / 'tools.json').exists():
        try:
            meta['n_tools'] = len(json.loads((d / 'tools.json').read_text()))
        except Exception:
            pass
    if (d / 'hidden_test.py').exists():
        meta['has_hidden_test'] = True
    if (d / 'check.py').exists():
        meta['has_check'] = True
    return meta


def run_detail(r):
    detail = {}
    lp = r.get('log_path') or ''
    if lp:
        p = Path(lp)
        if p.exists():
            if lp.endswith('.json'):
                try:
                    resp = json.loads(p.read_text())
                    msg = (resp.get('choices') or [{}])[0].get('message', {})
                    detail['content'] = (msg.get('content') or '')[:12000]
                    detail['tool_calls'] = [
                        {'name': c['function']['name'], 'args': c['function']['arguments'][:800]}
                        for c in (msg.get('tool_calls') or [])]
                except Exception:
                    detail['content'] = p.read_text(errors='replace')[:12000]
            else:
                detail['content'] = p.read_text(errors='replace')[-8000:]
    sp = r.get('session_path') or ''
    if sp:
        detail['has_session'] = Path(sp).exists()
        detail['session_path'] = sp
    gl = RUNS / (r['arm'] + '_' + r['task'].replace('/', '-') + '_t' + r['trial'] + '.grade')
    if gl.exists():
        detail['grade'] = gl.read_text(errors='replace')[-4000:]
    ck = RUNS / (r['arm'] + '_' + r['task'].replace('/', '-') + '_t' + r['trial'] + '.check')
    if ck.exists():
        detail['check'] = ck.read_text(errors='replace')[-4000:]
    return detail


def main():
    arms = load_arms()
    runs = []
    for csvf in ('results.csv', 'results_singleshot.csv'):
        p = RESULTS / csvf
        if not p.exists():
            continue
        with open(p) as f:
            for r in csv.DictReader(f):
                r = dict(r)
                r['cost_usd'] = float(r.get('cost_usd') or 0)
                r['seconds'] = int(r.get('seconds') or 0)
                r['input_tokens'] = int(r.get('input_tokens') or 0)
                r['cache_read_tokens'] = int(r.get('cache_read_tokens') or 0)
                r['output_tokens'] = int(r.get('output_tokens') or 0)
                r['reasoning_tokens'] = int(r.get('reasoning_tokens') or 0)
                r['passed'] = int(r.get('passed') or 0)
                runs.append(r)

    # attach details for the qualitative explorer
    for r in runs:
        r['detail'] = run_detail(r)

    # merge rubric judging into runs (keyed by arm|task|trial)
    judged = {}
    jp = RESULTS / 'judged.csv'
    if jp.exists():
        with open(jp) as f:
            for j in csv.DictReader(f):
                try:
                    j['scores'] = json.loads(j.get('scores') or '{}')
                    j['mean'] = float(j.get('mean') or 0)
                except Exception:
                    j['scores'] = {}
                judged[(j['arm'], j['task'], j['trial'])] = j
    for r in runs:
        j = judged.get((r['arm'], r['task'], r['trial']))
        if j:
            r['judged'] = {'mean': j['mean'], 'scores': j['scores'], 'judge': j['judge']}

    tasks = {}
    for cat in sorted(TASKS.iterdir()):
        if not cat.is_dir():
            continue
        for t in sorted(cat.iterdir()):
            if t.is_dir() and (t / 'PROMPT.txt').exists() or (t / 'prompt.txt').exists():
                tasks[t.name] = task_meta(cat.name, t.name)

    bundle = {
        'built_at': None,
        'arms': {k: {'display': v['display'], 'vendor': v['vendor'], 'model': v['model'],
                    'prices': v['prices']} for k, v in arms.items()},
        'tasks': tasks,
        'runs': runs,
        'counts': {'runs': len(runs),
                   'passed': sum(r['passed'] for r in runs),
                   'cost': round(sum(r['cost_usd'] for r in runs), 6)},
    }
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / 'results.json'
    out.write_text(json.dumps(bundle, indent=1))
    print(f'wrote {out} ({len(runs)} runs, {len(tasks)} tasks)')


if __name__ == "__main__":
    main()
