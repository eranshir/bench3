#!/usr/bin/env python3
from __future__ import annotations

import unittest
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from common import calculate_cost, load_config, luna_capacity, normalized_usage
from run_singleshot import anthropic_body, normalized_chat_response
from run_agentic import response_ids
from aegis_enforced_retry import build_contracts, gate_event


class CostTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.usage = {
            "input_tokens": 1000,
            "cache_read_tokens": 800,
            "cache_write_tokens": 0,
            "output_tokens": 500,
            "reasoning_tokens": 300,
            "total_tokens": 1500,
        }

    def test_cached_input_is_not_double_counted(self):
        route = self.config["routes"]["ds41-openrouter"]
        cost = calculate_cost(
            self.config, route, self.usage,
            datetime(2026, 10, 16, 12, tzinfo=timezone.utc),
        )
        expected = (200 * 0.15 + 800 * 0.003 + 500 * 0.60) / 1_000_000
        self.assertAlmostEqual(cost["catalog_estimated_cost_usd"], expected)
        self.assertAlmostEqual(cost["inference_cost_usd"], expected)
        self.assertAlmostEqual(cost["cash_cost_usd"], expected * 1.055)

    def test_provider_reported_cost_overrides_catalog_estimate(self):
        route = self.config["routes"]["ds41-openrouter"]
        cost = calculate_cost(
            self.config, route, self.usage,
            datetime(2026, 10, 16, 12, tzinfo=timezone.utc),
            provider_cost=0.0009,
        )
        self.assertEqual(cost["inference_cost_usd"], 0.0009)
        self.assertAlmostEqual(cost["cash_cost_usd"], 0.0009 * 1.055)
        self.assertEqual(cost["reconciliation_delta_usd"], 0.0)

    def test_lunaroute_full_month_capacity(self):
        capacity = luna_capacity(self.config, "lunaroute-teams-10-40", 30)
        self.assertEqual(capacity["monthly_tokens"], 120_000_000_000)
        self.assertAlmostEqual(capacity["cost_per_million_tokens"], 1 / 240)

    def test_lunaroute_one_active_day(self):
        capacity = luna_capacity(self.config, "lunaroute-teams-10-40", 1)
        self.assertAlmostEqual(capacity["cost_per_million_tokens"], 0.125)

    def test_deepseek_peak_window(self):
        route = self.config["routes"]["ds41-direct"]
        cost = calculate_cost(
            self.config, route, self.usage,
            datetime(2026, 10, 16, 2, tzinfo=timezone.utc),
        )
        self.assertEqual(cost["rate_period"], "peak")

    def test_anthropic_body_uses_direct_messages_shape(self):
        route = self.config["routes"]["claude-sonnet55-direct"]
        body = anthropic_body(
            route,
            [
                {"role": "system", "content": "Be exact."},
                {"role": "user", "content": "Solve it."},
            ],
            [{
                "type": "function",
                "function": {
                    "name": "lookup",
                    "description": "Find one value.",
                    "parameters": {"type": "object", "properties": {}},
                },
            }],
            "high",
            4096,
        )
        self.assertEqual(body["system"], "Be exact.")
        self.assertEqual(body["messages"], [{"role": "user", "content": "Solve it."}])
        self.assertEqual(body["output_config"], {"effort": "high"})
        self.assertEqual(body["tools"][0]["input_schema"]["type"], "object")

    def test_anthropic_response_and_usage_are_normalized(self):
        raw = {
            "content": [
                {"type": "thinking", "thinking": "hidden"},
                {"type": "text", "text": "Done."},
                {"type": "tool_use", "id": "tool-1", "name": "lookup", "input": {"id": 7}},
            ],
            "usage": {
                "input_tokens": 100,
                "cache_read_input_tokens": 80,
                "cache_creation_input_tokens": 20,
                "output_tokens": 40,
            },
        }
        normalized = normalized_chat_response(raw, "anthropic-messages")
        message = normalized["choices"][0]["message"]
        self.assertEqual(message["content"], "Done.")
        self.assertEqual(message["tool_calls"][0]["function"]["arguments"], '{"id":7}')
        usage = normalized_usage(raw)
        self.assertEqual(usage["input_tokens"], 200)
        self.assertEqual(usage["cache_read_tokens"], 80)
        self.assertEqual(usage["cache_write_tokens"], 20)
        self.assertEqual(usage["total_tokens"], 240)

    @patch("run_agentic.decompress")
    def test_agent_response_id_from_current_replay_shape(self, mocked_decompress):
        mocked_decompress.return_value = (
            '{"data":{"message":{"source":{"replayState":{"response":'
            '{"responseId":"gen-current"}}}}}}\n'
            '{"data":{"message":{"source":{"replayState":'
            '{"responseId":"gen-legacy"}}}}}\n'
        )
        self.assertEqual(
            response_ids(Path("unused.zstd")),
            ["gen-current", "gen-legacy"],
        )

    def test_enforced_contract_binds_existing_checker(self):
        task_dir = Path(__file__).resolve().parent.parent / "tasks" / "reasoning" / "r1_tiling"
        parent = {
            "record_path": "/tmp/base.json",
            "response_path": "/tmp/base-response.json",
        }
        plan, child = build_contracts(
            "ds41-lunaroute",
            "reasoning/r1_tiling",
            "high",
            parent,
            task_dir,
            Path("/tmp/enforced-response.json"),
            "0" * 64,
        )
        self.assertEqual(plan["schema_version"], "am.local_ir.plan.v2")
        self.assertEqual(child["schema_version"], "am.local_ir.child.v2")
        self.assertEqual(child["status"], "in_progress")
        command = child["falsifiers"][0]["check"]["command"]
        self.assertIn(str(task_dir / "check.py"), command)
        self.assertIn("/tmp/enforced-response.json", command)
        self.assertEqual(child["falsifiers"][0]["check"]["expected_outcome"], "zero")

    def test_gate_transcript_is_hash_linked(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "gate-transcript.jsonl"
            first = gate_event(path, "plan_gate_allow", {"ok": True})
            second = gate_event(path, "closure_gate_allow", {"ok": True})
            self.assertEqual(second["sequence"], 2)
            self.assertEqual(second["previous_event_sha256"], first["event_sha256"])
            stored = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(stored, [first, second])


if __name__ == "__main__":
    unittest.main()

