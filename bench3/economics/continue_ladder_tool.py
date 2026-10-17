#!/usr/bin/env python3
"""Human-approved continuation of the one interrupted 1017 tool workflow.

Replay the three saved responses locally through the unchanged tool harness.
Make no new provider call until the resulting history matches the saved tool
events. Preserve the timeout and charge every known receipt exactly once.
The lost fourth request consumes one of the original twelve request slots.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from aegis_enforced_retry import json_write, route_snapshot, sha256_file
from common import ECON, append_jsonl
from run_campaign import now
from run_ladder import verify_pins
from run_singleshot import call, chat_body, normalized_chat_response
import run_toolloop as loop
from tool_runtime import CONTRACT, ToolRuntime, check_trace, inputs

ROUTE="ds41-1017-openrouter"
TASK="tool-use/t2_toolselect"
EFFORT="high"
REP=7
STEM=f"{ROUTE}_{TASK.replace('/','-')}_{EFFORT}_rep{REP}_base"


def prefix(config: dict, folder: Path) -> tuple[Path, dict, list[dict], dict]:
    original=folder/"runs"/STEM
    trace=json.loads((original/"trace.json").read_text())
    if trace["task"]!=TASK or len(trace["turns"])!=3 or trace["final_answer"]:
        raise RuntimeError("This authorization covers exactly the saved three-turn prefix")
    failed=json.loads((original/"turn-04.json").read_text())
    if failed.get("error",{}).get("code")!=504 or failed.get("choices") or failed.get("usage"):
        raise RuntimeError("The fourth response is not the saved timeout without usage")
    messages,tools=inputs(TASK);history=copy.deepcopy(messages);runtime=ToolRuntime(TASK);raws=[]
    for index,turn in enumerate(trace["turns"],1):
        raw=json.loads((original/f"turn-{index:02d}.json").read_text());raws.append(raw)
        if turn["turn"]!=index or turn["response_id"]!=raw.get("id") or raw.get("error"):
            raise RuntimeError("Saved response identity differs")
        message=normalized_chat_response(raw,"openai-chat")["choices"][0]["message"]
        history.append(copy.deepcopy(message))
        for tool in message.get("tool_calls",[]):
            fn=tool["function"];output=runtime.execute(fn["name"],fn["arguments"],index)
            history.append({"role":"tool","tool_call_id":tool["id"],"content":json.dumps(output,separators=(",",":"))})
    if runtime.events!=trace["tool_events"]:
        raise RuntimeError("Saved tool results do not match local deterministic replay")
    expected=chat_body(config["routes"][ROUTE],history,tools,EFFORT,loop.MAX_OUTPUT_TOKENS)
    return original,trace,raws,expected


def continue_base(config: dict, folder: Path, started_at: str, request_fn=None) -> dict:
    record_path=folder/"results"/(STEM+".json")
    if record_path.exists():return json.loads(record_path.read_text())
    original,old,raws,expected=prefix(config,folder)
    if config["routes"][ROUTE]["api_shape"]!="openai-chat":
        raise RuntimeError("Only the authorized OpenRouter Chat route is supported")
    destination=folder/"continuations"/"human-approved-01"
    intent=destination/"continuation-intent.json"
    if intent.exists():
        raise RuntimeError("A continuation was already attempted. Diagnose receipts; do not repeat uncertain calls.")
    json_write(intent,{"state":"approved", "at_utc":now(),
        "authority":"User answered yes to continuing this exact workflow from saved results.",
        "completed_prefix_requests":3,"timed_out_requests":1,"remaining_provider_requests":8,
        "helper_sha256":sha256_file(Path(__file__)),
        "original_artifacts_sha256":{p.name:sha256_file(p) for p in [original/"trace.json",*sorted(original.glob("turn-*.json"))]}})
    replayed=0;new_calls=0;new_ids=[]
    actual=request_fn or (lambda route,key,body:call(route,key,body,retries=0))
    def request(route,key,body):
        nonlocal replayed,new_calls
        if replayed<len(raws):
            raw=raws[replayed];elapsed=old["turns"][replayed]["seconds"];replayed+=1
            return copy.deepcopy(raw),elapsed
        if new_calls==0 and body!=expected:
            raise RuntimeError("Continuation history changed before the first new paid request")
        if 4+new_calls>=loop.MAX_TURNS+1: # The loop cap is 11 inside this wrapper: 12 actual requests.
            raise RuntimeError("Original request budget exhausted")
        ordinal=5+new_calls;new_calls+=1
        request_path=destination/"requests"/f"request-{ordinal:02d}-intent.json"
        if request_path.exists():raise RuntimeError("Duplicate continuation request intent")
        json_write(request_path,{"ordinal":ordinal,"state":"request_started","at_utc":now()})
        raw,elapsed=actual(route,key,body)
        json_write(destination/"requests"/f"request-{ordinal:02d}-response.json",raw)
        json_write(request_path,{"ordinal":ordinal,"state":"response_saved","at_utc":now(),
            "response_id":raw.get("id"),"has_usage":bool(raw.get("usage")),"provider_error":raw.get("error")})
        new_ids.append(raw.get("id"))
        if not raw.get("error") and not raw.get("usage"):
            raise RuntimeError("New response lacks a usage receipt; preserve it for diagnosis")
        return raw,elapsed
    before=time.monotonic()
    try:
        # Three offline replay slots + eight new slots + the old timeout = 12.
        # This changes no pinned source and grants no extra model/tool budget.
        with patch.object(loop,"MAX_TURNS",11):
            trace,_usage,_costs,elapsed=loop.execute_loop(config,ROUTE,TASK,EFFORT,destination,request_fn=request)
    except Exception as exc:
        data=json.loads(intent.read_text());data.update(state="needs_attention",error=str(exc)[:1200],new_requests=new_calls)
        json_write(intent,data);raise
    if trace["tool_events"][:len(old["tool_events"])]!=old["tool_events"]:
        raise RuntimeError("Continuation changed the completed tool prefix")
    # Keep the original known charges and durations, not a new pricing of them.
    trace["turns"][:3]=copy.deepcopy(old["turns"])
    trace["elapsed_seconds"]=old["elapsed_seconds"]+elapsed
    trace["transport_continuation"]={"completed_prefix":3,"timed_out_requests":1,"new_requests":new_calls,
        "total_provider_requests":4+new_calls,"request_ordinals":[1,2,3,*range(5,5+new_calls)],
        "original_trace":str(original/"trace.json"),"missing_usage_response":str(original/"turn-04.json")}
    json_write(destination/"trace.json",trace)
    grade=check_trace(trace);json_write(destination/"objective-checker.json",grade)
    usage={}
    for turn in trace["turns"]:
        for k,v in turn["usage"].items():usage[k]=usage.get(k,0)+v
    costs=loop.aggregate_costs([t["costs"] for t in trace["turns"]])
    record={"schema_version":"bench3.economics.toolloop.v1","task_contract":CONTRACT,
        "catalog_as_of":config["catalog_as_of"],"started_at_utc":started_at,
        "route_id":ROUTE,"route":route_snapshot(config["routes"][ROUTE]),"task":TASK,"effort":EFFORT,
        "repetition":REP,"condition":"base","parent_record_path":None,"grade":grade,
        "usage":{**usage,"calls":4+new_calls},"costs":costs,"elapsed_seconds":trace["elapsed_seconds"],"aegis":None,
        "tool_calls":len(trace["tool_events"]),"tool_errors":sum(not e["result"].get("ok") for e in trace["tool_events"]),
        "stop_reason":trace["stop_reason"],"final_answer":trace["final_answer"],
        "transport_recovery":{"restarts":0,"continuations":1,"missing_usage_receipts":1,
            "partial_attempts":[],"completed_prefix_requests_replayed_offline":3,
            "known_prefix_cost_usd":sum(t["costs"]["cash_cost_usd"] for t in old["turns"]),
            "unknown_timeout_charge_usd":None,"source_trace":str(original/"trace.json"),
            "new_response_ids":new_ids,"human_authorization":str(intent)},
        "record_path":str(record_path),"response_path":str(destination/"trace.json"),
        "limits":{"max_turns":12,"max_tool_calls":32,"max_output_tokens_per_turn":4096},
        "harness_sha256":sha256_file(Path(loop.__file__)),"runtime_sha256":sha256_file(ECON/"tool_runtime.py"),
        "continuation_helper_sha256":sha256_file(Path(__file__))}
    json_write(record_path,record);append_jsonl(folder/"results"/"results.jsonl",record)
    data=json.loads(intent.read_text());data.update(state="recorded",record_path=str(record_path),
        completed_at_utc=now(),new_requests=new_calls,total_provider_requests=4+new_calls)
    json_write(intent,data)
    return record


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--campaign",type=Path,required=True)
    p.add_argument("--approved",action="store_true");args=p.parse_args()
    if not args.approved:p.error("This continuation requires the user's explicit approval")
    root=args.campaign.resolve();manifest=json.loads((root/"manifest.json").read_text())
    with (root/"worker.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);verify_pins(manifest)
        ident=f"{ROUTE}_{TASK.replace('/','-')}_{EFFORT}_rep{REP}"
        work=root/"chain_runs"/ident;folder=work/f"stage-01-{ROUTE}"
        started=json.loads((work/"timing.json").read_text())["started_at_utc"]
        record=continue_base(manifest["config"],folder,started)
        audit={"valid":True,"verified_at_utc":now(),"cell":[ROUTE,TASK,EFFORT,REP],
            "completed_calls_reissued":0,"completed_prefix_receipts_preserved":3,
            "new_provider_requests":record["usage"]["calls"]-4,"total_provider_requests":record["usage"]["calls"],
            "request_cap":12,"missing_usage_receipts":1,"unknown_timeout_charge_usd":None,
            "known_cost_usd":record["costs"]["cash_cost_usd"],"objective_passed":record["grade"]["passed"],
            "helper_sha256":sha256_file(Path(__file__)),"original_source_pins_unchanged":True}
        json_write(root/"recovery_audit.json",audit);print(json.dumps(audit,indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
