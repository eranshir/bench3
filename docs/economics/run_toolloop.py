#!/usr/bin/env python3
"""Run real tool loops on all configured routes; enforce Aegis on failures."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from common import (ECON, append_jsonl, calculate_cost, load_config, load_credentials,
                    normalized_usage, provider_reported_cost)
from run_singleshot import call, chat_body, normalized_chat_response, responses_body
from tool_runtime import CONTRACT, TASKS, ToolRuntime, check_trace, inputs
from toolloop_recovery import archive_incomplete, prior_receipts
from aegis_enforced_retry import (DEFAULT_METHOD_BIN, METHOD_PAYLOAD, build_contracts,
    build_method_instruction, gate_event, json_write, route_snapshot, run_json,
    sha256_file, write_closure, write_evidence_journal)


ROOT = ECON / "toolloop"
LOCK = threading.Lock()
MAX_TURNS = 12
MAX_TOOL_CALLS = 32
MAX_OUTPUT_TOKENS = 4096


def aggregate_costs(per_turn: list[dict[str, Any]]) -> dict[str, Any]:
    result = dict(per_turn[0])
    sums = ["inference_cost_usd", "marginal_cost_usd", "cash_cost_usd",
            "capacity_allocated_cost_usd", "provider_reported_cost_usd",
            "catalog_estimated_cost_usd", "uncached_input_tokens",
            "catalog_delta_usd", "reconciliation_delta_usd"]
    for key in sums:
        values = [row.get(key) for row in per_turn]
        result[key] = sum(values) if all(v is not None for v in values) else None
    result["provider_cost_coverage"] = {
        "reported_calls": sum(x.get("provider_reported_cost_usd") is not None for x in per_turn),
        "calls": len(per_turn),
    }
    return result


def execute_loop(
    config: dict[str, Any], route_id: str, task: str, effort: str,
    artifact_dir: Path, method_instruction: str | None = None,
    request_fn: Callable = call, gate_fn: Callable | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], float]:
    route = config["routes"][route_id]
    if route["api_shape"] not in {"openai-chat", "openai-responses"}:
        raise ValueError("tool-loop adapter does not support " + route["api_shape"])
    messages, tools = inputs(task)
    if method_instruction:
        messages.insert(0, {"role": "system", "content": method_instruction})
    runtime = ToolRuntime(task)
    key = load_credentials().get(route["credential"], "")
    if not key:
        raise RuntimeError("missing credential: " + route["credential"])
    history = copy.deepcopy(messages)
    response_id = None
    pending: list[dict[str, Any]] = []
    costs: list[dict[str, Any]] = []
    turns: list[dict[str, Any]] = []
    usage: dict[str, int] = {}
    final_answer = ""
    stop_reason = "turn_limit"
    started = time.monotonic()
    trace = {"schema_version": CONTRACT, "task": task, "turns": turns,
             "tool_events": runtime.events, "final_answer": "", "stop_reason": stop_reason}
    artifact_dir.mkdir(parents=True, exist_ok=True)
    try:
        for turn in range(1, MAX_TURNS + 1):
            if gate_fn:
                gate_fn("model_request", {"turn": turn})
            if route["api_shape"] == "openai-responses":
                body = responses_body(route, messages if not response_id else pending,
                                      tools, effort, MAX_OUTPUT_TOKENS)
                # Match best-effort Chat schemas. Preserve Responses reasoning via
                # its response chain rather than dropping output items.
                for tool in body["tools"]:
                    tool["strict"] = False
                if response_id:
                    body["previous_response_id"] = response_id
            else:
                body = chat_body(route, history, tools, effort, MAX_OUTPUT_TOKENS)
            when = datetime.now(timezone.utc)
            raw, elapsed = request_fn(route, key, body)
            json_write(artifact_dir / f"turn-{turn:02d}.json", raw)
            if raw.get("error"):
                raise RuntimeError("provider error: " + json.dumps(raw["error"])[:500])
            if route["api_shape"] == "openai-responses" and raw.get("status") == "failed":
                raise RuntimeError("provider returned failed Responses status")
            normalized = normalized_chat_response(raw, route["api_shape"])
            choices = normalized.get("choices") or []
            if not choices:
                raise RuntimeError("provider response contains no assistant message")
            message = choices[0].get("message") or {}
            turn_usage = normalized_usage(raw)
            turn_costs = calculate_cost(config, route, turn_usage, when,
                                        provider_cost=provider_reported_cost(raw))
            costs.append(turn_costs)
            for name, value in turn_usage.items():
                usage[name] = usage.get(name, 0) + value
            calls = message.get("tool_calls") or []
            turns.append({"turn": turn, "response_id": raw.get("id"),
                          "upstream_provider": raw.get("provider"), "usage": turn_usage,
                          "costs": turn_costs, "seconds": elapsed, "tool_call_count": len(calls)})
            if not calls:
                final_answer = message.get("content") or ""
                stop_reason = "final_answer" if final_answer.strip() else "empty_response"
                break
            if len(runtime.events) + len(calls) > MAX_TOOL_CALLS:
                stop_reason = "tool_call_limit"
                break
            ids = [c.get("id") for c in calls]
            if not all(ids) or len(set(ids)) != len(ids):
                raise RuntimeError("provider returned missing or duplicate tool call ids")
            results = []
            for tool_call in calls:
                function = tool_call.get("function") or {}
                name = function.get("name", "")
                args = function.get("arguments", "{}")
                if gate_fn:
                    gate_fn("tool_execution", {"turn": turn, "name": name})
                output = runtime.execute(name, args, turn)
                results.append((tool_call["id"], json.dumps(output, separators=(",", ":"))))
            if route["api_shape"] == "openai-responses":
                response_id = raw.get("id")
                if not response_id:
                    raise RuntimeError("Responses provider omitted response id")
                pending = [{"type": "function_call_output", "call_id": cid, "output": output}
                           for cid, output in results]
            else:
                # Preserve reasoning_details and reasoning_content byte-for-byte.
                history.append(copy.deepcopy(message))
                history.extend({"role": "tool", "tool_call_id": cid, "content": output}
                               for cid, output in results)
    finally:
        trace.update(final_answer=final_answer, stop_reason=stop_reason,
                     elapsed_seconds=time.monotonic() - started)
        json_write(artifact_dir / "trace.json", trace)
    if not costs:
        raise RuntimeError("no billable provider response captured")
    grade = check_trace(trace)
    return trace, usage, aggregate_costs(costs), time.monotonic() - started


def method_prepare(run_dir: Path, base: dict[str, Any], task: str,
                   route_id: str, effort: str) -> tuple[str, dict, dict, str]:
    trace_path = run_dir / "trace.json"
    # Reuse the method schema, then bind this child to the executed-loop checker.
    plan, child = build_contracts(route_id, task, effort, base,
                                 ECON.parent / "tasks" / task, trace_path,
                                 sha256_file(METHOD_PAYLOAD))
    plan["scope"] = "One bounded tool loop, real local tool execution, all request costs, objective outcome and closure evidence."
    plan["strategy"]["summary"] = "Execute tool calls, return every result, and validate the final fixture state."
    plan["evidence"].append({"ref": str(ECON / "tool_runtime.py"), "kind": "artifact",
                              "redaction_state": "metadata_only"})
    child["scope"] = "Complete the user task through executed tools and returned results."
    child["acceptance"] = ["The tool-loop outcome checker passes the saved execution trace.",
                           "All required state changes occur before the model's final response."]
    child["falsifiers"][0]["check"]["command"] = f"{sys.executable} {ECON / 'tool_runtime.py'} {trace_path}"
    child["falsifiers"][0]["description"] = "Replay tool execution and reject missing or incorrect final state."
    ir = run_dir / ".am"
    json_write(ir / "plan.json", plan)
    json_write(ir / "children" / "01.json", child)
    plan_gate = run_json([str(DEFAULT_METHOD_BIN), "validate", "plan", "--ir", str(run_dir), "--json"])
    json_write(run_dir / "plan-gate.json", plan_gate)
    if not plan_gate.get("ok") or plan_gate["_exit_code"] != 0:
        raise RuntimeError("Aegis plan gate denied request")
    digest = hashlib.sha256(json.dumps([plan, child], sort_keys=True).encode()).hexdigest()
    instruction = build_method_instruction(METHOD_PAYLOAD.read_text(), plan, child)
    instruction = instruction.replace("Produce one response", "Complete the tool loop")
    instruction += "\n\nThis task is a real tool loop. Tools execute and return results. Continue until the task is complete, then give a short final answer. The adapter runs the outcome checker after the loop."
    return instruction, child, plan_gate, digest


def run_one(config: dict, route_id: str, task: str, effort: str, rep: int = 1,
            base: dict | None = None, output_root: Path | None = None) -> dict:
    root = output_root or ROOT
    condition = "aegis_enforced_retry" if base else "base"
    stem = f"{route_id}_{task.replace('/', '-')}_{effort}_rep{rep}_{condition}"
    record_path = root / "results" / (stem + ".json")
    run_dir = root / "runs" / stem
    if record_path.exists():
        return json.loads(record_path.read_text())
    archive_incomplete(root, run_dir)
    instruction = None
    child = plan_gate = digest = None
    if base:
        instruction, child, plan_gate, digest = method_prepare(run_dir, base, task, route_id, effort)
        gate_event(run_dir / "gate-transcript.jsonl", "plan_gate_allow", {"ok": True, "contract_sha256": digest})

    def gate(action: str, detail: dict) -> None:
        plan_now = json.loads((run_dir / ".am" / "plan.json").read_text())
        child_now = json.loads((run_dir / ".am" / "children" / "01.json").read_text())
        current = hashlib.sha256(json.dumps([plan_now, child_now], sort_keys=True).encode()).hexdigest()
        if current != digest:
            raise RuntimeError("Aegis frozen contract changed")
        gate_event(run_dir / "gate-transcript.jsonl", action + "_allow", detail)

    started = datetime.now(timezone.utc)
    trace, usage, costs, elapsed = execute_loop(
        config, route_id, task, effort, run_dir, instruction,
        gate_fn=gate if base else None,
    )
    interrupted = prior_receipts(root, stem)
    all_turns = list(trace["turns"])
    for prior in interrupted:
        all_turns.extend(prior["turns"])
        for turn in prior["turns"]:
            for name, value in turn["usage"].items():
                usage[name] = usage.get(name, 0) + value
        elapsed += sum(turn["seconds"] for turn in prior["turns"])
    if interrupted:
        costs = aggregate_costs([turn["costs"] for turn in all_turns])
    # Run the actual declared falsifier command and read its own exit status.
    cp = subprocess.run([sys.executable, str(ECON / "tool_runtime.py"), str(run_dir / "trace.json")],
                        capture_output=True, text=True, timeout=60)
    grade = json.loads(cp.stdout)
    if bool(grade["passed"]) != (cp.returncode == 0):
        raise RuntimeError("checker result disagrees with exit status")
    json_write(run_dir / "objective-checker.json", grade)
    aegis = None
    if base:
        write_closure(run_dir / ".am", child, grade, run_dir / "trace.json", run_dir / "objective-checker.json")
        completion = run_json([str(DEFAULT_METHOD_BIN), "validate", "completion", "--ir", str(run_dir), "--json"])
        closure = run_json([str(DEFAULT_METHOD_BIN), "validate", "closure", "--ir", str(run_dir), "--json"])
        for name, result in [("completion", completion), ("closure", closure)]:
            json_write(run_dir / (name + "-gate.json"), result)
            gate_event(run_dir / "gate-transcript.jsonl", name + ("_allow" if result.get("ok") else "_deny"), result)
        ingest, export, verify = write_evidence_journal(
            run_dir, stem, route_id, task, effort, sha256_file(METHOD_PAYLOAD),
            plan_gate, grade, completion, closure,
        )
        aegis = {"adapter": "bench3-tool-loop-v1", "gates": {"plan": plan_gate, "completion": completion, "closure": closure},
                 "evidence": {"verify": verify}, "method_closed": bool(grade["passed"] and completion.get("ok") and closure.get("ok") and verify.get("valid")),
                 "run_dir": str(run_dir), "payload_sha256": sha256_file(METHOD_PAYLOAD)}
        if not verify.get("valid") or ingest.get("_exit_code") != 0:
            raise RuntimeError("Aegis evidence journal failed verification")
    record = {"schema_version": "bench3.economics.toolloop.v1", "task_contract": CONTRACT,
              "catalog_as_of": config["catalog_as_of"], "started_at_utc": started.isoformat(),
              "route_id": route_id, "route": route_snapshot(config["routes"][route_id]),
              "task": task, "effort": effort, "repetition": rep, "condition": condition,
              "parent_record_path": base.get("record_path") if base else None,
              "grade": grade, "usage": {**usage, "calls": len(all_turns)}, "costs": costs,
              "elapsed_seconds": elapsed, "aegis": aegis,
              "tool_calls": len(trace["tool_events"]) + sum(p["tool_calls"] for p in interrupted),
              "tool_errors": sum(not e["result"].get("ok") for e in trace["tool_events"]),
              "stop_reason": trace["stop_reason"], "final_answer": trace["final_answer"],
              "transport_recovery": {"restarts": len(interrupted), "partial_attempts": interrupted,
                                     "missing_usage_receipts": len(interrupted)},
              "record_path": str(record_path), "response_path": str(run_dir / "trace.json"),
              "limits": {"max_turns": MAX_TURNS, "max_tool_calls": MAX_TOOL_CALLS, "max_output_tokens_per_turn": MAX_OUTPUT_TOKENS},
              "harness_sha256": sha256_file(Path(__file__)), "runtime_sha256": sha256_file(ECON / "tool_runtime.py")}
    json_write(record_path, record)
    with LOCK:
        append_jsonl(root / "results" / "results.jsonl", record)
        print(f"{route_id} | {task} | {effort} | {condition} | pass={grade['passed']} | "
              f"{len(trace['turns'])} calls | {len(trace['tool_events'])} tools | {elapsed:.1f}s | ${costs['cash_cost_usd']:.6f}", flush=True)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", action="append", default=[])
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--effort", action="append", default=[])
    parser.add_argument("--rep", type=int, default=1)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--aegis-on-failure", action="store_true")
    args = parser.parse_args()
    config = load_config()
    routes = args.route or [rid for rid, r in config["routes"].items() if r.get("enabled", True)]
    cells = [(rid, task, effort) for rid in routes for task in (args.task or TASKS)
             for effort in (args.effort or ["low", "high"])]
    random.Random(20261017).shuffle(cells)
    if args.aegis_on_failure:
        if not DEFAULT_METHOD_BIN.is_file() or not METHOD_PAYLOAD.is_file():
            raise SystemExit("Aegis Method binary or payload is unavailable")
    failures = 0

    def run_cell(cell):
        rid, task, effort = cell
        row = run_one(config, rid, task, effort, args.rep)
        if args.aegis_on_failure and row["grade"]["passed"] is False:
            run_one(config, rid, task, effort, args.rep, base=row)

    print(f"selected {len(cells)} tool-loop base runs; Aegis retries={args.aegis_on_failure}", flush=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run_cell, cell): cell for cell in cells}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                failures += 1
                cell = futures[future]
                with LOCK:
                    append_jsonl(ROOT / "failures.jsonl", {"cell": cell, "at": datetime.now(timezone.utc).isoformat(), "error": str(exc)})
                    print(f"INFRA ERROR {cell}: {exc}", flush=True)
    print(f"completed {len(cells)-failures}/{len(cells)} cells; infrastructure errors={failures}", flush=True)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
