#!/usr/bin/env python3
"""Summarize complete tool workflows, including failure-only retry policy cost."""
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

from analyze import attempt_cost, records
from common import ECON, load_config


ROOT = ECON / "toolloop"


def load_rows(condition: str = "base") -> list[dict]:
    rows = []
    for path in sorted((ROOT / "results").glob("*.json")):
        row = json.loads(path.read_text())
        if row.get("schema_version") == "bench3.economics.toolloop.v1" and row.get("condition") == condition:
            rows.append(row)
    return rows


def key(row: dict) -> tuple:
    return row["route_id"], row["task"], row["effort"], row["repetition"]


def workflow_summary(base: list[dict], retries: list[dict], config: dict) -> dict:
    retry_map = {key(r): r for r in retries}
    successes = 0
    total_cost = 0.0
    latencies = []
    calls = 0
    tokens = 0
    used_retries = 0
    for row in base:
        retry = retry_map.get(key(row)) if row["grade"]["passed"] is False else None
        parts = [row] + ([retry] if retry else [])
        successes += bool(row["grade"]["passed"] or (retry and retry["grade"]["passed"]))
        used_retries += bool(retry)
        total_cost += sum(attempt_cost(p, config, 30.0) for p in parts)
        latencies.append(sum(p["elapsed_seconds"] for p in parts))
        calls += sum(p["usage"]["calls"] for p in parts)
        tokens += sum(p["usage"]["total_tokens"] for p in parts)
    return {
        "runs": len(base), "passes": successes, "retries": used_retries,
        "passRate": 100 * successes / len(base) if base else 0,
        "cost100kAttempts": 100_000 * total_cost / len(base) if base else None,
        "cost100kSuccesses": 100_000 * total_cost / successes if successes else None,
        "latency": statistics.median(latencies) if latencies else None,
        "meanCalls": calls / len(base) if base else None,
        "tokens": tokens, "totalCost": total_cost,
    }


def report_data() -> dict:
    config = load_config()
    base = load_rows()
    retries = load_rows("aegis_enforced_retry")
    old = [row for row in records() if row["task"].startswith("tool-use/")]
    routes = []
    for rid, route in config["routes"].items():
        if not route.get("enabled", True):
            continue
        group = [r for r in base if r["route_id"] == rid]
        if not group:
            continue  # A new route must not appear as a completed pilot route.
        old_group = [r for r in old if r["route_id"] == rid]
        routes.append({"id": rid, "name": route["display"],
                       "oldPasses": sum(bool(r["grade"]["passed"]) for r in old_group),
                       "oldRuns": len(old_group),
                       "toolErrors": sum(r["tool_errors"] for r in group),
                       "base": workflow_summary(group, [], config),
                       "withAegis": workflow_summary(group, retries, config)})
    return {
        "base": workflow_summary(base, [], config),
        "withAegis": workflow_summary(base, retries, config),
        "retries": len(retries),
        "recoveries": sum(bool(r["grade"]["passed"]) for r in retries),
        "journalsValid": sum(r["aegis"]["evidence"]["verify"].get("valid") is True for r in retries),
        "transportRestarts": sum(r.get("transport_recovery", {}).get("restarts", 0) for r in base + retries),
        "missingUsageReceipts": sum(r.get("transport_recovery", {}).get("missing_usage_receipts", 0) for r in base + retries),
        "routes": routes,
    }


