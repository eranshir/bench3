#!/usr/bin/env python3
"""bench3 Aegis k10 statistics: 3-arm (vanilla/guided/enforced) x k=10 comparison.

Reads runs/aegis-k10-records and reports, per task-model cell:
  - pass rate per arm (agentic: resolution.passed; singleshot: checker_passed)
  - paired arm deltas (vanilla->guided, guided->enforced) with McNemar
  - tokens / time / cost aggregates per arm (mean, bootstrap CI)
  - compliance (plan_valid, falsifiers) per arm (agentic only)
  - gate evidence (denies/reverts) per cell (enforced arm)
Honesty: procedural framing only; no causal claims per issue #1623.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
from collections import defaultdict
from math import comb

random.seed(2026)

ARMS = ("vanilla", "guided", "enforced")


def bootstrap_ci(values, n=5000):
    if not values:
        return {"mean": None, "ci95": None, "includes_zero": None}
    mean = sum(values) / len(values)
    boots = []
    for _ in range(n):
        s = sum(random.choice(values) for _ in range(len(values))) / len(values)
        boots.append(s)
    boots.sort()
    lo, hi = boots[int(0.025 * n)], boots[int(0.975 * n)]
    return {"mean": round(mean, 4), "ci95": [round(lo, 4), round(hi, 4)],
            "includes_zero": lo <= 0 <= hi}


def mcnemar(a, b):
    a = list(a); b = list(b)
    if len(a) != len(b):
        return {"statistic": "n/a (unequal k)", "p": None}
    b_yes_a_no = sum(1 for x, y in zip(a, b) if not x and y)
    b_no_a_yes = sum(1 for x, y in zip(a, b) if x and not y)
    n = b_yes_a_no + b_no_a_yes
    if n == 0:
        return {"statistic": "n/a (no discordant pairs)", "p": None}
    k = max(b_yes_a_no, b_no_a_yes)
    p = sum(comb(n, i) * (0.5 ** n) for i in range(k, n + 1)) * 2
    return {"b_yes_a_no": b_yes_a_no, "b_no_a_yes": b_no_a_yes,
            "p_value": round(min(p, 1.0), 4)}


def passed(rec):
    if rec.get("schema_version") == "aegis.bench3.agentic.v1":
        return bool(rec.get("resolution", {}).get("passed"))
    return bool(rec.get("checker_passed"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--min-cell", type=int, default=5,
                    help="minimum reps in a cell for paired stats")
    args = ap.parse_args()

    recs = []
    for p in sorted(pathlib.Path(args.records).glob("*.json")):
        try:
            recs.append(json.loads(p.read_text()))
        except Exception:
            continue
    if not recs:
        print("no records"); return 1

    agentic = [r for r in recs if r.get("schema_version") == "aegis.bench3.agentic.v1"]
    ss = [r for r in recs if r.get("schema_version") == "aegis.bench3.singleshot.v1"]

    # group by (task, model, arm)
    cells = defaultdict(lambda: {"agentic": [], "singleshot": []})
    for r in agentic:
        cells[(r["task"], r["model"], r["arm"])]["agentic"].append(r)
    for r in ss:
        cells[(r["task"], r["model"], r["arm"])]["singleshot"].append(r)

    tasks = sorted({k[0] for k in cells})
    models = sorted({k[1] for k in cells})

    # ---- per-arm aggregate pass rates (all cells pooled) ----
    arm_pass = {a: {"agentic": [], "singleshot": []} for a in ARMS}
    for (task, model, arm), cell in sorted(cells.items()):
        for kind in ("agentic", "singleshot"):
            arm_pass[arm][kind].extend(passed(r) for r in cell[kind])

    per_arm = {}
    for a in ARMS:
        per_arm[a] = {
            "agentic": {"passed": sum(arm_pass[a]["agentic"]), "n": len(arm_pass[a]["agentic"])},
            "singleshot": {"passed": sum(arm_pass[a]["singleshot"]), "n": len(arm_pass[a]["singleshot"])},
        }

    # ---- paired arm comparisons per (task, model) ----
    pair_keys = [("vanilla", "guided", "v_to_g"), ("guided", "enforced", "g_to_e"),
                 ("vanilla", "enforced", "v_to_e")]
    paired = []
    for (task, model) in sorted({(k[0], k[1]) for k in cells}):
        row = {"task": task, "model": model}
        for a, b, name in pair_keys:
            ca = cells.get((task, model, a), {"agentic": [], "singleshot": []})
            cb = cells.get((task, model, b), {"agentic": [], "singleshot": []})
            # agentic preferred; fall back to singleshot
            if len(ca["agentic"]) >= args.min_cell and len(cb["agentic"]) >= args.min_cell:
                pa = [passed(r) for r in ca["agentic"]]
                pb = [passed(r) for r in cb["agentic"]]
                kind = "agentic"
            elif len(ca["singleshot"]) >= args.min_cell and len(cb["singleshot"]) >= args.min_cell:
                pa = [passed(r) for r in ca["singleshot"]]
                pb = [passed(r) for r in cb["singleshot"]]
                kind = "singleshot"
            else:
                row[name] = {"n": 0, "statistic": "n/a (insufficient k)"}
                continue
            row[name] = {
                "n": min(len(pa), len(pb)),
                "kind": kind,
                "a_rate": round(sum(pa) / len(pa), 3),
                "b_rate": round(sum(pb) / len(pb), 3),
                "delta_b_minus_a": round(sum(pb) / len(pb) - sum(pa) / len(pa), 3),
                "mcnemar": mcnemar(pa[:min(len(pa), len(pb))], pb[:min(len(pa), len(pb))]),
            }
        paired.append(row)

    # ---- resource aggregates (tokens output, elapsed, cost) per arm ----
    resource = {}
    for a in ARMS:
        out_tok = [r.get("tokens", {}).get("output", 0) for r in agentic if r["arm"] == a]
        elapsed = [r.get("elapsed_seconds", 0) for r in agentic + ss if r["arm"] == a]
        cost = [r.get("cost_usd", float("nan")) for r in agentic + ss
                if r["arm"] == a and r.get("cost_usd") is not None]
        cost = [c for c in cost if c == c]  # drop nan
        resource[a] = {
            "agentic_output_tokens": bootstrap_ci(out_tok),
            "elapsed_seconds": bootstrap_ci(elapsed),
            "cost_usd": bootstrap_ci(cost),
        }

    # ---- compliance per arm (agentic) ----
    compliance = {}
    for a in ARMS:
        rs = [r for r in agentic if r["arm"] == a]
        if rs:
            compliance[a] = {
                "plan_valid": round(sum(1 for r in rs if r.get("compliance", {}).get("plan_valid")) / len(rs), 3),
                "falsifiers": round(sum(1 for r in rs if r.get("compliance", {}).get("all_children_have_falsifiers")) / len(rs), 3),
                "gate_denies": sum(r.get("materialization", {}).get("gate_transcript", {}).get("denies", 0) for r in rs),
                "gate_reverts": sum(r.get("materialization", {}).get("gate_transcript", {}).get("reverts", 0) for r in rs),
            }

    print(json.dumps({
        "k": args.k,
        "records_total": len(recs),
        "agentic": len(agentic),
        "singleshot": len(ss),
        "models": models,
        "tasks": tasks,
        "per_arm": per_arm,
        "paired": paired,
        "resource": resource,
        "compliance": compliance,
    }, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
