"""
setup_db.py - builds (or rebuilds) flights.db from schema.sql and seed.sql.

Run with:  python3 setup_db.py
Safe to run repeatedly: schema.sql drops the tables first, so every run
gives the same clean database with the sample data.
"""

import sqlite3
from pathlib import Path

# Find the .sql files next to this script, wherever it is run from
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "flights.db"
SCHEMA_FILE = BASE_DIR / "schema.sql"
SEED_FILE = BASE_DIR / "seed.sql"


def build_database():
    conn = sqlite3.connect(DB_PATH)
    try:
        # executescript() runs a whole file of SQL statements in one go.
        # schema.sql switches foreign keys on for this connection, so the
        # seed inserts below are checked against the foreign keys.
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        conn.executescript(SEED_FILE.read_text(encoding="utf-8"))
        conn.commit()

        # Quick confirmation that every table was populated
        for table in ("Airport", "Pilot", "Flight", "FlightAssignment"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table:<17} {count:>3} rows")
        print(f"Database created at {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    build_database()
