"""Statistics and report projection for the ten-repeat objective campaign."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from common import ECON
from aegis_enforced_retry import json_write


CURRENT = ECON / "campaigns" / "current.json"


def campaign_root() -> Path | None:
    if not CURRENT.exists():
        return None
    return Path(json.loads(CURRENT.read_text())["root"])


def read_records(root: Path) -> tuple[list[dict], list[dict]]:
    base, retries = [], []
    for folder in (root / "reasoning" / "results", root / "toolloop" / "results"):
        for path in sorted(folder.glob("*.json")):
            row = json.loads(path.read_text())
            (base if row.get("condition", "base") == "base" else retries).append(row)
    return base, retries


def row_key(row: dict) -> tuple:
    return row["route_id"], row["task"], row["effort"], row["repetition"]


def cost(row: dict) -> float:
    values = row["costs"]
    if values["billing"] == "subscription":
        return float(values["capacity_allocated_cost_usd"])
    return float(values["cash_cost_usd"])


def wilson(successes: int, total: int) -> list[float] | None:
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z*z / total
    center = (p + z*z / (2*total)) / denominator
    half = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / denominator
    return [max(0, center-half)*100, min(1, center+half)*100]


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = fraction * (len(ordered)-1)
    lo, hi = math.floor(index), math.ceil(index)
    return ordered[lo] + (ordered[hi]-ordered[lo])*(index-lo)


@lru_cache(maxsize=8192)
def cost_intervals(samples: tuple[tuple[float, bool], ...]) -> dict:
    if len(samples) < 2:
        return {"attempt": None, "success": None}
    seed = int(hashlib.sha256(repr(samples).encode()).hexdigest()[:16], 16)
    rng = random.Random(seed)
    attempt, success = [], []
    zero_success = 0
    for _ in range(1000):
        draw = [samples[rng.randrange(len(samples))] for _ in samples]
        amount = sum(x[0] for x in draw)
        count = sum(x[1] for x in draw)
        attempt.append(amount / len(draw)*100_000)
        if count:
            success.append(amount / count*100_000)
        else:
            zero_success += 1
    return {
        "attempt": [percentile(attempt, .025), percentile(attempt, .975)],
        "success": ([percentile(success, min(1, .025*1000/len(success))),
                     None if zero_success >= 25 else percentile(success, min(1, .975*1000/len(success)))]
                    if success else None),
    }


def summarize(rows: list[dict], retries: list[dict], *, intervals: bool = True) -> dict:
    retry_map = {row_key(r): r for r in retries}
    samples = []
    latency = []
    calls = 0
    for row in rows:
        retry = retry_map.get(row_key(row)) if not row["grade"]["passed"] else None
        parts = [row] + ([retry] if retry else [])
        passed = bool(row["grade"]["passed"] or (retry and retry["grade"]["passed"]))
        samples.append((sum(cost(p) for p in parts), passed))
        latency.append(sum(p["elapsed_seconds"] for p in parts))
        calls += sum(p["usage"].get("calls", 1) for p in parts)
    n, passes = len(samples), sum(x[1] for x in samples)
    amount = sum(x[0] for x in samples)
    ci = cost_intervals(tuple(samples)) if intervals else {"attempt": None, "success": None}
    return {
        "runs": n, "passes": passes, "passRate": 100*passes/n if n else 0,
        "passCI": wilson(passes, n),
        # The report's existing chart stores dollar values per 1,000 and scales
        # them by 100 for display per 100,000 workflows.
        "attempt": amount/n*1000 if n else None,
        "success": amount/passes*1000 if passes else None,
        "attemptCI100k": ci["attempt"], "successCI100k": ci["success"],
        "latency": statistics.median(latency) if latency else None,
        "meanCalls": calls/n if n else None,
        "retryCount": sum(row_key(r) in retry_map and not r["grade"]["passed"] for r in rows),
    }


def project(payload: dict) -> dict:
    root = campaign_root()
    if root is None:
        return payload
    manifest = json.loads((root / "manifest.json").read_text())
    status = json.loads((root / "status.json").read_text())
    base, retries = read_records(root)
    grouped = defaultdict(list)
    for row in base:
        grouped[(row["task"], row["route_id"], row["effort"])].append(row)
    tasks = []
    details = []
    for task in payload["tasks"]:
        task = {**task}
        by_effort = {}
        for effort in ["all", "low", "high"]:
            primary, policy = [], []
            for route in payload["routes"]:
                group = (grouped[(task["code"], route["id"], "low")] + grouped[(task["code"], route["id"], "high")]
                         if effort == "all" else grouped[(task["code"], route["id"], effort)])
                a = summarize(group, [])
                b = summarize(group, retries)
                primary.append(a)
                policy.append(b)
                if effort != "all":
                    details.append({"route_id": route["id"], "task": task["code"], "effort": effort,
                                    "base": a, "withAegis": b})
            by_effort[effort] = {"base": primary, "withAegis": policy}
        task.update(results=by_effort["all"]["base"], withAegis=by_effort["all"]["withAegis"],
                    byEffort=by_effort)
        tasks.append(task)
    configs = []
    for route in payload["routes"]:
        for effort in ["low", "high"]:
            group = [r for r in base if r["route_id"] == route["id"] and r["effort"] == effort]
            configs.append({"route_id": route["id"], "name": route["name"], "vendor": route["sub"],
                            "effort": effort, "base": summarize(group, [], intervals=False),
                            "withAegis": summarize(group, retries, intervals=False),
                            "plannedTasks": len(manifest["tasks"])*manifest["repetitions"]})
    retry_map = {row_key(r): r for r in retries}
    pending = sum(not r["grade"]["passed"] and row_key(r) not in retry_map for r in base)
    campaign = {
        **status, "root": str(root), "plannedBase": manifest["planned_base"],
        "repetitions": manifest["repetitions"], "baseRuns": len(base),
        "basePasses": sum(bool(r["grade"]["passed"]) for r in base),
        "retries": len(retries), "recoveries": sum(bool(r["grade"]["passed"]) for r in retries),
        "pendingRetries": pending,
        "cashCost": sum(float(r["costs"]["cash_cost_usd"]) for r in base+retries),
        "allocatedCost": sum(float(r["costs"].get("capacity_allocated_cost_usd") or 0) for r in base+retries),
        "configs": configs,
        "statistics": "95% Wilson pass intervals; 1,000-draw percentile bootstrap for task cost. Pilot excluded. Repeated fixed tasks do not establish general model quality.",
    }
    payload.update(tasks=tasks, campaign=campaign)
    json_write(root / "summary.json", {"campaign": campaign, "cells": details})
    # The full matrix remains machine-readable and keeps each effort separate.
    fields = ["route_id", "task", "effort", "runs", "passes", "pass_rate", "pass_ci_low", "pass_ci_high",
              "cost_per_100k_attempts", "cost_per_100k_successes", "median_seconds"]
    path = root / "TASK_ECONOMICS.csv"
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for detail in details:
            s = detail["base"]
            ci = s["passCI"] or [None, None]
            writer.writerow({"route_id": detail["route_id"], "task": detail["task"], "effort": detail["effort"],
                             "runs": s["runs"], "passes": s["passes"], "pass_rate": s["passRate"],
                             "pass_ci_low": ci[0], "pass_ci_high": ci[1],
                             "cost_per_100k_attempts": s["attempt"]*100 if s["attempt"] is not None else None,
                             "cost_per_100k_successes": s["success"]*100 if s["success"] is not None else None,
                             "median_seconds": s["latency"]})
    temporary.replace(path)
    return payload
