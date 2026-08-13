"""A tiny ledger and a worker pool used by the batch settlement job."""
import queue
import threading


class Ledger:
    """Account balances with transfers and deposits."""

    def __init__(self, balances):
        self.balances = dict(balances)
        self.audit = []
        self._lock = threading.Lock()

    def transfer(self, src, dst, amount):
        """Move `amount` from src to dst. Returns True if it happened."""
        with self._lock:
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
        with self._lock:
            current = self.balances[account]
            new = current + amount
            running = sum(self.balances.values())
            self.audit.append({"account": account, "amount": amount,
                               "balance_after": new, "ledger_total": running})
            self.balances[account] = new

    def total(self):
        with self._lock:
            return sum(self.balances.values())


class WorkerPool:
    """Runs submitted zero-argument callables across N threads."""

    def __init__(self, workers):
        self.workers = workers
        self.q = queue.Queue()
        self.results = []
        self._results_lock = threading.Lock()

    def submit(self, fn):
        self.q.put(fn)

    def _worker(self):
        while True:
            fn = self.q.get()
            if fn is None:
                return
            result = fn()
            with self._results_lock:
                self.results.append(result)

    def run(self):
        """Run every submitted task, then return the results."""
        for _ in range(self.workers):
            self.q.put(None)
        threads = [threading.Thread(target=self._worker)
                   for _ in range(self.workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return self.results
