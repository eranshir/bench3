#!/usr/bin/env python3
"""Add new model routes without repeating the completed baseline API calls."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from aegis_enforced_retry import json_write
from campaign_stats import read_records
from common import ECON, load_config
from run_campaign import digest, initialize, now


def prepare(root: Path, baseline: Path, routes: list[str], jobs: int) -> dict:
    old = json.loads((baseline / "manifest.json").read_text())
    status = json.loads((baseline / "status.json").read_text())
    audit = json.loads((baseline / "final_audit.json").read_text())
    if status["state"] != "complete" or not audit.get("valid"):
        raise RuntimeError("The baseline must be complete and independently audited")
    config = load_config()
    if not routes or len(set(routes)) != len(routes):
        raise ValueError("Choose distinct new routes")
    if set(routes) & set(old["routes"]):
        raise ValueError("A completed baseline route must not be run again")
    for rid in routes:
        if rid not in config["routes"] or not config["routes"][rid].get("enabled", True):
            raise ValueError("Unknown or disabled new route: " + rid)
    for rid in old["routes"]:
        if config["routes"][rid] != old["config"]["routes"][rid]:
            raise RuntimeError("A baseline route configuration changed: " + rid)
    for name, expected in old["source_sha256"].items():
        if digest(Path(name)) != expected:
            raise RuntimeError("A pinned baseline source changed: " + name)
    rows, retries = read_records(baseline)
    if len(rows) != old["planned_base"] or len(rows) != audit["base_records"]:
        raise RuntimeError("The baseline record count does not match its audit")
    initialize(root, jobs)
    manifest = json.loads((root / "manifest.json").read_text())
    if (manifest["tasks"], manifest["efforts"], manifest["rep_ids"], manifest["output_tokens"]) != (
            old["tasks"], old["efforts"], old["rep_ids"], old["output_tokens"]):
        raise RuntimeError("The extension does not match the baseline task contract")
    manifest["routes"] = routes
    manifest["planned_base"] = len(routes) * len(old["tasks"]) * len(old["efforts"]) * old["repetitions"]
    manifest["extension"] = {
        "baseline_root": str(baseline), "baseline_base_records": len(rows),
        "baseline_retry_records": len(retries), "new_routes": routes,
        "baseline_manifest_sha256": digest(baseline / "manifest.json"),
        "baseline_audit_sha256": digest(baseline / "final_audit.json"),
        "note": "Existing baseline observations are retained, not rerun. The new route runs later with the same task and budget contract.",
    }
    for name in ["extend_campaign.py", "campaign_stats.py", "build_report_data.py", "analyze_toolloop.py", "verify_campaign.py"]:
        path = ECON / name
        manifest["source_sha256"][str(path)] = digest(path)
    json_write(root / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--route", action="append", required=True)
    parser.add_argument("--campaign", type=Path)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    root = args.campaign or ECON / "campaigns" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-ds41-1017-k10")
    manifest = prepare(root.resolve(), args.baseline.resolve(), args.route, args.jobs)
    pid = None
    if not args.prepare_only:
        with (root / "worker.log").open("ab") as log:
            worker = subprocess.Popen([sys.executable, str(ECON / "run_campaign.py"), "--worker", "--campaign", str(root)],
                                      cwd=ECON, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                      start_new_session=True)
        pid = worker.pid
        json_write(root / "process.json", {"pid": pid, "launched_at_utc": now()})
    print(json.dumps({"root": str(root), "pid": pid, "new_base_tasks": manifest["planned_base"],
                      "reused_baseline_tasks": manifest["extension"]["baseline_base_records"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
