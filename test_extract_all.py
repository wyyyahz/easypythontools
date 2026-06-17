#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test extracting all hotels with improved extraction + heavy scrolling"""
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

service = Service(os.path.join(SCRIPT_DIR, 'chromedriver.exe'))
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    url = ("https://www.agoda.cn/search?city=5818&checkin=2026-06-05"
           "&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY")
    driver.get(url)
    time.sleep(6)

    # Scroll aggressively until stable
    print("Scrolling to load all hotels...")
    max_scrolls = 80
    prev_count = 0
    stable = 0

    for s in range(max_scrolls):
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(2)
        count = driver.execute_script("return document.querySelectorAll('[class*=\"PropertyCard__propertyContainer\"]').length")
        if count != prev_count:
            if (count - prev_count) > 0:
                print(f"  Scroll {s+1}: {count} containers (+{count-prev_count})")
            prev_count = count
            stable = 0
        else:
            stable += 1
            if stable >= 5:
                print(f"  Stable at {count}")
                break

    # Extract using correct structure
    print(f"\nExtracting hotels...")
    hotels_json = driver.execute_script("""
    const containers = document.querySelectorAll('[class*="PropertyCard__propertyContainer"]');
    const results = [];
    const seen = new Set();

    containers.forEach(container => {
        const propId = container.getAttribute('data-propertyid') || '';
        if (!propId) return;
        if (seen.has(propId)) return;
        seen.add(propId);

        const text = container.textContent;

        // Name
        let name = '';
        const nameEl = container.querySelector('[class*=hotelName] h3');
        if (nameEl) name = nameEl.textContent.trim();
        if (!name) {
            const alt = container.querySelector('[class*=hotelName]');
            if (alt) name = alt.textContent.trim();
        }
        if (!name || name.length < 2) return;

        // Rating
        let rating = null;
        const ratingEl = container.querySelector('[class*=reviewScoreAndText]');
        if (ratingEl) {
            const m = ratingEl.textContent.trim().match(/(\\d+\\.?\\d*)/);
            if (m) rating = parseFloat(m[1]);
        }

        // Reviews
        let reviewCount = 0;
        const countEl = container.querySelector('[class*=reviewScoreElem]');
        if (countEl) {
            const m = countEl.textContent.match(/(\\d+)/);
            if (m) reviewCount = parseInt(m[1]);
        }

        // Star
        let starRating = null;
        const starText = text.match(/(\\d+)\\s*星/);
        if (starText) starRating = parseInt(starText[1]);

        // Price
        let price = null;
        const footer = container.querySelector('[class*=PropertyCard__footer]');
        const footerText = footer ? footer.textContent : text;
        const priceMatch = footerText.match(/RMB\\s*(\\d{1,3}(?:,\\d{3})*|\\d{2,5})/);
        if (priceMatch) {
            price = parseInt(priceMatch[1].replace(/,/g, ''));
        }

        // Area
        let area = '';
        const areaEl = container.querySelector('[class*=BadgeStyled]');
        if (areaEl) area = areaEl.textContent.trim();

        results.push({
            '酒店ID': propId,
            '酒店名称': name,
            '区域': area,
            'Agoda评分': rating,
            '评价数': reviewCount,
            '星级': starRating,
            '最低价(CNY)': price,
        });
    });
    return JSON.stringify(results);
    """)

    hotels = json.loads(hotels_json) if hotels_json else []
    print(f"\nTotal unique hotels: {len(hotels)}")

    if hotels:
        for h in hotels[:5]:
            print(f"  {h['酒店名称'][:30]:30s} | ID={h['酒店ID']} | {h['Agoda评分']} | ¥{h['最低价(CNY)']} | {h['区域']}")

        prices = [h['最低价(CNY)'] for h in hotels if h['最低价(CNY)']]
        ratings = [h['Agoda评分'] for h in hotels if h['Agoda评分']]
        if prices: print(f"Price: {min(prices)}-{max(prices)} avg={sum(prices)/len(prices):.0f}")
        if ratings: print(f"Rating: {min(ratings):.1f}-{max(ratings):.1f} avg={sum(ratings)/len(ratings):.1f}")

        # Check the total page claim vs our count
    total_text = driver.execute_script("""const m = document.body.textContent.match(/(\\d+)\\s*个住宿/); return m ? parseInt(m[1]) : null; """)
    print(f"Page claims: {total_text} hotels, we got: {len(hotels)}")

except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()
finally:
    driver.quit()
