"""Database access and schema."""
import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY,
    customer    TEXT    NOT NULL,
    amount      INTEGER NOT NULL,
    currency    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS orders_created_at ON orders (created_at);
"""


def connect(path):
    """Open a connection to the sqlite database at `path`."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn):
    """Create the schema if it does not already exist."""
    conn.executescript(SCHEMA)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(orders)")}
    if "currency" not in columns:
        conn.execute(
            "ALTER TABLE orders ADD COLUMN currency TEXT NOT NULL DEFAULT 'USD'")
    conn.commit()
    return conn
