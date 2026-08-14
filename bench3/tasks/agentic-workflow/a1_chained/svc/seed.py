"""Creates the DEV database with the OLD (stale) schema, then inserts a
row. BUG 3: because this file already exists with the old schema,
`CREATE TABLE IF NOT EXISTS` in db.py will never add the missing column;
the schema has to be repaired explicitly."""
from .config import DB_PATH
from .db import connect


def main():
    conn = connect()
    conn.execute("INSERT INTO transactions (account, amount_cents, at) VALUES (?,?,?)",
                 ("alpha", 1000, "2026-08-01 10:00:00"))
    conn.commit()
    conn.close()
    print("seeded", DB_PATH)


if __name__ == "__main__":
    main()
