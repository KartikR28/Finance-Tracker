from datetime import date

from db import get_conn

CATEGORIES = [
    "Tri Color T-Shirt (School)",
    "Shirt Checks",
    "Shirt Sky Blue",
    "White T-Shirt",
    "Shirt Plain White",
    "Salwar",
    "Jacket Navy Blue",
    "Jacket Carbon Black",
    "Half Pant",
    "Divider",
    "Divider Strips",
    "Pant Carbon Black",
    "Gurukul Without Collar",
    "Gurukul With Collar",
]

SIZES = [22, 24, 26, 28, 30, 32, 34, 36, 38, 40]

def init_inventory_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                size INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT,
                UNIQUE(category, size)
            )
        """)

def seed_categories():
    with get_conn() as conn:
        for category in CATEGORIES:
            for size in SIZES:
                conn.execute(
                    "INSERT OR IGNORE INTO inventory (category, size, quantity, updated_at) "
                    "VALUES (?, ?, 0, NULL)",
                    (category, size),
                )

def fetch_inventory():
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM inventory ORDER BY category, size"
        ).fetchall()

def get_stock(category, size):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM inventory WHERE category = ? AND size = ?",
            (category, size),
        ).fetchone()

def update_stock(category, size, quantity):
    with get_conn() as conn:
        conn.execute(
            "UPDATE inventory SET quantity = ?, updated_at = ? WHERE category = ? AND size = ?",
            (quantity, date.today().isoformat(), category, size),
        )
