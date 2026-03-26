"""
scraper.py
----------
Amazon India luggage brand scraper using Playwright.

- Loads login cookies from cookies.json to bypass Amazon's sign-in wall
- Visits each brand's search page, grabs up to 10 product links
- Scrapes product info + up to 60 reviews per product
- Saves each row to CSV immediately so no data is lost on interruption
"""

import asyncio
import csv
import json
import os
import random
import re
import sys
import time
from typing import Any, Dict, List, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ── Config ────────────────────────────────────────────────────────────────────
LINKS_FILE             = "link.txt"
COOKIES_FILE           = "cookies.json"
OUTPUT_CSV             = "data/raw_data.csv"
MAX_PRODUCTS_PER_BRAND = 10
MAX_REVIEWS_PER_PRODUCT = 60
DELAY_RANGE            = (3, 6)   # seconds between requests

HEADERS = [
    "brand", "product_title", "price", "mrp", "discount_pct",
    "rating", "review_count", "reviewer_name", "reviewer_rating", "review_text",
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_links(path: str) -> List[Dict[str, str]]:
    brands = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "|" in line:
                name, url = line.split("|", 1)
                brands.append({"brand": name.strip(), "url": url.strip()})
    return brands


def load_cookies(path: str) -> List[Dict]:
    """Read Cookie-Editor exported JSON and convert to Playwright format."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    cleaned = []
    for c in raw:
        # Drop keys Playwright doesn't understand
        entry: Dict[str, Any] = {}
        for key in ("name", "value", "domain", "path", "httpOnly", "secure"):
            if key in c and c[key] is not None:
                entry[key] = c[key]
        # Convert expirationDate -> expires
        if c.get("expirationDate") is not None:
            entry["expires"] = int(c["expirationDate"])
        # Normalise sameSite
        ss = (c.get("sameSite") or "").lower()
        if ss == "no_restriction":
            entry["sameSite"] = "None"
        elif ss in ("strict", "lax"):
            entry["sameSite"] = ss.capitalize()
        else:
            entry["sameSite"] = "None"   # safe default
        cleaned.append(entry)
    return cleaned


async def delay():
    await asyncio.sleep(random.uniform(*DELAY_RANGE))


def is_blocked(title: str) -> bool:
    blocked_keywords = ["sign-in", "signin", "robot check", "captcha", "authentication"]
    return any(kw in title.lower() for kw in blocked_keywords)


# ── CSV Writer ────────────────────────────────────────────────────────────────

class CSVWriter:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._file = open(path, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=HEADERS)
        self._writer.writeheader()
        self._file.flush()
        self.count = 0

    def write(self, row: Dict[str, Any]):
        self._writer.writerow({k: row.get(k, "") for k in HEADERS})
        self._file.flush()
        self.count += 1

    def close(self):
        self._file.close()


# ── Scraping Functions ────────────────────────────────────────────────────────

async def get_product_links(page, search_url: str, brand: str) -> List[str]:
    """Return up to MAX_PRODUCTS_PER_BRAND product URLs from a search page."""
    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await delay()
        title = await page.title()
        if is_blocked(title):
            print(f"  [BLOCKED] Search page blocked for {brand}")
            return []

        links = await page.eval_on_selector_all(
            "a.a-link-normal.s-no-outline",
            "els => els.map(e => e.href)"
        )
        # Filter to product pages only
        product_links = [
            l for l in links
            if "/dp/" in l and "amazon.in" in l
        ]
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for l in product_links:
            # Normalise to base product URL
            m = re.search(r"/dp/([A-Z0-9]{10})", l)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                unique.append(f"https://www.amazon.in/dp/{m.group(1)}")
        return unique[:MAX_PRODUCTS_PER_BRAND]
    except PlaywrightTimeoutError:
        print(f"  [warn] Search page timed out for {brand}")
        return []


async def scrape_product(page, url: str) -> Optional[Dict]:
    """Scrape title, price, rating, etc. from a product page."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await delay()
        if is_blocked(await page.title()):
            return None

        async def text(sel: str) -> str:
            el = await page.query_selector(sel)
            return (await el.inner_text()).strip() if el else ""

        title = await text("#productTitle") or await text("span#productTitle")

        # Price
        price = None
        for sel in ["span.a-price-whole", ".priceToPay span.a-price-whole"]:
            raw = await text(sel)
            if raw:
                price = float(re.sub(r"[^\d.]", "", raw) or 0) or None
                break

        # MRP
        mrp = None
        for sel in ["span.a-price.a-text-price span.a-offscreen", ".basisPrice span.a-offscreen"]:
            raw = await text(sel)
            if raw:
                mrp = float(re.sub(r"[^\d.]", "", raw) or 0) or None
                break

        discount = round((mrp - price) / mrp * 100, 1) if mrp and price and mrp > price else None

        # Rating
        rating = None
        raw = await text("span[data-hook='rating-out-of-text']") or await text("i.a-icon-star span.a-icon-alt")
        if raw:
            m = re.search(r"([\d.]+)", raw)
            if m:
                rating = float(m.group(1))

        # Review count
        review_count = None
        raw = await text("span#acrCustomerReviewText") or await text("[data-hook='total-review-count']")
        if raw:
            review_count = int(re.sub(r"[^\d]", "", raw) or 0) or None

        # Build reviews URL from ASIN
        m = re.search(r"/dp/([A-Z0-9]{10})", url)
        reviews_url = (
            f"https://www.amazon.in/product-reviews/{m.group(1)}/?pageSize=10&sortBy=recent"
            if m else None
        )

        return {
            "product_title": title,
            "price": price,
            "mrp": mrp,
            "discount_pct": discount,
            "rating": rating,
            "review_count": review_count,
            "reviews_url": reviews_url,
        }

    except PlaywrightTimeoutError:
        print(f"  [warn] Product page timed out: {url}")
        return None


async def scrape_reviews(page, reviews_url: str, base_row: Dict, writer: CSVWriter) -> int:
    """Paginate through reviews and write each to CSV. Returns count scraped."""
    collected = 0
    url = reviews_url

    while collected < MAX_REVIEWS_PER_PRODUCT and url:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await delay()

            if is_blocked(await page.title()):
                print("  [BLOCKED] Reviews page is behind sign-in.")
                break

            # Wait up to 6s for reviews to appear
            try:
                await page.wait_for_selector("li.review, div[data-hook='review']", state="attached", timeout=6000)
            except PlaywrightTimeoutError:
                pass

            # Try both possible selectors (logged-in uses li.review)
            cards = await page.query_selector_all("li.review")
            if not cards:
                cards = await page.query_selector_all("div[data-hook='review']")
            if not cards:
                print("  [info] No review cards found on this page.")
                break

            for card in cards:
                if collected >= MAX_REVIEWS_PER_PRODUCT:
                    break

                name_el  = await card.query_selector("span.a-profile-name")
                star_el  = await card.query_selector("i[data-hook='review-star-rating'] span.a-icon-alt,"
                                                       "i[data-hook='cmps-review-star-rating'] span.a-icon-alt")
                body_el  = await card.query_selector("span[data-hook='review-body'] span")

                reviewer_name   = (await name_el.inner_text()).strip() if name_el else "Anonymous"
                reviewer_rating = None
                if star_el:
                    m = re.search(r"([\d.]+)", await star_el.inner_text())
                    if m:
                        reviewer_rating = float(m.group(1))
                review_text = (await body_el.inner_text()).strip() if body_el else ""

                if review_text:
                    writer.write({**base_row, "reviewer_name": reviewer_name,
                                  "reviewer_rating": reviewer_rating, "review_text": review_text})
                    collected += 1

            # Next page
            next_btn = await page.query_selector("li.a-last a")
            url = await next_btn.get_attribute("href") if next_btn else None
            if url and not url.startswith("http"):
                url = "https://www.amazon.in" + url

        except PlaywrightTimeoutError:
            print("  [warn] Reviews page timed out")
            break

    return collected


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    brands = load_links(LINKS_FILE)
    print(f"[links] Loaded {len(brands)} brand(s) from {LINKS_FILE}")

    cookies = load_cookies(COOKIES_FILE)
    print(f"[auth]  Loaded {len(cookies)} cookies from {COOKIES_FILE}")

    writer = CSVWriter(OUTPUT_CSV)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        ctx = await browser.new_context(user_agent=USER_AGENT, locale="en-IN")
        await ctx.add_cookies(cookies)
        page = await ctx.new_page()

        # Warm-up: go to amazon.in first and wait 3s
        print("[init] Warming up browser on amazon.in ...")
        await page.goto("https://www.amazon.in", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        title = await page.title()
        if is_blocked(title):
            print("[ERROR] Cookies are invalid or expired — Amazon is showing a sign-in page.")
            print("        Please re-export cookies from Cookie-Editor in Chrome and overwrite cookies.json")
            await browser.close()
            writer.close()
            return

        print(f"[auth]  Login confirmed — page title: {title[:60]}")

        for brand_info in brands:
            brand = brand_info["brand"]
            search_url = brand_info["url"]
            print(f"\n{'='*60}")
            print(f"[brand] {brand} — {search_url}")

            product_urls = await get_product_links(page, search_url, brand)
            print(f"  Found {len(product_urls)} products")

            for i, prod_url in enumerate(product_urls, 1):
                print(f"\n  [{i}/{len(product_urls)}] {prod_url}")
                info = await scrape_product(page, prod_url)
                if not info:
                    print("  [skip] Could not scrape product info")
                    continue

                print(f"  Title : {info['product_title'][:60]}")
                print(f"  Price : {info['price']} | MRP: {info['mrp']} | Discount: {info['discount_pct']}%")
                print(f"  Rating: {info['rating']} | Reviews: {info['review_count']}")

                base_row = {
                    "brand": brand,
                    "product_title": info["product_title"],
                    "price": info["price"],
                    "mrp": info["mrp"],
                    "discount_pct": info["discount_pct"],
                    "rating": info["rating"],
                    "review_count": info["review_count"],
                }

                if info["reviews_url"]:
                    n = await scrape_reviews(page, info["reviews_url"], base_row, writer)
                    print(f"  Saved {n} reviews  (total so far: {writer.count})")
                else:
                    # Save product row even with no reviews
                    writer.write(base_row)

        await browser.close()

    writer.close()
    print(f"\n[done] Finished. Total rows saved: {writer.count}")
    print(f"[done] CSV: {OUTPUT_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
