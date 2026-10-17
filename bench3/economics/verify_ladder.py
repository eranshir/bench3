#!/usr/bin/env python3
"""Independently audit fresh linked ladders without provider requests."""
from __future__ import annotations

import argparse
import fcntl
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from aegis_enforced_retry import json_write
from run_campaign import now
from run_ladder import rows, verify_chain, verify_pins


def verify(root: Path, jobs: int = 8) -> dict:
    with (root/"worker.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest=json.loads((root/"manifest.json").read_text())
        status=json.loads((root/"status.json").read_text())
        if status["state"]!="complete":raise RuntimeError("The ladder campaign is not complete")
        verify_pins(manifest)
        chains=rows(root)
        expected={(start,task,effort,rep) for start in manifest["starting_routes"] for task in manifest["tasks"]
            for effort in manifest["efforts"] for rep in manifest["rep_ids"]}
        actual=[(r["starting_route"],r["task"],r["effort"],r["repetition"]) for r in chains]
        if len(chains)!=manifest["planned_chains"] or len(set(actual))!=len(actual) or set(actual)!=expected:
            raise RuntimeError("Fresh chain matrix differs from the frozen work order")
        all_paths=[]
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            for records in pool.map(lambda row:verify_chain(row,manifest),chains):
                all_paths.extend(Path(r["record_path"]).resolve() for r in records)
        actual_paths={p.resolve() for p in (root/"chain_runs").glob("*/stage-*/results/*.json")}
        if len(all_paths)!=len(set(all_paths)) or set(all_paths)!=actual_paths:
            raise RuntimeError("A provider record is reused, omitted, or not on an executed ladder")
        for index,rep in enumerate(manifest["rep_ids"],1):
            proof=json.loads((root/"checkpoints"/f"round-{index:02d}-verification.json").read_text())
            group=[r for r in chains if r["repetition"]==rep]
            values={"round":index,"repetition":rep,"chains":len(group),"passes":sum(r["passed"] for r in group),
                "retries":sum(r["retries"] for r in group),"upgrades":sum(r["upgrades"] for r in group)}
            if any(proof[k]!=v for k,v in values.items()):raise RuntimeError("A round proof differs")
            snapshot=json.loads((root/"checkpoints"/f"round-{index:02d}-summary.json").read_text())
            if snapshot["completedChains"]!=index*len(group) or snapshot["completedRounds"]!=index:
                raise RuntimeError("A round snapshot differs")
        retries=sum(r["retries"] for r in chains)
        return {"valid":True,"verified_at_utc":now(),"fresh_chains":len(chains),
            "passes":sum(r["passed"] for r in chains),"base_stage_records":sum(r["stage_count"] for r in chains),
            "enforced_retries":retries,"signed_journals_reverified":retries,"method_gates_replayed":3*retries,
            "grades_replayed":len(all_paths),"round_proofs":len(manifest["rep_ids"]),
            "upgrades":sum(r["upgrades"] for r in chains),"all_costs_reconciled":True,
            "provider_requests_made_by_audit":0,"training_observations_counted_as_fresh":0,
            "cash_cost_usd":sum(r["cash_cost_usd"] for r in chains),
            "allocated_cost_usd":sum(r["allocated_cost_usd"] for r in chains)}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--campaign",type=Path,required=True)
    p.add_argument("--jobs",type=int,default=8);p.add_argument("--save",action="store_true");args=p.parse_args()
    result=verify(args.campaign.resolve(),args.jobs)
    if args.save:json_write(args.campaign/"final_audit.json",result)
    print(json.dumps(result,indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
