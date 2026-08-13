def percentile(values, p):
    """Return the p-th percentile (0-100) using nearest-rank.

    Nearest-rank: the smallest value at or below which at least p% of the
    data falls. For p=50 over [1,2,3,4] that is 2.
    """
    if not values:
        raise ValueError("values must be non-empty")
    s = sorted(values)
    rank = max(1, (p * len(s) + 99) // 100)
    return s[rank - 1]
