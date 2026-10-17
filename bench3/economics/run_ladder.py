#!/usr/bin/env python3
"""Run fresh, linked, frozen model ladders. Never reuse training observations."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from aegis_enforced_retry import DEFAULT_METHOD_BIN, METHOD_PAYLOAD, json_write
from aegis_enforced_retry import run_one as run_enforced
from common import ECON, load_config
from run_campaign import TASKS, digest, now
from run_singleshot import run_one as run_reasoning
from run_toolloop import run_one as run_tools
from verify_campaign import verify_row

CURRENT = ECON / "ladder_campaigns" / "current.json"


def policy_key(start: str, task: str, effort: str) -> str:
    return "|".join([start, task, effort])


def chain_id(start: str, task: str, effort: str, rep: int) -> str:
    return f"{start}_{task.replace('/', '-')}_{effort}_rep{rep}"


def select_plans() -> dict:
    script = """const fs=require('fs'),vm=require('vm'),c={window:{}};
vm.runInNewContext(fs.readFileSync('report_data.js','utf8'),c);
const d=require('./hybrid_cost.js').derive(c.window.REPORT_DATA),plans={};
for(const t of d.tasks)for(const effort of ['low','high'])d.routes.forEach((r,i)=>{
 const s=t.byEffort[effort].base[i];
 if(!s.ladderPlan)throw Error('Incomplete policy '+r.id+' '+t.code+' '+effort);
 plans[[r.id,t.code,effort].join('|')]={routes:s.ladderPlan.map(x=>x.id),
   estimated_cost_per_100k:s.ladder*100,selection_stages:s.ladderPlan};
});
process.stdout.write(JSON.stringify({plans,routes:d.routes,tasks:d.tasks.map(t=>({code:t.code,name:t.name})),
 qualifying_routes:d.hybridMethod.qualifyingRoutes,selection_rule:d.hybridMethod.ladderRule,
 training_counts:{base:d.campaign.comparisonBaseRuns,new_route:d.campaign.baseRuns,retained:d.campaign.baseline.baseRuns}}));"""
    return json.loads(subprocess.check_output(["node", "-e", script], cwd=ECON))


def initialize(root: Path, jobs: int) -> dict:
    if root.exists():
        raise RuntimeError("Ladder campaign already exists; use --resume")
    selected = select_plans()
    config = load_config()
    routes = [r["id"] for r in selected["routes"]]
    if len(routes) != 16 or {t["code"] for t in selected["tasks"]} != set(TASKS):
        raise RuntimeError("The authorized matrix is 16 starting routes and seven objective tasks")
    for start in routes:
        for task in TASKS:
            for effort in ["low", "high"]:
                plan = selected["plans"][policy_key(start, task, effort)]["routes"]
                if not plan or plan[0] != start or len(set(plan)) != len(plan):
                    raise RuntimeError("Invalid or repeated model levels")
                if plan[-1] not in selected["qualifying_routes"]:
                    raise RuntimeError("The final fallback is not fully qualified")
                if not all(r in routes and config["routes"][r].get("enabled", True) for r in plan):
                    raise RuntimeError("A selected route is missing or disabled")
    pinned = [ECON / name for name in ["run_ladder.py", "ladder_stats.py", "verify_ladder.py",
        "run_singleshot.py", "run_toolloop.py", "tool_runtime.py", "toolloop_recovery.py",
        "aegis_enforced_retry.py", "common.py", "run_campaign.py", "verify_campaign.py",
        "campaign_stats.py", "report_data.js", "hybrid_cost.js"]]
    pinned.extend([METHOD_PAYLOAD, DEFAULT_METHOD_BIN])
    for task in TASKS:
        pinned.extend(p for p in (ECON.parent / "tasks" / task).iterdir() if p.is_file())
    provenance = [ECON / "campaigns" / name / file for name in [
        "20261017T101248Z-objective-k10", "20261017T131926Z-ds41-1017-k10"]
        for file in ["manifest.json", "final_audit.json"]]
    for path in provenance:
        if path.name=="final_audit.json" and not json.loads(path.read_text()).get("valid"):
            raise RuntimeError("Training evidence does not have a valid final audit")
    if selected["training_counts"] != {"base":2240,"new_route":140,"retained":2100}:
        raise RuntimeError("The frozen training comparison is incomplete")
    pinned.extend(provenance)
    manifest = {"schema_version": "bench3.ladder.v1", "id": root.name,
        "created_at_utc": now(), "config": config, "starting_routes": routes,
        "route_labels": selected["routes"], "tasks": TASKS, "task_labels": selected["tasks"],
        "efforts": ["low", "high"], "rep_ids": list(range(1, 11)), "repetitions": 10,
        "planned_chains": len(routes)*len(TASKS)*2*10, "jobs": jobs,
        "plans": selected["plans"], "qualifying_routes": selected["qualifying_routes"],
        "selection_rule": selected["selection_rule"], "training_counts": selected["training_counts"],
        "output_tokens": {t:4096 if t == "reasoning/r1_tiling" or t.startswith("tool-use/") else 8192 for t in TASKS},
        "method": "Full Aegis plan/completion/closure gates and signed evidence journal before every upgrade.",
        "handoff": "Fresh original task and fresh tool state at every model. No previous-model answer is injected. The Aegis retry references that model's own failed base.",
        "stop": "Stop at the first objective pass. If the final model and its enforced retry fail, record a failed chain. Do not extend the frozen plan.",
        "transport": "A provider exception is not a model failure and cannot authorize an upgrade. An uncertain incomplete call blocks automatic resubmission.",
        "source_sha256": {str(p):digest(p) for p in pinned}}
    root.mkdir(parents=True)
    json_write(root / "manifest.json", manifest)
    json_write(root / "status.json", {"state":"prepared", "completedChains":0,
        "completedRounds":0, "currentRound":0, "started_at_utc":None,
        "updated_at_utc":now(), "infrastructureErrors":0, "message":"Ready for fresh linked ladders."})
    json_write(CURRENT, {"root":str(root)})
    return manifest


def verify_pins(manifest: dict) -> None:
    for path, expected in manifest["source_sha256"].items():
        if digest(Path(path)) != expected:
            raise RuntimeError("Pinned source or training evidence changed: " + path)


def rows(root: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((root / "chain_records").glob("*.json"))]


def checked_call(folder: Path, condition: str, fn) -> dict:
    """Persist intent. A crash must not silently issue a second uncertain call."""
    matches = [p for p in (folder / "results").glob("*.json")
               if json.loads(p.read_text()).get("condition", "base") == condition]
    if matches:
        if len(matches) != 1:
            raise RuntimeError("Duplicate stage records")
        return json.loads(matches[0].read_text())
    intent = folder / (condition + "-intent.json")
    if intent.exists():
        raise RuntimeError("Uncertain prior request; preserve receipts and diagnose before resubmission: " + str(intent))
    json_write(intent, {"condition":condition, "started_at_utc":now(), "state":"request_started"})
    try:
        row = fn()
    except Exception as exc:
        json_write(intent, {"condition":condition, "state":"needs_attention", "error":str(exc)[:1200], "at_utc":now()})
        raise
    json_write(intent, {"condition":condition, "state":"recorded", "record_path":row["record_path"], "at_utc":now()})
    return row


def check_identity(row: dict, rid: str, task: str, effort: str, rep: int, condition: str, cap: int) -> None:
    if (row["route_id"],row["task"],row["effort"],row["repetition"],row["condition"]) != (rid,task,effort,rep,condition):
        raise RuntimeError("Stage identity differs from the frozen work order")
    actual_cap = row.get("request", {}).get("max_output_tokens") or row.get("limits", {}).get("max_output_tokens_per_turn")
    if actual_cap != cap or row["grade"].get("passed") not in (True,False):
        raise RuntimeError("Stage budget or objective grade is invalid")


def run_chain(root: Path, manifest: dict, cell: tuple) -> dict:
    from campaign_stats import cost
    start, task, effort, rep = cell
    ident = chain_id(*cell)
    record_path = root / "chain_records" / (ident + ".json")
    if record_path.exists():
        return json.loads(record_path.read_text())
    work = root / "chain_runs" / ident
    timing_path = work / "timing.json"
    if not timing_path.exists():
        json_write(timing_path, {"started_at_utc":now()})
    started = json.loads(timing_path.read_text())["started_at_utc"]
    plan = manifest["plans"][policy_key(start,task,effort)]["routes"]
    stages, records, passed, resolved_by = [], [], False, None
    for index, rid in enumerate(plan):
        folder = work / f"stage-{index+1:02d}-{rid}"
        cap = manifest["output_tokens"][task]
        is_tool = task.startswith("tool-use/")
        base = checked_call(folder, "base", lambda: run_tools(manifest["config"],rid,task,effort,rep,output_root=folder)
            if is_tool else run_reasoning(manifest["config"],rid,effort,task,rep,False,max_output_tokens=cap,output_root=folder))
        check_identity(base,rid,task,effort,rep,"base",cap)
        records.append(base)
        retry = None
        if not base["grade"]["passed"]:
            retry = checked_call(folder,"aegis_enforced_retry",lambda: run_tools(manifest["config"],rid,task,effort,rep,base=base,output_root=folder)
                if is_tool else run_enforced(manifest["config"],base,DEFAULT_METHOD_BIN,False,output_root=folder,max_output_tokens=cap))
            check_identity(retry,rid,task,effort,rep,"aegis_enforced_retry",cap)
            if retry["parent_record_path"] != base["record_path"]:
                raise RuntimeError("Retry parent does not match the failed base")
            # Recheck all three official method gates and the signed journal.
            # A method failure is infrastructure failure, not an upgrade signal.
            verify_row(retry)
            records.append(retry)
        passed = bool(base["grade"]["passed"] or retry and retry["grade"]["passed"])
        stages.append({"route_id":rid, "base_record":base["record_path"],
            "retry_record":retry["record_path"] if retry else None,
            "base_passed":bool(base["grade"]["passed"]), "passed":passed,
            "cost_usd":sum(cost(r) for r in ([base,retry] if retry else [base])),
            "model_seconds":sum(r["elapsed_seconds"] for r in ([base,retry] if retry else [base]))})
        if passed:
            resolved_by = "base" if base["grade"]["passed"] else "aegis"
            break
        if index+1 < len(plan):
            json_write(folder / "upgrade-authorized.json", {"at_utc":now(),
                "base_failed":True,"enforced_retry_failed":True,"journal_reverified":True,
                "next_route":plan[index+1],"retry_record":retry["record_path"]})
    from campaign_stats import cost
    ended = now()
    result = {"schema_version":"bench3.ladder.chain.v1", "id":ident,
        "starting_route":start,"task":task,"effort":effort,"repetition":rep,
        "started_at_utc":started,"completed_at_utc":ended,
        "passed":passed,"resolved_by":resolved_by,"resolved_route":stages[-1]["route_id"] if passed else None,
        "stages":stages,"stage_count":len(stages),"upgrades":len(stages)-1,
        "retries":sum(s["retry_record"] is not None for s in stages),
        "cost_usd":sum(cost(r) for r in records),
        "cash_cost_usd":sum(r["costs"]["cash_cost_usd"] for r in records),
        "allocated_cost_usd":sum(r["costs"].get("capacity_allocated_cost_usd") or 0 for r in records),
        "model_seconds":sum(r["elapsed_seconds"] for r in records),
        "wall_seconds":(datetime.fromisoformat(ended)-datetime.fromisoformat(started)).total_seconds(),
        "model_calls":sum(r["usage"].get("calls",1) for r in records),
        "missing_usage_receipts":sum(r.get("transport_recovery",{}).get("missing_usage_receipts",0) for r in records),
        "record_path":str(record_path)}
    json_write(record_path,result)
    print(f"LADDER {ident} pass={passed} stages={len(stages)} retries={result['retries']} cost=${result['cost_usd']:.6f}",flush=True)
    return result


def verify_chain(row: dict, manifest: dict, replay: bool = True) -> list[dict]:
    plan = manifest["plans"][policy_key(row["starting_route"],row["task"],row["effort"])]["routes"]
    stages = row["stages"]
    if not stages or [s["route_id"] for s in stages] != plan[:len(stages)]:
        raise RuntimeError("Executed path is not a prefix of the frozen ladder")
    records = []
    for index, stage in enumerate(stages):
        base = json.loads(Path(stage["base_record"]).read_text())
        check_identity(base,stage["route_id"],row["task"],row["effort"],row["repetition"],"base",manifest["output_tokens"][row["task"]])
        retry = json.loads(Path(stage["retry_record"]).read_text()) if stage["retry_record"] else None
        if bool(retry) == bool(base["grade"]["passed"]):
            raise RuntimeError("A failed base must get exactly one enforced retry; a passing base must not")
        parts = [base]+([retry] if retry else [])
        for part in parts:
            if replay: verify_row(part)
        if retry:
            check_identity(retry,stage["route_id"],row["task"],row["effort"],row["repetition"],"aegis_enforced_retry",manifest["output_tokens"][row["task"]])
            if retry["parent_record_path"] != base["record_path"]:
                raise RuntimeError("Wrong retry parent")
        passed = bool(base["grade"]["passed"] or retry and retry["grade"]["passed"])
        if passed != stage["passed"] or bool(base["grade"]["passed"]) != stage["base_passed"]:
            raise RuntimeError("Stage outcome differs from evidence")
        if passed and index != len(stages)-1:
            raise RuntimeError("A call occurred after a successful stage")
        from campaign_stats import cost
        if abs(stage["cost_usd"]-sum(cost(p) for p in parts))>1e-10:
            raise RuntimeError("Stage cost differs from its provider records")
        folder=Path(base["record_path"]).parent.parent
        expected_folder=Path(row["record_path"]).parent.parent/"chain_runs"/row["id"]/f"stage-{index+1:02d}-{stage['route_id']}"
        if folder.resolve()!=expected_folder.resolve():
            raise RuntimeError("Stage records are outside this fresh chain")
        if index+1<len(stages):
            authorization=json.loads((folder/"upgrade-authorized.json").read_text())
            if not all(authorization.get(k) is True for k in ["base_failed","enforced_retry_failed","journal_reverified"]):
                raise RuntimeError("Upgrade lacks failure and journal authorization")
            if authorization["next_route"]!=stages[index+1]["route_id"] or authorization["retry_record"]!=stage["retry_record"]:
                raise RuntimeError("Upgrade authorization names the wrong stage")
            next_base=json.loads(Path(stages[index+1]["base_record"]).read_text())
            if next_base["started_at_utc"]<authorization["at_utc"]:
                raise RuntimeError("An upgrade ran before authorization")
        records.extend(parts)
    if bool(stages[-1]["passed"]) != bool(row["passed"]) or (not row["passed"] and len(stages) != len(plan)):
        raise RuntimeError("Chain stopped without passing or exhausting its plan")
    from campaign_stats import cost
    fields = {"cost_usd":sum(cost(r) for r in records),
        "cash_cost_usd":sum(r["costs"]["cash_cost_usd"] for r in records),
        "allocated_cost_usd":sum(r["costs"].get("capacity_allocated_cost_usd") or 0 for r in records)}
    if any(abs(row[k]-v)>1e-10 for k,v in fields.items()):
        raise RuntimeError("Chain cost omitted or duplicated a receipt")
    if row["stage_count"] != len(stages) or row["upgrades"] != len(stages)-1 or row["retries"] != sum(bool(s["retry_record"]) for s in stages):
        raise RuntimeError("Chain counters differ from evidence")
    return records


def publish(root: Path, intervals: bool = False) -> None:
    from ladder_stats import publish as publish_stats
    publish_stats(root,intervals=intervals)


def worker(root: Path) -> int:
    manifest=json.loads((root/"manifest.json").read_text())
    state=json.loads((root/"status.json").read_text())
    with (root/"worker.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        verify_pins(manifest)
        def update(**changes):
            state.update(changes,updated_at_utc=now());json_write(root/"status.json",state)
        update(state="running",pid=os.getpid(),started_at_utc=state.get("started_at_utc") or now())
        publish(root)
        try:
            for round_index,rep in enumerate(manifest["rep_ids"],1):
                verify_pins(manifest)
                proof_path=root/"checkpoints"/f"round-{round_index:02d}-verification.json"
                if proof_path.exists():continue
                cells=[(start,task,effort,rep) for start in manifest["starting_routes"] for task in manifest["tasks"] for effort in manifest["efforts"]]
                random.Random(20261017+rep).shuffle(cells)
                update(currentRound=round_index,message=f"Linked ladder repetition {round_index}/10 is running.")
                errors=[]
                with ThreadPoolExecutor(max_workers=manifest["jobs"]) as pool:
                    futures={pool.submit(run_chain,root,manifest,cell):cell for cell in cells}
                    for future in as_completed(futures):
                        try:future.result()
                        except Exception as exc:
                            errors.append({"cell":futures[future],"error":str(exc)[:1500]})
                            print("LADDER NEEDS ATTENTION",futures[future],str(exc),flush=True)
                        update(completedChains=len(rows(root)),infrastructureErrors=len(errors))
                        publish(root)
                if errors:
                    update(state="needs_attention",errors=errors,message="An infrastructure error blocks the next repetition. Do not upgrade or repeat uncertain requests.")
                    publish(root);return 2
                observed=[r for r in rows(root) if r["repetition"]==rep]
                expected=set(cells)
                actual={(r["starting_route"],r["task"],r["effort"],r["repetition"]) for r in observed}
                if len(observed)!=len(expected) or actual!=expected:raise RuntimeError("Round coverage differs")
                with ThreadPoolExecutor(max_workers=manifest["jobs"]) as pool:
                    list(pool.map(lambda r:verify_chain(r,manifest),observed))
                json_write(proof_path,{"round":round_index,"repetition":rep,"chains":len(observed),
                    "passes":sum(r["passed"] for r in observed),"upgrades":sum(r["upgrades"] for r in observed),
                    "retries":sum(r["retries"] for r in observed),"verified_at_utc":now()})
                update(completedRounds=round_index,message=f"Linked ladder repetition {round_index}/10 verified.")
                publish(root,intervals=True)
                json_write(root/"checkpoints"/f"round-{round_index:02d}-summary.json",json.loads((root/"summary.json").read_text()))
            update(state="complete",completed_at_utc=now(),message="All ten linked-ladder repetitions are complete. Independent final audit is pending.")
            publish(root,intervals=True);return 0
        except Exception as exc:
            update(state="needs_attention",message=str(exc)[:2000]);publish(root);raise


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ["launch","worker","resume","status","report-only"]:p.add_argument("--"+flag,action="store_true")
    p.add_argument("--campaign",type=Path);p.add_argument("--jobs",type=int,default=8)
    args=p.parse_args()
    root=args.campaign or (Path(json.loads(CURRENT.read_text())["root"]) if CURRENT.exists() else None)
    if args.launch:
        root=args.campaign or ECON/"ladder_campaigns"/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-greedy-k10")
        initialize(root.resolve(),args.jobs)
    if root is None:p.error("Use --launch or specify an existing --campaign")
    root=root.resolve()
    if args.worker:return worker(root)
    if args.status:print((root/"status.json").read_text());return 0
    if args.report_only:publish(root,intervals=True);return 0
    if args.launch or args.resume:
        with (root/"worker.log").open("ab") as log:
            process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),"--worker","--campaign",str(root)],cwd=ECON,
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        json_write(root/"process.json",{"pid":process.pid,"launched_at_utc":now()})
        print(json.dumps({"root":str(root),"pid":process.pid,"planned_chains":2240}));return 0
    p.error("Choose --launch, --resume, --worker, --status, or --report-only")


if __name__=="__main__":raise SystemExit(main())
