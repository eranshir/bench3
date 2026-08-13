"""Blind grader for h2_concurrency.

Every threaded scenario runs in a child process with a hard timeout. That is
deliberate: a deadlocked WorkerPool leaves non-daemon threads alive, so an
in-process check would hang the grader forever instead of failing. The child
also drops the GIL switch interval to 1us, which makes unsynchronised
read-modify-write races surface reliably rather than occasionally.
"""
import subprocess
import sys
import unittest

import pipeline

PRELUDE = """
import sys, threading
sys.setswitchinterval(1e-6)
from pipeline import Ledger, WorkerPool
"""

DEPOSITS = PRELUDE + """
led = Ledger({"treasury": 0})
ts = [threading.Thread(target=lambda: [led.deposit("treasury", 1)
                                       for _ in range(5000)])
      for _ in range(8)]
for t in ts: t.start()
for t in ts: t.join()
print(led.balances["treasury"])
"""

POOL = PRELUDE + """
p = WorkerPool(8)
for i in range(500):
    p.submit(lambda i=i: i * 2)
got = p.run()
print(len(got), sorted(got) == sorted(i * 2 for i in range(500)))
"""

OPPOSING = PRELUDE + """
led = Ledger({"a": 1000000, "b": 1000000})
x = threading.Thread(target=lambda: [led.transfer("a", "b", 1)
                                     for _ in range(20000)])
y = threading.Thread(target=lambda: [led.transfer("b", "a", 1)
                                     for _ in range(20000)])
x.start(); y.start(); x.join(); y.join()
print(led.total())
"""

# Deterministic mutual-exclusion probe. Wrapping `balances` in a dict that
# yields the GIL on every read forces a thread switch *inside* whatever
# critical section deposit uses. Correct locking is unaffected; any
# unsynchronised read-modify-write loses updates every time. This cannot be
# evaded by rewriting the body to avoid a Python-level loop.
INJECTED = PRELUDE + """
import time
class Yielding(dict):
    def __getitem__(self, key):
        time.sleep(0)
        return dict.__getitem__(self, key)

led = Ledger({"treasury": 0})
led.balances = Yielding(led.balances)
ts = [threading.Thread(target=lambda: [led.deposit("treasury", 1)
                                       for _ in range(2000)])
      for _ in range(6)]
for t in ts: t.start()
for t in ts: t.join()
print(led.balances["treasury"])
"""

MIXED = PRELUDE + """
names = ["a", "b", "c", "d", "e"]
led = Ledger({n: 100000 for n in names})
import random
def churn(seed):
    r = random.Random(seed)
    for _ in range(4000):
        s, d = r.sample(names, 2)
        led.transfer(s, d, r.randint(1, 50))
ts = [threading.Thread(target=churn, args=(i,)) for i in range(8)]
for t in ts: t.start()
for t in ts: t.join()
print(led.total(), all(v >= 0 for v in led.balances.values()))
"""


def run_child(src, timeout):
    """Returns stripped stdout. Fails the calling test on hang or crash."""
    return subprocess.run([sys.executable, "-c", src], capture_output=True,
                          text=True, timeout=timeout)


class Concurrency(unittest.TestCase):
    def test_deposits_lose_no_updates(self):
        try:
            r = run_child(DEPOSITS, 45)
        except subprocess.TimeoutExpired:
            self.fail("deposit scenario hung (45s)")
        self.assertEqual(r.returncode, 0, f"child crashed: {r.stderr[-800:]}")
        self.assertEqual(r.stdout.strip(), "40000",
                         "lost updates: deposit is not atomic")

    def test_deposit_is_mutually_exclusive(self):
        try:
            r = run_child(INJECTED, 45)
        except subprocess.TimeoutExpired:
            self.fail("injected-contention deposit scenario hung (45s)")
        self.assertEqual(r.returncode, 0, f"child crashed: {r.stderr[-800:]}")
        self.assertEqual(r.stdout.strip(), "12000",
                         "deposit's read-modify-write is not mutually "
                         "exclusive under forced contention")

    def test_worker_pool_runs_every_task(self):
        try:
            r = run_child(POOL, 45)
        except subprocess.TimeoutExpired:
            self.fail("worker pool hung (45s) - blocked get() on empty queue")
        self.assertEqual(r.returncode, 0, f"child crashed: {r.stderr[-800:]}")
        self.assertEqual(r.stdout.strip(), "500 True",
                         "pool dropped tasks or returned wrong results")

    def test_opposing_transfers_do_not_deadlock(self):
        try:
            r = run_child(OPPOSING, 45)
        except subprocess.TimeoutExpired:
            self.fail("opposing transfers deadlocked (45s) - lock ordering")
        self.assertEqual(r.returncode, 0, f"child crashed: {r.stderr[-800:]}")
        self.assertEqual(r.stdout.strip(), "2000000",
                         "money was created or destroyed")

    def test_mixed_churn_conserves_and_never_overdraws(self):
        try:
            r = run_child(MIXED, 45)
        except subprocess.TimeoutExpired:
            self.fail("mixed churn deadlocked or hung (45s)")
        self.assertEqual(r.returncode, 0, f"child crashed: {r.stderr[-800:]}")
        self.assertEqual(r.stdout.strip(), "500000 True",
                         "total drifted or an account went negative")


class ApiPreserved(unittest.TestCase):
    def test_transfer_refuses_overdraw(self):
        led = pipeline.Ledger({"a": 10, "b": 0})
        self.assertFalse(led.transfer("a", "b", 11))
        self.assertEqual(led.balances["a"], 10)
        self.assertEqual(led.balances["b"], 0)
        self.assertTrue(led.transfer("a", "b", 10))
        self.assertEqual(led.balances, {"a": 0, "b": 10})

    def test_surface(self):
        led = pipeline.Ledger({"a": 5})
        led.deposit("a", 3)
        self.assertEqual(led.balances["a"], 8)
        self.assertEqual(led.total(), 8)
        p = pipeline.WorkerPool(2)
        p.submit(lambda: 1)
        p.submit(lambda: 2)
        self.assertEqual(sorted(p.run()), [1, 2])


if __name__ == "__main__":
    unittest.main()
