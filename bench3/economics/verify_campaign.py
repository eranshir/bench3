#!/usr/bin/env python3
"""Recheck a completed campaign without making provider requests."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from aegis_enforced_retry import DEFAULT_METHOD_BIN, json_write
from campaign_stats import campaign_root, read_records, row_key, wilson
from common import ECON
from run_singleshot import run_checker
from tool_runtime import check_trace


def command_json(args: list[str]) -> dict:
    result = subprocess.run(args, capture_output=True, text=True, timeout=60)
    value = json.loads(result.stdout)
    value["command_exit_code"] = result.returncode
    return value


def verify_row(row: dict) -> None:
    response = Path(row["response_path"])
    grade = (check_trace(json.loads(response.read_text())) if row["task"].startswith("tool-use/")
             else run_checker(ECON.parent / "tasks" / row["task"], response))
    if grade != row["grade"]:
        raise RuntimeError("Grade replay differs: " + str(row_key(row)))
    if row.get("condition", "base") == "base":
        return
    method = row["aegis"]
    run_dir = Path(method.get("local_ir_dir") or method["run_dir"])
    for gate in ["plan", "completion", "closure"]:
        value = command_json([str(DEFAULT_METHOD_BIN), "validate", gate, "--ir", str(run_dir), "--json"])
        expected = gate == "plan" or bool(grade["passed"])
        if bool(value.get("ok")) != expected or (expected and value["command_exit_code"] != 0):
            raise RuntimeError("Method gate replay differs: " + gate + " " + str(row_key(row)))
    journal = command_json(["aegis", "evidence", "verify", "--state-dir", str(run_dir / "evidence-state"), "--json"])
    if not journal.get("valid") or journal["command_exit_code"] != 0:
        raise RuntimeError("Evidence journal is invalid: " + str(row_key(row)))
    if not method["evidence"]["verify"].get("valid"):
        raise RuntimeError("Saved evidence journal verification is invalid")
    if bool(method.get("method_closed")) != bool(grade["passed"]):
        raise RuntimeError("Method closure disagrees with grade")


def verify(root: Path, jobs: int = 8) -> dict:
    with (root / "worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status = json.loads((root / "status.json").read_text())
        manifest = json.loads((root / "manifest.json").read_text())
        if status["state"] != "complete":
            raise RuntimeError("The campaign is not complete")
        for name, expected in manifest["source_sha256"].items():
            if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
                raise RuntimeError("Pinned source changed: " + name)
        base, retries = read_records(root)
        expected = {(rid, task, effort, rep) for rid in manifest["routes"] for task in manifest["tasks"]
                    for effort in manifest["efforts"] for rep in manifest["rep_ids"]}
        actual = [row_key(r) for r in base]
        if len(base) != manifest["planned_base"] or len(set(actual)) != len(actual) or set(actual) != expected:
            raise RuntimeError("Base records do not match the declared matrix")
        failed = {row_key(r) for r in base if not r["grade"]["passed"]}
        retry_keys = [row_key(r) for r in retries]
        if len(retry_keys) != len(set(retry_keys)) or set(retry_keys) != failed:
            raise RuntimeError("Retry records do not match failed base tasks")
        if any(r["condition"] != "aegis_enforced_retry" for r in retries):
            raise RuntimeError("A retry did not use the enforced condition")
        round_size = len(manifest["routes"]) * len(manifest["tasks"]) * len(manifest["efforts"])
        for index, rep in enumerate(manifest["rep_ids"], 1):
            proof = json.loads((root / "checkpoints" / f"round-{index:02d}-verification.json").read_text())
            rows = [r for r in base if r["repetition"] == rep]
            required = {"round": index, "repetition": rep, "runs": round_size,
                        "passes": sum(bool(r["grade"]["passed"]) for r in rows),
                        "retries": sum(not r["grade"]["passed"] for r in rows)}
            if any(proof[k] != v for k, v in required.items()):
                raise RuntimeError("Round proof differs from records")
            snapshot_text = (root / "checkpoints" / f"round-{index:02d}-report_data.js").read_text()
            snapshot = json.loads(snapshot_text.removeprefix("window.REPORT_DATA = ").strip().removesuffix(";"))
            if snapshot["campaign"]["baseRuns"] != index * round_size or snapshot["campaign"]["completedRounds"] != index:
                raise RuntimeError("Round snapshot coverage differs")
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            list(pool.map(verify_row, base + retries))
        base_passes = sum(bool(r["grade"]["passed"]) for r in base)
        recovered = sum(bool(r["grade"]["passed"]) for r in retries)
        tool_rows = [r for r in base if r["task"].startswith("tool-use/")]
        return {
            "verified_at_utc": datetime.now(timezone.utc).isoformat(), "valid": True,
            "base_records": len(base), "matrix_cells": len(expected), "round_proofs": len(manifest["rep_ids"]),
            "replayed_grades": len(base) + len(retries), "enforced_retries": len(retries),
            "journals_reverified": len(retries), "method_gates_replayed": len(retries) * 3,
            "base_passes": base_passes, "base_pass_ci95": wilson(base_passes, len(base)),
            "recoveries": recovered, "recovery_ci95": wilson(recovered, len(retries)),
            "after_retry_passes": base_passes + recovered,
            "after_retry_ci95": wilson(base_passes + recovered, len(base)),
            "tool_passes": sum(bool(r["grade"]["passed"]) for r in tool_rows), "tool_runs": len(tool_rows),
            "failures_by_task": dict(Counter(r["task"] for r in base if not r["grade"]["passed"])),
            "cash_cost_usd": sum(r["costs"]["cash_cost_usd"] for r in base + retries),
            "allocated_cost_usd": sum(r["costs"].get("capacity_allocated_cost_usd") or 0 for r in base + retries),
            "provider_requests_made_by_audit": 0,
            "extension": manifest.get("extension"),
            "scope": "Repeated fixed tasks, not unseen-task generalization or a causal Aegis comparison.",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, default=campaign_root())
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()
    result = verify(args.campaign, args.jobs)
    if args.save:
        json_write(args.campaign / "final_audit.json", result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
