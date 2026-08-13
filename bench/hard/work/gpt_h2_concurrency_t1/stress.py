"""Reproduces the production symptoms. Run: python3 stress.py

Sometimes it prints a wrong total, sometimes it never finishes at all.
"""
import sys
import threading

from pipeline import Ledger, WorkerPool

sys.setswitchinterval(1e-6)


def deposits():
    led = Ledger({"treasury": 0})
    threads = [threading.Thread(
        target=lambda: [led.deposit("treasury", 1) for _ in range(5_000)])
        for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"deposits: expected 40000, got {led.balances['treasury']}")


def opposing_transfers():
    led = Ledger({"a": 1_000_000, "b": 1_000_000})
    a = threading.Thread(
        target=lambda: [led.transfer("a", "b", 1) for _ in range(20_000)])
    b = threading.Thread(
        target=lambda: [led.transfer("b", "a", 1) for _ in range(20_000)])
    a.start()
    b.start()
    a.join(timeout=20)
    b.join(timeout=20)
    stuck = a.is_alive() or b.is_alive()
    print(f"transfers: {'DEADLOCKED' if stuck else 'ok'}, "
          f"total={led.total()} (expected 2000000)")


def pool():
    p = WorkerPool(8)
    for i in range(500):
        p.submit(lambda i=i: i * 2)
    got = p.run()
    print(f"pool: expected 500 results, got {len(got)}")


if __name__ == "__main__":
    deposits()
    pool()
    opposing_transfers()
