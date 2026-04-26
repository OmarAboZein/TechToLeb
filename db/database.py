"""
Database setup for TechToLeb.
Uses SQLite — a simple file-based database, no server needed.
The database file lives at data/techtoleb.db and is created automatically.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/techtoleb.db")


def get_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["name"]
    return conn


def init_db():
    """
    Create the tables if they don't exist yet.
    Run this once before scraping.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Stores table — one row per shop (Ayoub, iStyle, Géant, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL UNIQUE,
            url     TEXT NOT NULL
        )
    """)

    # Products table — one row per unique product
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT,
            image_url   TEXT,
            category    TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Prices table — one row per (product, store) pair
    # This way the same product can appear in multiple stores with different prices.
    # We also keep a scraped_at timestamp so we can track price history later.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id      INTEGER NOT NULL REFERENCES products(id),
            store_id        INTEGER NOT NULL REFERENCES stores(id),
            price           REAL,
            original_price  REAL,
            currency        TEXT DEFAULT 'USD',
            product_url     TEXT,
            scraped_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized at:", os.path.abspath(DB_PATH))


if __name__ == "__main__":
    init_db()
