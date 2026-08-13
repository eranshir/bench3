#!/usr/bin/env python3
"""Summarise results.csv: pass rates, median latency/tokens, modelled cost bounds.

Cost is reported as a band, not a point. `codex exec` emits only an aggregate
token count with no input/output split, so the exact figure is not recoverable
from the logs. We bracket it:

  cached  - every token billed as cached input   (absolute floor)
  input   - every token billed as fresh input    (realistic-low)
  output  - every token billed as output         (ceiling)

Agent loops resend the whole context each turn, so the truth sits near the
input end. For DeepSeek the account balance delta is the ground truth and
supersedes all of this; the GPT figure is always modelled, never money spent.
"""
import csv, statistics, sys, os
from collections import defaultdict

# per 1M tokens. DeepSeek = standard (off-peak) rates; peak windows double them.
PRICES = {
    "deepseek": {"cached": 0.0028, "input": 0.14, "output": 0.28},
    "gpt":      {"cached": 0.50,   "input": 5.00, "output": 30.00},
}
ROOT = os.path.dirname(os.path.abspath(__file__))


def cost(model, tokens, kind):
    return tokens / 1_000_000 * PRICES[model][kind]


def main():
    # optional positional: path to a results csv (the hard suite has its own)
    path = sys.argv[1] if len(sys.argv) > 1 \
        else os.path.join(ROOT, "results.csv")
    rows = [r for r in csv.DictReader(open(path))]
    if not rows:
        print(f"no rows yet in {path}")
        return
    excluded = [r for r in rows if r["notes"] == "insufficient_balance"]
    rows = [r for r in rows if r["notes"] != "insufficient_balance"]
    for r in rows:
        r["seconds"] = int(r["seconds"]); r["tokens"] = int(r["tokens"])
        r["passed"] = int(r["passed"]); r["tests_failed"] = int(r["tests_failed"])

    efforts = sorted({r["effort"] for r in rows})
    for effort in efforts:
        sub = [r for r in rows if r["effort"] == effort]
        print(f"\n{'='*72}\nEFFORT = {effort}   ({len(sub)} runs)\n{'='*72}")

        by = defaultdict(list)
        for r in sub:
            by[(r["model"], r["task"])].append(r)

        tasks = sorted({r["task"] for r in sub})
        models = sorted({r["model"] for r in sub})

        print(f"\n{'task':<14}", end="")
        for m in models:
            print(f"{m+' pass':<12}{m+' med_s':<12}{m+' med_tok':<14}", end="")
        print()
        for t in tasks:
            print(f"{t:<14}", end="")
            for m in models:
                g = by[(m, t)]
                if not g:
                    print(f"{'-':<38}", end=""); continue
                p = sum(x["passed"] for x in g)
                print(f"{f'{p}/{len(g)}':<12}"
                      f"{statistics.median(x['seconds'] for x in g):<12.0f}"
                      f"{statistics.median(x['tokens'] for x in g):<14,.0f}", end="")
            print()

        print(f"\n{'model':<12}{'pass':<10}{'tot_tok':<12}"
              f"{'$cached':<11}{'$input':<11}{'$output':<11}{'$in/pass':<11}")
        for m in models:
            g = [r for r in sub if r["model"] == m]
            npass = sum(r["passed"] for r in g)
            tok = sum(r["tokens"] for r in g)
            ci, co, cc = (cost(m, tok, k) for k in ("input", "output", "cached"))
            per = f"{ci/npass:.4f}" if npass else "n/a"
            print(f"{m:<12}{f'{npass}/{len(g)}':<10}{tok:<12,}"
                  f"{cc:<11.4f}{ci:<11.4f}{co:<11.4f}{per:<11}")

        if len(models) == 2:
            a, b = models
            ga = [r for r in sub if r["model"] == a]
            gb = [r for r in sub if r["model"] == b]
            pa, pb = sum(r["passed"] for r in ga), sum(r["passed"] for r in gb)
            ta, tb = sum(r["tokens"] for r in ga), sum(r["tokens"] for r in gb)
            if pa and pb:
                cpa, cpb = cost(a, ta, "input")/pa, cost(b, tb, "input")/pb
                print(f"\ncost per PASSING task (all-input basis): "
                      f"{a} ${cpa:.4f}  vs  {b} ${cpb:.4f}  ->  {cpb/cpa:.1f}x")
                rawa, rawb = cost(a, ta, "input"), cost(b, tb, "input")
                print(f"raw token-cost ratio (ignoring pass rate): {rawb/rawa:.1f}x")

    if excluded:
        print(f"\n!! {len(excluded)} run(s) excluded: insufficient_balance "
              f"(not model failures)")
        for r in excluded:
            print(f"   {r['model']} {r['task']} trial {r['trial']}")


if __name__ == "__main__":
    main()
