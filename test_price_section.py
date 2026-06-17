#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Get price section of hotel card"""
import sys, os, time, json
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
    time.sleep(8)

    result = driver.execute_script("""
    // Try broad selector first
    let allCards = document.querySelectorAll('[class*="PropertyCard__"]');
    if (allCards.length === 0) allCards = document.querySelectorAll('[class*="PropertyCard"]');
    console.log('Total card-like elements:', allCards.length);

    for (const card of allCards) {
        const container = card.closest('[class*=propertyContainer]') || card;
        const nameEl = card.querySelector('[class*=hotelName]') || card.querySelector('h3');
        if (!nameEl) continue;
        const name = nameEl.textContent.trim();
        if (name.length < 2) continue;
        return {
            propId: container.getAttribute('data-propertyid') || '',
            name: name.substring(0, 50),
            html: container.outerHTML
        };
    }
    return 'NOT FOUND: ' + allCards.length + ' card-like elements found';
    """)

    if isinstance(result, dict):
        print(f"PropertyID: {result['propId']}")
        print(f"Name: {result['name']}")
        # Find and print the price/footer section
        html = result['html']
        # Find price - look for RMB and nearby text
        import re
        # Find all numeric price patterns
        prices = re.findall(r'RMB\s*[\d,]+', html)
        print(f"All prices found: {prices}")
        # Find footer section
        footer_start = html.find('PropertyCard__footer')
        if footer_start > 0:
            footer_html = html[footer_start:footer_start+2000]
            print(f"\nFooter section:")
            # Extract text from footer
            footer_text = re.sub(r'<[^>]+>', ' ', footer_html)
            footer_text = re.sub(r'\\s+', ' ', footer_text).strip()
            print(footer_text[:1000])
    else:
        print(result)
finally:
    driver.quit()
