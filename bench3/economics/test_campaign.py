import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from campaign_stats import cost_intervals, summarize, wilson
from run_campaign import initialize, run_cell, worker
from common import load_config


class CampaignTests(unittest.TestCase):
    def test_all_passes_does_not_imply_certainty(self):
        low, high = wilson(10, 10)
        self.assertAlmostEqual(low, 72.2467200137, places=6)
        self.assertAlmostEqual(high, 100)
        low, high = wilson(0, 10)
        self.assertAlmostEqual(low, 0)
        self.assertAlmostEqual(high, 27.7532799863, places=6)
        self.assertIsNone(wilson(0, 0))

    def test_small_sample_cost_and_zero_successes(self):
        self.assertEqual(cost_intervals(((.01, True),)), {"attempt": None, "success": None})
        self.assertIsNone(cost_intervals(((.01, False), (.02, False)))["success"])
        ci = cost_intervals(((.01, True), (.01, True)))
        self.assertEqual(ci["attempt"], [1000, 1000])
        self.assertEqual(ci["success"], [1000, 1000])

    def test_retry_preserves_workflow_denominator(self):
        base = {"route_id": "gpt61-sol-direct", "task": "reasoning/r1_tiling", "effort": "low", "repetition": 2,
                "grade": {"passed": False}, "costs": {"billing": "token", "cash_cost_usd": .01},
                "elapsed_seconds": 2, "usage": {}}
        retry = {**base, "grade": {"passed": True}, "costs": {"billing": "token", "cash_cost_usd": .03}}
        s = summarize([base], [retry])
        self.assertEqual(s["runs"], 1)
        self.assertEqual(s["passes"], 1)
        self.assertEqual(s["attempt"]*100, 4000)
        self.assertEqual(s["success"]*100, 4000)

    def test_manifest_excludes_pilot_and_pins_budgets(self):
        with tempfile.TemporaryDirectory() as temporary, patch("run_campaign.CURRENT", Path(temporary) / "current.json"):
            root = Path(temporary) / "campaign"
            initialize(root, 8)
            m = json.loads((root / "manifest.json").read_text())
            route_count = sum(r.get("enabled", True) for r in load_config()["routes"].values())
            self.assertEqual(m["planned_base"], route_count * 7 * 2 * 10)
            self.assertEqual(m["rep_ids"], list(range(2, 12)))
            self.assertEqual(m["output_tokens"]["reasoning/r1_tiling"], 4096)
            self.assertEqual(len(m["routes"]), route_count)
            self.assertIn(str(Path(__file__).with_name("tool_runtime.py")), m["source_sha256"])

    @patch("run_campaign.run_enforced")
    @patch("run_campaign.run_reasoning")
    def test_failed_reasoning_gets_one_paired_enforced_retry(self, base_call, retry_call):
        base_call.return_value = {"grade": {"passed": False}}
        retry_call.return_value = {"grade": {"passed": True}, "aegis": {"evidence": {"verify": {"valid": True}}, "method_closed": True}}
        manifest = {"config": load_config(), "output_tokens": {"reasoning/r1_tiling": 4096}}
        run_cell(Path("/tmp/campaign-test"), manifest, ("gpt61-sol-direct", "reasoning/r1_tiling", "low", 2))
        self.assertEqual(base_call.call_count, 1)
        self.assertEqual(retry_call.call_count, 1)
        self.assertEqual(base_call.call_args.kwargs["max_output_tokens"], 4096)
        self.assertEqual(retry_call.call_args.kwargs["max_output_tokens"], 4096)

    @patch("run_campaign.run_tools")
    def test_passing_tool_workflow_does_not_trigger_retry(self, tool_call):
        tool_call.return_value = {"grade": {"passed": True}}
        run_cell(Path("/tmp/campaign-test"), {"config": load_config()},
                 ("gpt61-sol-direct", "tool-use/t2_toolselect", "high", 2))
        self.assertEqual(tool_call.call_count, 1)

    @patch("run_campaign.shutil.copyfile")
    @patch("run_campaign.verify_round", return_value={"verified": True})
    @patch("run_campaign.publish")
    def test_worker_state_transitions_without_provider_calls(self, publish, verify, copy):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "manifest.json").write_text(json.dumps({"rep_ids": [2], "source_sha256": {},
                "routes": [], "tasks": [], "efforts": [], "jobs": 1, "planned_base": 0}))
            (root / "status.json").write_text(json.dumps({"state": "prepared"}))
            self.assertEqual(worker(root), 0)
            state = json.loads((root / "status.json").read_text())
            self.assertEqual(state["state"], "complete")
            self.assertEqual(state["completedRounds"], 1)
            self.assertGreaterEqual(publish.call_count, 3)


if __name__ == "__main__":
    unittest.main()
