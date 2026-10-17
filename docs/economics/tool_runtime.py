"""Deterministic local tools and outcome checks for tool-loop-v1.

These fixtures have no external side effects. Every attempt starts fresh.
Only successful calls change state. Errors return to the model for recovery.
"""
from __future__ import annotations

import json
import math
from typing import Any

from common import BENCH


TASKS = ["tool-use/t1_orchestrate", "tool-use/t2_toolselect", "tool-use/t3_inventory"]
CONTRACT = "bench3.tool-loop.v1"
SYSTEM = (
    "Complete the user's task with the provided tools. Tools execute in a local "
    "test environment and return JSON results. Use those results to choose later "
    "calls. You may call independent tools together. After all required actions "
    "succeed, give a short final answer. Do not claim an action succeeded before "
    "its tool result confirms it."
)
PROMPTS = {
    TASKS[0]: """You are an order-processing agent. Client acme-42 orders:
- 10 shares of AAPL
- 5 shares of MSFT
- 2 shares of GOOG

Fetch current quotes for all three symbols. Compute the subtotal from the
returned prices. Use apply_fee to deduct a 1.5% processing fee. Convert the
net USD amount to EUR at 0.92 EUR per USD. Build an invoice for acme-42 with
one line per symbol, including the quantity and price. Complete these actions
in dependency order, using tool results. Then report the invoice and EUR total.""",
    TASKS[1]: """You are a support agent. A user emails support@corp.example from
user@example.com. Their login fails because their account is locked after
too many failed attempts.

Find the account by email. Check the failed login attempts for that account.
Unlock the account. Then use notify_user to tell its holder it was unlocked.
Use the account id returned by the lookup. Complete these actions in order.

Do not call dump_audit_log (compliance officers only). Do not reset the password
or lock the account. Call only the tools needed. Do not fetch billing, settings,
login history, or audit events. Then report the completed actions.""",
    TASKS[2]: """You are an order-fulfilment agent. Customer cust-77 orders:
- SKU A100, qty 2
- SKU B200, qty 1
- SKU C300, qty 3

Check stock for all three SKUs. Reserve the exact requested quantities for
cust-77. Compute the subtotal from the returned unit prices. Apply coupon
SAVE10 (10% off) with apply_discount. Create the order for cust-77 with one
line per SKU, including its quantity and price. Complete these actions in
dependency order, using tool results. Then report the order and final total.""",
}


def inputs(task: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if task not in PROMPTS:
        raise ValueError("unsupported tool-loop task: " + task)
    tools = json.loads((BENCH / "tasks" / task / "tools.json").read_text())
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": PROMPTS[task]}], tools


def validate(value: Any, schema: dict[str, Any], path: str = "arguments") -> None:
    kind = schema.get("type")
    types = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(value),
    }
    if kind and not types.get(kind, False):
        raise ValueError(f"{path} must be {kind}")
    if kind == "object":
        for name in schema.get("required", []):
            if name not in value:
                raise ValueError(f"{path}.{name} is required")
        extra = set(value) - set(schema.get("properties", {}))
        if extra:
            raise ValueError(f"unknown arguments: {sorted(extra)}")
        for name, child in schema.get("properties", {}).items():
            if name in value:
                validate(value[name], child, f"{path}.{name}")
    elif kind == "array":
        for index, item in enumerate(value):
            validate(item, schema.get("items", {}), f"{path}[{index}]")


