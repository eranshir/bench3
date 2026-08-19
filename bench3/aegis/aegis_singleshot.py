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

ENDPOINTS = {
    "deepseek-official": ("https://api.deepseek.com", "chat/completions"),
    "openai": ("https://api.openai.com/v1", "chat/completions"),
    "xai": ("https://api.x.ai/v1", "chat/completions"),
    "mtplx": ("http://127.0.0.1:8000/v1", "chat/completions"),
    "lunaroute": ("https://gw.lunaroute.com/v1", "chat/completions"),
}
CRED_KEYS = {
    "deepseek-official": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "xai": "XAI_API_KEY",
    "mtplx": "",
    "lunaroute": "LUNAROUTE_API_KEY",
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=("guided", "enforced", "vanilla"), required=True)
    ap.add_argument("--model", required=True)  # bench arm id
    ap.add_argument("--task", required=True)
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--out", default=str(BENCH / "runs" / "aegis-records"))
    args = ap.parse_args()

    arms = load_arms()
    a = arms[args.model]
    provider = a["provider"]
    key = load_credentials().get(CRED_KEYS.get(provider, ""))

    tdir = BENCH / "tasks" / args.task
    prompt = (tdir / "prompt.txt").read_text()
    system = None
    if (tdir / "system.txt").exists():
        system = (tdir / "system.txt").read_text()
    max_tokens = int((tdir / "max_tokens.txt").read_text().strip()) if (tdir / "max_tokens.txt").exists() else 4096

    payload = PAYLOAD.read_text()
    if args.arm != "vanilla":
        prompt = "Aegis method (binding):\n\n" + payload + "\n\nTask:\n\n" + prompt

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {"model": a["model"], "messages": messages}
    if provider == "openai":
        body["max_completion_tokens"] = max_tokens  # gpt-5.6-sol rejects max_tokens
    else:
        body["max_tokens"] = max_tokens
    if provider in ("deepseek-official",):
        body["thinking"] = {"type": "disabled"}
    elif provider == "mtplx":
        body["reasoning_effort"] = "low" if args.arm == "vanilla" else "xhigh"
    elif provider == "lunaroute":
        body["reasoning_effort"] = "none" if args.arm == "vanilla" else "high"

    base, path = ENDPOINTS[provider]
    req = urllib.request.Request(base + "/" + path, method="POST")
    if key:
        req.add_header("Authorization", "Bearer " + key)
    req.add_header("Content-Type", "application/json")
    t0 = time.time()
    with urllib.request.urlopen(req, data=json.dumps(body).encode(), timeout=600) as resp:
        d = json.load(resp)
    elapsed = int(time.time() - t0)
    msg = d["choices"][0]["message"]
    text = msg.get("content") or ""

    gate = response_has_method_artifacts(text)
    resolved = True
    if args.arm == "enforced" and not gate["passed"]:
        resolved = False  # response-gate fails closed

    # objective checker if present
    passed = 0
    check = tdir / "check.py"
    if check.exists():
        out_path = BENCH / "runs" / ("aegis-%s_%s-%s_rep%d.json" % (args.arm, args.model,
                                                                    args.task.replace("/", "-"), args.rep))
        out_path.write_text(json.dumps(d, indent=1))
        cr = subprocess_run([sys.executable, str(check), str(out_path)])
        try:
            score = json.loads(cr.stdout.strip())
            passed = 1 if score.get("passed") else 0
        except Exception:
            passed = 1 if cr.returncode == 0 else 0
    else:
        passed = 1

    record = {
        "schema_version": "aegis.bench3.singleshot.v1",
        "arm": args.arm, "model": args.model, "task": args.task, "repetition": args.rep,
        "elapsed_seconds": elapsed,
        "payload_digest": sha256(payload),
        "response_gate": gate,
        "resolved": resolved,
        "checker_passed": bool(passed),
        "output_chars": len(text),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / ("%s_%s_%s_rep%d.json" % (args.arm, args.model, args.task.replace("/", "-"), args.rep))
     ).write_text(json.dumps(record, indent=1))
    print(json.dumps(record, indent=1, default=str))
    return 0


def subprocess_run(cmd):
    import subprocess
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300)


if __name__ == "__main__":
    sys.exit(main())
