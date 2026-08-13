def percentile(values, p):
    """Return the p-th percentile (0-100) using nearest-rank.

    Nearest-rank: the smallest value at or below which at least p% of the
    data falls. For p=50 over [1,2,3,4] that is 2.
    """
    if not values:
        raise ValueError("values must be non-empty")
    s = sorted(values)
    rank = (p * len(s) + 99) // 100  # ceil(p/100 * n), nearest-rank
    rank = max(1, rank)  # p=0 means the smallest value
    return s[rank - 1]
