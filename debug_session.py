#!/usr/bin/env python3
"""Capture all cookies and storage from a real Agoda browser session"""
import json, os, time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

BASE = os.path.dirname(os.path.abspath(__file__))
CHECKIN = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
CHECKOUT = (datetime.now() + timedelta(days=36)).strftime("%Y-%m-%d")

opts = Options()
opts.binary_location = r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe"
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_argument("--no-sandbox")
opts.add_argument("--window-size=1280,800")
opts.add_argument("--lang=zh-CN")
opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

chromedriver = os.path.join(BASE, "chromedriver.exe")
driver = webdriver.Chrome(service=Service(chromedriver), options=opts)

url = (f"https://www.agoda.cn/search?city=16958"
       f"&checkIn={CHECKIN}&checkOut={CHECKOUT}"
       f"&rooms=1&adults=2&currency=CNY")
print(f"Loading: {url}")
driver.get(url)
time.sleep(10)

cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
print(f"\n=== Cookies ({len(cookies)}) ===")
for k, v in sorted(cookies.items()):
    cv = v[:80] + "..." if len(v) > 80 else v
    print(f"  {k}: {cv}")

# Check if the page has any hotel data
hotel_elements = driver.find_elements("xpath", "//*[contains(@class,'PropertyCard')]")
print(f"\n=== PropertyCard elements found: {len(hotel_elements)} ===")

# Look for hotel name elements in the page
all_h3 = driver.find_elements("tag name", "h3")
print(f"\n=== h3 elements ({len(all_h3)}) ===")
for h3 in all_h3[:10]:
    try:
        print(f"  h3: '{h3.text[:60]}'")
    except:
        pass

# Check page title
print(f"\nTitle: {driver.title}")

# Try to get network logs
try:
    logs = driver.execute_script("return window.performance.getEntries().filter(e => e.name.includes('graphql')).map(e => ({name: e.name, duration: e.duration}))")
    print(f"\nGraphQL requests: {json.dumps(logs, indent=2)[:500]}")
except:
    print("\nNo performance data")

driver.quit()
