#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test: scroll to load ALL hotels, no price filter"""
import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--lang=zh-CN')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])

chromedriver_path = os.path.join(SCRIPT_DIR, 'chromedriver.exe')
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    url = ("https://www.agoda.cn/search?city=5818&checkin=2026-06-05"
           "&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY")
    print(f"Loading...")
    driver.get(url)
    time.sleep(6)

    # Get initial hotel count
    count = driver.execute_script("return document.querySelectorAll('[class*=\"PropertyCard\"]').length")
    print(f"Initial PropertyCards: {count}")

    # Scroll aggressively
    max_scrolls = 200
    prev_count = 0
    same_count_rounds = 0
    total_count = count

    for s in range(max_scrolls):
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(2.5)

        count = driver.execute_script("return document.querySelectorAll('[class*=\"PropertyCard\"]').length")
        if count != prev_count:
            if count - prev_count > 0:
                print(f"  Scroll {s+1}: {count} cards (+{count-prev_count})")
            prev_count = count
            same_count_rounds = 0
        else:
            same_count_rounds += 1
            if same_count_rounds >= 5:
                print(f"  Stable at {count} for 5 rounds")
                break

    print(f"\n=== After scrolling: {count} cards ===")

    # Extract ALL hotels
    hotels_json = driver.execute_script("""
    const cards = document.querySelectorAll('[class*="PropertyCard"]');
    const results = [];
    const seen = new Set();

    cards.forEach(card => {
        const text = card.textContent;
        const html = card.innerHTML;

        // Check if it's a real hotel card (has expected child structure)
        const hasName = card.querySelector('[class*=hotelName]');
        const hasLink = card.querySelector('a[href*="hotel"]');
        if (!hasName && !hasLink) return;

        // Hotel name
        const nameEl = card.querySelector('[class*=hotelName]');
        let name = '';
        if (nameEl) name = nameEl.textContent.trim();
        if (!name) {
            const m = html.match(/alt="([^"]*?)"/);
            if (m) name = m[1];
        }
        if (!name || name.length < 2) return;

        // Deduplicate by name within this batch
        const key = name.toLowerCase().trim();
        if (seen.has(key)) return;
        seen.add(key);

        // Rating
        let rating = null;
        const ratingEl = card.querySelector('[class*=reviewScore]');
        if (ratingEl) {
            const rm = ratingEl.textContent.trim().match(/(\\d+\\.?\\d*)/);
            if (rm) rating = parseFloat(rm[1]);
        }

        // Review count
        let reviewCount = 0;
        const text_clean = text.replace(/,/g, '');
        const reviewMatch = text_clean.match(/(\\d+)\\s*[条则]\\s*(?:评|点|评论)/);
        if (reviewMatch) reviewCount = parseInt(reviewMatch[1]);

        // Price
        let price = null;
        const priceMatch = text.match(/RMB\\s*(\\d{1,3}(?:,\\d{3})*|\\d{2,5})/);
        if (priceMatch) {
            price = parseInt(priceMatch[1].replace(/,/g, ''));
        }

        // Star rating
        let starRating = null;
        const starText = text.match(/(\\d+)\\s*星/);
        if (starText) starRating = parseInt(starText[1]);

        // Hotel ID
        let hotelId = '';
        const link = card.querySelector('a[href*="hotel"]');
        if (link) {
            const href = link.getAttribute('href') || '';
            const idMatch = href.match(/hotel\\/([^\\/?#]+)/);
            if (idMatch) hotelId = idMatch[1];
        }
        if (!hotelId) hotelId = 'dom_' + name.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);

        results.push({
            '酒店ID': hotelId,
            '酒店名称': name,
            'Agoda评分': rating,
            '评价数': reviewCount,
            '星级': starRating,
            '最低价(CNY)': price,
        });
    });
    return JSON.stringify(results);
    """)

    hotels = json.loads(hotels_json) if hotels_json else []
    print(f"\nUnique hotels extracted: {len(hotels)}")

    if hotels:
        for h in hotels[:5]:
            print(f"  {h['酒店名称'][:30]:30s} | {h['Agoda评分']} | {h['最低价(CNY)']} | {h['酒店ID'][:25]}")

        prices = [h['最低价(CNY)'] for h in hotels if h['最低价(CNY)']]
        ratings = [h['Agoda评分'] for h in hotels if h['Agoda评分']]
        if prices:
            print(f"Price range: {min(prices)} - {max(prices)}, avg={sum(prices)/len(prices):.0f}")
        if ratings:
            print(f"Rating range: {min(ratings):.1f} - {max(ratings):.1f}, avg={sum(ratings)/len(ratings):.1f}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("Done")
