"""Persistence layer. Fixed: currency column present; stale dbs migrated."""
import sqlite3
import os

from .config import DB_PATH


def connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            account TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            at TIMESTAMP NOT NULL,
            currency TEXT NOT NULL DEFAULT "USD"
        )
    """)
    # FIX 3: migrate a stale schema in place (ALTER, never drop live data)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(transactions)")]
    if "currency" not in cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN currency TEXT NOT NULL DEFAULT 'USD'")
    conn.commit()
    return conn
