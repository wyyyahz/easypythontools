#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test if price filter (pf/pt) affects the page content"""
import sys, os, time
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
    # Test 1: No filter
    url1 = ("https://www.agoda.cn/search?city=5818&checkin=2026-06-05"
            "&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY")
    print("Test 1: No price filter")
    driver.get(url1)
    time.sleep(8)
    containers1 = driver.execute_script("return document.querySelectorAll('[class*=\"PropertyCard__propertyContainer\"]').length")
    cards1 = driver.execute_script("return document.querySelectorAll('[class*=\"PropertyCard__propertyCard\"]').length")
    body1 = driver.find_element(By.TAG_NAME, 'body').text
    import re
    m1 = re.search(r'(\d+)\s*个住宿', body1)
    print(f"  Containers: {containers1}, Cards: {cards1}, Total text: '{m1.group(0) if m1 else 'N/A'}'")
    name1 = driver.execute_script("""const c = document.querySelector('[class*="PropertyCard__propertyContainer"]'); return c ? c.getAttribute('data-propertyid') + ' | ' + (c.querySelector('[class*=hotelName]')?.textContent?.trim() || 'N/A') : 'NONE'; """)
    print(f"  First hotel: {name1}")

    # Test 2: With price filter pf=80&pt=200
    url2 = ("https://www.agoda.cn/search?city=5818&checkin=2026-06-05"
            "&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY"
            "&pf=80&pt=200")
    print("\nTest 2: pf=80, pt=200")
    driver.get(url2)
    time.sleep(8)
    containers2 = driver.execute_script("return document.querySelectorAll('[class*=\"PropertyCard__propertyContainer\"]').length")
    cards2 = driver.execute_script("return document.querySelectorAll('[class*=\"PropertyCard__propertyCard\"]').length")
    body2 = driver.find_element(By.TAG_NAME, 'body').text
    m2 = re.search(r'(\d+)\s*个住宿', body2)
    print(f"  Containers: {containers2}, Cards: {cards2}, Total text: '{m2.group(0) if m2 else 'N/A'}'")
    name2 = driver.execute_script("""const c = document.querySelector('[class*="PropertyCard__propertyContainer"]'); return c ? c.getAttribute('data-propertyid') + ' | ' + (c.querySelector('[class*=hotelName]')?.textContent?.trim() || 'N/A') : 'NONE'; """)
    print(f"  First hotel: {name2}")
    print(f"  Body preview: {body2[:300]}")

    # Test 3: Wider filter pf=80&pt=500
    url3 = ("https://www.agoda.cn/search?city=5818&checkin=2026-06-05"
            "&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY"
            "&pf=80&pt=500")
    print("\nTest 3: pf=80, pt=500")
    driver.get(url3)
    time.sleep(8)
    containers3 = driver.execute_script("return document.querySelectorAll('[class*=\"PropertyCard__propertyContainer\"]').length")
    body3 = driver.find_element(By.TAG_NAME, 'body').text
    m3 = re.search(r'(\d+)\s*个住宿', body3)
    print(f"  Containers: {containers3}, Total: '{m3.group(0) if m3 else 'N/A'}'")
    name3 = driver.execute_script("""const c = document.querySelector('[class*="PropertyCard__propertyContainer"]'); return c ? c.getAttribute('data-propertyid') + ' | ' + (c.querySelector('[class*=hotelName]')?.textContent?.trim() || 'N/A') : 'NONE'; """)
    print(f"  First hotel: {name3}")

except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()
finally:
    driver.quit()
