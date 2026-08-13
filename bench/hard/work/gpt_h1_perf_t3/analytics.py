"""Sliding-window analytics over a numeric series."""

from bisect import bisect_left, insort_right
from math import isnan


def _can_use_sorted_window(values):
    """Whether bisect has the same ordering semantics as repeated ``sorted``."""
    for value in values:
        value_type = type(value)
        if value_type is float:
            # NaNs do not define a total ordering.  Their position under sorted()
            # depends on the other items in each individual slice.
            if isnan(value):
                return False
        elif value_type is not int and value_type is not bool:
            return False
    return True


def _can_use_frequency_table(values):
    """Whether all keys have side-effect-free built-in hash/equality behavior."""
    numeric_types = (int, bool, float, complex)
    return all(type(value) in numeric_types for value in values)


def rolling_median(values, window):
    """Median of every consecutive `window`-sized slice, left to right.

    Returns a list of length max(0, len(values) - window + 1).
    For an even window the median is the mean of the two central elements.
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")

    # For ordinary built-in numeric sequences, maintain one sorted window.
    # List insertion/deletion moves references in C, avoiding a Python-level
    # re-sort for every result.  Keep the original implementation as the
    # compatibility path for custom sequences, custom numeric classes and NaN.
    if (type(window) is int and type(values) in (list, tuple)
            and len(values) >= window and _can_use_sorted_window(values)):
        ordered = sorted(values[:window])
        mid = window // 2
        odd = window % 2
        out = []

        if odd:
            out.append(float(ordered[mid]))
        else:
            out.append((ordered[mid - 1] + ordered[mid]) / 2.0)

        for right in range(window, len(values)):
            old = values[right - window]
            del ordered[bisect_left(ordered, old)]
            insort_right(ordered, values[right])
            if odd:
                out.append(float(ordered[mid]))
            else:
                out.append((ordered[mid - 1] + ordered[mid]) / 2.0)
        return out

    out = []
    for i in range(len(values) - window + 1):
        chunk = sorted(values[i:i + window])
        mid = window // 2
        if window % 2:
            out.append(float(chunk[mid]))
        else:
            out.append((chunk[mid - 1] + chunk[mid]) / 2.0)
    return out


def window_distinct_counts(values, window):
    """Count of distinct values in every consecutive `window`-sized slice.

    Returns a list of length max(0, len(values) - window + 1).
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")

    # Counts let each slide update two entries instead of rebuilding a set.
    # Restrict the fast path to built-in numeric keys so that custom __hash__
    # and __eq__ calls (including their exceptions and side effects) retain the
    # exact behavior of the straightforward implementation below.
    if (type(window) is int and type(values) in (list, tuple)
            and len(values) >= window and _can_use_frequency_table(values)):
        counts = {}
        for value in values[:window]:
            counts[value] = counts.get(value, 0) + 1

        out = [len(counts)]
        for right in range(window, len(values)):
            old = values[right - window]
            remaining = counts[old] - 1
            if remaining:
                counts[old] = remaining
            else:
                del counts[old]

            new = values[right]
            counts[new] = counts.get(new, 0) + 1
            out.append(len(counts))
        return out

    return [len(set(values[i:i + window]))
            for i in range(len(values) - window + 1)]
