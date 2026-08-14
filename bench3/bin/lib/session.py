#!/usr/bin/env python3
"""Parse a DSH headless session (session.jsonl.zstd) into usage + trajectory.

Usage accounting: every assistant/message event carries per-call usage
{inputTokens, outputTokens, cacheReadTokens, reasoningTokens?}. Sum across
all calls for the run. The trajectory (for the webapp) is the ordered
user/assistant/tool events.
"""
import json
import shutil
import subprocess
from pathlib import Path


def decompress(path: Path) -> str:
    zstd = shutil.which("zstd") or "/opt/homebrew/bin/zstd"
    out = subprocess.run([zstd, "-dc", str(path)], capture_output=True)
    if out.returncode != 0:
        raise RuntimeError(f"zstd failed on {path}: {out.stderr.decode()[:200]}")
    return out.stdout.decode(errors="replace")


def parse_session(path: Path) -> dict:
    """Return {usage: {...}, events: [...], title, started, ended}."""
    text = decompress(path)
    usage = {"input": 0, "cached": 0, "output": 0, "reasoning": 0, "calls": 0}
    events = []
    title = None
    started = ended = None
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        t = e.get("type")
        ts = e.get("time")
        if started is None and ts:
            started = ts
        ended = ts or ended
        if t == "session/title" and title is None:
            title = e.get("data", {}).get("title")
        if t == "assistant/message":
            u = e.get("data", {}).get("usage") or {}
            usage["input"] += u.get("inputTokens", 0)
            usage["cached"] += u.get("cacheReadTokens", 0)
            usage["output"] += u.get("outputTokens", 0)
            usage["reasoning"] += u.get("reasoningTokens", 0)
            usage["calls"] += 1
            msg = e.get("data", {}).get("message", {})
            src = msg.get("source", {})
            events.append({
                "type": "assistant",
                "provider": src.get("provider"),
                "model": src.get("model"),
                "reasoning": "".join(b.get("text", "") for b in msg.get("content", []) if b.get("type") == "reasoning"),
                "text": "".join(b.get("text", "") for b in msg.get("content", []) if b.get("type") == "text"),
            })
        elif t == "user/message":
            msg = e.get("data", {}).get("message", {})
            text = "".join(b.get("text", "") for b in msg.get("content", []) if isinstance(b, dict) and b.get("type") == "text")
            events.append({"type": "user", "text": text})
        elif t == "tool/call" or t == "tool/result":
            events.append({"type": t, "data": e.get("data")})
    return {"usage": usage, "events": events, "title": title, "started": started, "ended": ended}


def newest_session(workspace_key: str, dsh_home: Path) -> Path | None:
    """Newest session.jsonl.zstd under dsh_home/sessions/<workspace_key>."""
    base = dsh_home / "sessions" / workspace_key
    if not base.exists():
        return None
    files = sorted(base.glob("*/session.jsonl.zstd"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None





def wait_session(workkey: str, dsh_home: Path, since_epoch: float, timeout: float = 120.0, interval: float = 2.0) -> Path | None:
    """Poll for a session file created after since_epoch. dsh flushes the
    session asynchronously (worker teardown), so the file can lag the process
    exit by seconds to a minute."""
    import time
    base = dsh_home / "sessions" / workkey
    deadline = time.time() + timeout
    while time.time() < deadline:
        files = []
        if base.exists():
            files = [p for p in base.glob("*/session.jsonl.zstd") if p.stat().st_mtime >= since_epoch]
        if files:
            return max(files, key=lambda p: p.stat().st_mtime)
        time.sleep(interval)
    return None

if __name__ == "__main__":
    import sys
    p = Path(sys.argv[1])
    r = parse_session(p)
    print(json.dumps({"usage": r["usage"], "events": len(r["events"]), "title": r["title"]}, indent=2))
