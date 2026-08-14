#!/usr/bin/env python3
"""Single-shot mode runner: reasoning, creativity, writing, function-calling.

Same client code for every arm (only model id + wire params differ), so the
comparison is harness-identical. Exact usage from each API response.

Usage:
  ./run_singleshot.py                     # all arms, all tasks, trial 1
  ./run_singleshot.py gpt-sol             # one arm
  ./run_singleshot.py gpt-sol 2 reasoning/r1
"""
import csv
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.common import BENCH, load_arms, load_credentials, cost_usd, append_row

ENDPOINTS = {
    "deepseek-official": ("https://api.deepseek.com", "chat/completions"),
    "openai": ("https://api.openai.com/v1", "chat/completions"),
    "xai": ("https://api.x.ai/v1", "chat/completions"),
}

CRED_KEYS = {
    "deepseek-official": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "xai": "XAI_API_KEY",
}


def call_api(provider, key, body, timeout=900):
    base, path = ENDPOINTS[provider]
    req = urllib.request.Request(base + "/" + path, method="POST")
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("Content-Type", "application/json")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, data=json.dumps(body).encode(), timeout=timeout) as r:
            return json.loads(r.read().decode()), time.time() - t0, None
    except urllib.error.HTTPError as e:
        return None, time.time() - t0, "HTTP %d: %s" % (e.code, e.read().decode()[:300])
    except Exception as e:
        return None, time.time() - t0, str(e)[:300]


def wire_params(provider, effort, max_tokens):
    """Per-provider wire spelling of the pinned effort + output cap."""
    if provider == "openai":
        return {"reasoning_effort": effort, "max_completion_tokens": max_tokens}
    if provider == "xai":
        return {"reasoning_effort": effort, "max_tokens": max_tokens}
    # deepseek: thinking enabled + effort
    return {"thinking": {"type": "enabled", "effort": effort}, "max_tokens": max_tokens}


