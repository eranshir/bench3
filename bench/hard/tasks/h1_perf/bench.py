"""Timing harness. Run: python3 bench.py"""
import random
import time

from analytics import rolling_median, window_distinct_counts

random.seed(7)


def timed(label, fn, *a):
    t = time.perf_counter()
    out = fn(*a)
    print(f"{label:<28} {time.perf_counter() - t:8.2f}s  ({len(out)} results)")
    return out


if __name__ == "__main__":
    series = [random.randint(0, 10_000) for _ in range(100_000)]
    timed("rolling_median n=100k w=1001", rolling_median, series, 1001)

    series2 = [random.randint(0, 500) for _ in range(200_000)]
    timed("distinct n=200k w=2001", window_distinct_counts, series2, 2001)
