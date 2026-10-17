import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aegis_enforced_retry import json_write
from ladder_stats import summarize
from run_ladder import checked_call, initialize, now, policy_key, run_chain, verify_chain
from audit_ladder_evidence import verify_evidence


class LadderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"ladder";self.root.mkdir()
        self.task="reasoning/r2_expectedflips";self.cell=("cheap",self.task,"low",1)
        self.manifest={"config":{},"plans":{policy_key(*self.cell[:3]):{"routes":["cheap","middle","sol"]}},
            "output_tokens":{self.task:8192}}
        self.calls=[];self.outcomes={}

    def fake_base(self,config,rid,effort,task,rep,force,**kw):
        return self.fake(rid,effort,task,rep,"base",None,kw)

    def fake_retry(self,config,base,binary,force,**kw):
        return self.fake(base["route_id"],base["effort"],base["task"],base["repetition"],"aegis_enforced_retry",base,kw)

    def fake(self,rid,effort,task,rep,condition,base,kw):
        self.calls.append((rid,condition));root=kw["output_root"]
        path=root/"results"/(rid+"-"+condition+".json")
        passed=self.outcomes.get((rid,condition),False)
        record={"route_id":rid,"task":task,"effort":effort,"repetition":rep,"condition":condition,
            "grade":{"passed":passed},"request":{"max_output_tokens":kw["max_output_tokens"]},
            "record_path":str(path),"response_path":str(root/"response.json"),"started_at_utc":now(),
            "parent_record_path":base["record_path"] if base else None,
            "elapsed_seconds":1,"usage":{"calls":1},
            "costs":{"billing":"token","cash_cost_usd":.001,"capacity_allocated_cost_usd":None}}
        json_write(path,record);return record

    def run_fake(self):
        with patch("run_ladder.run_reasoning",side_effect=self.fake_base),patch("run_ladder.run_enforced",side_effect=self.fake_retry),patch("run_ladder.verify_row"):
            return run_chain(self.root,self.manifest,self.cell)

    def test_successful_base_stops_without_retry_or_upgrade(self):
        self.outcomes[("cheap","base")]=True;r=self.run_fake()
        self.assertEqual(self.calls,[("cheap","base")]);self.assertTrue(r["passed"])
        self.assertEqual(r["cost_usd"],.001)
        verify_chain(r,self.manifest,replay=False)

    def test_aegis_success_stops_before_upgrade(self):
        self.outcomes[("cheap","aegis_enforced_retry")]=True;r=self.run_fake()
        self.assertEqual(len(self.calls),2);self.assertEqual(r["resolved_by"],"aegis")
        self.assertEqual(r["cost_usd"],.002);verify_chain(r,self.manifest,replay=False)

    def test_upgrade_requires_failed_base_and_enforced_retry(self):
        self.outcomes[("middle","base")]=True;r=self.run_fake()
        self.assertEqual(self.calls,[("cheap","base"),("cheap","aegis_enforced_retry"),("middle","base")])
        self.assertEqual(r["upgrades"],1);self.assertEqual(r["cost_usd"],.003)
        verify_chain(r,self.manifest,replay=False)

    def test_final_failure_gets_retry_and_remains_failure(self):
        r=self.run_fake();self.assertFalse(r["passed"])
        self.assertEqual(r["stage_count"],3);self.assertEqual(r["retries"],3)
        self.assertEqual(r["cost_usd"],.006);verify_chain(r,self.manifest,replay=False)
        self.assertIsNone(summarize([r])["success"])

    def test_resume_does_not_repeat_a_completed_chain(self):
        self.outcomes[("middle","base")]=True;first=self.run_fake();n=len(self.calls)
        self.assertEqual(self.run_fake(),first);self.assertEqual(len(self.calls),n)

    def test_uncertain_request_cannot_be_silently_reissued(self):
        folder=self.root/"uncertain";attempts=[]
        def fail():attempts.append(1);raise ConnectionError("reset")
        with self.assertRaises(ConnectionError):checked_call(folder,"base",fail)
        with self.assertRaisesRegex(RuntimeError,"Uncertain prior request"):
            checked_call(folder,"base",fail)
        self.assertEqual(len(attempts),1)

    def test_method_error_cannot_authorize_upgrade(self):
        with patch("run_ladder.run_reasoning",side_effect=self.fake_base),patch("run_ladder.run_enforced",side_effect=self.fake_retry),patch("run_ladder.verify_row",side_effect=RuntimeError("invalid journal")):
            with self.assertRaisesRegex(RuntimeError,"invalid journal"):run_chain(self.root,self.manifest,self.cell)
        self.assertEqual(len(self.calls),2)

    def test_cost_tampering_is_rejected(self):
        self.outcomes[("cheap","base")]=True;r=self.run_fake();r["cost_usd"]=0
        with self.assertRaisesRegex(RuntimeError,"cost omitted"):verify_chain(r,self.manifest,replay=False)

    def test_freeze_all_224_plans_without_provider_calls(self):
        root=Path(self.temp.name)/"new"
        with patch("run_ladder.CURRENT",Path(self.temp.name)/"current.json"):
            m=initialize(root,8)
        self.assertEqual(m["planned_chains"],2240);self.assertEqual(len(m["plans"]),224)
        self.assertEqual(len(m["starting_routes"]),16)
        self.assertEqual(m["training_counts"]["base"],2240)
        self.assertFalse((root/"chain_runs").exists())
        for plan in m["plans"].values():self.assertIn(plan["routes"][-1],m["qualifying_routes"])


class StrictJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.run=Path(self.temp.name)/"retry"
        json_write(self.run/"evidence-state"/"observed-events.jsonl",{})
        self.journal={"entry_count":2,"head_hash":"head","journal_id":"journal","segment_id":"segment",
            "evidence_key":{"public_key_sha256":"public"}}
        self.row={"grade":{"passed":True},"aegis":{"local_ir_dir":str(self.run/".am"),
            "evidence":{"verify":{"valid":True,"journal":dict(self.journal)}}}}

    def response(self,args):
        if args[0]=="aegis":return {"valid":True,"command_exit_code":0,"journal":self.journal}
        return {"ok":True,"command_exit_code":0}

    def test_reasoning_journal_uses_parent_of_local_ir(self):
        with patch("audit_ladder_evidence.command_json",side_effect=self.response) as command:
            self.assertTrue(verify_evidence(self.row)["nonempty"])
        self.assertEqual(command.call_args_list[0].args[0][-2],str(self.run/"evidence-state"))

    def test_valid_empty_journal_is_rejected(self):
        self.journal["entry_count"]=0
        with patch("audit_ladder_evidence.command_json",side_effect=self.response):
            with self.assertRaisesRegex(RuntimeError,"empty journal"):verify_evidence(self.row)

    def test_changed_signed_head_is_rejected(self):
        self.journal["head_hash"]="other"
        with patch("audit_ladder_evidence.command_json",side_effect=self.response):
            with self.assertRaisesRegex(RuntimeError,"head_hash"):verify_evidence(self.row)

    def test_missing_actual_journal_is_rejected(self):
        self.row["aegis"]["local_ir_dir"]=str(self.run/"wrong"/".am")
        with self.assertRaisesRegex(RuntimeError,"missing"):verify_evidence(self.row)

    def test_invalid_actual_gate_is_rejected(self):
        def response(args):
            r=self.response(args)
            if args[0]!="aegis":r["ok"]=False
            return r
        with patch("audit_ladder_evidence.command_json",side_effect=response):
            with self.assertRaisesRegex(RuntimeError,"method gate"):verify_evidence(self.row)


if __name__=="__main__":unittest.main()
