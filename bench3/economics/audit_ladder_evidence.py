#!/usr/bin/env python3
"""Recheck nonempty signed journals at their actual adapter path, offline.

The older verifier can confuse a reasoning adapter's .am directory with its
run directory. An empty journal can be valid, so valid=true alone is not
enough. This additional audit uses the actual evidence path and requires
the saved nonempty journal head and key to match the fresh verification.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from aegis_enforced_retry import DEFAULT_METHOD_BIN, json_write
from campaign_stats import read_records
from run_campaign import now
from run_ladder import rows
from verify_campaign import command_json


def verify_evidence(row: dict) -> dict:
    method=row["aegis"]
    run=Path(method["local_ir_dir"]).parent if method.get("local_ir_dir") else Path(method["run_dir"])
    state=run/"evidence-state"
    if not (state/"observed-events.jsonl").is_file():
        raise RuntimeError("Actual signed journal is missing: "+str(state))
    actual=command_json(["aegis","evidence","verify","--state-dir",str(state),"--json"])
    saved=method["evidence"]["verify"]
    if actual["command_exit_code"]!=0 or not actual.get("valid"):
        raise RuntimeError("Actual signed journal is invalid")
    journal=actual.get("journal",{});old=saved.get("journal",{})
    if not journal.get("entry_count") or journal.get("entry_count",0)<2:
        raise RuntimeError("An empty journal is not benchmark evidence")
    for field in ["entry_count","head_hash","journal_id","segment_id"]:
        if journal.get(field)!=old.get(field):
            raise RuntimeError("Signed journal differs from the saved retry verification: "+field)
    if journal.get("evidence_key",{}).get("public_key_sha256")!=old.get("evidence_key",{}).get("public_key_sha256"):
        raise RuntimeError("Journal signing identity differs")
    for gate in ["plan","completion","closure"]:
        value=command_json([str(DEFAULT_METHOD_BIN),"validate",gate,"--ir",str(run),"--json"])
        expected=gate=="plan" or bool(row["grade"]["passed"])
        if bool(value.get("ok"))!=expected or expected and value["command_exit_code"]!=0:
            raise RuntimeError("Actual method gate differs: "+gate)
    return {"nonempty":True,"entries":journal["entry_count"],"head_matches":True,"key_matches":True}


def audit(root: Path, training: bool = False, jobs: int = 8) -> dict:
    if training:
        _,retries=read_records(root)
    else:
        retries=[json.loads(Path(s["retry_record"]).read_text()) for r in rows(root)
            for s in r["stages"] if s["retry_record"]]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        verified=list(pool.map(verify_evidence,retries))
    return {"valid":True,"verified_at_utc":now(),"nonempty_signed_journals":len(verified),
        "signed_entries":sum(r["entries"] for r in verified),"journal_heads_and_signing_keys_match":True,
        "actual_run_root_method_gates":3*len(verified),"provider_requests_made":0,
        "scope":"Strict additional audit. Actual evidence-state path; nonempty signed journal; exact saved head, segment, journal and public-key identity; all method gates at the adapter run root."}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--campaign",type=Path,required=True)
    p.add_argument("--training",action="store_true");p.add_argument("--save",action="store_true");args=p.parse_args()
    result=audit(args.campaign.resolve(),args.training)
    if args.save:json_write(args.campaign/"journal_audit.json",result)
    print(json.dumps(result,indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
