"""Sliding-window analytics. Correct, but both functions are O(n*w): for a
window of size w over n points they recompute everything from scratch per
window position. They must become fast (sub-quadratic) without changing
behaviour: exact same outputs, same input validation."""
from collections import Counter


def rolling_median(values, window):
    """Median of each contiguous window of size `window` over values.
    O(n*w) implementation: sorts every window slice."""
    if window <= 0:
        raise ValueError("window must be positive")
    if window > len(values):
        raise ValueError("window larger than input")
    out = []
    for i in range(len(values) - window + 1):
        win = sorted(values[i:i + window])
        mid = len(win) // 2
        if len(win) % 2 == 1:
            out.append(float(win[mid]))
        else:
            out.append((win[mid - 1] + win[mid]) / 2.0)
    return out


def window_distinct_counts(values, window):
    """Number of distinct values in each contiguous window.
    O(n*w): recounts every window."""
    if window <= 0:
        raise ValueError("window must be positive")
    if window > len(values):
        raise ValueError("window larger than input")
    out = []
    for i in range(len(values) - window + 1):
        out.append(len(Counter(values[i:i + window])))
    return out
