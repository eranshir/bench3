"""Settlement reports.

Amounts are integer minor units (cents). Dates are 'YYYY-MM-DD' strings and
both ends of a range are inclusive of the whole day.
"""


def revenue_between(conn, start, end, currency="USD"):
    """Total revenue for `currency` over [start, end], both days inclusive."""
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM orders "
        "WHERE currency = ? AND created_at >= ? AND created_at < ?",
        (currency, start, end),
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
        (currency, page_size, page * page_size),
    ).fetchall()
    return [(r["customer"], r["total"]) for r in rows]
