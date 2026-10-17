#!/usr/bin/env python3
"""Shared route, usage, and cost helpers for the economics study."""
from __future__ import annotations

import json
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any

import yaml


ECON = Path(__file__).resolve().parent
BENCH = ECON.parent
CONFIG_PATH = ECON / "routes.yaml"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def load_credentials() -> dict[str, str]:
    """Read credential values without printing or persisting them."""
    store = Path.home() / ".dsh" / ".credentials.yaml"
    if not store.exists():
        return {}
    with store.open() as f:
        data = yaml.safe_load(f) or {}
    if isinstance(data, dict) and isinstance(data.get("refs"), dict):
        data = data["refs"]
    return {str(k): str(v) for k, v in data.items()}


def _parse_hhmm(value: str) -> time:
    hour, minute = (int(part) for part in value.split(":"))
    return time(hour=hour, minute=minute, tzinfo=timezone.utc)


def is_peak_utc(route: dict[str, Any], when: datetime) -> bool:
    """Return true in a configured weekday UTC peak window."""
    when = when.astimezone(timezone.utc)
    if when.weekday() >= 5:
        return False
    current = when.timetz()
    for start, end in route.get("peak_utc_weekday_windows", []):
        if _parse_hhmm(start) <= current < _parse_hhmm(end):
            return True
    return False


def price_card(route: dict[str, Any], when: datetime) -> tuple[str, dict[str, float]]:
    prices = route.get("prices") or {}
    if route.get("billing") == "token-time-window":
        label = "peak" if is_peak_utc(route, when) else "off_peak"
        return label, prices[label]
    return "standard", prices


def normalized_usage(response: dict[str, Any]) -> dict[str, int]:
    """Normalize OpenAI Chat, OpenAI Responses, and compatible usage shapes.

    `input_tokens` is the reported total prompt/input count. It can include
    cache reads and writes. The cost calculator separates those buckets.
    `output_tokens` is the provider's billed output count. Reasoning tokens are
    a subset for the routes in this study.
    """
    usage = response.get("usage") or {}
    input_tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
    output_tokens = int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0)
    input_details = usage.get("input_tokens_details") or usage.get("prompt_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or usage.get("completion_tokens_details") or {}
    cache_read = int(
        input_details.get("cached_tokens", usage.get("prompt_cache_hit_tokens", 0)) or 0
    )
    cache_write = int(
        input_details.get(
            "cache_write_tokens",
            usage.get("cache_creation_input_tokens", usage.get("prompt_cache_write_tokens", 0)),
        ) or 0
    )
    # Anthropic reports uncached input, cache reads, and cache writes as
    # separate top-level fields. Other providers include cached tokens in the
    # main input count.
    if "cache_read_input_tokens" in usage or "cache_creation_input_tokens" in usage:
        cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
        input_tokens += cache_read + cache_write
    reasoning = int(output_details.get("reasoning_tokens", 0) or 0)
    return {
        "input_tokens": input_tokens,
        "cache_read_tokens": cache_read,
        "cache_write_tokens": cache_write,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning,
        "total_tokens": input_tokens + output_tokens,
    }


def provider_reported_cost(response: dict[str, Any]) -> float | None:
    usage = response.get("usage") or {}
    value = usage.get("cost")
    if value is not None:
        return float(value)
    ticks = usage.get("cost_in_usd_ticks")
    if ticks is not None:
        return float(ticks) / 10_000_000_000
    return None


def luna_capacity(config: dict[str, Any], plan_id: str, active_days: float | None = None) -> dict[str, float]:
    plan = config["plans"][plan_id]
    days = float(active_days if active_days is not None else plan["capacity_days_per_month"])
    monthly_tokens = float(plan["observed_tokens_per_24h"]) * days
    monthly_usd = float(plan["monthly_usd"])
    return {
        "active_days": days,
        "monthly_tokens": monthly_tokens,
        "monthly_usd": monthly_usd,
        "cost_per_million_tokens": monthly_usd / monthly_tokens * 1_000_000,
    }


def calculate_cost(
    config: dict[str, Any],
    route: dict[str, Any],
    usage: dict[str, int],
    when: datetime,
    provider_cost: float | None = None,
    lunaroute_active_days: float | None = None,
) -> dict[str, Any]:
    total_input = usage["input_tokens"]
    cache_read = usage["cache_read_tokens"]
    cache_write = usage["cache_write_tokens"]
    if route.get("input_includes_cached", True):
        uncached_input = max(0, total_input - cache_read - cache_write)
    else:
        uncached_input = total_input
    billed_output = usage["output_tokens"]

    if route["billing"] == "subscription":
        capacity = luna_capacity(config, route["plan"], lunaroute_active_days)
        allocated = usage["total_tokens"] / 1_000_000 * capacity["cost_per_million_tokens"]
        return {
            "billing": "subscription",
            "rate_period": "capacity",
            "inference_cost_usd": 0.0,
            "marginal_cost_usd": 0.0,
            "cash_cost_usd": 0.0,
            "capacity_allocated_cost_usd": allocated,
            "capacity": capacity,
            "provider_reported_cost_usd": provider_cost,
            "reconciliation_delta_usd": None,
        }

    period, prices = price_card(route, when)
    catalog_estimate = (
        uncached_input * float(prices.get("input", 0))
        + cache_read * float(prices.get("cached_input", prices.get("input", 0)))
        + cache_write * float(prices.get("cache_write", prices.get("input", 0)))
        + billed_output * float(prices.get("output", 0))
    ) / 1_000_000
    inference = provider_cost if provider_cost is not None else catalog_estimate
    fee_percent = float(route.get("credit_fee_percent", 0))
    cash = inference * (1 + fee_percent / 100)
    delta = None if provider_cost is None else catalog_estimate - provider_cost
    return {
        "billing": route["billing"],
        "rate_period": period,
        "prices_per_million": prices,
        "uncached_input_tokens": uncached_input,
        "catalog_estimated_cost_usd": catalog_estimate,
        "inference_cost_usd": inference,
        "marginal_cost_usd": inference,
        "credit_fee_percent": fee_percent,
        "cash_cost_usd": cash,
        "capacity_allocated_cost_usd": None,
        "provider_reported_cost_usd": provider_cost,
        "catalog_delta_usd": delta,
        "reconciliation_delta_usd": 0.0 if provider_cost is not None else None,
    }


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record, separators=(",", ":"), default=str) + "\n")

