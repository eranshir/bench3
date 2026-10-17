#!/usr/bin/env python3
"""Export only public report assets to the existing GitHub Pages directory."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ECON = Path(__file__).resolve().parent
REPO = ECON.parents[1]
ASSETS = [
    "report.html", "report_data.js", "hybrid_cost.js", "REPORT.md", "SCALE.csv", "routes.yaml",
    "aegis_enforced_retry.py", "aegis_method_payload.md", "tool_runtime.py",
    "run_toolloop.py", "toolloop/REPORT.md", "toolloop/TASK_ECONOMICS.csv",
    "toolloop/audit.json",
]


def source_bytes(relative: str, staged: bool) -> bytes:
    path = Path("bench3/economics") / relative
    if staged:
        return subprocess.check_output(["git", "show", ":" + path.as_posix()], cwd=REPO)
    return (REPO / path).read_bytes()


def export(destination: Path, staged: bool = False) -> dict:
    data_source = source_bytes("report_data.js", staged)
    data = json.loads(data_source.decode().removeprefix("window.REPORT_DATA = ").strip().removesuffix(";"))
    campaign = data.get("campaign")
    assets = {name: source_bytes(name, staged) for name in ASSETS}
    assets["report_data.js"] = data_source
    if campaign:
        # Read only the campaign named in the public report. Never copy raw
        # sessions, credentials, signing keys, or complete run directories.
        name = Path(campaign["root"]).name
        if name in {"", ".", ".."}:
            raise ValueError("Invalid campaign directory name")
        prefix = f"campaigns/{name}/"
        summary = source_bytes(prefix + "summary.json", staged)
        stats = json.loads(summary)["campaign"]
        if (stats["baseRuns"], stats["updated_at_utc"]) != (campaign["baseRuns"], campaign["updated_at_utc"]):
            raise ValueError("Report and summary differ. Stage one consistent snapshot, then export again.")
        assets[prefix + "summary.json"] = summary
        assets[prefix + "TASK_ECONOMICS.csv"] = source_bytes(prefix + "TASK_ECONOMICS.csv", staged)
        if campaign["state"] == "complete":
            for name in ["FINAL_REPORT.md", "final_audit.json"]:
                assets[prefix + name] = source_bytes(prefix + name, staged)
        for round_id in range(1, campaign["completedRounds"] + 1):
            proof = prefix + f"checkpoints/round-{round_id:02d}-verification.json"
            assets[proof] = source_bytes(proof, staged)
        baseline = campaign.get("baseline")
        if baseline:
            baseline_prefix = f'campaigns/{Path(baseline["root"]).name}/'
            for name in ["summary.json", "TASK_ECONOMICS.csv", "FINAL_REPORT.md", "final_audit.json"]:
                assets[baseline_prefix + name] = source_bytes(baseline_prefix + name, staged)
            for round_id in range(1, baseline["completedRounds"] + 1):
                proof = baseline_prefix + f"checkpoints/round-{round_id:02d}-verification.json"
                assets[proof] = source_bytes(proof, staged)
    html = assets.pop("report.html").decode()
    marker = '<script>window.REPORT_SNAPSHOT = true;</script>\n'
    if '<script src="report_data.js"></script>' not in html:
        raise ValueError("Cannot find the report data entry point")
    html = html.replace('<script src="report_data.js"></script>', marker + '<script src="report_data.js"></script>', 1)
    assets["index.html"] = html.encode()
    # Retained reports link to report.html for local use. Keep that link
    # valid in the public snapshot as well as the directory's index URL.
    assets["report.html"] = html.encode()
    snapshot = {
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "campaign": campaign.get("root", "").split("/")[-1] if campaign else None,
        "base_tasks": campaign.get("baseRuns") if campaign else None,
        "comparison_base_tasks": campaign.get("comparisonBaseRuns") if campaign else None,
        "retained_baseline_tasks": campaign.get("baseline", {}).get("baseRuns") if campaign and campaign.get("baseline") else 0,
        "verified_repetitions": campaign.get("completedRounds") if campaign else None,
        "state": campaign.get("state") if campaign else None,
        "source": "Git index" if staged else "working tree",
        "note": "Public snapshot. Private run sessions and evidence signing keys are not exported.",
    }
    assets["snapshot.json"] = (json.dumps(snapshot, indent=2) + "\n").encode()
    for name, content in assets.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return {**snapshot, "files": len(assets), "destination": str(destination)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true", help="Export the reviewed Git index, not changing worker files")
    parser.add_argument("--output", type=Path, default=REPO / "docs" / "economics")
    args = parser.parse_args()
    print(json.dumps(export(args.output.resolve(), args.staged), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
