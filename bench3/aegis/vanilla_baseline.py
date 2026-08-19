"""Vanilla baseline comparison for the Aegis report (ADR 0043 worked comparison).

Reads the original bench3 agentic results (results/results.csv) and cross-references
the Aegis guided/enforced records so the sub-100% vanilla cells are the cells of
interest: does the Aegis method (guided or enforced) move the pass rate?
"""
from __future__ import annotations

import csv
import json
import pathlib
from collections import defaultdict

AEGIS = pathlib.Path(__file__).resolve().parent


def vanilla_baselines() -> dict:
    """(model, task-basename) -> {"passed": n, "trials": n} from original results.csv."""
    out = defaultdict(lambda: {"passed": 0, "trials": 0})
    csv_path = AEGIS.parent / "results" / "results.csv"
    if not csv_path.exists():
        return {}
    for row in csv.DictReader(open(csv_path)):
        if row.get("mode") != "agentic":
            continue
        task = row["task"].split("/")[-1]
        key = (row["arm"], task)
        out[key]["trials"] += 1
        out[key]["passed"] += int(row.get("passed") == "1")
    return dict(out)


def vanilla_table(records) -> list:
    """Markdown lines comparing vanilla baselines vs aegis guided/enforced records."""
    van = vanilla_baselines()
    if not van:
        return ["(no results/results.csv baseline found)", ""]
    aegis = defaultdict(lambda: {"guided": [], "enforced": []})
    for p in records:
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if d.get("schema_version") != "aegis.bench3.agentic.v1":
            continue
        task = d["task"].split("/")[-1]
        aegis[(d["model"], task)][d["arm"]].append(bool(d.get("resolution", {}).get("passed")))
    lines = ["", "| Model | Task | vanilla | guided | enforced |", "|---|---|---|---|---|"]
    for (model, task), v in sorted(van.items()):
        rate = f"{v['passed']}/{v['trials']}" + (" (sub-100%)" if v['passed'] < v['trials'] else "")
        g = aegis.get((model, task), {}).get("guided", [])
        e = aegis.get((model, task), {}).get("enforced", [])
        gs = f"{sum(g)}/{len(g)}" if g else "-"
        es = f"{sum(e)}/{len(e)}" if e else "-"
        lines.append(f"| {model} | {task} | {rate} | {gs} | {es} |")
    lines.append("")
    lines.append("Cells where vanilla was sub-100% are the cells of interest: does the Aegis method")
    lines.append("(guided or enforced) move the pass rate? n is small (k=3, vanilla 1-3 trials);")
    lines.append("direction-only, no causal claim per the honesty boundary.")
    return lines
