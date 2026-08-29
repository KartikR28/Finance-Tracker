from werkzeug.security import generate_password_hash, check_password_hash

from db import get_conn

def init_auth_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

def create_user(username, password):
    username = username.strip().lower()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )

def verify_user(username, password):
    username = username.strip().lower()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None or not check_password_hash(row["password_hash"], password):
        return None
    return row
