"""
db.py - the single place where the app opens a connection to flights.db.

Every other part of the program calls get_connection() instead of calling
sqlite3.connect() directly. That way the connection settings below
(foreign keys on, rows readable by column name) can never be forgotten.

Run this file on its own to check the connection works:
    python3 db.py
"""

import sqlite3
from pathlib import Path

# flights.db lives in the same folder as this file, wherever the app is run from
DB_PATH = Path(__file__).resolve().parent / "flights.db"


def get_connection():
    """Open flights.db with the app's standard settings and return the connection."""
    # sqlite3.connect() silently creates a new, EMPTY database if the file is
    # missing. Checking first gives a clear message instead of confusing
    # "no such table" errors later.
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"{DB_PATH.name} not found. Run 'python3 setup_db.py' first to create it."
        )

    conn = sqlite3.connect(DB_PATH)

    # SQLite does NOT enforce foreign keys unless each connection switches
    # them on. Without this, the app could e.g. add a flight to an airport
    # that doesn't exist, or delete an airport that flights still use.
    conn.execute("PRAGMA foreign_keys = ON")

    # By default each row comes back as a plain tuple, read by position
    # (row[0], row[1]...). sqlite3.Row lets us read by column name instead
    # (row["flight_number"]), which is clearer and doesn't break if the
    # column order in a SELECT changes.
    conn.row_factory = sqlite3.Row

    return conn


# This block only runs when the file is run directly (python3 db.py),
# not when another file does "from db import get_connection".
if __name__ == "__main__":
    conn = get_connection()
    try:
        fk_status = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        print("Foreign keys on:", "yes" if fk_status == 1 else "NO")

        row = conn.execute(
            "SELECT flight_number, status FROM Flight WHERE flight_id = ?", (1,)
        ).fetchone()
        print("Flight 1:", row["flight_number"], "-", row["status"])
    finally:
        conn.close()
