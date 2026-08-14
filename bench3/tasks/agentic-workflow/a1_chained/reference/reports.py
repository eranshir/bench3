"""Reporting. Fixed: inclusive end date, 1-indexed pagination."""
from .db import connect


def report_totals(start: str, end: str, page: int = 1, per_page: int = 10) -> dict:
    conn = connect()
    where = "at >= ? AND at <= ?"  # FIX 4a: inclusive end date
    total = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) FROM transactions WHERE " + where,
        (start, end)).fetchone()[0]
    offset = (page - 1) * per_page  # FIX 4b: 1-indexed pages
    rows = conn.execute(
        "SELECT account, amount_cents, at, currency FROM transactions WHERE " + where + " ORDER BY at, id LIMIT ? OFFSET ?",
        (start, end, per_page, offset)).fetchall()
    conn.close()
    return {"total_cents": total, "rows": rows, "page": page}
