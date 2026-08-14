#!/usr/bin/env python3
"""Shared helpers: arms, credentials, cost computation, CSV IO."""
import csv
import os
import subprocess
import sys
from pathlib import Path

import yaml

BENCH = Path(__file__).resolve().parent.parent.parent  # bench3/


def load_arms() -> dict:
    with open(BENCH / "arms.yaml") as f:
        return yaml.safe_load(f)["arms"]


def load_credentials() -> dict:
    """Read the user's DSH credential store. Never print values."""
    store = Path.home() / ".dsh" / ".credentials.yaml"
    with open(store) as f:
        return yaml.safe_load(f)


def arm_env(creds: dict) -> dict:
    """Environment for dsh invocations: keys come from the store via env
    (inherited process environment wins over the store, per dsh-credentials)."""
    env = dict(os.environ)
    for k, v in creds.items():
        env[k] = v
    return env


def cost_usd(arm: dict, input_tok: int, cached_tok: int, output_tok: int) -> float:
    p = arm["prices"]
    if "TBD" in str(p.get("input")) or "TBD" in str(p.get("output")):
        return float("nan")
    return (input_tok * p["input"] + cached_tok * p["cached_input"] + output_tok * p["output"]) / 1_000_000


RESULTS_HEADER = [
    "arm", "vendor", "model", "category", "task", "trial", "effort", "mode",
    "seconds", "input_tokens", "cache_read_tokens", "output_tokens",
    "reasoning_tokens", "cost_usd", "passed", "tests_failed", "grade_seconds",
    "notes", "session_path", "log_path",
]


def results_path() -> Path:
    return BENCH / "results" / "results.csv"


def load_done(path: Path) -> set:
    """Return set of (arm, task, trial) already in a results CSV."""
    if not path.exists():
        return set()
    done = set()
    with open(path) as f:
        for row in csv.DictReader(f):
            done.add((row["arm"], row["task"], row["trial"]))
    return done


def append_row(path: Path, row: dict):
    exists = path.exists()
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RESULTS_HEADER, extrasaction="ignore")
        if not exists:
            w.writeheader()
        w.writerow(row)


def secs_between(t0: float, t1: float) -> int:
    return int(round(t1 - t0))
