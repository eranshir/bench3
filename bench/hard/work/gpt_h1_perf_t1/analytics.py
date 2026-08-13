"""Sliding-window analytics over a numeric series."""

from bisect import bisect_left, insort_right
from math import isnan


def _plain_ordered_number(value):
    """Whether ``value`` has Python's stable, total numeric ordering."""
    value_type = type(value)
    return (value_type is int or value_type is bool or
            (value_type is float and not isnan(value)))


def _plain_hashable_number(value):
    """Whether counting ``value`` in a dict has ordinary set semantics."""
    return type(value) in (int, float, complex, bool)


def rolling_median(values, window):
    """Median of every consecutive `window`-sized slice, left to right.

    Returns a list of length max(0, len(values) - window + 1).
    For an even window the median is the mean of the two central elements.
    Raises ValueError if window is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")

    # Constructing range here deliberately preserves the original validation
    # and TypeError behaviour for non-integral window values.
    starts = range(len(values) - window + 1)
    if not starts:
        return []

    # Pairing each value with its position preserves sorted()'s stable ordering
    # for equal values (including 0.0 and -0.0).  Updating this ordered list is
    # O(window) per slide, but the movement happens in optimized C instead of
    # sorting the whole window again in Python.
    if (type(window) is int and type(values) in (list, tuple) and
            all(_plain_ordered_number(value) for value in values)):
        ordered = sorted((value, index)
                         for index, value in enumerate(values[:window]))
        mid = window // 2
        odd = window % 2
        out = []

        for start in starts:
            if odd:
                out.append(float(ordered[mid][0]))
            else:
                out.append((ordered[mid - 1][0] + ordered[mid][0]) / 2.0)

            incoming_index = start + window
            if incoming_index == len(values):
                break

            outgoing = (values[start], start)
            ordered.pop(bisect_left(ordered, outgoing))
            insort_right(ordered,
                         (values[incoming_index], incoming_index))
        return out

    # Keep the literal implementation for user-defined numeric objects and
    # partial orderings (notably NaN), whose comparison side effects and error
    # behaviour cannot safely be reproduced by an incremental data structure.
    out = []
    for i in starts:
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

    starts = range(len(values) - window + 1)
    if not starts:
        return []

    # Built-in numeric hashes and equality are stable, so one frequency table
    # can be updated as the window moves instead of rebuilding a set each time.
    if (type(window) is int and type(values) in (list, tuple) and
            all(_plain_hashable_number(value) for value in values)):
        counts = {}
        for value in values[:window]:
            counts[value] = counts.get(value, 0) + 1

        out = []
        for start in starts:
            out.append(len(counts))

            incoming_index = start + window
            if incoming_index == len(values):
                break

            outgoing = values[start]
            remaining = counts[outgoing] - 1
            if remaining:
                counts[outgoing] = remaining
            else:
                del counts[outgoing]

            incoming = values[incoming_index]
            counts[incoming] = counts.get(incoming, 0) + 1
        return out

    return [len(set(values[i:i + window])) for i in starts]
