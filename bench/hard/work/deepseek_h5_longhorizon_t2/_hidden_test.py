"""Blind grader for h5_longhorizon.

Builds its own database in a temp directory, so a stale ./data/service.db
neither helps nor hurts, and uses data the model never saw. Covers all four
links of the defect chain: the environment default, the missing column, and
the two query-logic bugs (inclusive end date, 1-indexed pages).
"""
import os
import sqlite3
import tempfile
import unittest

from svc import config, db, reports

ROWS = [
    (1, "ann", 10_000, "USD", "2026-05-01 00:00:00"),
    (2, "bob", 20_000, "USD", "2026-05-15 12:00:00"),
    (3, "ann", 30_000, "USD", "2026-05-31 23:59:59"),
    (4, "cid", 40_000, "EUR", "2026-05-10 10:00:00"),
    (5, "dee",  5_000, "USD", "2026-06-01 00:00:00"),
    (6, "bob", 20_000, "USD", "2026-04-30 23:59:59"),
]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.conn = db.connect(os.path.join(self.tmp.name, "t.db"))
        db.init_schema(self.conn)
        self.conn.executemany(
            "INSERT INTO orders (id, customer, amount, currency, created_at) "
            "VALUES (?, ?, ?, ?, ?)", ROWS)
        self.conn.commit()


class Schema(Base):
    def test_currency_column_exists(self):
        cols = {r[1] for r in self.conn.execute(
            "PRAGMA table_info(orders)").fetchall()}
        self.assertEqual(
            {"id", "customer", "amount", "currency", "created_at"} - cols,
            set(), f"orders is missing columns; has {sorted(cols)}")

    def test_init_schema_is_idempotent(self):
        db.init_schema(self.conn)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
            len(ROWS))


class Revenue(Base):
    def test_full_month_includes_both_boundary_days(self):
        self.assertEqual(
            reports.revenue_between(self.conn, "2026-05-01", "2026-05-31"),
            60_000)

    def test_single_day_range_is_inclusive(self):
        self.assertEqual(
            reports.revenue_between(self.conn, "2026-05-31", "2026-05-31"),
            30_000)

    def test_range_spanning_a_month_boundary(self):
        self.assertEqual(
            reports.revenue_between(self.conn, "2026-04-30", "2026-05-01"),
            30_000)

    def test_currency_is_respected(self):
        self.assertEqual(
            reports.revenue_between(self.conn, "2026-05-01", "2026-05-31",
                                    currency="EUR"), 40_000)

    def test_empty_range_is_zero(self):
        self.assertEqual(
            reports.revenue_between(self.conn, "2026-07-01", "2026-07-31"), 0)


class TopCustomers(Base):
    def test_first_page_is_page_one(self):
        self.assertEqual(
            reports.top_customers(self.conn, page=1, page_size=2),
            [("ann", 40_000), ("bob", 40_000)])

    def test_second_page_continues(self):
        self.assertEqual(
            reports.top_customers(self.conn, page=2, page_size=2),
            [("dee", 5_000)])

    def test_page_past_the_end_is_empty(self):
        self.assertEqual(
            reports.top_customers(self.conn, page=3, page_size=2), [])

    def test_ties_break_on_name_ascending(self):
        self.assertEqual(
            reports.top_customers(self.conn, page=1, page_size=10),
            [("ann", 40_000), ("bob", 40_000), ("dee", 5_000)])

    def test_defaults_return_everything(self):
        self.assertEqual(
            reports.top_customers(self.conn),
            [("ann", 40_000), ("bob", 40_000), ("dee", 5_000)])

    def test_currency_is_respected(self):
        self.assertEqual(
            reports.top_customers(self.conn, currency="EUR"),
            [("cid", 40_000)])


class Config(unittest.TestCase):
    def setUp(self):
        self.saved = os.environ.get("SVC_ENV")
        self.addCleanup(self.restore)

    def restore(self):
        if self.saved is None:
            os.environ.pop("SVC_ENV", None)
        else:
            os.environ["SVC_ENV"] = self.saved

    def test_unset_env_defaults_to_dev(self):
        os.environ.pop("SVC_ENV", None)
        cfg = config.load()
        self.assertEqual(cfg["env"], "dev")
        self.assertTrue(cfg["db_path"].endswith("data/service.db"),
                        f"dev db_path was {cfg['db_path']!r}")
        self.assertEqual(cfg["page_size"], 25)

    def test_prod_still_points_at_the_managed_volume(self):
        os.environ["SVC_ENV"] = "prod"
        cfg = config.load()
        self.assertEqual(cfg["env"], "prod")
        self.assertIn("/var/lib", cfg["db_path"])


class EndToEnd(unittest.TestCase):
    def test_run_check_passes(self):
        import subprocess
        import sys
        r = subprocess.run([sys.executable, "run_check.py"],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0,
                         f"run_check.py failed:\n{r.stdout}\n{r.stderr}")


if __name__ == "__main__":
    unittest.main()
