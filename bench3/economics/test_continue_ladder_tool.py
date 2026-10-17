import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from common import load_config
from continue_ladder_tool import ROUTE,TASK,EFFORT,STEM,continue_base
from run_toolloop import execute_loop
from test_toolloop import GOLD


def reply(index,name=None,args=None,cost=.01):
    message={"role":"assistant","content":"Completed." if name is None else None}
    if name:message["tool_calls"]=[{"id":f"call-{index}","type":"function",
        "function":{"name":name,"arguments":json.dumps(args)}}]
    return {"id":f"response-{index}","choices":[{"message":message}],
        "usage":{"prompt_tokens":10,"completion_tokens":10,"cost":cost}}


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name);self.config=load_config();self.started="2026-10-17T14:56:48+00:00"
        self.credentials=patch("run_toolloop.load_credentials",return_value={self.config['routes'][ROUTE]['credential']:"test"})
        self.credentials.start();self.addCleanup(self.credentials.stop)
        count=0
        def initial(route,key,body):
            nonlocal count
            count+=1
            if count==4:return {"id":"timeout-four","error":{"code":504,"message":"timeout"}},.1
            name,args=GOLD[TASK][count-1]
            return reply(count,name,args),.1
        with self.assertRaisesRegex(RuntimeError,"provider error"):
            execute_loop(self.config,ROUTE,TASK,EFFORT,self.folder/"runs"/STEM,request_fn=initial)
        self.old={p.name:p.read_bytes() for p in (self.folder/"runs"/STEM).glob('*.json')}

    def test_continuation_preserves_receipts_and_never_reissues_completed_calls(self):
        sent=[]
        def fresh(route,key,body):
            sent.append(json.loads(json.dumps(body)))
            self.assertEqual(body['max_tokens'],4096)
            if len(sent)==1:
                self.assertEqual(len([m for m in body['messages'] if m['role']=='tool']),3)
                return reply(5,*GOLD[TASK][3],cost=.02),.1
            return reply(6,cost=.03),.1
        r=continue_base(self.config,self.folder,self.started,request_fn=fresh)
        self.assertEqual(len(sent),2);self.assertTrue(r['grade']['passed'])
        self.assertEqual(r['usage']['calls'],6);self.assertEqual(r['tool_calls'],4)
        self.assertAlmostEqual(r['costs']['cash_cost_usd'],(.03+.02+.03)*1.055)
        self.assertEqual(r['transport_recovery']['missing_usage_receipts'],1)
        self.assertIsNone(r['transport_recovery']['unknown_timeout_charge_usd'])
        for name,data in self.old.items():self.assertEqual((self.folder/'runs'/STEM/name).read_bytes(),data)
        again=continue_base(self.config,self.folder,self.started,request_fn=fresh)
        self.assertEqual(again,r);self.assertEqual(len(sent),2)

    def test_timeout_consumes_one_of_original_twelve_request_slots(self):
        sent=[]
        def fresh(route,key,body):
            sent.append(body)
            return reply(4+len(sent),'unknown_tool',{}),.1
        r=continue_base(self.config,self.folder,self.started,request_fn=fresh)
        self.assertEqual(len(sent),8);self.assertEqual(r['usage']['calls'],12)
        self.assertEqual(r['stop_reason'],'turn_limit');self.assertFalse(r['grade']['passed'])
        from run_toolloop import MAX_TURNS
        self.assertEqual(MAX_TURNS,12)

    def test_repeated_uncertain_continuation_is_blocked(self):
        sent=[]
        def fail(route,key,body):sent.append(body);raise ConnectionError('reset')
        with self.assertRaises(ConnectionError):continue_base(self.config,self.folder,self.started,request_fn=fail)
        with self.assertRaisesRegex(RuntimeError,'already attempted'):
            continue_base(self.config,self.folder,self.started,request_fn=fail)
        self.assertEqual(len(sent),1)


if __name__=='__main__':unittest.main()
