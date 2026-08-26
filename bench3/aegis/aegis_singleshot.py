#!/usr/bin/env python3
"""bench3 Aegis singleshot runner — guided / enforced arms for single-prompt tasks.

guided:   method payload prepended to the system prompt; response recorded.
enforced: same prompt + response-gate — the run is UNRESOLVED (fails closed) if
          the response does not carry the method artifacts (plan, falsifiers,
          closure) as JSON blocks.

Usage:
  aegis_singleshot.py --arm guided|enforced --model deepseek-flash \
    --task reasoning/r2_expectedflips --rep 1 --out /tmp/aegis-records
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
import time
import urllib.request

AEGIS = pathlib.Path(__file__).resolve().parent
BENCH = AEGIS.parent
PAYLOAD = AEGIS / "method_payload.md"

sys.path.insert(0, str(BENCH / "bin"))
from lib.common import load_arms, load_credentials, append_row  # noqa: E402
from lib.common import cost_usd as _cost_usd  # noqa: E402

ENDPOINTS = {
    "deepseek-official": ("https://api.deepseek.com", "chat/completions"),
    "openai": ("https://api.openai.com/v1", "chat/completions"),
    "xai": ("https://api.x.ai/v1", "chat/completions"),
    "mtplx": ("http://127.0.0.1:8000/v1", "chat/completions"),
    "lunaroute": ("https://gw.lunaroute.com/v1", "chat/completions"),
    "openrouter": ("https://openrouter.ai/api/v1", "chat/completions"),
}
CRED_KEYS = {
    "deepseek-official": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "xai": "XAI_API_KEY",
    "mtplx": "",
    "lunaroute": "LUNAROUTE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def response_has_method_artifacts(text: str) -> dict:
    """Response-gate: the response must carry plan + falsifier artifacts."""
    has_plan = bool(re.search(r'"?(?:id|name)"?\s*[:=]\s*["\']', text) and
                    re.search(r"assumption", text, re.I))
    has_falsifier = bool(re.search(r"falsif", text, re.I))
    has_closure = bool(re.search(r"clos|reconcil", text, re.I))
    # accept explicit JSON blocks too
    has_json_plan = '"plan"' in text or ".bruno/plan" in text
    has_json_children = ".bruno/children" in text or '"children"' in text
    return {
        "passed": (has_plan or has_json_plan) and (has_falsifier) and (has_closure or has_json_children),
        "has_plan": has_plan or has_json_plan,
        "has_falsifier": has_falsifier,
        "has_closure": has_closure or has_json_children,
    }



def _main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', choices=('guided', 'enforced', 'vanilla'), required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--task', required=True)
    ap.add_argument('--rep', type=int, default=1)
    ap.add_argument('--out', default=str(BENCH / 'runs' / 'aegis-records'))
    args = ap.parse_args()

    arms = load_arms()
    a = arms[args.model]
    provider = a['provider']
    key = load_credentials().get(CRED_KEYS.get(provider, ''))

    tdir = BENCH / 'tasks' / args.task
    prompt = (tdir / 'prompt.txt').read_text()
    system = None
    if (tdir / 'system.txt').exists():
        system = (tdir / 'system.txt').read_text()
    max_tokens = int((tdir / 'max_tokens.txt').read_text().strip()) if (tdir / 'max_tokens.txt').exists() else 4096

    payload = PAYLOAD.read_text()
    if args.arm != 'vanilla':
        prompt = 'Aegis method (binding):\n\n' + payload + '\n\n' + "Task:\n\n" + prompt

    messages = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': prompt})

    body = {'model': a['model'], 'messages': messages}
    if provider == 'openai':
        body['max_completion_tokens'] = max_tokens
    else:
        body['max_tokens'] = max_tokens
    if provider in ('deepseek-official',):
        body['thinking'] = {'type': 'disabled'}
    elif provider == 'mtplx':
        body['reasoning_effort'] = 'low' if args.arm == 'vanilla' else 'high'
    elif provider == 'lunaroute':
        body['reasoning_effort'] = 'none' if args.arm == 'vanilla' else 'high'

    base, path = ENDPOINTS[provider]
    req = urllib.request.Request(base + '/' + path, method='POST')
    if provider == 'openrouter':
        req.add_header('HTTP-Referer', 'https://eranshir.github.io/bench3/')
        req.add_header('X-Title', 'bench3')
    if key:
        req.add_header('Authorization', 'Bearer ' + key)
    req.add_header('Content-Type', 'application/json')
    t0 = time.time()
    with urllib.request.urlopen(req, data=json.dumps(body).encode(), timeout=900) as resp:
        d = json.load(resp)
    elapsed = int(time.time() - t0)
    msg = d['choices'][0]['message']
    text = msg.get('content') or msg.get('reasoning') or ''

    gate = response_has_method_artifacts(text)
    resolved = True
    if args.arm == 'enforced' and not gate['passed']:
        resolved = False

    passed = 0
    check = tdir / 'check.py'
    if check.exists():
        out_path = BENCH / 'runs' / ('aegis-%s_%s-%s_rep%d.json' % (args.arm, args.model,
                                                                    args.task.replace('/', '-'), args.rep))
        out_path.write_text(json.dumps(d, indent=1))
        cr = subprocess_run([sys.executable, str(check), str(out_path)])
        try:
            score = json.loads(cr.stdout.strip())
            passed = 1 if score.get('passed') else 0
        except Exception:
            passed = 1 if cr.returncode == 0 else 0
    else:
        passed = 1

    usage = d.get('usage', {})
    in_tok = usage.get('prompt_tokens', 0)
    out_tok = usage.get('completion_tokens', 0)
    try:
        cost = round(_cost_usd(a, in_tok, 0, out_tok), 6)
    except Exception:
        cost = float('nan')

    record = {
        'schema_version': 'aegis.bench3.singleshot.v1',
        'arm': args.arm, 'model': args.model, 'task': args.task, 'repetition': args.rep,
        'elapsed_seconds': elapsed,
        'payload_digest': sha256(payload),
        'response_gate': gate,
        'resolved': resolved,
        'checker_passed': bool(passed),
        'output_chars': len(text),
        'tokens': {'input': in_tok, 'output': out_tok, 'observed': True},
        'cost_usd': cost,
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / ('%s_%s_%s_rep%d.json' % (args.arm, args.model, args.task.replace('/', '-'), args.rep))).write_text(json.dumps(record, indent=1))
    print(json.dumps(record, indent=1, default=str))
    return 0


def subprocess_run(cmd):
    import subprocess
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300)


def main() -> int:
    import argparse, pathlib as _pl
    try:
        return _main()
    except Exception as e:
        ap = argparse.ArgumentParser()
        ap.add_argument('--arm'); ap.add_argument('--model'); ap.add_argument('--task')
        ap.add_argument('--rep', type=int, default=1); ap.add_argument('--out', default='')
        a = ap.parse_known_args()[0]
        record = {
            'schema_version': 'aegis.bench3.singleshot.v1',
            'arm': a.arm, 'model': a.model, 'task': a.task, 'repetition': a.rep,
            'elapsed_seconds': 0,
            'payload_digest': sha256(PAYLOAD.read_text()),
            'response_gate': {'passed': False},
            'resolved': False,
            'checker_passed': False,
            'output_chars': 0,
            'tokens': {'input': 0, 'output': 0, 'observed': False},
            'cost_usd': 0.0,
            'error': str(e)[:300],
        }
        out = _pl.Path(a.out or str(BENCH / 'runs' / 'aegis-records'))
        out.mkdir(parents=True, exist_ok=True)
        (out / ('%s_%s_%s_rep%d.json' % (a.arm, a.model, a.task.replace('/', '-'), a.rep))).write_text(json.dumps(record, indent=1))
        print(json.dumps(record, indent=1, default=str))
        return 2


if __name__ == '__main__':
    sys.exit(main())

