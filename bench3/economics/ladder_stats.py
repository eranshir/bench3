"""Public aggregates of completed fresh ladder workflows; no provider calls."""
from __future__ import annotations

import csv
import json
import os
import statistics
from collections import Counter
from pathlib import Path

from aegis_enforced_retry import json_write
from campaign_stats import cost_intervals, wilson
from common import ECON


def summarize(group: list[dict], intervals: bool = False) -> dict:
    n=len(group);passed=sum(r["passed"] for r in group)
    amount=sum(r["cost_usd"] for r in group)
    ci=cost_intervals(tuple((r["cost_usd"],bool(r["passed"])) for r in group)) if intervals else {"attempt":None,"success":None}
    return {"runs":n,"passes":passed,"passRate":100*passed/n if n else 0,"passCI":wilson(passed,n),
        "attempt":amount/n*1000 if n else None,"success":amount/passed*1000 if passed else None,
        "attemptCI100k":ci["attempt"],"successCI100k":ci["success"],
        "latency":statistics.median(r["wall_seconds"] for r in group) if n else None,
        "modelSeconds":statistics.median(r["model_seconds"] for r in group) if n else None,
        "retries":sum(r["retries"] for r in group),"upgrades":sum(r["upgrades"] for r in group),
        "resolvedByBase":sum(r["resolved_by"]=="base" for r in group),
        "resolvedByAegis":sum(r["resolved_by"]=="aegis" for r in group),
        "cashCost":sum(r["cash_cost_usd"] for r in group),
        "allocatedCost":sum(r["allocated_cost_usd"] for r in group),
        "missingUsageReceipts":sum(r["missing_usage_receipts"] for r in group)}


def publish(root: Path, intervals: bool = False) -> dict:
    manifest=json.loads((root/"manifest.json").read_text())
    status=json.loads((root/"status.json").read_text())
    records=[json.loads(p.read_text()) for p in sorted((root/"chain_records").glob("*.json"))]
    cells=[]
    for task in manifest["tasks"]:
        for effort in manifest["efforts"]:
            for start in manifest["starting_routes"]:
                group=[r for r in records if (r["starting_route"],r["task"],r["effort"])==(start,task,effort)]
                policy=manifest["plans"]["|".join([start,task,effort])]
                stages=[]
                for index,rid in enumerate(policy["routes"]):
                    reached=[r["stages"][index] for r in group if len(r["stages"])>index]
                    passed=sum(s["passed"] for s in reached)
                    stages.append({"route_id":rid,"reached":len(reached),"basePasses":sum(s["base_passed"] for s in reached),
                        "retries":sum(bool(s["retry_record"]) for s in reached),
                        "recoveries":sum(s["passed"] and not s["base_passed"] for s in reached),
                        "passes":passed,"passCI":wilson(passed,len(reached)),
                        "contribution100k":sum(s["cost_usd"] for s in reached)/len(group)*100000 if group else None})
                cells.append({"starting_route":start,"task":task,"effort":effort,
                    **summarize(group,intervals),"plannedRuns":manifest["repetitions"],
                    "estimatedCost100k":policy["estimated_cost_per_100k"],"stages":stages})
    configs=[{"starting_route":start,"effort":effort,
        **summarize([r for r in records if r["starting_route"]==start and r["effort"]==effort],intervals),
        "plannedRuns":len(manifest["tasks"])*manifest["repetitions"]}
        for start in manifest["starting_routes"] for effort in manifest["efforts"]]
    payload={"schema_version":"bench3.ladder.summary.v1", "root":str(root),**status,
        "plannedChains":manifest["planned_chains"],"routes":manifest["route_labels"],
        "tasks":manifest["task_labels"],"qualifyingRoutes":manifest["qualifying_routes"],
        "trainingBaseObservations":manifest["training_counts"]["base"],
        "completedChains":len(records),"passes":sum(r["passed"] for r in records),
        "baseStages":sum(r["stage_count"] for r in records),"retries":sum(r["retries"] for r in records),
        "upgrades":sum(r["upgrades"] for r in records),
        "recoveries":sum(s["passed"] and not s["base_passed"] for r in records for s in r["stages"]),
        "cashCost":sum(r["cash_cost_usd"] for r in records),
        "allocatedCost":sum(r["allocated_cost_usd"] for r in records),
        "missingUsageReceipts":sum(r["missing_usage_receipts"] for r in records),
        "resolvedRoutes":dict(Counter(r["resolved_route"] for r in records if r["passed"])),
        "finalAuditAvailable":(root/"final_audit.json").exists(),"cells":cells,"configs":configs,
        "scope":"Fresh linked calls on seven fixed tasks. Plans selected on the older 2,240 observations. No training record is counted as a fresh call. Aegis at every failed base. Cost includes every reached stage and retry.",
        "liveCostNote":"Costs cover completed chains only. In-progress and interrupted requests are not fully accounted until their chain completes. Unknown provider charges are not treated as zero."}
    json_write(root/"summary.json",payload)
    target=root/"TASK_ECONOMICS.csv"
    tmp=target.with_suffix(".csv.tmp")
    with tmp.open("w",newline="") as f:
        writer=csv.writer(f);writer.writerow(["starting_route","task","effort","runs","passes","pass_ci_low","pass_ci_high",
            "measured_cost_per_100k_attempts","cost_ci_low","cost_ci_high","measured_cost_per_100k_successes",
            "estimated_cost_per_100k_attempts","median_wall_seconds","median_model_seconds","retries","upgrades"])
        for s in cells:
            writer.writerow([s["starting_route"],s["task"],s["effort"],s["runs"],s["passes"],*(s["passCI"] or [None,None]),
                s["attempt"]*100 if s["attempt"] is not None else None,*(s["attemptCI100k"] or [None,None]),
                s["success"]*100 if s["success"] is not None else None,s["estimatedCost100k"],s["latency"],s["modelSeconds"],s["retries"],s["upgrades"]])
    tmp.replace(target)
    js=ECON/"ladder_data.js"
    temporary=js.with_name(js.name+f".{os.getpid()}.tmp")
    temporary.write_text("window.LADDER_DATA = "+json.dumps(payload,separators=(",",":"))+";\n")
    temporary.replace(js)
    return payload
