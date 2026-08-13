"""Sliding-window analytics over a numeric series."""

import heapq
import math


_ORDERED_NUMBER_TYPES = (int, float, bool)
_HASHABLE_NUMBER_TYPES = (int, float, bool, complex)


def _rolling_median_reference(values, window):
    """The general implementation, kept for its exact Python semantics."""
    out = []
    for i in range(len(values) - window + 1):
        chunk = sorted(values[i:i + window])
        mid = window // 2
        if window % 2:
            out.append(float(chunk[mid]))
        else:
            out.append((chunk[mid - 1] + chunk[mid]) / 2.0)
    return out


def _numeric_medians(values, window):
    """O(n log window) sliding medians for totally ordered built-in numbers."""
    n = len(values)
    result_count = n - window + 1
    if result_count <= 0:
        return []

    # ``small`` is a max-heap encoded as a min-heap.  The original index is
    # part of each key so equal values retain sorted()'s stable ordering.  The
    # original value is also retained (not reconstructed by negation), which
    # matters for signed zero.
    small = []
    large = []
    delayed = set()
    side = bytearray(n)       # 0: small, 1: large
    small_size = 0
    large_size = 0

    def prune_small():
        while small and small[0][2] in delayed:
            index = heapq.heappop(small)[2]
            delayed.remove(index)

    def prune_large():
        while large and large[0][1] in delayed:
            index = heapq.heappop(large)[1]
            delayed.remove(index)

    def rebalance():
        nonlocal small_size, large_size
        if small_size > large_size + 1:
            prune_small()
            _, _, index, value = heapq.heappop(small)
            heapq.heappush(large, (value, index))
            side[index] = 1
            small_size -= 1
            large_size += 1
        elif small_size < large_size:
            prune_large()
            value, index = heapq.heappop(large)
            heapq.heappush(small, (-value, -index, index, value))
            side[index] = 0
            small_size += 1
            large_size -= 1
        prune_small()
        prune_large()

    def add(index):
        nonlocal small_size, large_size
        value = values[index]
        if not small or (value, index) <= (small[0][3], small[0][2]):
            heapq.heappush(small, (-value, -index, index, value))
            side[index] = 0
            small_size += 1
        else:
            heapq.heappush(large, (value, index))
            side[index] = 1
            large_size += 1
        rebalance()

    def remove(index):
        nonlocal small_size, large_size
        delayed.add(index)
        if side[index] == 0:
            small_size -= 1
            prune_small()
        else:
            large_size -= 1
            prune_large()
        rebalance()

    for index in range(window):
        add(index)

    out = []
    odd = window % 2
    for start in range(result_count):
        if odd:
            out.append(float(small[0][3]))
        else:
            out.append((small[0][3] + large[0][0]) / 2.0)

        incoming = start + window
        if incoming < n:
            remove(start)
            add(incoming)
    return out


def rolling_median(values, window):
    """Median of every consecutive `window`-sized slice, left to right.

    Returns a list of length max(0, len(values) - window + 1).
    For an even window the median is the mean of the two central elements.
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")

    # Keep the old implementation for arbitrary sequences and objects: their
    # slicing, comparison, and conversion methods may have observable custom
    # behavior.  NaN also needs the old path because sorted() deliberately does
    # not impose a total ordering on it.
    if type(window) is not int or type(values) not in (list, tuple):
        return _rolling_median_reference(values, window)
    if window > len(values):
        return []
    if not all(type(value) in _ORDERED_NUMBER_TYPES and
               not (type(value) is float and math.isnan(value))
               for value in values):
        return _rolling_median_reference(values, window)
    return _numeric_medians(values, window)


def _window_distinct_counts_reference(values, window):
    """The general implementation, kept for its exact Python semantics."""
    return [len(set(values[i:i + window]))
            for i in range(len(values) - window + 1)]


def window_distinct_counts(values, window):
    """Count of distinct values in every consecutive `window`-sized slice.

    Returns a list of length max(0, len(values) - window + 1).
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")

    if type(window) is not int or type(values) not in (list, tuple):
        return _window_distinct_counts_reference(values, window)
    n = len(values)
    result_count = n - window + 1
    if result_count <= 0:
        return []
    if not all(type(value) in _HASHABLE_NUMBER_TYPES for value in values):
        return _window_distinct_counts_reference(values, window)

    counts = {}
    for value in values[:window]:
        counts[value] = counts.get(value, 0) + 1

    out = [len(counts)]
    for incoming in range(window, n):
        outgoing_value = values[incoming - window]
        old_count = counts[outgoing_value]
        if old_count == 1:
            del counts[outgoing_value]
        else:
            counts[outgoing_value] = old_count - 1

        incoming_value = values[incoming]
        counts[incoming_value] = counts.get(incoming_value, 0) + 1
        out.append(len(counts))
    return out
