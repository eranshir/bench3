"""A tiny ledger and a worker pool used by the batch settlement job."""
from contextlib import contextmanager
import queue
import threading


class Ledger:
    """Account balances with transfers and deposits."""

    def __init__(self, balances):
        self.balances = dict(balances)
        self.audit = []
        self._locks = {name: threading.Lock() for name in self.balances}

    @contextmanager
    def _locked(self, names):
        """Acquire the given accounts' locks in a fixed order (by name)."""
        locks = [self._locks[name] for name in sorted(names)]
        for lock in locks:
            lock.acquire()
        try:
            yield
        finally:
            for lock in reversed(locks):
                lock.release()

    def transfer(self, src, dst, amount):
        """Move `amount` from src to dst. Returns True if it happened."""
        with self._locked((src, dst)):
            if self.balances[src] < amount:
                return False
            self.balances[src] = self.balances[src] - amount
            self.balances[dst] = self.balances[dst] + amount
            return True

    def deposit(self, account, amount):
        """Add `amount` to an account and record it in the audit trail.

        The audit entry snapshots the ledger-wide total at the moment of the
        deposit, which is what the settlement report reconciles against.
        """
        with self._locked(self.balances):
            current = self.balances[account]
            new = current + amount
            self.balances[account] = new
            running = sum(self.balances.values())
            self.audit.append({"account": account, "amount": amount,
                               "balance_after": new, "ledger_total": running})

    def total(self):
        with self._locked(self.balances):
            return sum(self.balances.values())


class WorkerPool:
    """Runs submitted zero-argument callables across N threads."""

    _sentinel = object()

    def __init__(self, workers):
        self.workers = workers
        self.q = queue.Queue()
        self.results = []
        self._results_lock = threading.Lock()

    def submit(self, fn):
        self.q.put(fn)

    def _worker(self):
        while True:
            item = self.q.get()
            if item is WorkerPool._sentinel:
                return
            result = item()
            with self._results_lock:
                self.results.append(result)

    def run(self):
        """Run every submitted task, then return the results."""
        for _ in range(self.workers):
            self.q.put(WorkerPool._sentinel)
        threads = [threading.Thread(target=self._worker)
                   for _ in range(self.workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return self.results
