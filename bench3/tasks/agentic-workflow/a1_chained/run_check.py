#!/usr/bin/env python3
"""End-to-end check for the svc package. Run: python3 run_check.py

A correct service prints `all checks passed`. Every shipped bug breaks
this script somewhere — fix them in whatever order the errors reveal."""
import os
import sys

from svc.config import DB_PATH
from svc.db import connect
from svc.reports import report_totals


def main():
    conn = connect()
    conn.execute("DELETE FROM transactions")
    rows = [
        ("a", 1000, "2026-08-01 10:00:00", "USD"),
        ("b", 2000, "2026-08-01 11:00:00", "USD"),
        ("c", 4000, "2026-08-01 12:00:00", "EUR"),  # exactly ON the end date
        ("d", 8000, "2026-08-01 13:00:00", "USD"),
    ]
    conn.executemany("INSERT INTO transactions (account, amount_cents, at, currency) VALUES (?,?,?,?)", rows)
    conn.commit()
    conn.close()

    r = report_totals("2026-08-01 00:00:00", "2026-08-01 12:00:00")
    assert r["total_cents"] == 7000, "inclusive end date: got %s" % r["total_cents"]

    p1 = report_totals("2026-08-01 00:00:00", "2026-08-01 23:59:59", page=1, per_page=2)
    p2 = report_totals("2026-08-01 00:00:00", "2026-08-01 23:59:59", page=2, per_page=2)
    assert [x[0] for x in p1["rows"]] == ["a", "b"], "page 1: %s" % [x[0] for x in p1["rows"]]
    assert [x[0] for x in p2["rows"]] == ["c", "d"], "page 2: %s" % [x[0] for x in p2["rows"]]
    assert p1["rows"][0][3] == "USD", "currency column missing"
    print("all checks passed")


if __name__ == "__main__":
    main()
