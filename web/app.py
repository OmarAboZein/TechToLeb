"""
Flask web app for TechToLeb.
Reads products from the SQLite database and displays them.

Run with:
    python web/app.py
Then open http://127.0.0.1:5000 in your browser.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request
from db.database import get_connection

app = Flask(__name__)


def get_products(search: str = "") -> list:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            p.name,
            p.description,
            p.image_url,
            p.category,
            pr.price,
            pr.original_price,
            pr.product_url,
            s.name AS store_name
        FROM products p
        JOIN prices pr ON p.id = pr.product_id
        JOIN stores s ON pr.store_id = s.id
    """

    if search:
        query += " WHERE p.name LIKE ?"
        cursor.execute(query + " ORDER BY pr.price ASC", (f"%{search}%",))
    else:
        cursor.execute(query + " ORDER BY pr.scraped_at DESC")

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    products = get_products(search)
    return render_template("index.html", products=products, search=search)


if __name__ == "__main__":
    app.run(debug=True)
