"""A tiny ledger and a worker pool used by the batch settlement job."""
import queue
import threading


class Ledger:
    """Account balances with transfers and deposits."""

    def __init__(self, balances):
        self.balances = dict(balances)
        self.audit = []
        self._locks = {name: threading.Lock() for name in self.balances}

    def transfer(self, src, dst, amount):
        """Move `amount` from src to dst. Returns True if it happened."""
        with self._locks[src]:
            with self._locks[dst]:
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
        current = self.balances[account]
        new = current + amount
        running = 0
        for value in self.balances.values():
            running += value
        self.audit.append({"account": account, "amount": amount,
                           "balance_after": new, "ledger_total": running})
        self.balances[account] = new

    def total(self):
        return sum(self.balances.values())


class WorkerPool:
    """Runs submitted zero-argument callables across N threads."""

    def __init__(self, workers):
        self.workers = workers
        self.q = queue.Queue()
        self.results = []

    def submit(self, fn):
        self.q.put(fn)

    def _worker(self):
        while not self.q.empty():
            fn = self.q.get()
            self.results.append(fn())

    def run(self):
        """Run every submitted task, then return the results."""
        threads = [threading.Thread(target=self._worker)
                   for _ in range(self.workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return self.results
