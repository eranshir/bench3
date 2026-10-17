#!/usr/bin/env python3
"""Run one or more single-shot benchmark routes with exact usage capture."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import (
    BENCH,
    ECON,
    append_jsonl,
    calculate_cost,
    load_config,
    load_credentials,
    normalized_usage,
    provider_reported_cost,
)


AEGIS_PAYLOAD_PATH = ECON / "aegis_method_payload.md"


def load_aegis_payload() -> tuple[str, str]:
    payload = AEGIS_PAYLOAD_PATH.read_text()
    return payload, hashlib.sha256(payload.encode()).hexdigest()


def request_headers(route: dict[str, Any], key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if key:
        if route["provider"] == "lunaroute":
            headers["LUNAROUTE-API-KEY"] = key
        else:
            headers["Authorization"] = "Bearer " + key
    if route["provider"] == "openrouter":
        headers["HTTP-Referer"] = "https://eranshir.github.io/bench3/"
        headers["X-Title"] = "bench3 economics"
    if route["provider"] == "anthropic":
        headers["anthropic-version"] = "2023-06-01"
    return headers


def effort_fields(route: dict[str, Any], effort: str) -> dict[str, Any]:
    style = route["effort_style"]
    if style == "deepseek-thinking":
        if effort == "off":
            return {"thinking": {"type": "disabled"}}
        return {"thinking": {"type": "enabled", "effort": effort}}
    if style == "openrouter-reasoning":
        if effort == "off":
            return {"reasoning": {"enabled": False}}
        return {"reasoning": {"effort": effort}}
    if style == "openai-reasoning-effort":
        return {"reasoning_effort": "none" if effort == "off" else effort}
    if style == "openai-responses":
        return {"reasoning": {"effort": "none" if effort == "off" else effort}}
    if style == "anthropic-effort":
        return {
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": "low" if effort == "off" else effort},
        }
    raise ValueError("unknown effort style: %s" % style)


def chat_body(
    route: dict[str, Any], messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None,
    effort: str, max_tokens: int,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": route["model"],
        "messages": messages,
        "max_tokens": max_tokens,
        **effort_fields(route, effort),
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    if route.get("provider_preferences"):
        body["provider"] = route["provider_preferences"]
    return body


def responses_body(
    route: dict[str, Any], messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None,
    effort: str, max_tokens: int,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": route["model"],
        "input": messages,
        "max_output_tokens": max_tokens,
        **effort_fields(route, effort),
    }
    if tools:
        body["tools"] = [
            {
                "type": "function",
                "name": tool["function"]["name"],
                "description": tool["function"].get("description", ""),
                "parameters": tool["function"]["parameters"],
            }
            for tool in tools
        ]
    return body


def anthropic_body(
    route: dict[str, Any], messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None,
    effort: str, max_tokens: int,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": route["model"],
        "messages": [message for message in messages if message.get("role") != "system"],
        "max_tokens": max_tokens,
        **effort_fields(route, effort),
    }
    system_parts = [
        str(message.get("content", ""))
        for message in messages
        if message.get("role") == "system"
    ]
    if system_parts:
        body["system"] = "\n\n".join(system_parts)
    if tools:
        body["tools"] = [
            {
                "name": tool["function"]["name"],
                "description": tool["function"].get("description", ""),
                "input_schema": tool["function"]["parameters"],
            }
            for tool in tools
        ]
        body["tool_choice"] = {"type": "auto"}
    return body


def call(route: dict[str, Any], key: str, body: dict[str, Any], retries: int = 2) -> tuple[dict[str, Any], float]:
    payload = json.dumps(body).encode()
    started = time.time()
    for attempt in range(retries + 1):
        req = urllib.request.Request(route["endpoint"], data=payload, method="POST")
        for name, value in request_headers(route, key).items():
            req.add_header(name, value)
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                return json.load(resp), time.time() - started
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:800]
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError("HTTP %d: %s" % (exc.code, detail)) from exc
    raise RuntimeError("request retry loop ended unexpectedly")


def normalized_chat_response(raw: dict[str, Any], api_shape: str) -> dict[str, Any]:
    if api_shape == "anthropic-messages":
        text_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        for item in raw.get("content", []):
            if item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif item.get("type") == "tool_use":
                tool_calls.append({
                    "id": item.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": item.get("name", ""),
                        "arguments": json.dumps(item.get("input", {}), separators=(",", ":")),
                    },
                })
        message: dict[str, Any] = {"role": "assistant", "content": "".join(text_parts)}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message}], "usage": raw.get("usage", {}), "_raw": raw}
    if api_shape != "openai-responses":
        return raw
    text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for item in raw.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") in ("output_text", "text"):
                    text_parts.append(content.get("text", ""))
        elif item.get("type") == "function_call":
            tool_calls.append({
                "id": item.get("call_id", ""),
                "type": "function",
                "function": {
                    "name": item.get("name", ""),
                    "arguments": item.get("arguments", "{}"),
                },
            })
    message: dict[str, Any] = {"role": "assistant", "content": "".join(text_parts)}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {"choices": [{"message": message}], "usage": raw.get("usage", {}), "_raw": raw}


def run_checker(task_dir: Path, response_path: Path) -> dict[str, Any]:
    checker = task_dir / "check.py"
    if not checker.exists():
        return {"kind": "ungraded", "passed": None}
    result = subprocess.run(
        [sys.executable, str(checker), str(response_path)],
        capture_output=True, text=True, timeout=300,
    )
    try:
        detail = json.loads(result.stdout.strip())
    except Exception:
        detail = {"detail": result.stdout.strip()[-1000:], "stderr": result.stderr.strip()[-1000:]}
    return {"kind": "objective", "passed": bool(detail.get("passed", result.returncode == 0)), "detail": detail}


def task_inputs(task: str) -> tuple[Path, list[dict[str, Any]], list[dict[str, Any]] | None, int]:
    task_dir = BENCH / "tasks" / task
    if not (task_dir / "prompt.txt").exists():
        raise ValueError("single-shot task required: %s" % task)
    messages: list[dict[str, Any]] = []
    if (task_dir / "system.txt").exists():
        messages.append({"role": "system", "content": (task_dir / "system.txt").read_text()})
    messages.append({"role": "user", "content": (task_dir / "prompt.txt").read_text()})
    tools = json.loads((task_dir / "tools.json").read_text()) if (task_dir / "tools.json").exists() else None
    max_tokens = int((task_dir / "max_tokens.txt").read_text()) if (task_dir / "max_tokens.txt").exists() else 8192
    return task_dir, messages, tools, max_tokens


def run_one(
    config: dict[str, Any], route_id: str, effort: str, task: str, rep: int,
    force: bool, max_output_tokens: int | None = None,
    aegis_injected: bool = False, parent_record_path: str | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    output_root = output_root or ECON
    route = config["routes"][route_id]
    task_dir, messages, tools, max_tokens = task_inputs(task)
    payload_sha256 = None
    if aegis_injected:
        payload, payload_sha256 = load_aegis_payload()
        messages.insert(0, {"role": "system", "content": payload})
    if max_output_tokens is not None:
        max_tokens = max_output_tokens
    safe_task = task.replace("/", "-")
    suffix = "_aegis" if aegis_injected else ""
    stem = "%s_%s_%s_rep%d%s" % (route_id, safe_task, effort, rep, suffix)
    record_path = output_root / "results" / (stem + ".json")
    response_path = output_root / "runs" / (stem + ".response.json")
    if record_path.exists() and not force:
        print("skip existing: %s" % record_path)
        return json.loads(record_path.read_text())

    creds = load_credentials()
    key = creds.get(route["credential"], "")
    if not key:
        raise RuntimeError("missing credential: %s" % route["credential"])
    if route["api_shape"] == "openai-responses":
        body = responses_body(route, messages, tools, effort, max_tokens)
    elif route["api_shape"] == "anthropic-messages":
        body = anthropic_body(route, messages, tools, effort, max_tokens)
    else:
        body = chat_body(route, messages, tools, effort, max_tokens)

    started = datetime.now(timezone.utc)
    raw, elapsed = call(route, key, body)
    normalized = normalized_chat_response(raw, route["api_shape"])
    response_path.parent.mkdir(parents=True, exist_ok=True)
    response_path.write_text(json.dumps(normalized, indent=1))
    grade = run_checker(task_dir, response_path)
    usage = normalized_usage(raw)
    provider_cost = provider_reported_cost(raw)
    costs = calculate_cost(config, route, usage, started, provider_cost=provider_cost)

    record = {
        "schema_version": "bench3.economics.v1",
        "catalog_as_of": config["catalog_as_of"],
        "started_at_utc": started.isoformat(),
        "route_id": route_id,
        "route": {key: route[key] for key in (
            "model_family", "display", "vendor", "route", "provider", "model", "billing"
        )},
        "upstream_provider": raw.get("provider"),
        "task": task,
        "effort": effort,
        "repetition": rep,
        "condition": "aegis_retry" if aegis_injected else "base",
        "parent_record_path": parent_record_path,
        "aegis": {
            "injected": aegis_injected,
            "payload_path": str(AEGIS_PAYLOAD_PATH) if aegis_injected else None,
            "payload_sha256": payload_sha256,
        },
        "elapsed_seconds": elapsed,
        "usage": usage,
        "costs": costs,
        "grade": grade,
        "request": {"max_output_tokens": max_tokens, "has_tools": bool(tools)},
        "record_path": str(record_path),
        "response_path": str(response_path),
    }
    record_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = record_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(record, indent=1))
    temporary.replace(record_path)
    append_jsonl(output_root / "results" / "results.jsonl", record)
    print(
        "%s | %s | pass=%s | %.1fs | %d tokens | cash=$%.6f | allocated=$%s"
        % (
            route_id,
            task,
            grade["passed"],
            elapsed,
            usage["total_tokens"],
            costs["cash_cost_usd"],
            "-" if costs["capacity_allocated_cost_usd"] is None else "%.6f" % costs["capacity_allocated_cost_usd"],
        )
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", action="append", default=[])
    parser.add_argument("--effort", action="append", default=[])
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--rep", type=int, default=1)
    parser.add_argument("--max-output-tokens", type=int)
    parser.add_argument(
        "--aegis-on-failure", action="store_true",
        help="Retry a failure: enforced Aegis for tool loops, Method Lite for single-shot tasks.",
    )
    parser.add_argument("--legacy-one-shot-tools", action="store_true",
                        help="Reproduce the historical one-response tool-plan contract.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = load_config()
    requested = args.route or ["all"]
    route_ids = [rid for rid, route in config["routes"].items() if route.get("enabled", True)] if "all" in requested else requested
    efforts = args.effort or ["high"]
    tasks = args.task or ["reasoning/r2_expectedflips"]
    failures = 0
    for route_id in route_ids:
        for task in tasks:
            for effort in efforts:
                try:
                    if (BENCH / "tasks" / task / "tools.json").exists() and not args.legacy_one_shot_tools:
                        from run_toolloop import run_one as run_tool_workflow
                        if args.force or args.max_output_tokens is not None:
                            raise ValueError("Executed tools use a fixed 4096-token per-request limit. Use a new --rep for a new run, or --legacy-one-shot-tools to reproduce the old contract.")
                        base = run_tool_workflow(config, route_id, task, effort, args.rep)
                        if args.aegis_on_failure and base["grade"]["passed"] is False:
                            run_tool_workflow(config, route_id, task, effort, args.rep, base=base)
                        continue
                    base = run_one(
                        config, route_id, effort, task, args.rep, args.force,
                        max_output_tokens=args.max_output_tokens,
                    )
                    if args.aegis_on_failure and base.get("grade", {}).get("passed") is False:
                        run_one(
                            config, route_id, effort, task, args.rep, args.force,
                            max_output_tokens=args.max_output_tokens,
                            aegis_injected=True,
                            parent_record_path=base.get("record_path") or base.get("response_path"),
                        )
                except Exception as exc:
                    failures += 1
                    append_jsonl(ECON / "results" / "failures.jsonl", {
                        "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                        "route_id": route_id,
                        "task": task,
                        "effort": effort,
                        "repetition": args.rep,
                        "error": str(exc)[:1000],
                    })
                    print("FAILED %s | %s | %s: %s" % (route_id, task, effort, exc), file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

