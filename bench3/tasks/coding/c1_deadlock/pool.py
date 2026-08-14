"""A tiny thread pool with a shared ledger. Contains three subtle concurrency bugs."""
import threading
import time


class Ledger:
    """Per-account integer balances. Thread-safe is the claim; it is not."""

    def __init__(self):
        self.balances = {}          # account -> int
        self._lock = threading.Lock()   # guards balances
        self._log = threading.Lock()    # guards ops
        self.ops = []

    def _audit_total(self):
        """Sum all balances. The GIL is yielded between each read so a
        concurrent writer interleaves, exactly like a real audit walk."""
        total = 0
        for v in self.balances.values():
            total += v
            time.sleep(0)           # yield: interleaving point
        return total

    def deposit(self, acct, amount):
        """Add amount to acct. Atomic."""
        with self._lock:
            self.balances[acct] = self.balances.get(acct, 0) + amount

    def withdraw(self, acct, amount):
        """Subtract amount from acct. BUG 1: the read-modify-write is not
        protected end-to-end; the audit yield sits between read and write."""
        cur = self.balances.get(acct, 0)
        time.sleep(0)               # interleaving point
        self.balances[acct] = cur - amount

    def transfer(self, src, dst, amount):
        """Move amount from src to dst, logging the op. Takes _lock then _log."""
        with self._lock:
            with self._log:
                self.balances[src] = self.balances.get(src, 0) - amount
                self.balances[dst] = self.balances.get(dst, 0) + amount
                self.ops.append(("xfer", src, dst, amount))

    def reconcile(self, src, dst, amount):
        """Correct an earlier transfer (move amount back dst -> src).
        BUG 2: takes _log then _lock — the opposite order of transfer()."""
        with self._log:
            with self._lock:
                self.balances[dst] = self.balances.get(dst, 0) - amount
                self.balances[src] = self.balances.get(src, 0) + amount
                self.ops.append(("recon", dst, src, amount))


class WorkerPool:
    """Fixed pool of workers draining a shared task queue.
    BUG 3: check-then-act on an empty queue (pop can race another worker)."""

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
            if not self._queue:          # BUG 3: check happens outside the lock
                time.sleep(0.001)
                continue
            with self._qlock:
                time.sleep(0.001)        # interleaving point: another worker
                fn, args = self._queue.pop(0)   # may pop the last item first
            fn(*args)                            # -> IndexError, worker dies

    def stop(self):
        self._stop = True
        for t in self._threads:
            t.join(timeout=5)
