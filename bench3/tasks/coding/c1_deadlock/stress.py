#!/usr/bin/env python3
"""Demonstrates the three bugs in pool.py. Run: python3 stress.py

Expected when all bugs are fixed:
  withdraw race: 0 (lost updates gone)
  transfer/reconcile: no deadlock, balances consistent
  pool: all 300 tasks ran
"""
import threading
import time

from pool import Ledger, WorkerPool


def bug1_withdraw():
    g = Ledger()
    g.deposit("a", 1000)
    n = 200
    done = []
    def worker():
        for _ in range(n):
            g.withdraw("a", 1)
        done.append(True)
    ts = [threading.Thread(target=worker) for _ in range(2)]
    for t in ts: t.start()
    for t in ts: t.join()
    left = g.balances["a"]
    print(f"  withdraw race: balance left = {left} (want 0) ->", "OK" if left == 0 else "LOST UPDATES")


def bug2_deadlock():
    g = Ledger()
    g.deposit("x", 100); g.deposit("y", 100)
    stop = threading.Event()
    def tfer():
        while not stop.is_set():
            g.transfer("x", "y", 1)
    def recon():
        while not stop.is_set():
            g.reconcile("x", "y", 1)
    a = threading.Thread(target=tfer); b = threading.Thread(target=recon)
    a.start(); b.start()
    time.sleep(2)
    stop.set()
    a.join(timeout=1); b.join(timeout=1)
    alive = a.is_alive() or b.is_alive()
    total = g.balances["x"] + g.balances["y"]
    print(f"  transfer/reconcile: deadlock={'YES' if alive else 'no'}, total={total} ->",
          "OK" if not alive and total == 200 else "BUG")


def bug3_pool():
    pool = WorkerPool(n=6)
    counter = {"n": 0}
    lock = threading.Lock()
    def task():
        with lock:
            counter["n"] += 1
    for _ in range(300):
        pool.submit(task)
    time.sleep(1.5)
    pool.stop()
    print(f"  pool: ran {counter['n']}/300 ->", "OK" if counter["n"] == 300 else "LOST TASKS")


if __name__ == "__main__":
    print("Bug 1 — unsynchronized read-modify-write:")
    bug1_withdraw()
    print("Bug 2 — lock-order inversion:")
    bug2_deadlock()
    print("Bug 3 — queue check-then-act:")
    bug3_pool()
