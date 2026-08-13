"""Sliding-window analytics over a numeric series."""

from bisect import bisect_left, insort


def rolling_median(values, window):
    """Median of every consecutive `window`-sized slice, left to right.

    Returns a list of length max(0, len(values) - window + 1).
    For an even window the median is the mean of the two central elements.
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    n = len(values)
    if window > n:
        return []

    # Keep the current window in sorted order.  bisect insert/remove are
    # C-backed, so each slide costs O(window) pointer moves instead of a
    # full O(window log window) sort per window.
    sorted_window = sorted(values[:window])
    mid = window // 2
    odd = window % 2
    out = []
    append = out.append
    if odd:
        append(float(sorted_window[mid]))
    else:
        append((sorted_window[mid - 1] + sorted_window[mid]) / 2.0)

    for i in range(window, n):
        insort(sorted_window, values[i])
        del sorted_window[bisect_left(sorted_window, values[i - window])]
        if odd:
            append(float(sorted_window[mid]))
        else:
            append((sorted_window[mid - 1] + sorted_window[mid]) / 2.0)
    return out


def window_distinct_counts(values, window):
    """Count of distinct values in every consecutive `window`-sized slice.

    Returns a list of length max(0, len(values) - window + 1).
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    n = len(values)
    if window > n:
        return []

    # Slide a frequency map over the window instead of rebuilding a set
    # for every position.
    counts = {}
    distinct = 0
    for x in values[:window]:
        c = counts.get(x, 0)
        counts[x] = c + 1
        if c == 0:
            distinct += 1

    out = [distinct]
    append = out.append
    for i in range(window, n):
        leaving = values[i - window]
        c = counts[leaving] - 1
        if c:
            counts[leaving] = c
        else:
            del counts[leaving]
            distinct -= 1
        entering = values[i]
        c = counts.get(entering, 0)
        counts[entering] = c + 1
        if c == 0:
            distinct += 1
        append(distinct)
    return out
