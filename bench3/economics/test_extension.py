import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from campaign_stats import read_records
from common import ECON
from extend_campaign import prepare
from run_campaign import TASKS
from verify_campaign import verify


BASELINE = ECON / "campaigns" / "20261017T101248Z-objective-k10"
ROUTE = "ds41-1017-openrouter"


class ExtensionTests(unittest.TestCase):
    def test_prepare_only_adds_140_new_tasks_without_copying_baseline(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "extension"
            with patch("run_campaign.CURRENT", Path(name) / "current.json"):
                manifest = prepare(root, BASELINE, [ROUTE], 8)
            self.assertEqual(manifest["routes"], [ROUTE])
            self.assertEqual(manifest["planned_base"], 140)
            self.assertEqual(manifest["extension"]["baseline_base_records"], 2100)
            self.assertEqual(manifest["output_tokens"]["reasoning/r1_tiling"], 4096)
            self.assertEqual(read_records(root), ([], []))

    def test_completed_route_cannot_be_resubmitted_as_new(self):
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError, "must not be run again"):
                prepare(Path(name) / "extension", BASELINE, ["ds41-openrouter"], 8)

    @patch("verify_campaign.verify_row")
    def test_audit_supports_exact_140_cell_extension(self, replay):
        base = [{"route_id": ROUTE, "task": task, "effort": effort, "repetition": rep,
                 "condition": "base", "grade": {"passed": True},
                 "costs": {"cash_cost_usd": .001}} for rep in range(2, 12)
                for task in TASKS for effort in ["low", "high"]]
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "checkpoints").mkdir()
            (root / "status.json").write_text(json.dumps({"state": "complete"}))
            (root / "manifest.json").write_text(json.dumps({"routes": [ROUTE], "tasks": TASKS,
                "efforts": ["low", "high"], "rep_ids": list(range(2, 12)), "planned_base": 140,
                "source_sha256": {}}))
            for index, rep in enumerate(range(2, 12), 1):
                (root / "checkpoints" / f"round-{index:02d}-verification.json").write_text(json.dumps({
                    "round": index, "repetition": rep, "runs": 14, "passes": 14, "retries": 0}))
                (root / "checkpoints" / f"round-{index:02d}-report_data.js").write_text(
                    "window.REPORT_DATA = " + json.dumps({"campaign": {"baseRuns": index*14, "completedRounds": index}}) + ";")
            with patch("verify_campaign.read_records", return_value=(base, [])):
                result = verify(root)
            self.assertTrue(result["valid"])
            self.assertEqual(result["base_records"], 140)
            self.assertEqual(result["round_proofs"], 10)
            self.assertEqual(replay.call_count, 140)
            base[0]["grade"]["passed"] = False
            with patch("verify_campaign.read_records", return_value=(base, [])):
                with self.assertRaisesRegex(RuntimeError, "Retry records"):
                    verify(root)


if __name__ == "__main__":
    unittest.main()
