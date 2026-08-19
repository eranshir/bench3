#!/usr/bin/env python3
"""bench3 Aegis gate daemon — workspace-resident enforcement.

The DSH-adapter analogue of the codex PreToolUse gate (Recorded divergence,
ADR 0043 Rule 3): mutating the implementation workspace is REVERTED until the
Aegis IR validates (.bruno/plan.json + children with falsifiers). Authoring
.bruno/ is always allowed. Every decision is appended to
<workspace>/.bruno/gate-events.jsonl — the materialization-proof transcript.

Stdlib only. No DSH modification: the daemon owns the workspace the runner
gives the agent, so the agent experiences refusal without any harness fork.

Usage: gate_daemon.py --workspace <path> [--interval 1.0] [--mode strict|soft]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gate_validator import validate_workspace  # noqa: E402

BRUNO = ".bruno"
EVENTS = "gate-events.jsonl"


def git(cwd: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def ensure_git_baseline(workspace: pathlib.Path) -> None:
    """git-init the workspace and commit the fixture baseline so the gate can revert to it."""
    if not (workspace / ".git").exists():
        git(workspace, "init", "-q")
        git(workspace, "config", "user.email", "gate@bench3")
        git(workspace, "config", "user.name", "bench3-gate")
    if git(workspace, "status", "--porcelain").stdout.strip():
        git(workspace, "add", "-A")
        git(workspace, "commit", "-q", "-m", "bench3 gate baseline")
    # install the pre-commit hook: refuse commits without valid IR
    hooks = workspace / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    hook = hooks / "pre-commit"
    validator = pathlib.Path(__file__).resolve().parent / "gate_validator.py"
    hook.write_text(
        "#!/bin/sh\n"
        + "python3 %s . || { echo 'Aegis gate: commit refused - .bruno/ IR does not validate'; exit 1; }\n" % validator
    )
    hook.chmod(0o755)


def log_event(workspace: pathlib.Path, event: dict) -> None:
    event["ts"] = datetime.now(timezone.utc).isoformat()
    with open(workspace / BRUNO / EVENTS, "a") as f:
        f.write(json.dumps(event) + "\n")


def gate_open(workspace: pathlib.Path) -> bool:
    return validate_workspace(workspace)["valid"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--mode", choices=("strict", "soft"), default="strict")
    args = ap.parse_args()

    ws = pathlib.Path(args.workspace).resolve()
    bruno = ws / BRUNO
    bruno.mkdir(parents=True, exist_ok=True)
    events = bruno / EVENTS
    if not events.exists():
        log_event(ws, {"event": "gate_start", "mode": args.mode})

    ensure_git_baseline(ws)
    log_event(ws, {"event": "gate_baseline", "mode": args.mode})

    print("gate: watching %s (%s mode)" % (ws, args.mode), flush=True)
    while True:
        open_now = gate_open(ws)
        # mutations = non-.bruno changes vs baseline
        status = git(ws, "status", "--porcelain", "--", ":(exclude).bruno").stdout
        paths = [line.split(maxsplit=1)[-1] for line in status.splitlines() if line.strip()]
        if paths and not open_now:
            reason = "deny: implementation mutation before Aegis IR validation (moves 2-4)"
            log_event(ws, {"event": "deny", "reason": reason, "paths": paths})
            if args.mode == "strict":
                git(ws, "checkout", "--", ".")
                git(ws, "clean", "-fdq", "--", ":(exclude).bruno")
                log_event(ws, {"event": "revert", "reason": reason, "paths": paths})
        elif paths and open_now:
            log_event(ws, {"event": "allow", "paths": paths, "gate": "open"})
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
