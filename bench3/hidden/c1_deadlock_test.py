import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pool import Ledger, WorkerPool


class GilYieldingDict(dict):
    """Yields the GIL on every read, exposing unsynchronized read-modify-writes."""
    def __getitem__(self, k):
        time.sleep(0)
        return dict.__getitem__(self, k)
    def get(self, k, d=None):
        time.sleep(0)
        return dict.get(self, k, d)


def run_isolated(scenario, timeout=45):
    """Run a scenario script in a child process (its dir is added to sys.path).
    A deadlocked pool leaves non-daemon threads alive, so an in-process check
    would hang the grader; a child process can be killed on timeout."""
    import tempfile
    task_dir = Path(__file__).parent
    header = "import sys; sys.path.insert(0, %r)\n" % str(task_dir)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(header + scenario)
        tmp = f.name
    try:
        r = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -9, "", "TIMEOUT"
    finally:
        import os
        os.unlink(tmp)


class T(unittest.TestCase):
    def test_withdraw_is_mutually_exclusive(self):
        """Deterministic: every read yields the GIL; a non-atomic RMW loses updates."""
        g = Ledger()
        g.balances = GilYieldingDict(g.balances)
        g.deposit("a", 1000)
        n = 300
        def worker():
            for _ in range(n):
                g.withdraw("a", 1)
        ts = [threading.Thread(target=worker) for _ in range(2)]
        for t in ts: t.start()
        for t in ts: t.join()
        self.assertEqual(g.balances["a"], 400, "lost updates: balance=%d" % g.balances["a"])

    def test_audit_consistent_under_load(self):
        """Audit totals must be exact while deposits/withdraws run."""
        g = Ledger()
        g.deposit("a", 5000); g.deposit("b", 5000)
        stop = threading.Event()
        results = []
        def churn():
            while not stop.is_set():
                g.deposit("a", 1); g.withdraw("b", 1)
        def audit():
            while not stop.is_set():
                results.append(g._audit_total())
        c = threading.Thread(target=churn); a = threading.Thread(target=audit)
        c.start(); a.start()
        time.sleep(0.5)
        stop.set(); c.join(); a.join()
        self.assertTrue(results, "no audits ran")
        self.assertEqual(set(results), {10000}, "torn audit totals: %s" % sorted(set(results))[:5])

    def test_transfer_reconcile_no_deadlock(self):
        scenario = '''from pool import Ledger
import threading, time
g = Ledger(); g.deposit('x', 100); g.deposit('y', 100)
stop = threading.Event()
def t():
    while not stop.is_set():
        g.transfer('x', 'y', 1)
def r():
    while not stop.is_set():
        g.reconcile('x', 'y', 1)
a = threading.Thread(target=t); b = threading.Thread(target=r)
a.start(); b.start()
time.sleep(1.5); stop.set()
a.join(timeout=1); b.join(timeout=1)
print('alive', a.is_alive() or b.is_alive())
print('total', g.balances['x'] + g.balances['y'])
'''
        rc, out, err = run_isolated(scenario)
        self.assertNotEqual(rc, -9, "deadlock: scenario hung (timeout)")
        self.assertIn("alive False", out, out + err)
        self.assertIn("total 200", out, out + err)

    def test_pool_runs_every_task(self):
        p = WorkerPool(n=6)
        counter = {"n": 0}
        lock = threading.Lock()
        def task():
            with lock:
                counter["n"] += 1
        for _ in range(300):
            p.submit(task)
        time.sleep(1.5)
        p.stop()
        self.assertEqual(counter["n"], 300, "lost tasks: %d/300" % counter["n"])


if __name__ == "__main__":
    unittest.main()
