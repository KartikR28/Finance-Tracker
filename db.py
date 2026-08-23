import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finance.db")

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                t_type TEXT,
                category TEXT,
                amount REAL,
                date TEXT,
                note TEXT
            )
        """)

def insert_transaction(t_type, category, amount, date, note=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO transactions (t_type, category, amount, date, note) VALUES (?, ?, ?, ?, ?)",
            (t_type, category, amount, date, note),
        )

def fetch_all():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM transactions ORDER BY date DESC").fetchall()

def fetch_one(transaction_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()

def update_transaction(transaction_id, t_type, category, amount, date, note=""):
    with get_conn() as conn:
        conn.execute(
            "UPDATE transactions SET t_type = ?, category = ?, amount = ?, date = ?, note = ? WHERE id = ?",
            (t_type, category, amount, date, note, transaction_id),
        )

def delete_transaction(transaction_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))

def get_summary():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT t_type, SUM(amount) AS total FROM transactions GROUP BY t_type"
        ).fetchall()
        return {row["t_type"]: row["total"] for row in rows}

