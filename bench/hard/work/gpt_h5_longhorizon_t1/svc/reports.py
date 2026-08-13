"""Settlement reports.

Amounts are integer minor units (cents). Dates are 'YYYY-MM-DD' strings and
both ends of a range are inclusive of the whole day.
"""
from datetime import date, timedelta


def revenue_between(conn, start, end, currency="USD"):
    """Total revenue for `currency` over [start, end], both days inclusive."""
    # Timestamps sort lexicographically in SQLite, so use the start of the day
    # after `end` as an exclusive upper bound.  Appending a time to `end`
    # would be fragile in the presence of fractional seconds.
    end_exclusive = (date.fromisoformat(end) + timedelta(days=1)).isoformat()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM orders "
        "WHERE currency = ? AND created_at >= ? AND created_at < ?",
        (currency, start, end_exclusive),
    ).fetchone()
    return row["total"]


def top_customers(conn, page=1, page_size=25, currency="USD"):
    """Customers by revenue, highest first. Pages are 1-indexed.

    Ties break on customer name ascending. Returns a list of
    (customer, total) tuples.
    """
    rows = conn.execute(
        "SELECT customer, SUM(amount) AS total FROM orders "
        "WHERE currency = ? "
        "GROUP BY customer ORDER BY total DESC, customer ASC "
        "LIMIT ? OFFSET ?",
        (currency, page_size, (page - 1) * page_size),
    ).fetchall()
    return [(r["customer"], r["total"]) for r in rows]
