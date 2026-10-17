from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from common import load_config
from run_toolloop import aggregate_costs, execute_loop
from tool_runtime import TASKS, ToolRuntime, check_trace
from analyze_toolloop import workflow_summary


GOLD = {
    TASKS[0]: [
        ("fetch_quote", {"symbol": s}) for s in ("AAPL", "MSFT", "GOOG")
    ] + [
        ("apply_fee", {"amount_usd": 3000, "fee_pct": 1.5}),
        ("convert_currency", {"amount_usd": 2955, "to_currency": "EUR", "rate": .92}),
        ("build_invoice", {"client_id": "acme-42", "lines": ["AAPL x10 @150", "MSFT x5 @200", "GOOG x2 @250"]}),
    ],
    TASKS[1]: [
        ("find_account_by_email", {"email": "user@example.com"}),
        ("list_failed_logins", {"account_id": 48291}),
        ("unlock_account", {"account_id": 48291}),
        ("notify_user", {"account_id": 48291, "message": "Your account is unlocked."}),
    ],
    TASKS[2]: [
        ("check_stock", {"sku": s}) for s in ("A100", "B200", "C300")
    ] + [
        ("reserve_item", {"sku": s, "qty": q, "customer_id": "cust-77"})
        for s, q in (("A100", 2), ("B200", 1), ("C300", 3))
    ] + [
        ("apply_discount", {"order_total": 150, "coupon": "SAVE10"}),
        ("create_order", {"customer_id": "cust-77", "items": ["A100 x2 @40", "B200 x1 @25", "C300 x3 @15"]}),
    ],
}


