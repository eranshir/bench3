#!/usr/bin/env python3
"""Audit coverage, saved provider responses, replayed outcomes and all receipts."""
from __future__ import annotations

import json
from pathlib import Path

from analyze_toolloop import ROOT, load_rows
from common import load_config, normalized_usage
from run_singleshot import normalized_chat_response
from tool_runtime import TASKS, check_trace


def audit() -> dict:
    config = load_config()
    rows = load_rows()
    expected = {(rid, task, effort, 1) for rid, route in config["routes"].items()
                if route.get("enabled", True) for task in TASKS for effort in ["low", "high"]}
    actual = {(r["route_id"], r["task"], r["effort"], r["repetition"]) for r in rows}
    errors = []
    if actual != expected or len(rows) != len(expected):
        errors.append({"coverage": {"missing": sorted(expected-actual), "unexpected": sorted(actual-expected)}})
    tool_count = 0
    receipt_count = 0
    for row in rows:
        faults = []
        path = Path(row["response_path"])
        trace = json.loads(path.read_text())
        if check_trace(trace) != row["grade"]:
            faults.append("fresh checker differs")
        route = config["routes"][row["route_id"]]
        emitted = []
        for turn in trace["turns"]:
            raw = json.loads((path.parent / f"turn-{turn['turn']:02d}.json").read_text())
            if normalized_usage(raw) != turn["usage"]:
                faults.append("provider usage differs")
            message = normalized_chat_response(raw, route["api_shape"])["choices"][0]["message"]
            for call in message.get("tool_calls") or []:
                fn = call["function"]
                try:
                    args = json.loads(fn["arguments"])
                except Exception:
                    args = fn["arguments"]
                emitted.append((turn["turn"], fn["name"], args))
        executed = []
        for event in trace["tool_events"]:
            args = event["arguments"]
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass
            executed.append((event["turn"], event["name"], args))
        if emitted != executed:
            faults.append("emitted calls differ from executed tools")
        if trace["turns"][-1]["tool_call_count"] != 0:
            faults.append("final model response did not consume last tool results")
        all_turns = list(trace["turns"])
        for prior in row.get("transport_recovery", {}).get("partial_attempts", []):
            all_turns.extend(json.loads(Path(prior["trace_path"]).read_text())["turns"])
        for name in ["input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens", "reasoning_tokens", "total_tokens"]:
            if row["usage"][name] != sum(t["usage"][name] for t in all_turns):
                faults.append("summed usage differs: " + name)
        if row["usage"]["calls"] != len(all_turns):
            faults.append("model request count differs")
        for name in ["cash_cost_usd", "inference_cost_usd", "capacity_allocated_cost_usd"]:
            values = [t["costs"].get(name) for t in all_turns]
            expected_cost = sum(values) if all(v is not None for v in values) else None
            actual_cost = row["costs"].get(name)
            if (expected_cost is None) != (actual_cost is None) or (
                expected_cost is not None and abs(expected_cost - actual_cost) > 1e-10
            ):
                faults.append("summed cost differs: " + name)
        if faults:
            errors.append({"record": row["record_path"], "faults": faults})
        tool_count += len(executed)
        receipt_count += len(all_turns)
    return {"schema_version": "bench3.toolloop.audit.v1", "base_records": len(rows),
            "base_passes": sum(r["grade"]["passed"] for r in rows),
            "executed_tools_in_completed_workflows": tool_count,
            "provider_receipts_audited": receipt_count, "errors": errors, "ok": not errors}


if __name__ == "__main__":
    report = audit()
    (ROOT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["ok"] else 1)
