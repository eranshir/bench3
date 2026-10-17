#!/usr/bin/env python3
"""Retry failed economics tasks through a benchmark-native Aegis gate.

The adapter keeps the original provider route. It uses the full managed Aegis
Method payload, validates local IR with the official `aegis-method` engine,
blocks task execution until the plan gate passes, runs the existing objective
checker as the falsifier, validates completion and closure, and records a
signed Aegis evidence journal in an isolated per-run state directory.

This is a provider-neutral benchmark adapter. It is not the native Codex or
Claude hook transport.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import (
    ECON,
    append_jsonl,
    calculate_cost,
    load_config,
    load_credentials,
    normalized_usage,
    provider_reported_cost,
)
from run_singleshot import (
    anthropic_body,
    call,
    chat_body,
    normalized_chat_response,
    responses_body,
    run_checker,
    task_inputs,
)


MITHRAN = Path("/Users/eranshir/Documents/Projects/mithran")
METHOD_ROOT = MITHRAN / "aegis-method"
METHOD_PAYLOAD = METHOD_ROOT / "artifacts" / "agents" / "codex" / "AGENTS.md"
DEFAULT_METHOD_BIN = METHOD_ROOT / "target" / "release" / "aegis-method"
RUN_ROOT = ECON / "aegis_enforced_runs"
RESULTS = ECON / "results"
RESPONSES = ECON / "runs"
RESULTS_LOCK = threading.Lock()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.{threading.get_ident()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def run_json(command: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=300,
    )
    try:
        payload = json.loads(completed.stdout)
    except Exception:
        payload = {
            "ok": False,
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
        }
    payload["_exit_code"] = completed.returncode
    return payload


def gate_event(path: Path, event: str, detail: dict[str, Any]) -> dict[str, Any]:
    previous = None
    sequence = 1
    if path.exists():
        lines = [line for line in path.read_text().splitlines() if line.strip()]
        if lines:
            prior = json.loads(lines[-1])
            previous = prior["event_sha256"]
            sequence = int(prior["sequence"]) + 1
    record = {
        "schema_version": "bench3.aegis_gate_event.v1",
        "sequence": sequence,
        "event": event,
        "previous_event_sha256": previous,
        "detail": detail,
    }
    record["event_sha256"] = sha256_bytes(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    )
    append_jsonl(path, record)
    return record


def route_snapshot(route: dict[str, Any]) -> dict[str, Any]:
    return {
        key: route[key]
        for key in (
            "model_family",
            "display",
            "vendor",
            "route",
            "provider",
            "model",
            "billing",
        )
    }


def build_contracts(
    route_id: str,
    task: str,
    effort: str,
    parent_record: dict[str, Any],
    task_dir: Path,
    response_path: Path,
    method_digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt_path = task_dir / "prompt.txt"
    checker_path = task_dir / "check.py"
    parent_ref = parent_record.get("record_path") or parent_record.get("response_path")
    evidence = [
        {
            "ref": "sha256:" + sha256_file(prompt_path),
            "kind": "artifact",
            "redaction_state": "metadata_only",
        },
        {
            "ref": str(parent_ref),
            "kind": "artifact",
            "redaction_state": "metadata_only",
        },
        {
            "ref": "sha256:" + method_digest,
            "kind": "artifact",
            "redaction_state": "metadata_only",
        },
    ]
    plan = {
        "schema_version": "am.local_ir.plan.v2",
        "goal": f"Resolve failed benchmark task {task} with route {route_id} at {effort} effort.",
        "scope": "One provider request, its response artifact, the existing objective checker, and local closure evidence.",
        "target": f"bench3:{task}",
        "evidence": evidence,
        "strategy": {
            "summary": "Keep the original task and route, apply the full Aegis Method payload, and accept only the existing checker result.",
            "assumptions": [
                {
                    "statement": "The existing task checker is the acceptance authority for this retry.",
                    "holds_if": "The checker runs against the saved normalized response and returns a passing result.",
                    "fails_if": "The checker is missing, does not run, or returns a failing result.",
                }
            ],
        },
        "decisions": [
            {
                "statement": "Use a provider-neutral benchmark gate because the Aegis product launcher exposes native hooks only for Codex and Claude Code.",
                "rationale": "The retry must keep the original OpenRouter, LunaRoute, or direct provider route.",
                "reversible": True,
            }
        ],
        "non_goals": [
            "This retry does not claim native Codex-hook or Claude-hook transport equivalence.",
            "This retry does not change the task checker or the base result.",
        ],
    }
    checker_command = f"{sys.executable} {checker_path} {response_path}"
    child = {
        "schema_version": "am.local_ir.child.v2",
        "id": "solve-task",
        "scope": "Produce one response for the benchmark task and evaluate it with the existing objective checker.",
        "acceptance": [
            "The existing objective checker reports passed for the saved normalized response.",
            "The response uses the task's required answer or tool-call format.",
        ],
        "falsifiers": [
            {
                "id": "objective-checker",
                "description": "The existing benchmark checker rejects an incorrect response or tool call.",
                "check": {
                    "command": checker_command,
                    "expected_outcome": "zero",
                },
            }
        ],
        "status": "in_progress",
        "evidence_refs": evidence,
    }
    return plan, child


def build_method_instruction(
    method_text: str,
    plan: dict[str, Any],
    child: dict[str, Any],
) -> str:
    return "\n\n".join(
        [
            method_text.strip(),
            """# Benchmark work order

