#!/usr/bin/env python3
"""Build the aggregate cost, success, and LunaRoute capacity report."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import ECON, load_config, luna_capacity


def records() -> list[dict[str, Any]]:
    out = []
    for path in sorted((ECON / "results").glob("*.json")):
        try:
            row = json.loads(path.read_text())
        except Exception:
            continue
        if (
            row.get("schema_version") == "bench3.economics.v1"
            and row.get("condition", "base") == "base"
        ):
            out.append(row)
    return out


def aegis_records() -> list[dict[str, Any]]:
    out = []
    for path in sorted((ECON / "results").glob("*.json")):
        try:
            row = json.loads(path.read_text())
        except Exception:
            continue
        if (
            row.get("schema_version") == "bench3.economics.v1"
            and row.get("condition") == "aegis_retry"
        ):
            out.append(row)
    return out


def aegis_enforced_records() -> list[dict[str, Any]]:
    out = []
    for path in sorted((ECON / "results").glob("*.json")):
        try:
            row = json.loads(path.read_text())
        except Exception:
            continue
        if (
            row.get("schema_version") == "bench3.economics.v1"
            and row.get("condition") == "aegis_enforced_retry"
        ):
            out.append(row)
    return out


def agentic_records() -> list[dict[str, Any]]:
    out = []
    for path in sorted((ECON / "agentic_results").glob("*.json")):
        try:
            row = json.loads(path.read_text())
        except Exception:
            continue
        if (
            row.get("schema_version") == "bench3.economics.agentic.v1"
            and row.get("condition", "base") == "base"
        ):
            out.append(row)
    return out


def money(value: float | None) -> str:
    if value is None:
        return "—"
    if value < 0.01:
        return "$%.6f" % value
    if value < 1000:
        return "$%.3f" % value
    return "${:,.2f}".format(value)


def count(value: float) -> str:
    if value >= 1e9:
        return "%.2fB" % (value / 1e9)
    if value >= 1e6:
        return "%.1fM" % (value / 1e6)
    return "{:,.0f}".format(value)


def attempt_cost(row: dict[str, Any], config: dict[str, Any], active_days: float) -> float:
    if row["costs"]["billing"] != "subscription":
        return float(row["costs"]["cash_cost_usd"])
    route = config["routes"][row["route_id"]]
    capacity = luna_capacity(config, route["plan"], active_days)
    return row["usage"]["total_tokens"] / 1e6 * capacity["cost_per_million_tokens"]


def summarize(group: list[dict[str, Any]], config: dict[str, Any], active_days: float) -> dict[str, Any]:
    costs = [attempt_cost(row, config, active_days) for row in group]
    passes = sum(1 for row in group if row["grade"]["passed"])
    tokens = sum(row["usage"]["total_tokens"] for row in group)
    total_cost = sum(costs)
    return {
        "runs": len(group),
        "passes": passes,
        "pass_rate": passes / len(group) if group else 0.0,
        "tokens": tokens,
        "total_cost": total_cost,
        "cost_per_pass": total_cost / passes if passes else None,
        "cost_per_100k_attempts": total_cost / len(group) * 100_000 if group else None,
        "cost_per_100k_successes": total_cost / passes * 100_000 if passes else None,
        "cost_per_million": total_cost / tokens * 1e6 if tokens else None,
        "median_seconds": statistics.median(row["elapsed_seconds"] for row in group) if group else None,
    }


def multiple(value: float | None) -> str:
    if value is None:
        return "—"
    if value < 100:
        return "%.1f×" % value
    if value < 10_000:
        return "%.0f×" % value
    return "%.1fK×" % (value / 1000)


def build_report(
    rows: list[dict[str, Any]], active_days: float,
    agent_rows: list[dict[str, Any]] | None = None,
    aegis_rows: list[dict[str, Any]] | None = None,
    aegis_enforced_rows: list[dict[str, Any]] | None = None,
) -> str:
    config = load_config()
    capacity = luna_capacity(config, "lunaroute-teams-10-40", active_days)
    by_route: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_route[row["route_id"]].append(row)
    route_summaries = {
        route_id: summarize(group, config, active_days)
        for route_id, group in by_route.items()
    }
    task_order = [
        "reasoning/r1_tiling", "reasoning/r2_expectedflips", "reasoning/r3_die_expected",
        "reasoning/r4_catalan", "tool-use/t1_orchestrate", "tool-use/t2_toolselect",
        "tool-use/t3_inventory",
    ]
    task_routes = [
        "ds41-lunaroute", "glm53-lunaroute", "glm53-flash-lunaroute",
        "muse-spark-open-lunaroute", "ds41-openrouter-floor",
        "dspro-openrouter-floor", "gpt6-luna-direct", "ds41-openrouter",
        "dspro-openrouter", "gpt61-sol-direct", "claude-haiku55-openrouter",
        "claude-sonnet55-openrouter", "claude-opus55-openrouter",
        "gpt6-astra-direct", "claude-fable51-openrouter",
    ]
    short_names = {
        "ds41-lunaroute": "DS LunaRoute",
        "glm53-lunaroute": "GLM 5.3 LunaRoute",
        "glm53-flash-lunaroute": "GLM 5.3 Flash LunaRoute",
        "muse-spark-open-lunaroute": "Muse LunaRoute",
        "ds41-openrouter-floor": "DS OR price-first",
        "dspro-openrouter-floor": "DS Pro OR price-first",
        "gpt6-luna-direct": "GPT-6 Luna",
        "ds41-openrouter": "DS OR default",
        "dspro-openrouter": "DS Pro OR default",
        "gpt61-sol-direct": "GPT-6.1 Sol",
        "claude-haiku55-openrouter": "Claude Haiku",
        "claude-sonnet55-openrouter": "Claude Sonnet",
        "claude-opus55-openrouter": "Claude Opus",
        "gpt6-astra-direct": "GPT-6 Astra",
        "claude-fable51-openrouter": "Claude Fable",
    }
    by_task_route: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task_route[(row["task"], row["route_id"])].append(row)

    lines = [
        "# Economics of 100,000 tasks",
        "",
        "Catalog date: `%s`. Completed objective runs: **%d**." % (config["catalog_as_of"], len(rows)),
        "",
        "The main unit is one task. All costs below are scaled to 100,000 attempts or 100,000 successful tasks.",
        "",
        "## Task economics",
        "",
        "Each cell shows `passes/runs; cost per 100,000 successful tasks`. A zero-pass cell shows the cost per 100,000 attempts and states that the successful-task cost is undefined.",
        "",
        "The three tool rows are one-shot tool-plan tasks. The harness did not execute tool calls or return tool results.",
        "",
        "| Task | " + " | ".join(short_names[route_id] for route_id in task_routes) + " |",
        "|---|" + "---:|" * len(task_routes),
    ]
    for task in task_order:
        cells = []
        for route_id in task_routes:
            summary = summarize(by_task_route[(task, route_id)], config, active_days)
            if summary["passes"]:
                cells.append(
                    "%d/%d; %s / 100K successes" % (
                        summary["passes"], summary["runs"],
                        money(summary["cost_per_100k_successes"]),
                    )
                )
            else:
                cells.append(
                    "0/%d; no success (%s / 100K attempts)" % (
                        summary["runs"], money(summary["cost_per_100k_attempts"]),
                    )
                )
        lines.append("| %s | %s |" % (task, " | ".join(cells)))

    lines.extend([
        "",
        "## Route aggregate",
        "",
        "This table combines both effort levels and all seven tasks. The tool rows still use the one-shot tool-plan contract.",
        "",
        "| Route | Passes | Pass rate | Cost / 100K attempts | Cost / 100K successes | Median seconds |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    ordered_routes = sorted(
        route_summaries,
        key=lambda route_id: route_summaries[route_id]["cost_per_100k_successes"] or float("inf"),
    )
    for route_id in ordered_routes:
        summary = route_summaries[route_id]
        route = config["routes"][route_id]
        lines.append(
            "| %s | %d/%d | %.0f%% | %s | %s | %.1f |"
            % (
                route["display"], summary["passes"], summary["runs"], summary["pass_rate"] * 100,
                money(summary["cost_per_100k_attempts"]),
                money(summary["cost_per_100k_successes"]), summary["median_seconds"],
            )
        )

    lines.extend([
        "",
        "## Catalog price points",
        "",
        "List prices are USD per one million tokens. OpenRouter cash purchases add the configured 5.5% credit fee.",
        "",
        "| Model and route | Input | Output | Bench status |",
        "|---|---:|---:|---|",
        "| DeepSeek V4.1 Flash — LunaRoute | $0.004167 allocated per 1M total | $0.004167 allocated per 1M total | Tested |",
        "| GLM 5.3 — LunaRoute | $0.004167 allocated per 1M total | $0.004167 allocated per 1M total | Tested |",
        "| GLM 5.3 Flash — LunaRoute | $0.004167 allocated per 1M total | $0.004167 allocated per 1M total | Tested |",
        "| Muse Spark Open — LunaRoute | $0.004167 allocated per 1M total | $0.004167 allocated per 1M total | Tested |",
        "| GPT-6 Luna — OpenAI API | $0.10 | $0.50 | Tested |",
        "| Claude Haiku 5.5 — OpenRouter | $0.10 | $0.50 | Tested |",
        "| DeepSeek V4.1 Flash — OpenRouter | $0.15 | $0.60 | Tested |",
        "| DeepSeek V4 Pro 0813 — OpenRouter | $0.66 | $1.98 | Tested: default and price-first |",
        "| GPT-6.1 Sol — OpenAI API | $2.00 | $10.00 | Tested |",
        "| Claude Sonnet 5.5 — OpenRouter | $2.00 | $10.00 | Tested |",
        "| Claude Opus 5.5 — OpenRouter | $4.00 | $20.00 | Tested |",
        "| GPT-6 Astra — OpenAI API | $10.00 | $50.00 | Tested |",
        "| Claude Fable 5.1 — OpenRouter | $10.00 | $50.00 | Tested |",
        "",
        "DeepSeek and Claude runs use OpenRouter. GPT runs use the direct OpenAI Responses API.",
        "",
        "## LunaRoute catalog review",
        "",
        "The authenticated live main catalog has 13 entries. Background entries change scheduler priority; they are not separate quality models.",
        "",
        "| Catalog entry | Type | Benchmark decision |",
        "|---|---|---|",
        "| `deepseek-4.1-flash` | Chat | Already tested |",
        "| `glm-5.3` | Chat | Tested in main text benchmark |",
        "| `glm-5.3-flash` | Chat speed variant | Tested in main text benchmark |",
        "| `muse-spark-open` | Chat | Tested in main text benchmark |",
        "| Four `-background` chat entries | Lower-priority scheduler variants | Test once under sustained load |",
        "| `glm-5.3-vision` and `glm-5.3-vision-background` | Vision variants | Defer until image-input tasks exist |",
        "| `clef-flash` and `djev` | System One decision models | Use a separate routing and triage benchmark |",
        "| `whisper-large-v3` | Transcription | Exclude from this text benchmark |",
        "",
        "The separate LunaRoute catalogs contain four image models, four embedding models, and one reranker. They need task-specific benchmarks and are outside the current text and coding scope.",
    ])

    default_summary = route_summaries.get("ds41-openrouter")
    floor_summary = route_summaries.get("ds41-openrouter-floor")
    floor_saving = 0.0
    floor_latency = 0.0
    if default_summary and floor_summary:
        floor_saving = 1 - floor_summary["total_cost"] / default_summary["total_cost"]
        floor_latency = floor_summary["median_seconds"] / default_summary["median_seconds"] - 1
    lines.extend([
        "",
        "## Findings",
        "",
        "- Task type changes the economic result. Use task-level cost and success thresholds for route selection.",
        "- GPT-6 Luna, GPT-6.1 Sol, and GPT-6 Astra passed all eight reasoning runs.",
        "- GLM 5.3 Flash, Claude Sonnet 5.5, Claude Opus 5.5, and Claude Fable 5.1 each completed 12 of 14 one-shot runs. This is the highest aggregate result in the present data.",
        "- GPT-6 Luna, GPT-6.1 Sol, and GPT-6 Astra failed all six one-shot tool-plan runs. The harness did not run a real tool loop, so this is not a general tool-use result.",
        "- Across all 61 graded base failures, the enforced Aegis retry recovered 18 tasks. All 61 evidence journals verified.",
        "- OpenRouter price-first routing cut observed DeepSeek cash cost by %.0f%% and changed median latency by %+.0f%% against default routing." % (
            floor_saving * 100, floor_latency * 100
        ),
        "- In the objective scale, OpenRouter default routing used six upstream providers. Price-first routing used two. These runs use provider-reported cost.",
        "- DeepSeek Pro default completed 10 of 14 base runs. Price-first completed 9 of 14. Price-first reduced aggregate cash cost, but it also reduced the observed pass count.",
        "",
        "## LunaRoute accounting note",
        "",
        "The fixed plan is $500 per month. The supplied full-capacity assumption is 4 billion reported tokens per 24 hours for %.0f days. This gives %.1f billion monthly tokens and an allocated cost of $%.6f per one million total tokens." % (
            active_days, capacity["monthly_tokens"] / 1e9, capacity["cost_per_million_tokens"],
        ),
        "",
        "LunaRoute has zero marginal cash cost for an included request. The task tables use allocated plan cost so the route remains comparable with token-billed routes.",
    ])

    aegis_rows = aegis_rows or []
    if aegis_rows:
        base_by_key = {
            (row["route_id"], row["task"], row["effort"], row["repetition"]): row
            for row in rows
        }
        by_aegis_route: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in aegis_rows:
            by_aegis_route[row["route_id"]].append(row)
        lines.extend([
            "",
            "## Aegis Method Lite failure retries",
            "",
            "A base failure triggers one paired retry with the exact Aegis Method Lite payload in the system prompt. Base and retry results remain separate.",
            "",
            "| Route | Retries | Recovered | Recovery rate | Failed-base tokens | Aegis tokens | Incremental cost / 100K retries |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ])
        for route_id, guided_group in sorted(by_aegis_route.items()):
            paired = []
            for guided in guided_group:
                key = (route_id, guided["task"], guided["effort"], guided["repetition"])
                base = base_by_key.get(key)
                if base:
                    paired.append((base, guided))
            recovered = sum(1 for _base, guided in paired if guided["grade"].get("passed"))
            base_tokens = sum(base["usage"]["total_tokens"] for base, _guided in paired)
            guided_tokens = sum(guided["usage"]["total_tokens"] for _base, guided in paired)
            guided_cost = sum(attempt_cost(guided, config, active_days) for _base, guided in paired)
            cost_per_100k = guided_cost / len(paired) * 100_000 if paired else None
            lines.append(
                "| %s | %d | %d | %.0f%% | %s | %s | %s |"
                % (
                    config["routes"][route_id]["display"], len(paired), recovered,
                    recovered / len(paired) * 100 if paired else 0,
                    count(base_tokens), count(guided_tokens), money(cost_per_100k),
                )
            )
        lines.extend([
            "",
            "The Aegis retry is an intervention result. It does not replace the base score. For one-shot tasks, the payload is prompt guidance without file or shell enforcement.",
        ])

    aegis_enforced_rows = aegis_enforced_rows or []
    if aegis_enforced_rows:
        base_by_key = {
            (row["route_id"], row["task"], row["effort"], row["repetition"]): row
            for row in rows
        }
        by_enforced_route: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in aegis_enforced_rows:
            by_enforced_route[row["route_id"]].append(row)
        recovered_total = sum(
            1 for row in aegis_enforced_rows if row["grade"].get("passed") is True
        )
        valid_journals = sum(
            1
            for row in aegis_enforced_rows
            if row.get("aegis", {}).get("evidence", {}).get("verify", {}).get("valid") is True
        )
        lines.extend([
            "",
            "## Enforced Aegis Method failure retries",
            "",
            "The provider-neutral benchmark adapter keeps each original provider route. It validates `.am` plan and child contracts before the request, runs the existing task checker as the falsifier, validates completion and closure with Aegis Method 0.3.0, and writes an isolated signed Aegis evidence journal.",
            "",
            "This is a benchmark-native reimplementation. It does not claim native Codex-hook or Claude-hook transport equivalence.",
            "",
            "Recovered **%d of %d** failed base tasks. **%d of %d** signed journals verified." % (
                recovered_total,
                len(aegis_enforced_rows),
                valid_journals,
                len(aegis_enforced_rows),
            ),
            "",
            "| Route | Retries | Recovered | Recovery rate | Failed-base tokens | Enforced tokens | Incremental cost / 100K retries |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ])
        for route_id, enforced_group in sorted(by_enforced_route.items()):
            paired = []
            for enforced in enforced_group:
                key = (route_id, enforced["task"], enforced["effort"], enforced["repetition"])
                base = base_by_key.get(key)
                if base:
                    paired.append((base, enforced))
            recovered = sum(
                1 for _base, enforced in paired if enforced["grade"].get("passed")
            )
            base_tokens = sum(base["usage"]["total_tokens"] for base, _enforced in paired)
            enforced_tokens = sum(
                enforced["usage"]["total_tokens"] for _base, enforced in paired
            )
            enforced_cost = sum(
                attempt_cost(enforced, config, active_days) for _base, enforced in paired
            )
            cost_per_100k = enforced_cost / len(paired) * 100_000 if paired else None
            lines.append(
                "| %s | %d | %d | %.0f%% | %s | %s | %s |"
                % (
                    config["routes"][route_id]["display"],
                    len(paired),
                    recovered,
                    recovered / len(paired) * 100 if paired else 0,
                    count(base_tokens),
                    count(enforced_tokens),
                    money(cost_per_100k),
                )
            )
        lines.extend([
            "",
            "A failed falsifier leaves the child open. The completion and closure gates block the success claim. A passed retry closes only when the plan, completion, closure, and evidence-journal checks all pass.",
        ])

    agent_rows = agent_rows or []
    if agent_rows:
        lines.extend([
            "",
            "## Sandboxed coding pilot",
            "",
            "This pilot uses one coding task and one high-effort run per route. It is separate from the %d-run objective scale." % len(rows),
            "",
            "| Route | Status | Hidden tests | Calls | Reported tokens | Cost / 100K attempts | Cost source | Seconds |",
            "|---|---|---:|---:|---:|---:|---|---:|",
        ])
        for row in sorted(agent_rows, key=lambda item: item["route_id"]):
            route = config["routes"][row["route_id"]]
            if row["usage"]["calls"] == 0:
                status = "Harness failure"
            elif not row.get("valid", False):
                status = "Invalid"
            else:
                status = "Pass" if row["grade"]["passed"] else "Fail"
            tests_failed = row["grade"].get("tests_failed")
            hidden = "—" if tests_failed is None else "%d/4 passed" % (4 - tests_failed)
            cost = attempt_cost(row, config, active_days)
            cost_source = row["cost_source"]
            if row["costs"]["billing"] == "subscription":
                cost_source = "full-capacity allocation"
            lines.append(
                "| %s | %s | %s | %d | %d | %s | %s | %.1f |"
                % (
                    route["display"], status, hidden, row["usage"]["calls"],
                    row["usage"]["total_tokens"], money(cost * 100_000), cost_source,
                    row["elapsed_seconds"],
                )
            )
        lines.extend([
            "",
            "The pilot uses an operating-system file sandbox. The sandbox blocks the source benchmark, hidden tests, and reference files during the model run.",
            "Earlier pilot attempts exposed those files. They are marked invalid and excluded from this table.",
            "All four routes failed the same concurrent audit consistency test. Each route passed the other three hidden tests.",
            "Cost per 100,000 successful coding tasks is undefined because no route passed all four hidden tests.",
        ])

    lines.extend([
        "",
        "## Bench expansion order",
        "",
        "### Testable — repair the tool journey",
        "",
        "- Promise: one real tool task runs end to end on each current route.",
        "- Journey: prompt, tool call, deterministic tool result, model continuation, final answer, grade, and total cost.",
        "- Threshold: 100% harness completion with no provider-format exception and a reconciled cost record.",
        "- Falsifier: the providers need different task contracts that cannot be normalized.",
        "- Rule: stop model expansion if this gate fails. Repair the harness first.",
        "",
        "### Usable — add the price ladder",
        "",
        "- Repeat all 15 active routes three times.",
        "- Keep DeepSeek and Claude on OpenRouter. Keep GPT on the direct OpenAI Responses API.",
        "- Run LunaRoute background variants in a separate sustained-load slice.",
        "- Run three repetitions on representative reasoning, real tool-loop, and coding tasks.",
        "- Report cost per 100,000 attempts, pass rate, cost per 100,000 successes, and latency.",
        "- Reconcile OpenRouter provider receipts and refusals before using fine cost differences for a route decision.",
        "",
        "### Lovable — select a route for a workload",
        "",
        "- Let the user set a task mix, minimum success rate, and maximum latency.",
        "- Return the lowest-cost route that meets the threshold.",
        "- Continue only after users repeat this decision or prefer it to the current spreadsheet workflow.",
        ])

    lines.extend([
        "",
        "## Interpretation limits",
        "",
        "- LunaRoute allocation assumes sustained full use: 120 billion reported tokens per 30-day month.",
        "- The LunaRoute token basis assumes reported input plus output tokens. Reconcile this with the plan ledger.",
        "- OpenRouter cash cost applies the 5.5% Standard credit-purchase fee. The fee is not an inference-line item.",
        "- The earlier Aegis Method Lite arm covered 41 failures and recovered nine. The enforced arm covered all 61 failures and recovered 18. These are single stochastic retries, not a causal estimate.",
        "- The OpenRouter price-first coding cost is an advertised-floor estimate. The generation receipt endpoint did not return the per-call receipts.",
        "- One uncapped OpenRouter price-first long-task request was stopped after more than three minutes. It has no usage receipt and is not in the totals.",
        "- The objective set has one low-effort and one high-effort run per route and task. This is not enough for a stable quality or latency rank.",
        "- The benchmark measures this task set and harness. It does not prove a general model rank.",
        "",
    ])
    return "\n".join(lines)


def write_scale_csv(rows: list[dict[str, Any]], active_days: float, path: Path) -> None:
    config = load_config()
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["route_id"], row["effort"])].append(row)
    fields = [
        "route_id", "display", "effort", "runs", "passes", "pass_rate",
        "total_tokens", "observed_cost_usd", "cost_per_pass_usd",
        "cost_per_100k_attempts_usd", "cost_per_100k_successes_usd",
        "blended_cost_per_million_total_tokens_usd", "median_seconds",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for (route_id, effort), group in sorted(grouped.items()):
            summary = summarize(group, config, active_days)
            writer.writerow({
                "route_id": route_id,
                "display": config["routes"][route_id]["display"],
                "effort": effort,
                "runs": summary["runs"],
                "passes": summary["passes"],
                "pass_rate": summary["pass_rate"],
                "total_tokens": summary["tokens"],
                "observed_cost_usd": summary["total_cost"],
                "cost_per_pass_usd": summary["cost_per_pass"],
                "cost_per_100k_attempts_usd": summary["cost_per_100k_attempts"],
                "cost_per_100k_successes_usd": summary["cost_per_100k_successes"],
                "blended_cost_per_million_total_tokens_usd": summary["cost_per_million"],
                "median_seconds": summary["median_seconds"],
            })


def write_task_csv(rows: list[dict[str, Any]], active_days: float, path: Path) -> None:
    config = load_config()
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["task"], row["route_id"])].append(row)
    fields = [
        "task", "task_contract", "route_id", "display", "runs", "passes",
        "pass_rate", "cost_per_100k_attempts_usd",
        "cost_per_100k_successes_usd", "median_seconds",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for (task, route_id), group in sorted(grouped.items()):
            summary = summarize(group, config, active_days)
            writer.writerow({
                "task": task,
                "task_contract": "one-shot tool plan" if task.startswith("tool-use/") else "reasoning answer",
                "route_id": route_id,
                "display": config["routes"][route_id]["display"],
                "runs": summary["runs"],
                "passes": summary["passes"],
                "pass_rate": summary["pass_rate"],
                "cost_per_100k_attempts_usd": summary["cost_per_100k_attempts"],
                "cost_per_100k_successes_usd": summary["cost_per_100k_successes"],
                "median_seconds": summary["median_seconds"],
            })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lunaroute-active-days", type=float, default=30)
    parser.add_argument("--out", default=str(ECON / "REPORT.md"))
    args = parser.parse_args()
    rows = records()
    report = build_report(
        rows,
        args.lunaroute_active_days,
        agentic_records(),
        aegis_records(),
        aegis_enforced_records(),
    )
    Path(args.out).write_text(report)
    write_scale_csv(rows, args.lunaroute_active_days, ECON / "SCALE.csv")
    write_task_csv(rows, args.lunaroute_active_days, ECON / "TASK_ECONOMICS.csv")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
