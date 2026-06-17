#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump full HTML of one proper hotel card including review/price section"""
import sys, os, time
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

    # Get full card HTML including footer/price section
    html = driver.execute_script("""
    const cards = document.querySelectorAll('[class*="PropertyCard"]');
    for (const card of cards) {
        if (card.querySelector('[class*=hotelName]')) {
            // Also get the full card container (go up to propertyContainer)
            const container = card.closest('[class*=propertyContainer]') || card;
            return {
                containerHTML: container.outerHTML.substring(0, 8000),
                propertyid: container.getAttribute('data-propertyid') || 'N/A',
                Name: (card.querySelector('[class*=hotelName]') || {}).textContent || 'N/A'
            };
        }
    }
    return 'NOT FOUND';
    """)
    print(f"PropertyID: {html['propertyid']}")
    print(f"Name: {html['Name']}")
    print("HTML:")
    print(html['containerHTML'])

except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()
finally:
    driver.quit()
