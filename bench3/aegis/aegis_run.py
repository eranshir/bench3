#!/usr/bin/env python3
"""bench3 Aegis agentic runner — guided / enforced / vanilla arms.

Runs one agentic task under a bench3 arm with the Aegis method, writing a
per-task record satisfying ADR 0043 (arm_config + materialization proof +
resolution + compliance vector + gate transcript).

Usage:
  aegis_run.py --arm guided|enforced|vanilla --model deepseek-flash \
    --task coding/c3_adversarial --rep 1 --out /tmp/aegis-records

The enforced arm starts the gate daemon over the workspace: pre-plan
mutations are reverted and logged (canary-verified). All arms git-init the
workspace for identical baseline state and run through the same DSH headless
path as the existing bench3 runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

BENCH = pathlib.Path(__file__).resolve().parents[1]
AEGIS = pathlib.Path(__file__).resolve().parent
DSH_HOME = BENCH / ".dsh-home"
RUNS = BENCH / "runs"
WORK = BENCH / "work"

PAYLOAD_PATH = AEGIS / "method_payload.md"
VALIDATOR = AEGIS / "gate_validator.py"
DAEMON = AEGIS / "gate_daemon.py"

MODELS = {
    "deepseek-flash": ("deepseek-official", "deepseek-v4-flash"),
    "deepseek-pro": ("deepseek-official", "deepseek-v4-pro"),
    "gpt-sol": ("openai", "gpt-5.6-sol"),
    "grok": ("xai", "grok-4.6"),
    "mtplx": ("mtplx", "mtplx"),
    "lunaroute": ("lunaroute", "glm-5.2-vision"),
}
LIMIT = int(os.environ.get("LIMIT", "900"))


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def write_settings(provider: str, model: str, effort: str = "high") -> None:
    subprocess.run([sys.executable, str(BENCH / "bin" / "lib" / "write_settings.py"),
                    provider, model, effort], cwd=str(BENCH), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def git(cwd: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=False,
                   capture_output=True, text=True)


def setup_workspace(arm: str, task: str, rep: int) -> pathlib.Path:
    name = "aegis-%s_%s_rep%d" % (arm, task.replace("/", "-"), rep)
    work = WORK / name
    shutil.rmtree(work, ignore_errors=True)
    src = BENCH / "tasks" / task
    shutil.copytree(src, work)
    (work / "PROMPT.txt").unlink(missing_ok=True)
    git(work, "init", "-q")
    git(work, "config", "user.email", "aegis@bench3")
    git(work, "config", "user.name", "aegis-bench3")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "fixture baseline")
    return work


def build_prompt(task: str, arm: str) -> str:
    prompt = (BENCH / "tasks" / task / "PROMPT.txt").read_text()
    if arm in ("guided", "enforced"):
        payload = PAYLOAD_PATH.read_text()
        return "# Aegis method (binding)\n\n" + payload + "\n\n# Task\n\n" + prompt
    return prompt


def session_tokens(work: pathlib.Path, dsh_home: pathlib.Path, start: float) -> dict:
    """Parse the newest DSH session under the workspace key (same as run_agentic.sh)."""
    import sys as _sys
    _sys.path.insert(0, str(BENCH / "bin"))
    try:
        from lib.session import wait_session, parse_session
        workkey = "--" + str(work.resolve()).lstrip("/").replace("/", "-") + "--"
        sess = wait_session(workkey, pathlib.Path(dsh_home), start, timeout=120)
        if not sess:
            return {"observed": False}
        usage = parse_session(sess)["usage"]
        return {"observed": True, "input": usage["input"], "cached": usage["cached"],
                "output": usage["output"], "reasoning": usage["reasoning"], "calls": usage["calls"]}
    except Exception as exc:
        return {"observed": False, "error": str(exc)[:200]}


def isolation_proof(work: pathlib.Path, task: str) -> dict:
    """Rule 1: fail-closed clean git status + HEAD at fixture baseline before the agent starts."""
    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(work),
                            capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(work),
                          capture_output=True, text=True).stdout.strip()
    return {"clean_before": status == "", "head": head}


def hidden_test(work: pathlib.Path, task: str) -> dict:
    hidden = BENCH / "tasks" / task / "hidden_test.py"
    if not hidden.exists():
        return {"evaluated": False}
    shutil.copyfile(hidden, work / "_hidden_test.py")
    r = subprocess.run([sys.executable, "-m", "unittest", "_hidden_test", "-v"],
                       cwd=str(work), capture_output=True, text=True, timeout=300)
    failed = sum(1 for line in r.stdout.splitlines() if line.startswith(("FAIL:", "ERROR:")))
    return {"evaluated": True, "passed": r.returncode == 0, "failed": failed,
            "output_tail": r.stdout[-400:]}


def compliance_vector(work: pathlib.Path) -> dict:
    v = subprocess.run([sys.executable, str(VALIDATOR), str(work)],
                       capture_output=True, text=True).stdout
    try:
        vr = json.loads(v)
    except Exception:
        vr = {"valid": False, "reasons": ["validator failed"]}
    children = vr.get("children") or []
    return {
        "plan_present": bool(vr.get("plan")),
        "plan_valid": vr["valid"],
        "children_count": vr.get("children_count", 0),
        "falsifier_counts": [len(c.get("falsifiers", [])) for c in children],
        "all_children_have_falsifiers": all(len(c.get("falsifiers", [])) > 0 for c in children),
        "reasons": vr.get("reasons", []),
    }


def transcript_summary(work: pathlib.Path) -> dict:
    events_path = work / ".bruno" / "gate-events.jsonl"
    if not events_path.exists():
        return {"present": False}
    denies = reverts = allows = 0
    for line in events_path.read_text().splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("event") == "deny":
            denies += 1
        elif e.get("event") == "revert":
            reverts += 1
        elif e.get("event") == "allow":
            allows += 1
    return {"present": True, "denies": denies, "reverts": reverts, "allows": allows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=("guided", "enforced", "vanilla"), required=True)
    ap.add_argument("--model", choices=MODELS, required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--out", default=str(RUNS / "aegis-records"))
    args = ap.parse_args()

    payload_text = PAYLOAD_PATH.read_text()
    config_digest = sha256(payload_text + "|" + args.arm + "|" + "strict")

    work = setup_workspace(args.arm, args.task, args.rep)
    prompt = build_prompt(args.task, args.arm)

    provider, model = MODELS[args.model]
    write_settings(provider, model)

    # Rule 1: fail-closed clean-before assert, captured BEFORE the agent starts
    iso_pre = isolation_proof(work, args.task)
    if not iso_pre["clean_before"]:
        raise SystemExit("isolation failure: workspace not clean at start")

    # start the gate daemon (enforced only)
    daemon_proc = None
    if args.arm == "enforced":
        daemon_proc = subprocess.Popen(
            [sys.executable, str(DAEMON), "--workspace", str(work),
             "--interval", "0.5", "--mode", "strict"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    env = dict(os.environ)
    env["DSH_HOME"] = str(DSH_HOME)  # isolated bench3 home (was missing -> wrong model!)
    # export provider keys into the env so the isolated home's routes resolve
    # (mirrors run_agentic.sh's credential export)
    sys.path.insert(0, str(BENCH / "bin"))
    from lib.common import load_credentials  # noqa: E402
    env.update(load_credentials())
    if args.model == "mtplx":
        env.setdefault("MTPLX_API_KEY", "local")
    if args.arm in ("guided", "vanilla"):
        env["AEGIS_BENCH_CONTROL_ARM"] = "1" if args.arm == "vanilla" else "0"
    env["MLXFAST_NO_SANDBOX"] = os.environ.get("MLXFAST_NO_SANDBOX", "1")

    start = time.time()
    try:
        r = subprocess.run(
            ["dsh", "--profile", "headless", prompt],
            cwd=str(work), env=env, capture_output=True, text=True, timeout=LIMIT)
        cli_rc = r.returncode
    except subprocess.TimeoutExpired:
        cli_rc = -1
    finally:
        if daemon_proc is not None:
            daemon_proc.terminate()
            try:
                daemon_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                daemon_proc.kill()
    elapsed = int(time.time() - start)

    grade = hidden_test(work, args.task)
    comp = compliance_vector(work)
    trans = transcript_summary(work)
    toks = session_tokens(work, DSH_HOME, start)
    iso_post = isolation_proof(work, args.task)
    import subprocess as _sp
    dsh_ver = _sp.run(["dsh", "--version"], capture_output=True, text=True).stdout.strip() or "unknown"

    record = {
        "schema_version": "aegis.bench3.agentic.v1",
        "arm": args.arm,
        "model": args.model,
        "task": args.task,
        "repetition": args.rep,
        "elapsed_seconds": elapsed,
        "cli_rc": cli_rc,
        "arm_config": {
            "name": "aegis-" + args.arm,
            "config_digest": config_digest,
            "method_gates_mode": "off" if args.arm != "enforced" else "strict",
            "method_evidence_profile": {
                "guided": "prose-digest",
                "enforced": "gate-transcript",
                "vanilla": "absent",
            }[args.arm],
            "env": {"AEGIS_BENCH_CONTROL_ARM": "1"} if args.arm == "vanilla" else {},
            "expected_token_buckets": ["codex_llm"],
        },
        "materialization": {
            "payload_digest": sha256(payload_text),
            "gate_transcript": trans,
            "control_absent_by_config": args.arm == "vanilla",
        },
        "parity": {"dsh_version": dsh_ver, "model": model, "provider": provider,
                   "gate_validator_digest": sha256(VALIDATOR.read_text())},
        "tokens": toks,
        "isolation": {"pre": iso_pre, "post": iso_post},
        "resolution": grade,
        "compliance": comp,
        "workspace": str(work),
    }

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rec_path = out / ("%s_%s_%s_rep%d.json" % (args.arm, args.model,
                                               args.task.replace("/", "-"), args.rep))
    rec_path.write_text(json.dumps(record, indent=1, default=str))
    print(json.dumps({k: record[k] for k in
                      ("arm", "model", "task", "elapsed_seconds", "resolution", "compliance",
                       "materialization")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
