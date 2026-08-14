"""Reporting. BUG 4: the end-date filter is exclusive (rows ON the end date
are dropped) and pagination is 0-indexed while the caller uses 1-indexed
pages, so page 1 silently skips the first row."""
from .db import connect


def report_totals(start: str, end: str, page: int = 1, per_page: int = 10) -> dict:
    conn = connect()
    # BUG 4a: exclusive end date
    where = "at >= ? AND at < ?"
    total = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) FROM transactions WHERE " + where,
        (start, end)).fetchone()[0]
    # BUG 4b: 0-indexed pagination (page 1 skips the first page worth of rows)
    offset = page * per_page
    rows = conn.execute(
        "SELECT account, amount_cents, at, currency FROM transactions WHERE " + where + " ORDER BY at, id LIMIT ? OFFSET ?",
        (start, end, per_page, offset)).fetchall()
    conn.close()
    return {"total_cents": total, "rows": rows, "page": page}