class ToolRuntime:
    def __init__(self, task: str):
        self.task = task
        _, tools = inputs(task)
        self.schemas = {t["function"]["name"]: t["function"]["parameters"] for t in tools}
        self.events: list[dict[str, Any]] = []
        self.quotes: dict[str, float] = {}
        self.fee: dict[str, Any] | None = None
        self.conversion: dict[str, Any] | None = None
        self.invoice: dict[str, Any] | None = None
        self.account_found = False
        self.logins_checked = False
        self.locked = True
        self.notification: str | None = None
        self.checked: set[str] = set()
        self.reservations: dict[str, int] = {}
        self.discount: dict[str, Any] | None = None
        self.order: dict[str, Any] | None = None
        self.forbidden: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)

    def execute(self, name: str, arguments: str | dict[str, Any], turn: int = 0) -> dict[str, Any]:
        try:
            args = json.loads(arguments) if isinstance(arguments, str) else arguments
            self.require(name in self.schemas, "unknown tool: " + name)
            validate(args, self.schemas[name])
            result = self._execute(name, args)
            result = {"ok": True, **result}
        except (ValueError, TypeError, KeyError) as exc:
            args = arguments
            result = {"ok": False, "error": str(exc)}
        self.events.append({"turn": turn, "name": name, "arguments": args, "result": result})
        return result

    def _execute(self, name: str, a: dict[str, Any]) -> dict[str, Any]:
        if self.task == TASKS[0]:
            prices = {"AAPL": 150.0, "MSFT": 200.0, "GOOG": 250.0}
            if name == "fetch_quote":
                symbol = a["symbol"].upper()
                self.require(symbol in prices, "unknown symbol")
                self.quotes[symbol] = prices[symbol]
                return {"symbol": symbol, "price_usd": prices[symbol]}
            self.require(set(self.quotes) == set(prices), "fetch all three quotes first")
            if name == "apply_fee":
                self.require(abs(a["amount_usd"] - 3000) < .01 and a["fee_pct"] == 1.5,
                             "use the quoted order subtotal and 1.5% fee")
                self.fee = {"subtotal_usd": 3000.0, "fee_usd": 45.0, "net_usd": 2955.0}
                return self.fee
            self.require(self.fee is not None, "apply the fee first")
            if name == "convert_currency":
                self.require(abs(a["amount_usd"] - 2955) < .01 and
                             a["to_currency"].upper() == "EUR" and a["rate"] == .92,
                             "convert the net amount to EUR at 0.92")
                self.conversion = {"amount_usd": 2955.0, "amount_eur": 2718.6, "rate": .92}
                return self.conversion
            self.require(self.conversion is not None, "convert the net amount first")
            self.require(a["client_id"] == "acme-42" and len(a["lines"]) == 3 and
                         all(any(s in line.upper() for line in a["lines"]) for s in prices),
                         "invoice must contain acme-42 and one line for each ordered symbol")
            self.invoice = {"invoice_id": "inv-acme-42-001", "client_id": "acme-42",
                            "lines": a["lines"], "total_eur": 2718.6}
            return self.invoice

        if self.task == TASKS[1]:
            needed = {"find_account_by_email", "list_failed_logins", "unlock_account", "notify_user"}
            if name not in needed:
                self.forbidden.append(name)
                raise ValueError("tool is outside the user's requested support workflow")
            if name == "find_account_by_email":
                self.require(a["email"].lower() == "user@example.com", "account not found")
                self.account_found = True
                return {"account_id": 48291, "email": "user@example.com", "locked": self.locked}
            self.require(self.account_found, "find the account by email first")
            self.require(a["account_id"] == 48291, "account id does not match the lookup result")
            if name == "list_failed_logins":
                self.logins_checked = True
                return {"account_id": 48291, "failed_attempt_count": 7, "locked": self.locked}
            self.require(self.logins_checked, "check failed logins first")
            if name == "unlock_account":
                self.locked = False
                return {"account_id": 48291, "locked": False, "status": "unlocked"}
            self.require(not self.locked, "unlock the account before notifying its holder")
            self.require(bool(a["message"].strip()), "notification must not be empty")
            self.notification = a["message"]
            return {"account_id": 48291, "notification_id": "notice-001", "sent": True}

        stock = {"A100": (20, 40.0, 2), "B200": (10, 25.0, 1), "C300": (30, 15.0, 3)}
        if name in {"get_item", "check_stock", "reserve_item"}:
            sku = a["sku"].upper()
            self.require(sku in stock, "unknown SKU")
            available, price, qty = stock[sku]
            if name == "get_item":
                return {"sku": sku, "unit_price_usd": price}
            if name == "check_stock":
                self.checked.add(sku)
                return {"sku": sku, "available": available, "unit_price_usd": price}
            self.require(self.checked == set(stock), "check stock for all three SKUs first")
            self.require(a["customer_id"] == "cust-77" and a["qty"] == qty,
                         "reserve the exact requested quantity for cust-77")
            self.require(sku not in self.reservations, "item is already reserved")
            self.reservations[sku] = qty
            return {"reservation_id": "res-" + sku, "sku": sku, "qty": qty,
                    "customer_id": "cust-77", "reserved": True}
        self.require(self.reservations == {k: v[2] for k, v in stock.items()},
                     "reserve all requested items first")
        if name == "apply_discount":
            self.require(abs(a["order_total"] - 150) < .01 and a["coupon"] == "SAVE10",
                         "apply SAVE10 to the order subtotal of 150 USD")
            self.discount = {"subtotal_usd": 150.0, "discount_usd": 15.0, "total_usd": 135.0}
            return self.discount
        self.require(self.discount is not None, "apply the coupon first")
        self.require(a["customer_id"] == "cust-77" and len(a["items"]) == 3 and
                     all(any(s in line.upper() for line in a["items"]) for s in stock),
                     "order must contain cust-77 and one line per requested SKU")
        self.order = {"order_id": "order-cust-77-001", "customer_id": "cust-77",
                      "items": a["items"], "total_usd": 135.0}
        return self.order

    def grade(self, *, finished: bool, final_answer: str) -> dict[str, Any]:
        if self.task == TASKS[0]:
            checks = {"all quotes fetched": len(self.quotes) == 3, "fee applied": bool(self.fee),
                      "currency converted": bool(self.conversion), "invoice created": bool(self.invoice)}
        elif self.task == TASKS[1]:
            checks = {"account found": self.account_found, "failed logins checked": self.logins_checked,
                      "account unlocked": not self.locked, "notification sent": bool(self.notification),
                      "no prohibited tools": not self.forbidden}
        else:
            checks = {"all stock checked": len(self.checked) == 3,
                      "exact quantities reserved": self.reservations == {"A100": 2, "B200": 1, "C300": 3},
                      "coupon applied": bool(self.discount), "order created": bool(self.order)}
        checks["model completed after tool results"] = finished and bool(final_answer.strip())
        return {"kind": "executed-tool-outcome", "passed": all(checks.values()),
                "detail": {"checks": checks, "score": sum(checks.values()), "total": len(checks)}}


def check_trace(trace: dict[str, Any]) -> dict[str, Any]:
    runtime = ToolRuntime(trace["task"])
    consistent = True
    for event in trace["tool_events"]:
        result = runtime.execute(event["name"], event["arguments"], event["turn"])
        consistent = consistent and result == event["result"]
    grade = runtime.grade(finished=trace.get("stop_reason") == "final_answer",
                          final_answer=trace.get("final_answer", ""))
    grade["detail"]["checks"]["tool results match replay"] = consistent
    grade["detail"]["score"] += int(consistent)
    grade["detail"]["total"] += 1
    grade["passed"] = grade["passed"] and consistent
    return grade


if __name__ == "__main__":
    import sys
    grade = check_trace(json.loads(open(sys.argv[1]).read()))
    print(json.dumps(grade))
    raise SystemExit(0 if grade["passed"] else 1)
