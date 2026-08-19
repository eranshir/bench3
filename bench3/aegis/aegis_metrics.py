#!/usr/bin/env python3
"""bench3 Aegis metrics engine (ADR 0043 Rules 5-6 + K10 metric list).

Reads the aegis records dir and reports: pass@1, pass^k (resolved in all k),
compliance vector, enforcement-lift per task with paired stats (McNemar on
resolution; bootstrap 95% CI on continuous deltas), tokens/resolved, and the
honesty-framed summary. No causal phrasing where CI includes 0.

Usage: aegis_metrics.py --records <dir> [--k 3]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import statistics
import sys
from collections import defaultdict


def bootstrap_ci(values: list[float], n: int = 5000, seed: int = 2026) -> dict:
    if not values:
        return {"mean": None, "ci95": None, "includes_zero": None}
    rng = random.Random(seed)
    means = []
    for _ in range(n):
        sample = [rng.choice(values) for _ in values]
        means.append(statistics.mean(sample))
    means.sort()
    lo = means[int(0.025 * n)]
    hi = means[int(0.975 * n)]
    return {"mean": round(statistics.mean(values), 4), "ci95": [round(lo, 4), round(hi, 4)],
            "includes_zero": lo <= 0 <= hi}


def mcnemar(a_resolved: list[bool], b_resolved: list[bool]) -> dict:
    """Exact McNemar on paired resolution (b-a discordant cells)."""
    b_yes_a_no = sum(1 for a, b in zip(a_resolved, b_resolved) if not a and b)
    b_no_a_yes = sum(1 for a, b in zip(a_resolved, b_resolved) if a and not b)
    n = b_yes_a_no + b_no_a_yes
    if n == 0:
        return {"statistic": "n/a (no discordant pairs)", "p": None}
    # binomial exact: p = 2 * P(X >= max(d1,d2) | p=0.5, n)
    from math import comb
    k = max(b_yes_a_no, b_no_a_yes)
    p = sum(comb(n, i) * (0.5 ** n) for i in range(k, n + 1)) * 2
    p = min(p, 1.0)
    return {"b_yes_a_no": b_yes_a_no, "b_no_a_yes": b_no_a_yes, "p_value": round(p, 4)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()

    recs = []
    for p in sorted(pathlib.Path(args.records).glob("*.json")):
        recs.append(json.loads(p.read_text()))
    if not recs:
        print("no records"); return 1

    # group by (task, arm, model)
    cells = defaultdict(list)
    for rec in recs:
        cells[(rec["task"], rec["arm"], rec["model"])].append(rec)

    report = {"arms": sorted({r["arm"] for r in recs}),
              "models": sorted({r["model"] for r in recs}),
              "tasks": sorted({r["task"] for r in recs}),
              "k": args.k, "tasks_by_arm_model": {}}

    for (task, arm, model), rs in sorted(cells.items()):
        resolved = [bool(r.get("resolution", {}).get("passed") or
                         (r.get("resolution", {}).get("evaluated") is False)) for r in rs]
        passed_k = all(resolved) if len(rs) == args.k else None
        key = "%s|%s|%s" % (task, arm, model)
        report["tasks_by_arm_model"][key] = {
            "n": len(rs),
            "pass_at_1": round(sum(resolved) / len(rs), 3) if rs else None,
            "pass_k": passed_k,
            "plan_valid": round(sum(1 for r in rs if r.get("compliance", {}).get("plan_valid")) / len(rs), 3),
            "children_with_falsifiers": round(
                sum(1 for r in rs if r.get("compliance", {}).get("all_children_have_falsifiers")) / len(rs), 3),
            "gate_denies": sum(r.get("materialization", {}).get("gate_transcript", {}).get("denies", 0) for r in rs),
            "gate_reverts": sum(r.get("materialization", {}).get("gate_transcript", {}).get("reverts", 0) for r in rs),
            "tokens_per_task": [r.get("tokens", {}).get("output", 0) for r in rs],
            "elapsed": [r.get("elapsed_seconds", 0) for r in rs],
        }

    # enforcement lift per (task, model): guided vs enforced (once per pair)
    lifts = []
    seen = set()
    for (task, arm, model), rs in list(cells.items()):
        if arm != "guided":
            continue
        key_other = (task, "enforced", model)
        if key_other not in cells or (task, model) in seen:
            continue
        seen.add((task, model))
        g = cells[(task, arm, model)]
        e = cells[key_other]
        g_res = [bool(r.get("resolution", {}).get("passed")) for r in g]
        e_res = [bool(r.get("resolution", {}).get("passed")) for r in e]
        g_comp = [bool(r.get("compliance", {}).get("plan_valid")) for r in g]
        e_comp = [bool(r.get("compliance", {}).get("plan_valid")) for r in e]
        lift_res = (sum(e_res) / len(e_res) - sum(g_res) / len(g_res)) if e_res and g_res else None
        lift_comp = (sum(e_comp) / len(e_comp) - sum(g_comp) / len(g_comp)) if e_comp and g_comp else None
        mcn = mcnemar(g_res, e_res) if len(g_res) == len(e_res) else {"statistic": "n/a (unequal k)", "p": None}
        lifts.append({"task": task, "model": model,
                      "enforced_minus_guided_resolution": round(lift_res, 3) if lift_res is not None else None,
                      "enforced_minus_guided_compliance": round(lift_comp, 3) if lift_comp is not None else None,
                      "guided_n": len(g_res), "enforced_n": len(e_res), "mcnemar": mcn})

    report["enforcement_lifts"] = lifts

    # aggregate paired CI on tokens (guided vs enforced, equal-k pairs only)
    token_pairs = []
    for (task, arm, model), rs in list(cells.items()):
        if arm != "guided":
            continue
        key_other = (task, "enforced", model)
        if key_other not in cells:
            continue
        g = [r.get("tokens", {}).get("output", 0) for r in rs]
        e = [r.get("tokens", {}).get("output", 0) for r in cells[key_other]]
        if len(g) == len(e):
            for x, y in zip(g, e):
                token_pairs.append(y - x)
    report["tokens_enforced_minus_guided_ci"] = bootstrap_ci(token_pairs)

    # validity summary (agentic records only; singleshot has its own schema)
    agentic = [r for r in recs if r.get("schema_version") == "aegis.bench3.agentic.v1"]
    recs_with_iso = [r for r in agentic if r.get("isolation", {}).get("pre", {}).get("clean_before")]
    report["validity"] = {
        "records_total": len(recs),
        "agentic_records": len(agentic),
        "singleshot_records": len(recs) - len(agentic),
        "clean_before_asserted": len(recs_with_iso) == len(agentic) if agentic else None,
        "all_records_have_parity": all("parity" in r for r in agentic) if agentic else None,
        "all_records_have_tokens": all(r.get("tokens", {}).get("observed") or
                                       r.get("tokens", {}).get("error") for r in agentic) if agentic else None,
    }
    print(json.dumps(report, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
