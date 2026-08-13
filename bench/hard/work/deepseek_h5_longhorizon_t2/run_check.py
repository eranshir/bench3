"""End-to-end check for the settlement reports.

This is the check that runs before a release. It must pass on a developer
machine, against the local dev database that seed.py creates under ./data.

Run: python3 run_check.py
"""
import seed
from svc import config, db, reports

# Agreed with finance. March 2026, USD, both end days inclusive.
EXPECTED_MARCH_USD = 320_000
EXPECTED_PAGE_1 = [("acme", 90_000), ("gamma", 90_000), ("beta", 75_000)]
EXPECTED_PAGE_2 = [("theta", 65_000), ("delta", 10_000), ("zeta", 5_000)]


def main():
    seed.main()
    cfg = config.load()
    conn = db.connect(cfg["db_path"])

    failures = []

    march = reports.revenue_between(conn, "2026-03-01", "2026-03-31")
    if march != EXPECTED_MARCH_USD:
        failures.append(f"march revenue: got {march}, "
                        f"want {EXPECTED_MARCH_USD}")

    page1 = reports.top_customers(conn, page=1, page_size=3)
    if page1 != EXPECTED_PAGE_1:
        failures.append(f"page 1: got {page1}, want {EXPECTED_PAGE_1}")

    page2 = reports.top_customers(conn, page=2, page_size=3)
    if page2 != EXPECTED_PAGE_2:
        failures.append(f"page 2: got {page2}, want {EXPECTED_PAGE_2}")

    if failures:
        for f in failures:
            print(f"FAIL {f}")
        raise SystemExit(1)
    print("OK - all checks passed")


if __name__ == "__main__":
    main()
