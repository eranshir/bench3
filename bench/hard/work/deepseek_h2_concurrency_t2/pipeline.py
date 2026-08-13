"""A tiny ledger and a worker pool used by the batch settlement job."""
import itertools
import queue
import threading


class Ledger:
    """Account balances with transfers and deposits."""

    def __init__(self, balances):
        self.balances = dict(balances)
        self.audit = []
        self._locks = {name: threading.Lock() for name in self.balances}

    def _locked(self, names):
        """Acquire locks for `names` in a canonical order (no deadlocks)."""
        locks = [self._locks[name] for name in sorted(names)]
        for lock in locks:
            lock.acquire()
        return locks

    def transfer(self, src, dst, amount):
        """Move `amount` from src to dst. Returns True if it happened."""
        locks = self._locked((src, dst))
        try:
            if self.balances[src] < amount:
                return False
            self.balances[src] = self.balances[src] - amount
            self.balances[dst] = self.balances[dst] + amount
            return True
        finally:
            for lock in reversed(locks):
                lock.release()

    def deposit(self, account, amount):
        """Add `amount` to an account and record it in the audit trail.

        The audit entry snapshots the ledger-wide total at the moment of the
        deposit, which is what the settlement report reconciles against.
        """
        locks = self._locked(self.balances)
        try:
            current = self.balances[account]
            new = current + amount
            running = 0
            for value in self.balances.values():
                running += value
            self.audit.append({"account": account, "amount": amount,
                               "balance_after": new, "ledger_total": running})
            self.balances[account] = new
        finally:
            for lock in reversed(locks):
                lock.release()

    def total(self):
        locks = self._locked(self.balances)
        try:
            return sum(self.balances.values())
        finally:
            for lock in reversed(locks):
                lock.release()


class WorkerPool:
    """Runs submitted zero-argument callables across N threads."""

    def __init__(self, workers):
        self.workers = workers
        self.q = queue.Queue()
        self._seq = itertools.count()
        self._sentinel = object()

    def submit(self, fn):
        self.q.put((next(self._seq), fn))

    def run(self):
        """Run every submitted task, then return the results."""
        results = {}
        errors = []
        results_lock = threading.Lock()
        for _ in range(self.workers):
            self.q.put((None, self._sentinel))

        def worker():
            while True:
                index, fn = self.q.get()
                if fn is self._sentinel:
                    return
                try:
                    value = fn()
                except BaseException as exc:
                    with results_lock:
                        errors.append((index, exc))
                else:
                    with results_lock:
                        results[index] = value

        threads = [threading.Thread(target=worker)
                   for _ in range(self.workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        if errors:
            raise errors[0][1]
        return [results[i] for i in sorted(results)]