def main() -> int:
    data = report_data()
    base = load_rows()
    retries = load_rows("aegis_enforced_retry")
    config = load_config()
    lines = [
        "# Executed tool workflows — 17 October 2026", "",
        f"Completed {len(base)} base workflows across 15 routes. "
        f"Passed {data['base']['passes']}. Ran {len(retries)} enforced Aegis failure retries; "
        f"recovered {data['recoveries']}.", "",
        "Each workflow executes local tools, returns each result to the model, and continues to a final answer. "
        "The grader replays the tool events and checks final fixture state. "
        "All model requests, including failed calls within a workflow and failure retries, contribute to cost.", "",
        "The old prompts requested a complete tool plan in one response. Two explicitly said no results would be returned. "
        "The new prompts request executed actions and require the model to obtain prices and account IDs from tools. "
        "These are different task contracts. The old scores do not measure real tool-loop ability.", "",
        "| Route | Old one-shot | Executed loop | After Aegis | Corrected tool errors | Model calls / workflow | Seconds (median) | Cost / 100K attempts | Cost / 100K successes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for route in data["routes"]:
        s = route["base"]
        a = route["withAegis"]
        cost_success = "undefined" if a["cost100kSuccesses"] is None else f"${a['cost100kSuccesses']:,.2f}"
        lines.append(f"| {route['name']} | {route['oldPasses']}/{route['oldRuns']} | {s['passes']}/{s['runs']} | "
                     f"{a['passes']}/{a['runs']} | {route['toolErrors']} | {a['meanCalls']:.1f} | {a['latency']:.1f} | "
                     f"${a['cost100kAttempts']:,.2f} | {cost_success} |")
    lines.extend(["", "Costs in the table include failure-only Aegis retries. LunaRoute uses the supplied full-capacity allocation. "
                  "Token-billed routes use the sum of each request's cost, including OpenRouter credit fees.", "",
                  "## Run contract", "",
                  "- Three tasks: invoice creation, account unlock and notification, and inventory order creation.",
                  "- One low-effort and one high-effort attempt per route and task.",
                  "- Maximum 12 model requests, 32 tool calls, and 4,096 output tokens per request.",
                  "- Independent calls may share a model response. The runtime executes calls in listed order and returns a result for each call.",
                  "- Tool errors return to the model. A model may correct an argument error within its budget. Prohibited support-tool attempts fail acceptance.",
                  "- OpenAI Responses uses previous_response_id and function_call_output. Chat routes retain assistant reasoning fields and tool_call_id.",
                  "- Aegis failure retries use fresh fixture state, the full method payload, frozen local contracts, the official method gates, and a signed journal.",
                  "- There is no real email, purchase, invoice, or account mutation outside the local fixture.",
                  "- These three small deterministic tasks establish harness behavior. They do not establish a broad model ranking.", ""])
    lines.extend([f"Provider connections required {data['transportRestarts']} fresh-state restarts. "
                  "Returned receipts from partial workflows are included in cost and token totals. "
                  f"The {data['missingUsageReceipts']} interrupted requests had no usage receipt, so their charges are unknown. "
                  "Latency includes completed model requests and known partial-request time; the lost-connection wait is not fully measured.", ""])
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "REPORT.md").write_text("\n".join(lines))
    (ROOT / "summary.json").write_text(json.dumps(data, indent=2) + "\n")
    with (ROOT / "TASK_ECONOMICS.csv").open("w", newline="") as stream:
        fields = ["route_id", "task", "effort", "base_passed", "final_passed", "retry_count",
                  "model_requests", "tool_calls", "total_tokens", "cost_per_100k_attempts_usd", "seconds"]
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        retry_map = {key(r): r for r in retries}
        for row in base:
            retry = retry_map.get(key(row))
            parts = [row] + ([retry] if retry else [])
            summary = workflow_summary([row], retries, config)
            writer.writerow({"route_id": row["route_id"], "task": row["task"], "effort": row["effort"],
                             "base_passed": row["grade"]["passed"], "final_passed": summary["passes"] == 1,
                             "retry_count": summary["retries"], "model_requests": sum(p["usage"]["calls"] for p in parts),
                             "tool_calls": sum(p["tool_calls"] for p in parts), "total_tokens": summary["tokens"],
                             "cost_per_100k_attempts_usd": summary["cost100kAttempts"], "seconds": summary["latency"]})
    print(json.dumps({k:v for k,v in data.items() if k != "routes"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
