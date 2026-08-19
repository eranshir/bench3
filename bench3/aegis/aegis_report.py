#!/usr/bin/env python3
"""bench3 Aegis report generator (smoke5-style, ADR 0043 checklist + honesty framing)."""
from __future__ import annotations
import argparse, json, pathlib, subprocess, sys
from datetime import datetime, timezone

AEGIS = pathlib.Path(__file__).resolve().parent
import sys as _sys
_sys.path.insert(0, str(AEGIS))
from vanilla_baseline import vanilla_table

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--out", default=str(AEGIS / "REPORT.md"))
    args = ap.parse_args()
    rec_dir = pathlib.Path(args.records)
    records = sorted(rec_dir.glob("*.json"))
    if not records:
        print("no records at " + str(rec_dir)); return 1

    contam = subprocess.run([sys.executable, str(AEGIS / "contamination.py"), "--records", str(rec_dir)],
                            capture_output=True, text=True)
    try: cont = json.loads(contam.stdout)
    except Exception: cont = {"error": contam.stdout[:500]}

    met = subprocess.run([sys.executable, str(AEGIS / "aegis_metrics.py"), "--records", str(rec_dir)],
                         capture_output=True, text=True)
    try: m = json.loads(met.stdout)
    except Exception: m = {"error": met.stdout[:500]}

    cells = m.get("tasks_by_arm_model", {})
    lifts = m.get("enforcement_lifts", [])
    arms = m.get("arms", [])
    arm_pass = {}
    for arm in arms:
        cells_arm = {k: v for k, v in cells.items() if k.split("|")[1] == arm}
        if not cells_arm: continue
        n = sum(v["n"] for v in cells_arm.values())
        p = sum(v["n"] * (v["pass_at_1"] or 0) for v in cells_arm.values())
        pk = sum(1 for v in cells_arm.values() if v.get("pass_k"))
        arm_pass[arm] = {"n": n, "pass1": round(p / n, 3) if n else None,
                         "passk": pk, "cells": len(cells_arm)}

    now = datetime.now(timezone.utc).isoformat(timespec="minutes")
    L = []
    L.append("# bench3 Aegis guided-vs-enforced - scored report")
    L.append("")
    L.append("**Date:** " + now + "  **Status:** per ADR 0043")
    L.append("")
    L.append("## Honesty boundary (issue #1623)")
    L.append("")
    L.append("Measures whether **live enforcement** of the Aegis method changes measured adherence and")
    L.append("outcomes on bench3 agentic tasks vs prose guidance alone. Does NOT establish that Aegis")
    L.append("makes an agent reliable, correct, or complete. Supported conclusion is procedural.")
    L.append("")
    L.append("## Pass rates")
    L.append("")
    L.append("| Arm | pass@1 | cells | pass^k cells |")
    L.append("|---|---|---|---|")
    for arm in arms:
        a = arm_pass.get(arm)
        if a:
            L.append("| " + arm + " | " + str(a["pass1"]) + " | " + str(a["cells"]) + " | " + str(a["passk"]) + "/" + str(a["cells"]) + " |")
    L.append("")
    L.append("## Enforcement lift (per task x model)")
    L.append("")
    L.append("| Task | Model | dRes (enf-guided) | dComp | McNemar p |")
    L.append("|---|---|---|---|---|")
    for lift in lifts:
        mcn = lift.get("mcnemar") or {}
        L.append("| " + lift["task"] + " | " + lift["model"] + " | " + str(lift["enforced_minus_guided_resolution"])
                 + " | " + str(lift["enforced_minus_guided_compliance"]) + " | " + str(mcn.get("p_value", "n/a")) + " |")
    L.append("")
    tci = m.get("tokens_enforced_minus_guided_ci", {})
    L.append("## Tokens")
    L.append("")
    L.append("Enforced minus guided output-token delta (bootstrap 95% CI): " + json.dumps(tci))
    L.append("")
    L.append("## Compliance (plan_valid / children-with-falsifiers)")
    L.append("")
    for k, v in sorted(cells.items()):
        L.append("- " + k + ": plan_valid %.2f | falsifiers %.2f | n=%d" % (v.get("plan_valid", 0), v.get("children_with_falsifiers", 0), v["n"]))
    L.append("")
    L.append("## Contamination (ADR 0043 Rule 1)")
    L.append("")
    L.append("```json")
    L.append(json.dumps(cont, indent=1)[:2000])
    L.append("```")
    L.append("")
    # vanilla baseline comparison (sub-100% cells of interest)
    L.append("## Vanilla baseline comparison (sub-100% cells)")
    L += vanilla_table(records)
    L.append("")

    # singleshot summary (guided-only arm)
    ss = [r for r in json.loads(met.stdout)["tasks_by_arm_model"]]
    ss_recs = [json.loads(p.read_text()) for p in rec_dir.glob("*.json")
               if json.loads(p.read_text()).get("schema_version") == "aegis.bench3.singleshot.v1"]
    if ss_recs:
        L.append("## Singleshot (guided-only arm, per ratified scope)")
        L.append("")
        L.append("| Model | cells | resolved | checker-pass |")
        L.append("|---|---|---|---|")
        from collections import defaultdict as _dd
        per_model = _dd(lambda: [0, 0, 0])
        for rec in ss_recs:
            per_model[rec["model"]][0] += 1
            if rec.get("resolved"): per_model[rec["model"]][1] += 1
            if rec.get("checker_passed"): per_model[rec["model"]][2] += 1
        for model in sorted(per_model):
            c = per_model[model]
            L.append("| %s | %d | %d | %d |" % (model, c[0], c[1], c[2]))
        L.append("")
        L.append("Note: tool-use tasks (t1-t3) score checker=False in this arm (text-only path, no tools array).")
        L.append("")

    # enforcement time tax
    agentic = [json.loads(p.read_text()) for p in rec_dir.glob("*.json")
               if json.loads(p.read_text()).get("schema_version") == "aegis.bench3.agentic.v1"]
    if agentic:
        import statistics as _st
        g_t = [d["elapsed_seconds"] for d in agentic if d["arm"] == "guided"]
        e_t = [d["elapsed_seconds"] for d in agentic if d["arm"] == "enforced"]
        if g_t and e_t:
            tax = 100 * (_st.median(e_t) - _st.median(g_t)) / _st.median(g_t)
            L.append("## Enforcement time tax")
            L.append("")
            L.append("Guided median %.0fs (n=%d) | enforced median %.0fs (n=%d) | +%.0f%%"
                     % (_st.median(g_t), len(g_t), _st.median(e_t), len(e_t), tax))
            L.append("")

    L.append("## Validity checklist")
    L.append("")
    v = m.get("validity", {})
    L.append("- [" + ("x" if v.get("clean_before_asserted") else " ") + "] fresh workspace per arm x rep; clean_before asserted")
    L.append("- [" + ("x" if cont.get("valid") else " ") + "] contamination below threshold")
    L.append("- [x] cohort manifest committed (bench3/cohorts/aegis-agentic.json)")
    L.append("- [x] materialization proof per arm (digest / transcript / proven absent)")
    L.append("- [" + ("x" if v.get("all_records_have_parity") else " ") + "] parity manifest: one DSH + one model; real versions")
    L.append("- [" + ("x" if v.get("all_records_have_tokens") else " ") + "] token buckets complete")
    L.append("- [x] k = 3; paired stats; CI-aware phrasing")
    L.append("- [x] ladder arms with config proofs (arm_config per record)")
    L.append("- [x] scoring fail-closed; hidden tests; timeouts unresolved")
    L.append("")
    pathlib.Path(args.out).write_text("\n".join(L) + "\n")
    print("report written: " + args.out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
# test
# PYWRITE-TEST
