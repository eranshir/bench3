#!/usr/bin/env python3
"""Run ten new objective repetitions with resumable cells and live reports."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import http.client
import json
import os
import random
import shutil
import subprocess
import sys
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from common import ECON, append_jsonl, load_config
from aegis_enforced_retry import DEFAULT_METHOD_BIN, METHOD_PAYLOAD, json_write
from aegis_enforced_retry import run_one as run_enforced
from run_singleshot import run_one as run_reasoning
from run_toolloop import run_one as run_tools
from campaign_stats import CURRENT, campaign_root, cost, read_records, row_key


TASKS = ["reasoning/r1_tiling", "reasoning/r2_expectedflips", "reasoning/r3_die_expected",
         "reasoning/r4_catalan", "tool-use/t1_orchestrate", "tool-use/t2_toolselect", "tool-use/t3_inventory"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def initialize(root: Path, jobs: int) -> None:
    if (root / "manifest.json").exists():
        raise RuntimeError("campaign already exists; use --resume")
    config = load_config()
    routes = [rid for rid, r in config["routes"].items() if r.get("enabled", True)]
    pinned = [ECON / name for name in ["run_campaign.py", "run_singleshot.py", "run_toolloop.py", "tool_runtime.py",
              "toolloop_recovery.py", "aegis_enforced_retry.py", "common.py"]]
    pinned.extend([METHOD_PAYLOAD, DEFAULT_METHOD_BIN])
    for task in TASKS:
        pinned.extend(p for p in (ECON.parent / "tasks" / task).iterdir() if p.is_file())
    root.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": "bench3.campaign.v1", "id": root.name,
                "created_at_utc": now(), "config": config, "routes": routes, "tasks": TASKS,
                "efforts": ["low", "high"], "repetitions": 10,
                "rep_ids": list(range(2, 12)), "pilot_rep_excluded": 1,
                "planned_base": len(routes)*len(TASKS)*2*10, "jobs": jobs,
                "output_tokens": {task: 4096 if task == "reasoning/r1_tiling" or task.startswith("tool-use/") else 8192 for task in TASKS},
                "method": "full managed Aegis, official plan/completion/closure gates and signed journals",
                "source_sha256": {str(p): digest(p) for p in pinned}}
    json_write(root / "manifest.json", manifest)
    json_write(root / "status.json", {"state": "prepared", "started_at_utc": None,
               "updated_at_utc": now(), "completedRounds": 0, "currentRound": 0,
               "completedCells": 0, "infrastructureErrors": 0, "message": "Ready for ten new repetitions."})
    json_write(CURRENT, {"root": str(root)})


def state_write(root: Path, document: dict, **updates) -> None:
    document.update(updates, updated_at_utc=now())
    json_write(root / "status.json", document)


def publish(root: Path) -> None:
    from build_report_data import main as build_report
    build_report()


def is_transport_error(exc: Exception) -> bool:
    if isinstance(exc, (ConnectionError, TimeoutError, urllib.error.URLError, http.client.IncompleteRead)):
        return True
    text = str(exc)
    return any(fragment in text for fragment in ["HTTP 429", "HTTP 500", "HTTP 502", "HTTP 503", "HTTP 504"])


def run_cell(root: Path, manifest: dict, cell: tuple) -> None:
    rid, task, effort, rep = cell
    config = manifest["config"]
    for attempt in range(1, 4):
        try:
            if task.startswith("tool-use/"):
                base = run_tools(config, rid, task, effort, rep, output_root=root / "toolloop")
                if base["grade"]["passed"] is False:
                    retry = run_tools(config, rid, task, effort, rep, base=base, output_root=root / "toolloop")
                else:
                    retry = None
            else:
                cap = manifest["output_tokens"][task]
                base = run_reasoning(config, rid, effort, task, rep, False,
                                     max_output_tokens=cap, output_root=root / "reasoning")
                retry = (run_enforced(config, base, DEFAULT_METHOD_BIN, False,
                                      output_root=root / "reasoning", max_output_tokens=cap)
                         if base["grade"]["passed"] is False else None)
            if retry:
                verification = retry["aegis"]["evidence"]["verify"]
                if not verification.get("valid"):
                    raise RuntimeError("Aegis journal is invalid")
                if retry["grade"]["passed"] and not retry["aegis"].get("method_closed"):
                    raise RuntimeError("Aegis closure is missing for a passing retry")
            return
        except Exception as exc:
            append_jsonl(root / "transport-events.jsonl", {"cell": cell, "attempt": attempt,
                         "at_utc": now(), "error": str(exc)[:1500], "transport": is_transport_error(exc)})
            if not is_transport_error(exc) or attempt == 3:
                raise
            # This retry addresses transport only. Model task failures use the
            # separate enforced Aegis condition, never this exception path.
            time.sleep(min(attempt*2, 6))


def verify_round(root: Path, manifest: dict, rep: int) -> dict:
    base, retries = read_records(root)
    rows = [r for r in base if r["repetition"] == rep]
    expected = {(rid, task, effort, rep) for rid in manifest["routes"] for task in TASKS for effort in manifest["efforts"]}
    actual = {row_key(r) for r in rows}
    if len(rows) != len(expected) or actual != expected:
        raise RuntimeError("round coverage does not match the pinned matrix")
    retry_map = {row_key(r): r for r in retries}
    for row in rows:
        if row["task"].startswith("tool-use/"):
            from tool_runtime import check_trace
            if check_trace(json.loads(Path(row["response_path"]).read_text())) != row["grade"]:
                raise RuntimeError("tool trace failed independent replay")
        else:
            from run_singleshot import run_checker
            if run_checker(ECON.parent / "tasks" / row["task"], Path(row["response_path"])) != row["grade"]:
                raise RuntimeError("reasoning grade failed independent replay")
        if row["grade"]["passed"] is False and row_key(row) not in retry_map:
            raise RuntimeError("failed base task is missing its Aegis retry")
    return {"repetition": rep, "round": rep-1, "runs": len(rows),
            "passes": sum(bool(r["grade"]["passed"]) for r in rows),
            "retries": sum(row_key(r) in retry_map for r in rows), "verified_at_utc": now()}


def worker(root: Path) -> int:
    manifest = json.loads((root / "manifest.json").read_text())
    state = json.loads((root / "status.json").read_text())
    # One worker owns a campaign. A second resume process cannot duplicate calls.
    with (root / "worker.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("This campaign already has an active worker.")
        state_write(root, state, state="running", pid=os.getpid(),
                    started_at_utc=state.get("started_at_utc") or now(),
                    message="Ten new repetitions are running.")
        publish(root)
        try:
            for index, rep in enumerate(manifest["rep_ids"], 1):
                for path, expected in manifest["source_sha256"].items():
                    if digest(Path(path)) != expected:
                        raise RuntimeError("Pinned benchmark source changed: " + path)
                cells = [(rid, task, effort, rep) for rid in manifest["routes"]
                         for task in manifest["tasks"] for effort in manifest["efforts"]]
                random.Random(20261017 + rep).shuffle(cells)
                state_write(root, state, currentRound=index, message=f"Repetition {index}/10 is running.")
                errors = []
                with ThreadPoolExecutor(max_workers=manifest["jobs"]) as pool:
                    futures = {pool.submit(run_cell, root, manifest, cell): cell for cell in cells}
                    for future in as_completed(futures):
                        cell = futures[future]
                        try:
                            future.result()
                        except Exception as exc:
                            errors.append({"cell": cell, "error": str(exc)[:1500]})
                            print(f"CELL NEEDS ATTENTION {cell}: {exc}", flush=True)
                        base, retry = read_records(root)
                        state_write(root, state, completedCells=len(base),
                                    infrastructureErrors=len(errors),
                                    message=f"Repetition {index}/10; {len(base)}/{manifest['planned_base']} base tasks recorded.")
                        # Every completed cell publishes a fresh page data file.
                        publish(root)
                if errors:
                    state_write(root, state, state="needs_attention", errors=errors,
                                message="Some cells have unresolved infrastructure errors. Resume after diagnosis.")
                    publish(root)
                    return 2
                proof = verify_round(root, manifest, rep)
                json_write(root / "checkpoints" / f"round-{index:02d}-verification.json", proof)
                state_write(root, state, completedRounds=index, message=f"Repetition {index}/10 verified and published.")
                publish(root)
                shutil.copyfile(ECON / "report_data.js", root / "checkpoints" / f"round-{index:02d}-report_data.js")
                print(f"ROUND {index}/10 VERIFIED {proof}", flush=True)
            state_write(root, state, state="complete", completed_at_utc=now(),
                        message="All ten repetitions are complete. Every round passed the coverage and replay checks.")
            publish(root)
            return 0
        except Exception as exc:
            state_write(root, state, state="needs_attention", message=str(exc)[:2000])
            publish(root)
            raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--campaign", type=Path)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()
    root = args.campaign or campaign_root()
    if args.status:
        print(json.dumps(json.loads((root / "status.json").read_text()), indent=2))
        return 0
    if args.report_only:
        publish(root)
        return 0
    if args.worker:
        return worker(root)
    if args.launch or args.resume:
        if not args.resume:
            root = args.campaign or ECON / "campaigns" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-objective-k10")
            initialize(root, args.jobs)
        elif root is None:
            raise SystemExit("No campaign is available to resume.")
        with (root / "worker.log").open("ab") as log:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--worker", "--campaign", str(root)],
                                       cwd=str(ECON), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
        json_write(root / "process.json", {"pid": process.pid, "launched_at_utc": now()})
        print(json.dumps({"root": str(root), "pid": process.pid, "planned_base": 2100, "repetitions": 10}, indent=2))
        return 0
    parser.error("Choose --launch, --resume, --status, --report-only, or --worker.")


if __name__ == "__main__":
    raise SystemExit(main())