The benchmark adapter is the coordinator. You are a delegate. The adapter has
validated the local Aegis IR before this request. Do not change the contract.
Do not discuss the method in the answer. Complete only the benchmark task.
Return only the answer or tool call that the task requests. The adapter will
run the independent checker and will record closure after your response.""",
            "# Validated parent contract\n\n```json\n"
            + json.dumps(plan, sort_keys=True)
            + "\n```",
            "# Validated child contract\n\n```json\n"
            + json.dumps(child, sort_keys=True)
            + "\n```",
        ]
    )


def write_closure(
    ir_dir: Path,
    child: dict[str, Any],
    grade: dict[str, Any],
    response_path: Path,
    checker_output_path: Path,
) -> dict[str, Any]:
    passed = grade.get("passed") is True
    child = dict(child)
    child["status"] = "complete" if passed else "in_progress"
    json_write(ir_dir / "children" / "01.json", child)
    closure = {
        "schema_version": "am.local_ir.closure.v2",
        "reconciliations": [
            {
                "child_id": "solve-task",
                "falsifier_results": [
                    {
                        "falsifier_id": "objective-checker",
                        "result": "pass" if passed else "fail",
                        "output_ref": str(checker_output_path),
                    }
                ],
                "acceptance_reconciliation": (
                    "Both acceptance criteria are met. The objective checker passed the saved normalized response."
                    if passed
                    else "Acceptance is not met. The objective checker rejected the saved normalized response."
                ),
                "landed_refs": [str(response_path)],
            }
        ],
    }
    json_write(ir_dir / "closure.json", closure)
    return closure


def write_evidence_journal(
    run_dir: Path,
    session_id: str,
    route_id: str,
    task: str,
    effort: str,
    method_digest: str,
    plan_gate: dict[str, Any],
    grade: dict[str, Any],
    completion_gate: dict[str, Any],
    closure_gate: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state_dir = run_dir / "evidence-state"
    observations_path = run_dir / "evidence-observations.json"
    steps = [
        {
            "text": "plan_gate",
            "status": "completed" if plan_gate.get("ok") else "blocked",
        },
        {
            "text": "objective_checker",
            "status": "completed" if grade.get("passed") else "blocked",
        },
        {
            "text": "completion_gate",
            "status": "completed" if completion_gate.get("ok") else "blocked",
        },
        {
            "text": "closure_gate",
            "status": "completed" if closure_gate.get("ok") else "blocked",
        },
    ]
    observation = {
        "observations": [
            {
                "schema_version": "aegis.local.observation.v0",
                "surface": "bench3-provider-neutral",
                "kind": "plan_update",
                "session_id": session_id,
                "project_path": str(run_dir),
                "route_id": route_id,
                "task": task,
                "effort": effort,
                "method_digest": "sha256:" + method_digest,
                "steps": steps,
            }
        ]
    }
    json_write(observations_path, observation)
    ingest = run_json(
        [
            "aegis",
            "observe",
            "review",
            "--file",
            str(observations_path),
            "--state-dir",
            str(state_dir),
            "--write-store",
        ]
    )
    export_path = run_dir / "evidence-export.json"
    export = run_json(
        [
            "aegis",
            "evidence",
            "export",
            "--state-dir",
            str(state_dir),
            "--output",
            str(export_path),
            "--json",
        ]
    )
    verify = run_json(
        [
            "aegis",
            "evidence",
            "verify",
            "--state-dir",
            str(state_dir),
            "--json",
        ]
    )
    json_write(run_dir / "evidence-ingest-result.json", ingest)
    json_write(run_dir / "evidence-export-result.json", export)
    json_write(run_dir / "evidence-verify-result.json", verify)
    return ingest, export, verify


def run_one(
    config: dict[str, Any],
    parent_record: dict[str, Any],
    method_bin: Path,
    force: bool,
    output_root: Path | None = None,
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    route_id = parent_record["route_id"]
    task = parent_record["task"]
    effort = parent_record["effort"]
    rep = int(parent_record.get("repetition", 1))
    route = config["routes"][route_id]
    safe_task = task.replace("/", "-")
    stem = f"{route_id}_{safe_task}_{effort}_rep{rep}_aegis_enforced"
    results_dir = output_root / "results" if output_root else RESULTS
    responses_dir = output_root / "runs" if output_root else RESPONSES
    run_root = output_root / "aegis_enforced_runs" if output_root else RUN_ROOT
    record_path = results_dir / f"{stem}.json"
    response_path = responses_dir / f"{stem}.response.json"
    run_dir = run_root / stem
    transcript_path = run_dir / "gate-transcript.jsonl"
    if record_path.exists() and not force:
        return json.loads(record_path.read_text())
    if force and run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    session_id = sha256_bytes(stem.encode())[:24]
    method_text = METHOD_PAYLOAD.read_text()
    method_digest = sha256_bytes(method_text.encode())
    task_dir, messages, tools, max_tokens = task_inputs(task)
    # A paired retry must use the same output budget as its failed base task.
    max_tokens = max_output_tokens or parent_record.get("request", {}).get("max_output_tokens") or max_tokens
    plan, child = build_contracts(
        route_id,
        task,
        effort,
        parent_record,
        task_dir,
        response_path,
        method_digest,
    )
    ir_dir = run_dir / ".am"
    json_write(ir_dir / "plan.json", plan)
    json_write(ir_dir / "children" / "01.json", child)
    gate_event(
        transcript_path,
        "original_commitments_frozen",
        {
            "session_id": session_id,
            "method_digest": "sha256:" + method_digest,
            "parent_record_path": parent_record.get("record_path"),
        },
    )
    plan_gate = run_json(
        [str(method_bin), "validate", "plan", "--ir", str(run_dir), "--json"]
    )
    json_write(run_dir / "plan-gate.json", plan_gate)
    gate_event(
        transcript_path,
        "plan_gate_allow" if plan_gate.get("ok") else "plan_gate_deny",
        {"exit_code": plan_gate["_exit_code"], "finding_class": plan_gate.get("finding_class")},
    )
    if not plan_gate.get("ok"):
        raise RuntimeError(f"plan gate denied {stem}: {plan_gate.get('verdict')}")

    messages.insert(0, {
        "role": "system",
        "content": build_method_instruction(method_text, plan, child),
    })
    if route["api_shape"] == "openai-responses":
        body = responses_body(route, messages, tools, effort, max_tokens)
    elif route["api_shape"] == "anthropic-messages":
        body = anthropic_body(route, messages, tools, effort, max_tokens)
    else:
        body = chat_body(route, messages, tools, effort, max_tokens)
    creds = load_credentials()
    key = creds.get(route["credential"], "")
    if not key:
        raise RuntimeError("missing credential: %s" % route["credential"])
    started = datetime.now(timezone.utc)
    gate_event(
        transcript_path,
        "task_request_allow",
        {"route_id": route_id, "task": task, "effort": effort},
    )
    raw, elapsed = call(route, key, body)
    normalized = normalized_chat_response(raw, route["api_shape"])
    json_write(response_path, normalized)
    grade = run_checker(task_dir, response_path)
    checker_output_path = run_dir / "objective-checker.json"
    json_write(checker_output_path, grade)
    gate_event(
        transcript_path,
        "falsifier_pass" if grade.get("passed") else "falsifier_fail",
        {
            "checker": str(task_dir / "check.py"),
            "response_sha256": "sha256:" + sha256_file(response_path),
        },
    )
    closure = write_closure(ir_dir, child, grade, response_path, checker_output_path)
    completion_gate = run_json(
        [str(method_bin), "validate", "completion", "--ir", str(run_dir), "--json"]
    )
    closure_gate = run_json(
        [str(method_bin), "validate", "closure", "--ir", str(run_dir), "--json"]
    )
    json_write(run_dir / "completion-gate.json", completion_gate)
    json_write(run_dir / "closure-gate.json", closure_gate)
    gate_event(
        transcript_path,
        "completion_gate_allow" if completion_gate.get("ok") else "completion_gate_deny",
        {"exit_code": completion_gate["_exit_code"], "finding_class": completion_gate.get("finding_class")},
    )
    gate_event(
        transcript_path,
        "closure_gate_allow" if closure_gate.get("ok") else "closure_gate_deny",
        {"exit_code": closure_gate["_exit_code"], "finding_class": closure_gate.get("finding_class")},
    )
    ingest, export, verify = write_evidence_journal(
        run_dir,
        session_id,
        route_id,
        task,
        effort,
        method_digest,
        plan_gate,
        grade,
        completion_gate,
        closure_gate,
    )
    gate_event(
        transcript_path,
        "evidence_journal_verified" if verify.get("valid") else "evidence_journal_invalid",
        {
            "evidence_ref": verify.get("evidence_ref"),
            "entry_count": verify.get("journal", {}).get("entry_count"),
        },
    )

    usage = normalized_usage(raw)
    provider_cost = provider_reported_cost(raw)
    costs = calculate_cost(config, route, usage, started, provider_cost=provider_cost)
    task_passed = grade.get("passed") is True
    method_closed = bool(
        plan_gate.get("ok")
        and completion_gate.get("ok")
        and closure_gate.get("ok")
        and verify.get("valid")
    )
    record = {
        "schema_version": "bench3.economics.v1",
        "catalog_as_of": config["catalog_as_of"],
        "started_at_utc": started.isoformat(),
        "route_id": route_id,
        "route": route_snapshot(route),
        "upstream_provider": raw.get("provider"),
        "task": task,
        "effort": effort,
        "repetition": rep,
        "condition": "aegis_enforced_retry",
        "parent_record_path": parent_record.get("record_path"),
        "aegis": {
            "mode": "enforce",
            "adapter": "bench3-provider-neutral-v1",
            "native_hook_transport": False,
            "method_source": str(METHOD_PAYLOAD),
            "method_version": plan_gate.get("method", {}).get("version"),
            "method_sha256": method_digest,
            "method_binary": str(method_bin),
            "method_binary_sha256": sha256_file(method_bin),
            "local_ir_dir": str(ir_dir),
            "contracts": {
                "plan": str(ir_dir / "plan.json"),
                "child": str(ir_dir / "children" / "01.json"),
                "closure": str(ir_dir / "closure.json"),
            },
            "gates": {
                "plan": plan_gate,
                "completion": completion_gate,
                "closure": closure_gate,
            },
            "gate_transcript": str(transcript_path),
            "evidence": {
                "ingest": ingest,
                "export": export,
                "verify": verify,
                "journal_path": str(run_dir / "evidence-state" / "observed-events.jsonl"),
                "export_path": str(run_dir / "evidence-export.json"),
            },
            "method_closed": method_closed,
        },
        "elapsed_seconds": elapsed,
        "usage": usage,
        "costs": costs,
        "grade": grade,
        "request": {
            "max_output_tokens": max_tokens,
            "has_tools": bool(tools),
            "method_input_chars": len(messages[0]["content"]),
        },
        "record_path": str(record_path),
        "response_path": str(response_path),
    }
    json_write(record_path, record)
    with RESULTS_LOCK:
        append_jsonl(results_dir / "results.jsonl", record)
    print(
        "%s | %s | %s | pass=%s | closed=%s | %.1fs | %d tokens | cash=$%.6f"
        % (
            route_id,
            task,
            effort,
            task_passed,
            method_closed,
            elapsed,
            usage["total_tokens"],
            costs["cash_cost_usd"],
        ),
        flush=True,
    )
    return record


def failed_base_records(
    route_filters: set[str], task_filters: set[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(RESULTS.glob("*.json")):
        try:
            row = json.loads(path.read_text())
        except Exception:
            continue
        if row.get("schema_version") != "bench3.economics.v1":
            continue
        if row.get("condition", "base") != "base":
            continue
        if row.get("grade", {}).get("passed") is not False:
            continue
        if route_filters and row.get("route_id") not in route_filters:
            continue
        if task_filters and row.get("task") not in task_filters:
            continue
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", action="append", default=[])
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--method-bin",
        default=os.environ.get("AEGIS_METHOD_CMD", str(DEFAULT_METHOD_BIN)),
    )
    args = parser.parse_args()
    method_bin = Path(args.method_bin).resolve()
    if not method_bin.exists() or not os.access(method_bin, os.X_OK):
        raise SystemExit("Aegis Method binary is not executable: %s" % method_bin)
    if not METHOD_PAYLOAD.exists():
        raise SystemExit("Aegis Method payload is missing: %s" % METHOD_PAYLOAD)
    if not shutil.which("aegis"):
        raise SystemExit("Aegis CLI is not available on PATH")
    config = load_config()
    rows = failed_base_records(set(args.route), set(args.task))
    if args.limit is not None:
        rows = rows[: args.limit]
    print("selected %d failed base task(s)" % len(rows), flush=True)
    failures = 0
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        future_rows = {
            pool.submit(run_one, config, row, method_bin, args.force): row for row in rows
        }
        for future in as_completed(future_rows):
            row = future_rows[future]
            try:
                future.result()
            except Exception as exc:
                failures += 1
                failure = {
                    "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "condition": "aegis_enforced_retry",
                    "route_id": row.get("route_id"),
                    "task": row.get("task"),
                    "effort": row.get("effort"),
                    "error": str(exc)[:2000],
                }
                with RESULTS_LOCK:
                    append_jsonl(RESULTS / "failures.jsonl", failure)
                print(
                    "FAILED %s | %s | %s: %s"
                    % (row.get("route_id"), row.get("task"), row.get("effort"), exc),
                    file=sys.stderr,
                    flush=True,
                )
    print("completed=%d failed=%d" % (len(rows) - failures, failures), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
