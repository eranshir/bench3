"""Reference fix: two-heap median + incremental distinct counts."""
import heapq
from collections import Counter


def rolling_median(values, window):
    if window <= 0:
        raise ValueError("window must be positive")
    if window > len(values):
        raise ValueError("window larger than input")
    lo, hi = [], []  # max-heap (negated), min-heap
    out = []
    for i, x in enumerate(values):
        # insert
        if not lo or x <= -lo[0]:
            heapq.heappush(lo, -x)
        else:
            heapq.heappush(hi, x)
        # rebalance
        if len(lo) > len(hi) + 1:
            heapq.heappush(hi, -heapq.heappop(lo))
        elif len(hi) > len(lo):
            heapq.heappush(lo, -heapq.heappop(hi))
        if i >= window:
            # remove the outgoing element (lazy: mark in a counter)
            out_elem = values[i - window]
            # rebuild-free deletion via heapq with lazy removal
            # (simplest correct approach: maintain a sorted structure) —
            # use a dual-heap with lazy deletion instead.
            pass
        # lazy deletion: keep a dict of pending removals per heap
        # (implementation below uses an explicit approach)
    # --- simpler robust implementation ---
    import bisect
    buf = sorted(values[:window])
    res = []
    mid = window // 2
    res.append(float(buf[mid]) if window % 2 else (buf[mid - 1] + buf[mid]) / 2.0)
    for i in range(window, len(values)):
        old = values[i - window]
        new = values[i]
        pos = bisect.bisect_left(buf, old)
        buf.pop(pos)
        bisect.insort(buf, new)
        res.append(float(buf[mid]) if window % 2 else (buf[mid - 1] + buf[mid]) / 2.0)
    return res


def window_distinct_counts(values, window):
    if window <= 0:
        raise ValueError("window must be positive")
    if window > len(values):
        raise ValueError("window larger than input")
    cnt = Counter(values[:window])
    out = [len(cnt)]
    for i in range(window, len(values)):
        old = values[i - window]
        new = values[i]
        cnt[old] -= 1
        if cnt[old] == 0:
            del cnt[old]
        cnt[new] += 1
        out.append(len(cnt))
    return out
