"""Sliding-window analytics over a numeric series."""

from bisect import bisect_left, insort_right


def _rolling_median_scan(values, window):
    """Reference implementation: sort each window slice independently."""
    out = []
    for i in range(len(values) - window + 1):
        chunk = sorted(values[i:i + window])
        mid = window // 2
        if window % 2:
            out.append(float(chunk[mid]))
        else:
            out.append((chunk[mid - 1] + chunk[mid]) / 2.0)
    return out


def rolling_median(values, window):
    """Median of every consecutive `window`-sized slice, left to right.

    Returns a list of length max(0, len(values) - window + 1).
    For an even window the median is the mean of the two central elements.
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    # Building the range first reproduces the original's TypeError for
    # non-integer windows before any other work happens.
    n = len(range(len(values) - window + 1))
    if n == 0:
        return []

    # NaN does not order against itself, so an incrementally maintained
    # sorted window cannot reproduce sorted()'s per-window ordering.
    # Keep the original scan-and-sort path for those inputs.
    if any(x != x for x in values):
        return _rolling_median_scan(values, window)

    win = sorted(values[:window])
    out = []
    mid = window // 2
    even = window % 2 == 0
    if even:
        out.append((win[mid - 1] + win[mid]) / 2.0)
    else:
        out.append(float(win[mid]))

    # Slide: drop the outgoing element, insert the incoming one, then read
    # the two central elements directly.
    for i in range(1, n):
        leaving = values[i - 1]
        entering = values[i + window - 1]
        del win[bisect_left(win, leaving)]
        insort_right(win, entering)
        if even:
            out.append((win[mid - 1] + win[mid]) / 2.0)
        else:
            out.append(float(win[mid]))
    return out


def window_distinct_counts(values, window):
    """Count of distinct values in every consecutive `window`-sized slice.

    Returns a list of length max(0, len(values) - window + 1).
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    # Same non-integer-window TypeError behaviour as the original.
    n = len(range(len(values) - window + 1))
    if n == 0:
        return []

    # A sliding count map is equivalent to len(set(...)) for every hashable
    # value: set and dict share the same hash/equality semantics, including
    # the identity shortcut.  NaN does not equal itself, so sets treat each
    # distinct NaN *object* as a separate element while collapsing repeats
    # of the same object; track those by identity (id) to mirror that.
    counts = {}
    nan_ids = {}
    distinct = 0
    get = counts.get
    for x in values[:window]:
        if x != x:
            i = id(x)
            c = nan_ids.get(i)
            if c is None:
                distinct += 1
                nan_ids[i] = 1
            else:
                nan_ids[i] = c + 1
        elif get(x) is None:
            distinct += 1
            counts[x] = 1
        else:
            counts[x] = get(x) + 1

    out = [distinct]
    append = out.append
    for i in range(window, len(values)):
        leaving = values[i - window]
        if leaving != leaving:
            j = id(leaving)
            c = nan_ids[j] - 1
            if c:
                nan_ids[j] = c
            else:
                del nan_ids[j]
                distinct -= 1
        else:
            c = counts[leaving]
            if c == 1:
                del counts[leaving]
                distinct -= 1
            else:
                counts[leaving] = c - 1

        entering = values[i]
        if entering != entering:
            j = id(entering)
            c = nan_ids.get(j)
            if c is None:
                distinct += 1
                nan_ids[j] = 1
            else:
                nan_ids[j] = c + 1
        else:
            c = get(entering)
            if c is None:
                distinct += 1
                counts[entering] = 1
            else:
                counts[entering] = c + 1
        append(distinct)
    return out
