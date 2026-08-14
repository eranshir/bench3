#!/usr/bin/env python3
"""Times the two analytics functions on inputs sized to expose O(n*w).
Run: python3 bench.py   (prints timings; the task is to make them fast)"""
import random
import time

from analytics import rolling_median, window_distinct_counts

random.seed(7)
n, w = 150_000, 2_500
data = [random.randint(0, 1000) for _ in range(n)]

for name, fn in (("rolling_median", rolling_median),
                 ("window_distinct_counts", window_distinct_counts)):
    t0 = time.time()
    fn(data, w)
    dt = time.time() - t0
    print(f"{name}: {dt:.1f}s")
