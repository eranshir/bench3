"""Reference fix for c1_deadlock: all three bugs corrected."""
import threading
import time


class Ledger:
    def __init__(self):
        self.balances = {}
        self._lock = threading.Lock()
        self._log = threading.Lock()
        self.ops = []

    def _audit_total(self):
        total = 0
        with self._lock:
            for v in self.balances.values():
                total += v
                time.sleep(0)
        return total

    def deposit(self, acct, amount):
        with self._lock:
            self.balances[acct] = self.balances.get(acct, 0) + amount

    def withdraw(self, acct, amount):
        with self._lock:  # FIX 1: RMW atomic
            cur = self.balances.get(acct, 0)
            time.sleep(0)
            self.balances[acct] = cur - amount

    def transfer(self, src, dst, amount):
        with self._lock:
            with self._log:  # consistent order: _lock then _log
                self.balances[src] = self.balances.get(src, 0) - amount
                self.balances[dst] = self.balances.get(dst, 0) + amount
                self.ops.append(("xfer", src, dst, amount))

    def reconcile(self, src, dst, amount):
        with self._lock:  # FIX 2: same order as transfer -> no inversion
            with self._log:
                self.balances[dst] = self.balances.get(dst, 0) - amount
                self.balances[src] = self.balances.get(src, 0) + amount
                self.ops.append(("recon", dst, src, amount))


class WorkerPool:
    def __init__(self, n=4):
        self._queue = []
        self._qlock = threading.Lock()
        self._stop = False
        self._threads = [threading.Thread(target=self._run, daemon=True) for _ in range(n)]
        for t in self._threads:
            t.start()

    def submit(self, fn, *args):
        with self._qlock:
            self._queue.append((fn, args))

    def _run(self):
        while not self._stop:
            with self._qlock:  # FIX 3: check+pop atomic
                if not self._queue:
                    continue
                time.sleep(0.001)
                fn, args = self._queue.pop(0)
            fn(*args)

    def stop(self):
        self._stop = True
        for t in self._threads:
            t.join(timeout=5)
