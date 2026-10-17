#!/usr/bin/env python3
"""Build the data block used by the local interactive HTML report."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from analyze import aegis_enforced_records, aegis_records, attempt_cost, records, summarize
from common import ECON, load_config
from analyze_toolloop import load_rows as toolloop_rows, report_data as toolloop_report_data, workflow_summary


ACTIVE_DAYS = 30.0

ROUTE_SPECS = [
    ("ds41-lunaroute", "DS 4.1 · Luna", "DeepSeek V4.1 Flash", "LunaRoute", "#3dd9d0"),
    ("glm53-lunaroute", "GLM 5.3", "GLM 5.3", "LunaRoute", "#7dd3fc"),
    ("glm53-flash-lunaroute", "GLM 5.3 Flash", "GLM 5.3 Flash", "LunaRoute", "#22c55e"),
    ("muse-spark-open-lunaroute", "Muse", "Muse Spark Open", "LunaRoute", "#f6c85f"),
    ("ds41-openrouter-floor", "DS 4.1 · OR floor", "DeepSeek V4.1 Flash", "OpenRouter · price-first", "#a78bfa"),
    ("dspro-openrouter-floor", "DS Pro · OR floor", "DeepSeek V4 Pro 0813", "OpenRouter · price-first", "#c084fc"),
    ("gpt6-luna-direct", "GPT-6 Luna", "GPT-6 Luna", "OpenAI API", "#34d399"),
    ("ds41-openrouter", "DS 4.1 · OR", "DeepSeek V4.1 Flash", "OpenRouter · default", "#4c7dff"),
    ("dspro-openrouter", "DS Pro · OR", "DeepSeek V4 Pro 0813", "OpenRouter · default", "#60a5fa"),
    ("gpt61-sol-direct", "GPT-6.1 Sol", "GPT-6.1 Sol", "OpenAI API", "#17b890"),
    ("claude-haiku55-openrouter", "Claude Haiku", "Claude Haiku 5.5", "OpenRouter", "#fb923c"),
    ("claude-sonnet55-openrouter", "Claude Sonnet", "Claude Sonnet 5.5", "OpenRouter", "#e98963"),
    ("claude-opus55-openrouter", "Claude Opus", "Claude Opus 5.5", "OpenRouter", "#f97316"),
    ("gpt6-astra-direct", "GPT-6 Astra", "GPT-6 Astra", "OpenAI API", "#ff6b78"),
    ("claude-fable51-openrouter", "Claude Fable", "Claude Fable 5.1", "OpenRouter", "#fdba74"),
]

TASK_SPECS = [
    ("reasoning/r1_tiling", "Long tiling proof", "reasoning"),
    ("reasoning/r2_expectedflips", "Expected flips", "reasoning"),
    ("reasoning/r3_die_expected", "Die expectation", "reasoning"),
    ("reasoning/r4_catalan", "Catalan count", "reasoning"),
    ("tool-use/t1_orchestrate", "Invoice workflow", "tool-loop"),
    ("tool-use/t2_toolselect", "Account unlock workflow", "tool-loop"),
    ("tool-use/t3_inventory", "Inventory workflow", "tool-loop"),
]


def main() -> int:
    config = load_config()
    base_rows = records()
    loop_base = toolloop_rows()
    loop_retries = toolloop_rows("aegis_enforced_retry")
    loop_complete = len(loop_base) == 90
    measured_rows = ([r for r in base_rows if not r["task"].startswith("tool-use/")] + loop_base
                     if loop_complete else base_rows)
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in measured_rows:
        grouped[(row["task"], row["route_id"])].append(row)

    routes = [
        {"id": route_id, "head": head, "name": name, "sub": sub, "color": color}
        for route_id, head, name, sub, color in ROUTE_SPECS
    ]
    tasks = []
    for task_id, name, category in TASK_SPECS:
        results = []
        for route_id, *_rest in ROUTE_SPECS:
            summary = summarize(grouped[(task_id, route_id)], config, ACTIVE_DAYS)
            results.append({
                "attempt": summary["cost_per_100k_attempts"] / 100
                if summary["cost_per_100k_attempts"] is not None else None,
                "success": summary["cost_per_100k_successes"] / 100
                if summary["cost_per_100k_successes"] is not None else None,
                "passRate": round(summary["pass_rate"] * 100, 6),
                "latency": summary["median_seconds"],
                "passes": summary["passes"],
                "runs": summary["runs"],
            })
        with_aegis = []
        if category == "tool-loop" and loop_complete:
            for route_id, *_rest in ROUTE_SPECS:
                s = workflow_summary(grouped[(task_id, route_id)], loop_retries, config)
                with_aegis.append({"attempt": s["cost100kAttempts"] / 100 if s["cost100kAttempts"] is not None else None,
                                   "success": s["cost100kSuccesses"] / 100 if s["cost100kSuccesses"] is not None else None,
                                   "passRate": s["passRate"], "latency": s["latency"],
                                   "passes": s["passes"], "runs": s["runs"]})
        tasks.append({"category": category if loop_complete or category == "reasoning" else "tool-plan",
                      "name": name, "code": task_id, "results": results,
                      "withAegis": with_aegis or results})

    base_by_key = {
        (row["route_id"], row["task"], row["effort"], row["repetition"]): row
        for row in base_rows
    }
    enforced_rows = aegis_enforced_records()
    lite_rows = aegis_records()
    lite_by_key = {
        (row["route_id"], row["task"], row["effort"], row["repetition"]): row
        for row in lite_rows
    }
    enforced_by_route: dict[str, list[dict]] = defaultdict(list)
    for row in enforced_rows:
        enforced_by_route[row["route_id"]].append(row)
    enforced_routes = []
    for route_id, head, name, sub, _color in ROUTE_SPECS:
        group = enforced_by_route[route_id]
        if not group:
            continue
        pairs = []
        for row in group:
            key = (route_id, row["task"], row["effort"], row["repetition"])
            if key in base_by_key:
                pairs.append((base_by_key[key], row))
        recovered = sum(1 for _base, row in pairs if row["grade"].get("passed") is True)
        total_cost = sum(attempt_cost(row, config, ACTIVE_DAYS) for _base, row in pairs)
        enforced_routes.append({
            "id": route_id,
            "head": head,
            "name": name,
            "sub": sub,
            "retries": len(pairs),
            "recovered": recovered,
            "recoveryRate": recovered / len(pairs) * 100 if pairs else 0,
            "baseTokens": sum(base["usage"]["total_tokens"] for base, _row in pairs),
            "enforcedTokens": sum(row["usage"]["total_tokens"] for _base, row in pairs),
            "extraCost100k": total_cost / len(pairs) * 100_000 if pairs else None,
        })
    overlap = []
    for row in enforced_rows:
        key = (row["route_id"], row["task"], row["effort"], row["repetition"])
        if key in lite_by_key:
            overlap.append((lite_by_key[key], row))
    enforced = {
        "retries": len(enforced_rows),
        "recovered": sum(1 for row in enforced_rows if row["grade"].get("passed") is True),
        "journalsValid": sum(
            1
            for row in enforced_rows
            if row.get("aegis", {}).get("evidence", {}).get("verify", {}).get("valid") is True
        ),
        "closuresAllowed": sum(
            1 for row in enforced_rows if row.get("aegis", {}).get("method_closed") is True
        ),
        "tokens": sum(row["usage"]["total_tokens"] for row in enforced_rows),
        "cashCost": sum(float(row["costs"]["cash_cost_usd"]) for row in enforced_rows),
        "allocatedCost": sum(
            float(row["costs"].get("capacity_allocated_cost_usd") or 0)
            for row in enforced_rows
        ),
        "overlap": {
            "runs": len(overlap),
            "liteRecovered": sum(1 for lite, _full in overlap if lite["grade"].get("passed") is True),
            "enforcedRecovered": sum(1 for _lite, full in overlap if full["grade"].get("passed") is True),
        },
        "routes": enforced_routes,
    }

    payload = {
        "catalogDate": config["catalog_as_of"],
        "baseRuns": len(base_rows),
        "routes": routes,
        "tasks": tasks,
        "aegisEnforced": enforced,
        "toolLoop": toolloop_report_data(),
        "toolLoopComplete": loop_complete,
    }
    from campaign_stats import project
    payload = project(payload)
    output = "window.REPORT_DATA = " + json.dumps(payload, separators=(",", ":")) + ";\n"
    path = ECON / "report_data.js"
    temporary = path.with_suffix(".js.tmp")
    temporary.write_text(output)
    temporary.replace(path)
    print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
