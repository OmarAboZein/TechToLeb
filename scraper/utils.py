"""
Shared helpers used by all scrapers.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from db.database import get_connection


def get_or_create_store(name: str, url: str) -> int:
    """
    Look up a store by name. If it doesn't exist, insert it.
    Returns the store's id.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM stores WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row:
        store_id = row["id"]
    else:
        cursor.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (name, url))
        conn.commit()
        store_id = cursor.lastrowid

    conn.close()
    return store_id


def save_product(name: str, description: str, image_url: str, category: str,
                 price: float, original_price: float, product_url: str,
                 store_id: int) -> None:
    """
    Insert a product and its price into the database.
    If a product with the same name already exists, we still add a new price row
    (so we can compare prices across stores later).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Check if product already exists
    cursor.execute("SELECT id FROM products WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row:
        product_id = row["id"]
    else:
        cursor.execute(
            "INSERT INTO products (name, description, image_url, category) VALUES (?, ?, ?, ?)",
            (name, description, image_url, category)
        )
        conn.commit()
        product_id = cursor.lastrowid

    # Always insert a fresh price row
    cursor.execute(
        """INSERT INTO prices (product_id, store_id, price, original_price, product_url)
           VALUES (?, ?, ?, ?, ?)""",
        (product_id, store_id, price, original_price, product_url)
    )

    conn.commit()
    conn.close()
