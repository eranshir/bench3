"""A tiny ledger and a worker pool used by the batch settlement job."""
import queue
import threading


class Ledger:
    """Account balances with transfers and deposits."""

    def __init__(self, balances):
        self.balances = dict(balances)
        self.audit = []
        self._locks = {name: threading.Lock() for name in self.balances}
        # Transfers leave the ledger total unchanged, so deposits only need a
        # separate lock to update the cached total and audit trail atomically.
        # This avoids making unrelated transfers contend on one global lock.
        self._total_lock = threading.Lock()
        self._total = sum(self.balances.values())

    def transfer(self, src, dst, amount):
        """Move `amount` from src to dst. Returns True if it happened."""
        src_lock = self._locks[src]
        dst_lock = self._locks[dst]

        if src == dst:
            with src_lock:
                return self.balances[src] >= amount

        # Every transfer acquires account locks in the same order. Ordering by
        # lock identity also works for account keys that cannot be compared.
        first, second = sorted((src_lock, dst_lock), key=id)
        with first:
            with second:
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
        # Always take these locks in this order. Transfers never take the
        # total lock, so waiting for an account here cannot form a cycle.
        with self._total_lock:
            with self._locks[account]:
                new = self.balances[account] + amount
                self.balances[account] = new
                self._total += amount
                self.audit.append({"account": account, "amount": amount,
                                   "balance_after": new,
                                   "ledger_total": self._total})

    def total(self):
        with self._total_lock:
            return self._total


class WorkerPool:
    """Runs submitted zero-argument callables across N threads."""

    def __init__(self, workers):
        if workers <= 0:
            raise ValueError("workers must be greater than zero")
        self.workers = workers
        self.q = queue.Queue()
        self.results = []
        self._results_lock = threading.Lock()
        self._submit_lock = threading.Lock()
        self._run_lock = threading.Lock()
        self._stop = object()

    def submit(self, fn):
        with self._submit_lock:
            self.q.put(fn)

    def _worker(self):
        while True:
            fn = self.q.get()
            try:
                if fn is self._stop:
                    return
                try:
                    result = fn()
                except BaseException as error:
                    # A failed callable still occupies its result slot and
                    # must not kill a worker before the queue is drained.
                    result = error
                with self._results_lock:
                    self.results.append(result)
            finally:
                self.q.task_done()

    def run(self):
        """Run every submitted task, then return the results."""
        with self._run_lock:
            threads = [threading.Thread(target=self._worker)
                       for _ in range(self.workers)]
            for t in threads:
                t.start()

            # Queue.join() also accounts for work submitted by a running task.
            # Once it drains, queue the stopping markers while submissions are
            # excluded so new work has a clean cutoff for the next run.
            self.q.join()
            with self._submit_lock:
                for _ in range(self.workers):
                    self.q.put(self._stop)

            for t in threads:
                t.join()
            return self.results
