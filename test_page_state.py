#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check page state in detail"""
import sys, os, time, json, re
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

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
    time.sleep(10)

    # Page title
    print(f"Title: '{driver.title}'")
    print(f"URL: {driver.current_url}")

    # Check body text for key markers
    body = driver.find_element(By.TAG_NAME, 'body').text
    print(f"\nBody text length: {len(body)}")

    # Search for hotel-related content
    for term in ['住宿', '酒店', '点评', '评分', 'RMB', 'PropertyCard', 'hotel']:
        count = body.count(term)
        print(f"  '{term}' count: {count}")

    # Check for loading spinners
    loading = driver.execute_script("""
    const spinners = document.querySelectorAll('[class*=loading], [class*=spinner], [class*=skeleton], [class*=Loader], [class*=loader]');
    return spinners.length;
    """)
    print(f"Loading/spinner elements: {loading}")

    # Check all class names containing PropertyCard
    pc_details = driver.execute_script("""
    const els = document.querySelectorAll('[class*="PropertyCard"]');
    const result = [];
    els.forEach((el, i) => {
        if (i > 60) return;
        let cls = '';
        if (typeof el.className === 'string') cls = el.className;
        const tag = el.tagName.toLowerCase();
        const hasH3 = !!el.querySelector('h3');
        const hasHotelName = !!el.querySelector('[class*=hotelName]');
        const hasLink = !!el.querySelector('a[href*="hotel"]');
        const textLen = (el.textContent || '').trim().length;
        result.push({
            idx: i, tag, class: cls.substring(0, 120),
            hasH3, hasHotelName, hasLink, textLen
        });
    });
    return result;
    """)
    print(f"\nPropertyCard elements ({len(pc_details)}):")
    for p in pc_details[:30]:
        short_class = p['class'][:80]
        flags = ''
        if p['hasH3']: flags += ' [H3]'
        if p['hasHotelName']: flags += ' [HN]'
        if p['hasLink']: flags += ' [L]'
        print(f"  #{p['idx']} <{p['tag']}> .{short_class}{flags} text={p['textLen']}")

    # Check if there's a hotel count
    hotel_count_match = re.search(r'(\d+)\s*家住宿', body)
    if hotel_count_match:
        print(f"\nHotel count on page: {hotel_count_match.group(1)}")

    # Get body text sample
    print(f"\nBody text sample (first 1000 chars):")
    print(body[:1000])

except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()
finally:
    driver.quit()