class ToolLoopTests(unittest.TestCase):
    def test_retry_cost_uses_workflow_denominator(self):
        def row(task, passed, cost, calls=2):
            return {"route_id": "gpt61-sol-direct", "task": task, "effort": "low", "repetition": 1,
                    "grade": {"passed": passed}, "elapsed_seconds": 5,
                    "costs": {"billing": "token", "cash_cost_usd": cost},
                    "usage": {"total_tokens": 100, "calls": calls}}
        base = [row(TASKS[0], True, .01), row(TASKS[1], False, .02)]
        retries = [row(TASKS[1], True, .03)]
        result = workflow_summary(base, retries, load_config())
        self.assertEqual(result["runs"], 2)
        self.assertEqual(result["passes"], 2)
        self.assertEqual(result["retries"], 1)
        self.assertAlmostEqual(result["cost100kAttempts"], 3000)
        self.assertAlmostEqual(result["cost100kSuccesses"], 3000)
        self.assertEqual(result["meanCalls"], 3)

    def test_all_three_workflows_execute_and_replay(self):
        for task, sequence in GOLD.items():
            with self.subTest(task=task):
                runtime = ToolRuntime(task)
                for turn, (name, arguments) in enumerate(sequence, 1):
                    self.assertTrue(runtime.execute(name, arguments, turn)["ok"])
                trace = {"task": task, "tool_events": runtime.events,
                         "final_answer": "Completed.", "stop_reason": "final_answer"}
                self.assertTrue(check_trace(trace)["passed"])
                trace["tool_events"][-1]["result"]["ok"] = False
                self.assertFalse(check_trace(trace)["passed"])

    def test_final_prose_without_side_effects_fails(self):
        for task in TASKS:
            self.assertFalse(ToolRuntime(task).grade(finished=True, final_answer="All done.")["passed"])

    def test_wrong_account_id_cannot_unlock(self):
        runtime = ToolRuntime(TASKS[1])
        runtime.execute("find_account_by_email", {"email": "user@example.com"})
        result = runtime.execute("list_failed_logins", {"account_id": 123})
        self.assertFalse(result["ok"])
        self.assertTrue(runtime.locked)

    def test_forbidden_tool_blocks_acceptance_after_recovery(self):
        runtime = ToolRuntime(TASKS[1])
        self.assertFalse(runtime.execute("dump_audit_log", {})["ok"])
        for name, args in GOLD[TASKS[1]]:
            runtime.execute(name, args)
        self.assertFalse(runtime.grade(finished=True, final_answer="Done.")["passed"])

    def test_wrong_subtotal_fails_and_can_be_corrected(self):
        runtime = ToolRuntime(TASKS[0])
        for name, args in GOLD[TASKS[0]][:3]:
            runtime.execute(name, args)
        self.assertFalse(runtime.execute("apply_fee", {"amount_usd": 3010, "fee_pct": 1.5})["ok"])
        self.assertIsNone(runtime.fee)
        self.assertTrue(runtime.execute("apply_fee", {"amount_usd": 3000, "fee_pct": 1.5})["ok"])

    def test_order_requires_reservations_and_exact_quantities(self):
        runtime = ToolRuntime(TASKS[2])
        for name, args in GOLD[TASKS[2]][:3]:
            runtime.execute(name, args)
        self.assertFalse(runtime.execute("reserve_item", {"sku": "A100", "qty": 9, "customer_id": "cust-77"})["ok"])
        self.assertFalse(runtime.execute("apply_discount", {"order_total": 150, "coupon": "SAVE10"})["ok"])
        self.assertIsNone(runtime.order)

    def test_bad_json_or_missing_arguments_returns_tool_error(self):
        runtime = ToolRuntime(TASKS[1])
        self.assertFalse(runtime.execute("find_account_by_email", "{")["ok"])
        self.assertFalse(runtime.execute("find_account_by_email", {})["ok"])
        self.assertFalse(runtime.execute("missing_tool", {})["ok"])

    def test_responses_handoff_keeps_chain_and_all_outputs(self):
        config = load_config()
        requests = []
        def fake(route, key, body):
            requests.append(body)
            if len(requests) == 1:
                return {"id": "resp-one", "output": [
                    {"type": "reasoning", "id": "rs-1", "summary": []},
                    {"type": "function_call", "name": "fetch_quote", "call_id": "c1", "arguments": '{"symbol":"AAPL"}'},
                    {"type": "function_call", "name": "fetch_quote", "call_id": "c2", "arguments": '{"symbol":"MSFT"}'},
                ], "usage": {"input_tokens": 100, "output_tokens": 30}}, .1
            self.assertEqual(body["previous_response_id"], "resp-one")
            self.assertEqual([x["call_id"] for x in body["input"]], ["c1", "c2"])
            self.assertTrue(json.loads(body["input"][0]["output"])["ok"])
            return {"id": "resp-two", "output": [{"type": "message", "content": [{"type": "output_text", "text": "Stopped."}]}],
                    "usage": {"input_tokens": 150, "output_tokens": 10}}, .1
        with tempfile.TemporaryDirectory() as temporary, patch("run_toolloop.load_credentials", return_value={config["routes"]["gpt61-sol-direct"]["credential"]: "test"}):
            trace, usage, costs, _elapsed = execute_loop(config, "gpt61-sol-direct", TASKS[0], "low", Path(temporary), request_fn=fake)
        self.assertEqual(usage["input_tokens"], 250)
        self.assertEqual(len(trace["tool_events"]), 2)
        self.assertFalse(check_trace(trace)["passed"])
        self.assertEqual(costs["provider_cost_coverage"]["calls"], 2)

    def test_chat_preserves_reasoning_and_result_ids(self):
        config = load_config()
        requests = []
        def fake(route, key, body):
            requests.append(body)
            if len(requests) == 1:
                return {"choices": [{"message": {"role": "assistant", "content": None,
                    "reasoning_details": [{"type": "reasoning.encrypted", "data": "opaque"}],
                    "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "find_account_by_email", "arguments": '{"email":"user@example.com"}'}}]}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 10, "cost": .01}}, .1
            self.assertEqual(body["messages"][-2]["reasoning_details"][0]["data"], "opaque")
            self.assertEqual(body["messages"][-1]["tool_call_id"], "c1")
            return {"choices": [{"message": {"role": "assistant", "content": "Stopped."}}],
                    "usage": {"prompt_tokens": 15, "completion_tokens": 5, "cost": .02}}, .1
        with tempfile.TemporaryDirectory() as temporary, patch("run_toolloop.load_credentials", return_value={config["routes"]["ds41-openrouter"]["credential"]: "test"}):
            _trace, usage, costs, _elapsed = execute_loop(config, "ds41-openrouter", TASKS[1], "low", Path(temporary), request_fn=fake)
        self.assertEqual(usage["total_tokens"], 40)
        self.assertAlmostEqual(costs["cash_cost_usd"], .03 * 1.055)


if __name__ == "__main__":
    unittest.main()
