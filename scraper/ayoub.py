"""
Scraper for Ayoub Computers (ayoubcomputers.com).
The site runs on BigCommerce. Products are server-side rendered so we can
fetch them with plain HTTP requests — no browser automation needed.

Run this file directly:
    python scraper/ayoub.py
"""

import sys
import os
import time
import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from db.database import init_db
from scraper.utils import get_or_create_store, save_product

BASE_URL = "https://ayoubcomputers.com"
CATALOG_URL = "https://ayoubcomputers.com/computers-tech-devices-latest-tech-solutions-ayoub-computers/"
STORE_NAME = "Ayoub Computers"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def parse_price(text: str) -> float | None:
    """Turn a price string like '$1,299.00' into a float 1299.0."""
    if not text:
        return None
    cleaned = text.strip().replace("$", "").replace(",", "").replace("Now:", "").replace("Was:", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_page(url: str, store_id: int) -> str | None:
    """
    Fetch one page of products, parse each product card, save to DB.
    Returns the URL of the next page, or None if we're on the last page.
    """
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    product_cards = soup.select("li.product")

    if not product_cards:
        print(f"  No product cards found on {url} — the selector may need updating.")
        return None

    for card in product_cards:
        # Product name
        name_tag = card.select_one(".card-title a")
        name = name_tag.get_text(strip=True) if name_tag else "Unknown"

        # Product URL
        product_url = name_tag["href"] if name_tag and name_tag.get("href") else ""
        if product_url and not product_url.startswith("http"):
            product_url = BASE_URL + product_url

        # Current price
        price_tag = card.select_one("[data-product-price-without-tax]")
        price = parse_price(price_tag.get_text() if price_tag else "")

        # Original price (before discount), if on sale
        original_price_tag = card.select_one("[data-product-non-sale-price-without-tax]")
        original_price = parse_price(original_price_tag.get_text() if original_price_tag else "")

        # Product image — site lazy-loads, real URL is in data-srcset
        img_tag = card.select_one("img.card-image")
        image_url = ""
        if img_tag:
            srcset = img_tag.get("data-srcset") or img_tag.get("srcset", "")
            image_url = srcset.split(",")[0].split(" ")[0] if srcset else (img_tag.get("src") or "")

        # Description
        desc_tag = card.select_one(".card-text--summary")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # Category (we'll fill this in more precisely later)
        category = "General"

        save_product(
            name=name,
            description=description,
            image_url=image_url,
            category=category,
            price=price,
            original_price=original_price,
            product_url=product_url,
            store_id=store_id,
        )
        print(f"  Saved: {name[:60]} | ${price}")

    # Find the "Next" pagination link
    next_link = soup.select_one("a[rel='next'], .pagination-item--next a, li.pagination-item--next a")
    if next_link and next_link.get("href"):
        next_url = next_link["href"]
        if not next_url.startswith("http"):
            next_url = BASE_URL + next_url
        return next_url

    return None


def run(max_pages: int = 5):
    """
    Main entry point.
    max_pages: how many pages to scrape (12 products each).
               Set to None to scrape all ~834 pages (takes a while).
    """
    print("Initializing database...")
    init_db()

    store_id = get_or_create_store(STORE_NAME, BASE_URL)
    print(f"Store ID for '{STORE_NAME}': {store_id}")

    current_url = CATALOG_URL
    page_number = 1

    while current_url:
        print(f"\nScraping page {page_number}: {current_url}")
        next_url = scrape_page(current_url, store_id)

        if max_pages and page_number >= max_pages:
            print(f"\nReached max_pages limit ({max_pages}). Stopping.")
            break

        current_url = next_url
        page_number += 1
        time.sleep(1)  # be polite — 1 second between requests

    print("\nDone scraping Ayoub Computers.")


if __name__ == "__main__":
    run(max_pages=5)  # start with 5 pages (60 products) to test
