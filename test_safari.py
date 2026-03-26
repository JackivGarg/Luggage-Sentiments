"""Quick single-brand test: runs scraper logic for Safari only."""
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

COOKIES_FILE = "cookies.json"
OUTPUT_CSV   = "data/raw_data.csv"
MAX_PRODUCTS = 10
MAX_REVIEWS  = 60
DELAY_RANGE  = (3, 6)
USER_AGENT   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
HEADERS      = ["brand","product_title","price","mrp","discount_pct","rating","review_count","reviewer_name","reviewer_rating","review_text"]

BRANDS = [
    {"brand": "Safari", "url": "https://www.amazon.in/s?k=safari+trolley+bag"},
]

def load_cookies(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    cleaned = []
    for c in raw:
        entry = {}
        for key in ("name","value","domain","path","httpOnly","secure"):
            if key in c and c[key] is not None:
                entry[key] = c[key]
        if c.get("expirationDate") is not None:
            entry["expires"] = int(c["expirationDate"])
        ss = (c.get("sameSite") or "").lower()
        entry["sameSite"] = "None" if ss in ("no_restriction","") else ss.capitalize()
        cleaned.append(entry)
    return cleaned

async def delay():
    await asyncio.sleep(random.uniform(*DELAY_RANGE))

def is_blocked(title):
    return any(w in title.lower() for w in ["sign-in","signin","robot check","captcha"])

class CSVWriter:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._file = open(path, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=HEADERS)
        self._writer.writeheader()
        self._file.flush()
        self.count = 0
    def write(self, row):
        self._writer.writerow({k: row.get(k, "") for k in HEADERS})
        self._file.flush()
        self.count += 1
    def close(self):
        self._file.close()

async def get_product_links(page, url, brand):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await delay()
        if is_blocked(await page.title()):
            print(f"  [BLOCKED]"); return []
        links = await page.eval_on_selector_all("a.a-link-normal.s-no-outline", "els => els.map(e => e.href)")
        seen, unique = set(), []
        for l in links:
            if "/dp/" in l:
                m = re.search(r"/dp/([A-Z0-9]{10})", l)
                if m and m.group(1) not in seen:
                    seen.add(m.group(1))
                    unique.append(f"https://www.amazon.in/dp/{m.group(1)}")
        return unique[:MAX_PRODUCTS]
    except PlaywrightTimeoutError:
        return []

async def scrape_product(page, url):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await delay()
        if is_blocked(await page.title()): return None
        async def txt(sel):
            el = await page.query_selector(sel)
            return (await el.inner_text()).strip() if el else ""
        title = await txt("#productTitle")
        price = None
        for sel in ["span.a-price-whole", ".priceToPay span.a-price-whole"]:
            raw = await txt(sel)
            if raw: price = float(re.sub(r"[^\d.]","",raw) or 0) or None; break
        mrp = None
        for sel in ["span.a-price.a-text-price span.a-offscreen", ".basisPrice span.a-offscreen"]:
            raw = await txt(sel)
            if raw: mrp = float(re.sub(r"[^\d.]","",raw) or 0) or None; break
        discount = round((mrp-price)/mrp*100,1) if mrp and price and mrp > price else None
        rating = None
        raw = await txt("span[data-hook='rating-out-of-text']") or await txt("i.a-icon-star span.a-icon-alt")
        if raw:
            m = re.search(r"([\d.]+)", raw)
            if m: rating = float(m.group(1))
        review_count = None
        raw = await txt("span#acrCustomerReviewText") or await txt("[data-hook='total-review-count']")
        if raw: review_count = int(re.sub(r"[^\d]","",raw) or 0) or None
        m = re.search(r"/dp/([A-Z0-9]{10})", url)
        reviews_url = f"https://www.amazon.in/product-reviews/{m.group(1)}/?pageSize=10&sortBy=recent" if m else None
        return {"product_title": title, "price": price, "mrp": mrp, "discount_pct": discount,
                "rating": rating, "review_count": review_count, "reviews_url": reviews_url}
    except PlaywrightTimeoutError:
        return None

async def scrape_reviews(page, reviews_url, base_row, writer):
    collected, url = 0, reviews_url
    while collected < MAX_REVIEWS and url:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await delay()
            if is_blocked(await page.title()): break

            # Wait up to 6s for any review cards to appear
            for sel in ["li.review", "div[data-hook='review']"]:
                try:
                    await page.wait_for_selector(sel, timeout=6000)
                    break
                except PlaywrightTimeoutError:
                    continue

            cards = await page.query_selector_all("li.review") or await page.query_selector_all("div[data-hook='review']")
            if not cards:
                print("  [info] No review cards found on this page.")
                break

            for card in cards:
                if collected >= MAX_REVIEWS: break
                name_el = await card.query_selector("span.a-profile-name")
                star_el = await card.query_selector("i[data-hook='review-star-rating'] span.a-icon-alt, i[data-hook='cmps-review-star-rating'] span.a-icon-alt")
                body_el = await card.query_selector("span[data-hook='review-body'] span")
                reviewer_name = (await name_el.inner_text()).strip() if name_el else "Anonymous"
                reviewer_rating = None
                if star_el:
                    m = re.search(r"([\d.]+)", await star_el.inner_text())
                    if m: reviewer_rating = float(m.group(1))
                review_text = (await body_el.inner_text()).strip() if body_el else ""
                if review_text:
                    writer.write({**base_row, "reviewer_name": reviewer_name,
                                  "reviewer_rating": reviewer_rating, "review_text": review_text})
                    collected += 1

            next_btn = await page.query_selector("li.a-last a")
            url = await next_btn.get_attribute("href") if next_btn else None
            if url and not url.startswith("http"):
                url = "https://www.amazon.in" + url
        except PlaywrightTimeoutError:
            break
    return collected

async def main():
    cookies = load_cookies(COOKIES_FILE)
    print(f"[auth]  Loaded {len(cookies)} cookies")
    writer = CSVWriter(OUTPUT_CSV)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        ctx = await browser.new_context(user_agent=USER_AGENT, locale="en-IN")
        await ctx.add_cookies(cookies)
        page = await ctx.new_page()

        print("[init] Warming up browser on amazon.in ...")
        await page.goto("https://www.amazon.in", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        title = await page.title()
        if is_blocked(title):
            print("[ERROR] Cookies expired — please re-export from Cookie-Editor")
            await browser.close(); writer.close(); return

        print(f"[auth]  Logged in — {title[:60]}")

        for brand_info in BRANDS:
            brand, search_url = brand_info["brand"], brand_info["url"]
            print(f"\n{'='*60}")
            print(f"[brand] {brand}")
            product_urls = await get_product_links(page, search_url, brand)
            print(f"  Found {len(product_urls)} products")

            for i, prod_url in enumerate(product_urls, 1):
                print(f"\n  [{i}/{len(product_urls)}] {prod_url}")
                info = await scrape_product(page, prod_url)
                if not info:
                    print("  [skip] Could not scrape product info"); continue

                # Skip products that don't belong to this brand
                if brand.lower() not in info["product_title"].lower():
                    print(f"  [skip] Not a {brand} product: {info['product_title'][:50]}"); continue

                print(f"  Title : {info['product_title'][:60]}")
                print(f"  Price : {info['price']} | MRP: {info['mrp']} | Reviews: {info['review_count']}")
                base_row = {"brand": brand, "product_title": info["product_title"],
                            "price": info["price"], "mrp": info["mrp"],
                            "discount_pct": info["discount_pct"], "rating": info["rating"],
                            "review_count": info["review_count"]}
                if info["reviews_url"]:
                    n = await scrape_reviews(page, info["reviews_url"], base_row, writer)
                    print(f"  Saved {n} reviews  (total: {writer.count})")
                else:
                    writer.write(base_row)

        await browser.close()

    writer.close()
    print(f"\n[done] Safari test finished. Total reviews saved: {writer.count}")

if __name__ == "__main__":
    asyncio.run(main())