def extract_usage(provider, resp):
    u = resp.get("usage", {})
    p = u.get("prompt_tokens", 0)
    o = u.get("completion_tokens", 0)
    cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    reasoning = (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
    if not reasoning and u.get('completion_tokens_details'):
        reasoning = u.get("completion_tokens_details").get("reasoning_tokens", 0)
    cost_ticks = u.get("cost_in_usd_ticks")
    return {"input": p, "cached": cached, "output": o, "reasoning": reasoning}, cost_ticks


def run_check(task_dir, out_path, log_path):
    """Optional objective checker: check.py <output_file>; exit 0 = pass, prints JSON score."""
    cp = task_dir / "check.py"
    if not cp.exists():
        return None
    r = subprocess.run([sys.executable, str(cp), str(out_path)], capture_output=True, text=True, timeout=300)
    try:
        score = json.loads(r.stdout.strip())
        if not isinstance(score, dict):
            raise ValueError('check.py must print a JSON object')
    except Exception:
        score = {"passed": r.returncode == 0, "detail": r.stdout.strip()[-500:]}
    with open(log_path, "w") as f:
        f.write(r.stdout)
        f.write("\n---STDERR---\n")
        f.write(r.stderr)
    return score


def main():
    args = [a for a in sys.argv[1:]]
    arm = args[0] if args else "all"
    trial = args[1] if len(args) > 1 else "1"
    only = args[2] if len(args) > 2 else ""

    arms = load_arms()
    arm_ids = list(arms) if arm == "all" else [arm]
    creds = load_credentials()

    results = BENCH / "results" / "results_singleshot.csv"
    runs = BENCH / "runs"
    runs.mkdir(exist_ok=True)

    tasks = []
    for cat in sorted((BENCH / 'tasks').iterdir()):
        if not cat.is_dir():
            continue
        for t in sorted(cat.iterdir()):
            if (t / 'prompt.txt').exists() and (t / 'mode.txt').exists() and (t / 'mode.txt').read_text().strip() == 'singleshot':
                tasks.append(cat.name + "/" + t.name)
    if only:
        tasks = [only]

    done = set()
    if results.exists():
        with open(results) as f:
            for row in csv.DictReader(f):
                done.add((row["arm"], row["task"], row["trial"]))

    for aid in arm_ids:
        a = arms[aid]
        provider = a["provider"]
        key = creds.get(CRED_KEYS.get(provider, ""))
        if not key:
            print("!! no credential for %s (%s)" % (aid, provider)); continue
        for task in tasks:
            catname, tname = task.split("/")
            tdir = BENCH / "tasks" / task
            if (aid, task, trial) in done:
                print("skip (done): %s %s t%s" % (aid, task, trial)); continue

            system = (tdir / "system.txt").read_text() if (tdir / "system.txt").exists() else None
            prompt = (tdir / "prompt.txt").read_text()
            max_tokens = int((tdir / "max_tokens.txt").read_text().strip()) if (tdir / "max_tokens.txt").exists() else 8192
            tools = json.loads((tdir / "tools.json").read_text()) if (tdir / "tools.json").exists() else None

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            body = {
                "model": a["model"],
                "messages": messages,
                **wire_params(provider, a['effort'], max_tokens),
            }
            if tools:
                body["tools"] = tools
                body["tool_choice"] = "auto"

            print("=== %s / %s / trial %s ===" % (aid, task, trial))
            resp, secs, err = call_api(provider, key, body)
            notes = ""
            if err:
                notes = err
                print("  FAILED: %s" % err)
                append_row(results, {"arm": aid, "vendor": a["vendor"], "model": a["model"], "category": catname,
                                     "task": task, "trial": trial, "effort": a["effort"], "mode": "singleshot",
                                     "seconds": int(secs), "input_tokens": 0, "cache_read_tokens": 0,
                                     "output_tokens": 0, "reasoning_tokens": 0, "cost_usd": 0.0,
                                     "passed": 0, "tests_failed": 1, "grade_seconds": 0, "notes": notes[:200],
                                     "session_path": "", "log_path": ""})
                continue

            usage, ticks = extract_usage(provider, resp)
            cost = cost_usd(a, usage["input"], usage["cached"], usage["output"])
            if ticks:
                notes = "xai_ticks=%s" % ticks

            # save raw output
            out_path = runs / ("%s_%s-%s_t%s.json" % (aid, catname, tname, trial))
            out_path.write_text(json.dumps(resp, indent=1))

            # objective check if provided
            passed, tests_failed = 0, 0
            if tdir.joinpath("check.py").exists():
                score = run_check(tdir, out_path, runs / ("%s_%s-%s_t%s.check" % (aid, catname, tname, trial)))
                if score:
                    passed = 1 if score.get("passed") else 0
                    tests_failed = 0 if passed else 1
            else:
                passed = 1  # subjective categories: judged later, not auto-failed

            text = (resp.get("choices") or [{}])[0].get("message", {}).get("content") or ""
            n_calls = len((resp.get("choices") or [{}])[0].get("message", {}).get("tool_calls") or [])
            append_row(results, {"arm": aid, "vendor": a["vendor"], "model": a["model"], "category": catname,
                                 "task": task, "trial": trial, "effort": a["effort"], "mode": "singleshot",
                                 "seconds": int(secs), "input_tokens": usage["input"], "cache_read_tokens": usage["cached"],
                                 "output_tokens": usage["output"], "reasoning_tokens": usage["reasoning"],
                                 "cost_usd": round(cost, 6), "passed": passed, "tests_failed": tests_failed,
                                 "grade_seconds": 0, "notes": notes, "session_path": "", "log_path": str(out_path)})
            print("  -> %.1fs in=%d cached=%d out=%d reas=%d cost=$%.5f passed=%d calls=%d reply=%r"
                  % (secs, usage["input"], usage["cached"], usage["output"], usage["reasoning"], cost, passed, n_calls, text[:60]))


if __name__ == "__main__":
    main()
