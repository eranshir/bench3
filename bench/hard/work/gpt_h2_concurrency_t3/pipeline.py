"""A tiny ledger and a worker pool used by the batch settlement job."""
import queue
import threading


class Ledger:
    """Account balances with transfers and deposits."""

    def __init__(self, balances):
        self.balances = dict(balances)
        self.audit = []
        self._locks = {name: threading.Lock() for name in self.balances}
        # All operations that take more than one account lock use this fixed
        # order.  In particular, a -> b and b -> a must not choose opposite
        # lock orders.
        self._lock_order = {name: index
                            for index, name in enumerate(self.balances)}

    @staticmethod
    def _acquire(locks):
        for lock in locks:
            lock.acquire()

    @staticmethod
    def _release(locks):
        for lock in reversed(locks):
            lock.release()

    def transfer(self, src, dst, amount):
        """Move `amount` from src to dst. Returns True if it happened."""
        accounts = sorted({src, dst}, key=self._lock_order.__getitem__)
        locks = [self._locks[account] for account in accounts]
        self._acquire(locks)
        try:
            if self.balances[src] < amount:
                return False
            self.balances[src] = self.balances[src] - amount
            self.balances[dst] = self.balances[dst] + amount
            return True
        finally:
            self._release(locks)

    def deposit(self, account, amount):
        """Add `amount` to an account and record it in the audit trail.

        The audit entry snapshots the ledger-wide total at the moment of the
        deposit, which is what the settlement report reconciles against.
        """
        # The audit record contains a ledger-wide snapshot, so an account-only
        # lock is insufficient here: another account could change halfway
        # through the sum.  Taking every lock in the same canonical order used
        # by transfer gives the deposit a consistent linearization point.
        locks = list(self._locks.values())
        self._acquire(locks)
        try:
            current = self.balances[account]
            new = current + amount
            running = 0
            for value in self.balances.values():
                running += value
            self.audit.append({"account": account, "amount": amount,
                               "balance_after": new,
                               "ledger_total": running})
            self.balances[account] = new
        finally:
            self._release(locks)

    def total(self):
        locks = list(self._locks.values())
        self._acquire(locks)
        try:
            return sum(self.balances.values())
        finally:
            self._release(locks)


class WorkerPool:
    """Runs submitted zero-argument callables across N threads."""

    def __init__(self, workers):
        if workers < 1:
            raise ValueError("workers must be at least 1")
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
                except BaseException as exc:
                    # A failed task is still a completed submitted task.  Keep
                    # its exception in the corresponding result slot and let
                    # the worker continue with the rest of the queue.
                    result = exc
                with self._results_lock:
                    self.results.append(result)
            finally:
                self.q.task_done()

    def run(self):
        """Run every submitted task, then return the results."""
        # Sentinels create an exact boundary for this batch.  Queue.empty() is
        # only a momentary observation and can otherwise make one worker block
        # in get() after another worker takes the final item.
        with self._run_lock:
            with self._submit_lock:
                for _ in range(self.workers):
                    self.q.put(self._stop)

            threads = [threading.Thread(target=self._worker)
                       for _ in range(self.workers)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            return self.results
