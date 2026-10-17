"""Retain and account for provider receipts from interrupted tool workflows."""
from __future__ import annotations

import json
from pathlib import Path


def archive_incomplete(root: Path, run_dir: Path) -> None:
    if not (run_dir / "trace.json").exists():
        return
    parent = root / "infra_attempts"
    parent.mkdir(parents=True, exist_ok=True)
    number = 1
    while (parent / f"{run_dir.name}_attempt{number}").exists():
        number += 1
    run_dir.rename(parent / f"{run_dir.name}_attempt{number}")


def prior_receipts(root: Path, stem: str) -> list[dict]:
    rows = []
    for path in sorted((root / "infra_attempts").glob(stem + "_attempt*/trace.json")):
        trace = json.loads(path.read_text())
        rows.append({"trace_path": str(path), "turns": trace["turns"],
                     "tool_calls": len(trace["tool_events"]),
                     "note": "Interrupted provider connection. Tool state was discarded before restart. "
                             "Returned receipts are included. The interrupted request had no usage receipt."})
    return rows
