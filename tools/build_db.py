"""One-time script: load tickets.csv into a SQLite database."""
import csv
import os
import sqlite3

HERE = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(HERE, "data", "tickets.db")
CSV_PATH = os.path.join(HERE, "data", "tickets.csv")

conn = sqlite3.connect(DB_PATH)
conn.execute("DROP TABLE IF EXISTS tickets")
conn.execute("""
    CREATE TABLE tickets (
        ticket_id     TEXT PRIMARY KEY,
        customer_name TEXT,
        subject       TEXT,
        body          TEXT,
        received_at   TEXT
    )
""")

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    rows = [
        (r["ticket_id"], r["customer_name"], r["subject"], r["body"], r["received_at"])
        for r in csv.DictReader(f)
    ]

conn.executemany("INSERT INTO tickets VALUES (?,?,?,?,?)", rows)
conn.commit()
print(f"Loaded {len(rows)} tickets into {DB_PATH}")