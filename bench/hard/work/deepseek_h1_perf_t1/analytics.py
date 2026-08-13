"""Sliding-window analytics over a numeric series."""

import heapq
from collections import Counter


def rolling_median(values, window):
    """Median of every consecutive `window`-sized slice, left to right.

    Returns a list of length max(0, len(values) - window + 1).
    For an even window the median is the mean of the two central elements.
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")

    n = len(values)
    out_len = len(range(n - window + 1))
    out = [0.0] * out_len
    if not out:
        return out

    # Keep the current window split into two halves:
    #   low  -- max-heap (values stored negated) of the smaller half
    #   high -- min-heap of the larger half
    # Entries are (value, index) tuples so equal values stay orderable.
    # Elements that leave the window are only flagged in `removed` and are
    # physically popped once they reach the top of their heap, so every
    # step costs O(log window) instead of re-sorting the whole window.
    low = []
    high = []
    removed = [False] * n
    in_low = [True] * n
    low_live = 0
    high_live = 0

    heappush = heapq.heappush
    heappop = heapq.heappop

    def clean_low():
        while low and removed[low[0][1]]:
            heappop(low)

    def clean_high():
        while high and removed[high[0][1]]:
            heappop(high)

    def add(i):
        nonlocal low_live, high_live
        clean_low()
        clean_high()
        v = values[i]
        if low and v <= -low[0][0]:
            heappush(low, (-v, i))
            low_live += 1
        else:
            heappush(high, (v, i))
            in_low[i] = False
            high_live += 1
        while low_live > high_live + 1:
            neg, j = heappop(low)
            heappush(high, (-neg, j))
            in_low[j] = False
            low_live -= 1
            high_live += 1
        while high_live > low_live:
            v2, j2 = heappop(high)
            heappush(low, (-v2, j2))
            in_low[j2] = True
            high_live -= 1
            low_live += 1

    def drop(i):
        nonlocal low_live, high_live
        removed[i] = True
        if in_low[i]:
            low_live -= 1
        else:
            high_live -= 1
        while high_live > low_live:
            clean_high()
            v2, j2 = heappop(high)
            heappush(low, (-v2, j2))
            in_low[j2] = True
            high_live -= 1
            low_live += 1
        while low_live > high_live + 1:
            clean_low()
            neg, j = heappop(low)
            heappush(high, (-neg, j))
            in_low[j] = False
            low_live -= 1
            high_live += 1

    for i in range(window):
        add(i)

    if window & 1:
        for j in range(out_len):
            clean_low()
            out[j] = float(-low[0][0])
            if j + window < n:
                add(j + window)
                drop(j)
    else:
        for j in range(out_len):
            clean_low()
            clean_high()
            out[j] = (-low[0][0] + high[0][0]) / 2.0
            if j + window < n:
                add(j + window)
                drop(j)

    return out


def window_distinct_counts(values, window):
    """Count of distinct values in every consecutive `window`-sized slice.

    Returns a list of length max(0, len(values) - window + 1).
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")

    n = len(values)
    out_len = len(range(n - window + 1))
    out = [0] * out_len
    if not out:
        return out

    counts = Counter(values[:window])
    distinct = len(counts)
    out[0] = distinct
    for i in range(window, n):
        new_v = values[i]
        old_v = values[i - window]
        c = counts.get(new_v, 0)
        if c:
            counts[new_v] = c + 1
        else:
            counts[new_v] = 1
            distinct += 1
        c = counts[old_v]
        if c == 1:
            del counts[old_v]
            distinct -= 1
        else:
            counts[old_v] = c - 1
        out[i - window + 1] = distinct

    return out
