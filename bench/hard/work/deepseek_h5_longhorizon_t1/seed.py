"""Populate the dev database. Run: python3 seed.py"""
from svc import config, db

ORDERS = [
    # id, customer, amount (cents), currency, created_at
    (1,  "acme",    50_000, "USD", "2026-03-01 09:15:00"),
    (2,  "beta",    30_000, "USD", "2026-03-01 18:40:00"),
    (3,  "acme",    25_000, "USD", "2026-03-15 12:00:00"),
    (4,  "gamma",   90_000, "USD", "2026-03-31 23:59:00"),
    (5,  "delta",   10_000, "USD", "2026-04-02 08:00:00"),
    (6,  "beta",    45_000, "USD", "2026-03-31 00:00:01"),
    (7,  "epsilon", 70_000, "EUR", "2026-03-10 11:00:00"),
    (8,  "zeta",     5_000, "USD", "2026-02-28 23:59:59"),
    (9,  "acme",    15_000, "USD", "2026-03-20 07:30:00"),
    (10, "theta",   65_000, "USD", "2026-03-05 16:20:00"),
]


def main():
    cfg = config.load()
    conn = db.connect(cfg["db_path"])
    db.init_schema(conn)
    conn.execute("DELETE FROM orders")
    conn.executemany(
        "INSERT INTO orders (id, customer, amount, currency, created_at) "
        "VALUES (?, ?, ?, ?, ?)", ORDERS)
    conn.commit()
    print(f"seeded {len(ORDERS)} orders into {cfg['db_path']} "
          f"(env={cfg['env']})")


if __name__ == "__main__":
    main()
