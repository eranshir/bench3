#!/usr/bin/env python3
"""Run current model routes through the DSH agent harness."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from common import BENCH, ECON, calculate_cost, load_config, load_credentials

sys.path.append(str(BENCH / "bin"))
from lib.session import decompress, parse_session, wait_session  # noqa: E402


DSH_TEMPLATE_HOME = BENCH / ".dsh-home"
ISOLATED_DSH_HOME = Path(tempfile.gettempdir()) / "bench3-economics-dsh-home"
AEGIS_PAYLOAD_PATH = ECON / "aegis_method_payload.md"


def load_aegis_payload() -> tuple[str, str]:
    payload = AEGIS_PAYLOAD_PATH.read_text()
    return payload, hashlib.sha256(payload.encode()).hexdigest()


def workspace_key(path: Path) -> str:
    return "--" + str(path.resolve()).lstrip("/").replace("/", "-") + "--"


def hide_test_assets(work: Path) -> None:
    for name in ("PROMPT.txt", "hidden_test.py", "_hidden_test.py"):
        path = work / name
        if path.exists():
            path.unlink()
    for name in ("reference", "__pycache__"):
        path = work / name
        if path.exists() and path.is_dir():
            shutil.rmtree(path)


def make_sandbox_profile(root: Path, work: Path) -> Path:
    """Allow normal execution, but deny all reads and writes to the source repo."""
    profile = root / "agent.sb"
    repo_root = BENCH.parent
    profile.write_text(
        '(version 1)\n'
        '(allow default)\n'
        '(deny file-read* file-write* (subpath %s))\n' % json.dumps(str(repo_root))
    )
    visible_file = next(path for path in work.rglob("*") if path.is_file())
    probe = subprocess.run(
        [
            "/usr/bin/sandbox-exec", "-f", str(profile), "/bin/sh", "-c",
            'cat "$1" >/dev/null && ! cat "$2" >/dev/null 2>&1',
            "probe", str(visible_file), str(BENCH / "tasks" / "coding" / "c1_deadlock" / "hidden_test.py"),
        ],
        capture_output=True, text=True,
    )
    if probe.returncode != 0:
        raise RuntimeError("file sandbox probe failed")
    return profile


def isolated_dsh_home(
    provider: str, model: str, effort: str, aegis_payload: str | None = None,
) -> Path:
    home = ISOLATED_DSH_HOME
    home.mkdir(exist_ok=True)
    if not (home / "profiles").exists():
        shutil.copytree(
            DSH_TEMPLATE_HOME / "profiles", home / "profiles",
            ignore=shutil.ignore_patterns("node_modules"),
        )
    sessions = home / "sessions"
    if sessions.exists():
        shutil.rmtree(sessions)
    with (DSH_TEMPLATE_HOME / "settings.yaml").open() as handle:
        settings = yaml.safe_load(handle) or {}
    if provider == "openai":
        providers = settings.setdefault("llm-pi-ai", {}).setdefault("providers", {})
        openai = providers.setdefault("openai", {})
        openai.setdefault("apiKeyEnv", "OPENAI_API_KEY")
        openai.setdefault("api", "openai-responses")
        models = openai.setdefault("models", [])
        if not any(item.get("id") == model for item in models):
            models.append({
                "id": model,
                "reasoningEfforts": {
                    "off": "none", "minimal": "minimal", "low": "low",
                    "medium": "medium", "high": "high", "xhigh": "xhigh",
                    "max": "max",
                },
            })
    settings["agent-default-model"] = {
        "provider": provider,
        "model": model,
        "reasoningEffort": effort,
    }
    with (home / "settings.yaml").open("w") as handle:
        yaml.safe_dump(settings, handle, sort_keys=False)
    persona = "You are a coding agent powered by the {{model}} model. Your working directory is {{cwd}}."
    if aegis_payload:
        persona += "\n\n" + aegis_payload
    patch = [{"id": "system-prompt", "config": {"persona": persona}}]
    patch_path = home / "profiles" / "headless" / "cordis.patch.yml"
    patch_path.write_text(yaml.safe_dump(patch, sort_keys=False))
    return home


def forbidden_repo_access(session_path: Path) -> list[str]:
    """Return tool-call records that directly reference the benchmark source."""
    found = []
    source_root = str(BENCH)
    for line in decompress(session_path).splitlines():
        try:
            event = json.loads(line)
        except Exception:
            continue
        if event.get("type") != "tool/call":
            continue
        data = json.dumps(event.get("data", {}), separators=(",", ":"))
        if source_root in data:
            found.append(data[:1000])
    return found


def response_ids(session_path: Path) -> list[str]:
    ids = []
    for line in decompress(session_path).splitlines():
        try:
            event = json.loads(line)
        except Exception:
            continue
        source = event.get("data", {}).get("message", {}).get("source", {})
        replay = source.get("replayState") or {}
        response_id = replay.get("responseId") or (replay.get("response") or {}).get("responseId")
        if response_id and response_id not in ids:
            ids.append(str(response_id))
    return ids


def openrouter_generation_cost(ids: list[str], key: str) -> tuple[float | None, list[str]]:
    if not key or not ids:
        return None, []
    costs = []
    providers = []
    for response_id in ids:
        url = "https://openrouter.ai/api/v1/generation?id=" + response_id
        request = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
        row = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    row = json.load(response).get("data", {})
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 404 and attempt < 3:
                    time.sleep(3)
                    continue
                break
        if not row or row.get("total_cost") is None:
            return None, providers
        costs.append(float(row["total_cost"]))
        if row.get("provider_name"):
            providers.append(str(row["provider_name"]))
    return sum(costs), sorted(set(providers))


def grade(task_dir: Path, work: Path) -> dict[str, Any]:
    hidden = task_dir / "hidden_test.py"
    if not hidden.exists():
        return {"kind": "ungraded", "passed": None}
    shutil.copy2(hidden, work / "_hidden_test.py")
    started = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "_hidden_test", "-v"],
        cwd=work, capture_output=True, text=True, timeout=300,
    )
    text = result.stdout + "\n" + result.stderr
    return {
        "kind": "hidden-tests",
        "passed": result.returncode == 0,
        "seconds": time.time() - started,
        "tests_failed": len(re.findall(r"^(?:FAIL|ERROR):", text, re.M)),
        "tail": text[-2000:],
    }


def run_one(
    config: dict[str, Any], route_id: str, effort: str, task: str, rep: int,
    limit: int, force: bool, aegis_injected: bool = False,
    parent_record_path: str | None = None,
) -> dict[str, Any]:
    route = config["routes"][route_id]
    task_dir = BENCH / "tasks" / task
    prompt_path = task_dir / "PROMPT.txt"
    if not prompt_path.exists():
        raise ValueError("agentic task required: %s" % task)
    suffix = "_aegis" if aegis_injected else ""
    stem = "%s_%s_%s_rep%d%s" % (
        route_id, task.replace("/", "-"), effort, rep, suffix,
    )
    record_path = ECON / "agentic_results" / (stem + ".json")
    if record_path.exists() and not force:
        print("skip existing: %s" % record_path)
        return json.loads(record_path.read_text())

    started = datetime.now(timezone.utc)
    temp_root = Path(tempfile.mkdtemp(prefix="bench3-economics-"))
    work = temp_root / "work"
    shutil.copytree(task_dir, work)
    prompt = prompt_path.read_text()
    hide_test_assets(work)
    sandbox_profile = make_sandbox_profile(temp_root, work)

    model = route.get("agent_model", route["model"])
    aegis_payload = None
    aegis_payload_sha256 = None
    if aegis_injected:
        aegis_payload, aegis_payload_sha256 = load_aegis_payload()
    dsh_home = isolated_dsh_home(route["provider"], model, effort, aegis_payload)
    creds = load_credentials()
    env = dict(os.environ)
    env.update(creds)
    env["DSH_HOME"] = str(dsh_home)
    log_path = ECON / "agentic_runs" / (stem + ".log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timed_out = False
    begin = time.time()
    try:
        result = subprocess.run(
            ["/usr/bin/sandbox-exec", "-f", str(sandbox_profile), "dsh", "--profile", "headless", prompt],
            cwd=work, env=env,
            capture_output=True, text=True, timeout=limit,
        )
        exit_code = result.returncode
        log_path.write_text(result.stdout + "\n--- STDERR ---\n" + result.stderr)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        log_path.write_text(stdout + "\n--- STDERR ---\n" + stderr)
    elapsed = time.time() - begin

    session_path = wait_session(workspace_key(work), dsh_home, started.timestamp(), timeout=120)
    if not session_path:
        raise RuntimeError("no DSH session after agent run")
    leak_evidence = forbidden_repo_access(session_path)
    parsed = parse_session(session_path)
    raw_usage = parsed["usage"]
    usage = {
        "input_tokens": raw_usage["input"] + raw_usage["cached"],
        "cache_read_tokens": raw_usage["cached"],
        "cache_write_tokens": 0,
        "output_tokens": raw_usage["output"],
        "reasoning_tokens": raw_usage["reasoning"],
        "total_tokens": raw_usage["input"] + raw_usage["cached"] + raw_usage["output"],
        "calls": raw_usage["calls"],
    }

    ids = response_ids(session_path)
    provider_cost = None
    upstream_providers: list[str] = []
    cost_source = "capacity-allocation" if route["billing"] == "subscription" else "list-price"
    cost_route = dict(route)
    if route["provider"] == "openrouter":
        provider_cost, upstream_providers = openrouter_generation_cost(
            ids, creds.get("OPENROUTER_API_KEY", "")
        )
        if provider_cost is not None:
            cost_source = "provider-reported"
        elif route.get("agent_estimate_prices"):
            cost_route["prices"] = route["agent_estimate_prices"]
            cost_source = "advertised-floor-estimate"
        else:
            cost_source = "catalog-estimate"
    costs = calculate_cost(config, cost_route, usage, started, provider_cost=provider_cost)
    artifact_path = ECON / "agentic_artifacts" / (stem + "_" + str(int(started.timestamp())))
    shutil.copytree(work, artifact_path)
    result_grade = grade(task_dir, work)
    if leak_evidence:
        result_grade["passed"] = False
        result_grade["invalid_reason"] = "agent accessed benchmark source outside isolated work root"
    saved_session = ECON / "agentic_sessions" / stem / "session.jsonl.zstd"
    saved_session.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(session_path, saved_session)
    record = {
        "schema_version": "bench3.economics.agentic.v1",
        "catalog_as_of": config["catalog_as_of"],
        "started_at_utc": started.isoformat(),
        "route_id": route_id,
        "route": {key: route[key] for key in (
            "model_family", "display", "vendor", "route", "provider", "billing"
        )},
        "model": model,
        "task": task,
        "effort": effort,
        "repetition": rep,
        "condition": "aegis_retry" if aegis_injected else "base",
        "parent_record_path": parent_record_path,
        "aegis": {
            "injected": aegis_injected,
            "payload_path": str(AEGIS_PAYLOAD_PATH) if aegis_injected else None,
            "payload_sha256": aegis_payload_sha256,
        },
        "elapsed_seconds": elapsed,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "sandbox_enforced": True,
        "valid": not leak_evidence,
        "leak_evidence": leak_evidence,
        "usage": usage,
        "costs": costs,
        "cost_source": cost_source,
        "upstream_providers": upstream_providers,
        "grade": result_grade,
        "record_path": str(record_path),
        "session_path": str(saved_session),
        "log_path": str(log_path),
        "artifact_path": str(artifact_path),
        "response_ids": ids,
    }
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, indent=1))
    print(
        "%s | %s | pass=%s | %.1fs | %d calls | %d tokens | cost=%s | %s"
        % (
            route_id, task, result_grade["passed"], elapsed, usage["calls"], usage["total_tokens"],
            "$%.6f" % (costs["capacity_allocated_cost_usd"] if costs["billing"] == "subscription" else costs["cash_cost_usd"]),
            cost_source,
        )
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", action="append", default=[])
    parser.add_argument("--effort", action="append", default=[])
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--rep", type=int, default=1)
    parser.add_argument("--limit", type=int, default=600)
    parser.add_argument(
        "--aegis-on-failure", action="store_true",
        help="Retry a failed coding task with the Aegis Method Lite payload in the system prompt.",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    routes = args.route or [
        "ds41-lunaroute", "ds41-openrouter-floor",
        "claude-sonnet55-direct", "gpt61-sol-direct",
    ]
    tasks = args.task or ["coding/c1_deadlock"]
    efforts = args.effort or ["high"]
    config = load_config()
    failures = 0
    for route_id in routes:
        for task in tasks:
            for effort in efforts:
                try:
                    base = run_one(
                        config, route_id, effort, task, args.rep, args.limit, args.force,
                    )
                    if args.aegis_on_failure and base.get("grade", {}).get("passed") is False:
                        run_one(
                            config, route_id, effort, task, args.rep, args.limit, args.force,
                            aegis_injected=True,
                            parent_record_path=base.get("record_path") or base.get("artifact_path"),
                        )
                except Exception as exc:
                    failures += 1
                    print("FAILED %s | %s | %s: %s" % (route_id, task, effort, exc), file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
