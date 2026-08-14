"""Interval scheduler: return the maximum number of non-overlapping
intervals that can be selected from the input.

The current implementation sorts by START time and greedily picks the
first interval that does not overlap the previous pick. That looks
reasonable and passes many cases, but it is WRONG: sorting by start time
is not the optimal greedy ordering, so on some inputs it returns a
suboptimal count."""


def schedule(intervals):
    """intervals: list of (start, end). Returns the maximum number of
    mutually non-overlapping intervals."""
    # BUG: greedy by start time is not optimal (should be by end time)
    ordered = sorted(intervals, key=lambda iv: iv[0])
    count = 0
    last_end = float('-inf')
    for start, end in ordered:
        if start >= last_end:
            count += 1
            last_end = end
    return count
