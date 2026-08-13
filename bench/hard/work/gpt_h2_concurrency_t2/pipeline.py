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
        # Lock ordering must not depend on the direction of a transfer (or on
        # account names being mutually comparable).
        self._lock_order = {name: position
                            for position, name in enumerate(self.balances)}

    @contextmanager
    def _locked(self, accounts):
        """Hold each requested account lock in one consistent order."""
        names = sorted(set(accounts), key=self._lock_order.__getitem__)
        locks = [self._locks[name] for name in names]
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
            if src != dst:
                self.balances[src] = self.balances[src] - amount
                self.balances[dst] = self.balances[dst] + amount
            return True

    def deposit(self, account, amount):
        """Add `amount` to an account and record it in the audit trail.

        The audit entry snapshots the ledger-wide total at the moment of the
        deposit, which is what the settlement report reconciles against.
        """
        # The audit entry promises a ledger-wide snapshot. Taking all account
        # locks makes the balance update and that snapshot one atomic event.
        with self._locked(self._locks):
            new = self.balances[account] + amount
            self.balances[account] = new
            running = sum(self.balances.values())
            self.audit.append({"account": account, "amount": amount,
                               "balance_after": new,
                               "ledger_total": running})

    def total(self):
        with self._locked(self._locks):
            return sum(self.balances.values())


class WorkerPool:
    """Runs submitted zero-argument callables across N threads."""

    _STOP = object()

    def __init__(self, workers):
        if workers <= 0:
            raise ValueError("workers must be greater than zero")
        self.workers = workers
        self.q = queue.Queue()
        self.results = []
        self._results_lock = threading.Lock()
        self._submission_lock = threading.Lock()
        self._run_lock = threading.Lock()

    def submit(self, fn):
        with self._submission_lock:
            self.q.put(fn)

    def _worker(self):
        while True:
            fn = self.q.get()
            try:
                if fn is self._STOP:
                    return
                try:
                    result = fn()
                except BaseException as exc:
                    # A failed callable still occupies its result slot and
                    # must not strand the rest of the queue.
                    result = exc
                with self._results_lock:
                    self.results.append(result)
            finally:
                self.q.task_done()

    def run(self):
        """Run every submitted task, then return the results."""
        # Block only competing run()/submit() bookkeeping while defining this
        # batch. Callables run without either lock held.
        with self._run_lock:
            with self._submission_lock:
                self.results = []
                for _ in range(self.workers):
                    self.q.put(self._STOP)

            threads = [threading.Thread(target=self._worker)
                       for _ in range(self.workers)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            return self.results
