"""Persistence layer. BUG 2: the schema is missing the `currency` column
that reports.py needs; BUG 3: CREATE TABLE IF NOT EXISTS will not alter a
database file already created with the old schema (see seed.py)."""
import sqlite3
import os

from .config import DB_PATH


def connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # BUG 2: missing currency column in the schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            account TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    return conn
