#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug: wait longer and check page state"""
import sys, os, json, time
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

chromedriver_path = os.path.join(SCRIPT_DIR, 'chromedriver.exe')
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    url = ("https://www.agoda.cn/search?city=5818&checkin=2026-06-05"
           "&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY")
    print(f"Loading: {url}")
    driver.get(url)

    # Check state every 2 seconds for 30 seconds
    for i in range(15):
        time.sleep(2)
        title = driver.title
        state = driver.execute_script("return document.readyState")
        card_count = driver.execute_script("""
            // Try multiple selectors
            const selectors = [
                '[class*="PropertyCard"]',
                '[class*="propertyCard"]',
                '[class*="hotelName"]',
                '[data-selenium*="hotel"]',
                'a[href*="/hotel/"]'
            ];
            return selectors.map(s => s + ': ' + document.querySelectorAll(s).length).join(' | ');
        """)
        body_text = driver.find_element(By.TAG_NAME, 'body').text
        body_len = len(body_text)
        # Get body text sample
        sample = body_text[:500].replace('\\n', ' ').replace('\\r', ' ')
        print(f"[{i*2+2}s] readyState={state}, title='{title}', body={body_len}chars")
        print(f"  Selectors: {card_count}")
        if '住宿' in body_text:
            import re
            m = re.search(r'(\d+)\s*家住宿', body_text)
            if m:
                print(f"  Total hotels: {m.group(1)}")
        if card_count and '0' not in card_count.split(': ')[-1]:
            print("  Found cards! Breaking...")
            break

    if card_count:
        final_count = driver.execute_script('return document.querySelectorAll(\'[class*="PropertyCard"]\').length')
        print(f"\nFinal card count: {final_count}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("Done")
