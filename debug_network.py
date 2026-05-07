#!/usr/bin/env python3
"""Capture the actual GraphQL request Agoda makes"""
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
opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

chromedriver = os.path.join(BASE, "chromedriver.exe")
driver = webdriver.Chrome(service=Service(chromedriver), options=opts)

url = (f"https://www.agoda.cn/search?city=16958"
       f"&checkIn={CHECKIN}&checkOut={CHECKOUT}"
       f"&rooms=1&adults=2&currency=CNY")
print(f"Loading: {url}")
driver.get(url)
time.sleep(12)

# Get performance logs and find graphql requests
logs = driver.get_log("performance")
print(f"\nPerformance log entries: {len(logs)}")

graphql_requests = []
for entry in logs:
    try:
        msg = json.loads(entry["message"])
        if "graphql" in str(msg).lower():
            graphql_requests.append(msg)
    except:
        pass

print(f"GraphQL-related entries: {len(graphql_requests)}")

# Extract actual request bodies from network events
request_bodies = {}
for entry in logs:
    try:
        msg = json.loads(entry["message"])
        params = msg.get("message", {}).get("params", {})

        # Request sent
        if params.get("type") == "Network" and params.get("request"):
            req = params["request"]
            url = req.get("url", "")
            if "graphql" in url.lower():
                request_id = params.get("requestId")
                post_data = req.get("postData")
                if post_data:
                    try:
                        request_bodies[request_id] = json.loads(post_data)
                    except:
                        request_bodies[request_id] = post_data

        # Response received - get response body
        if params.get("type") == "Network" and "response" in params:
            resp = params["response"]
            if "graphql" in resp.get("url", "").lower():
                rid = params.get("requestId")
                if rid in request_bodies:
                    request_bodies[rid] = {
                        "request": request_bodies[rid],
                        "status": resp.get("status"),
                        "url": resp.get("url")
                    }
    except:
        pass

print(f"\n=== Captured GraphQL requests: {len(request_bodies)} ===")
for rid, data in request_bodies.items():
    print(f"\nRequest ID: {rid}")
    s = json.dumps(data, ensure_ascii=False, indent=2)
    print(s[:3000])

# Also check what's visible on the page
print("\n=== Page state ===")
print(f"Title: {driver.title}")
print(f"URL: {driver.current_url}")

# Check for hotel/PropertyCard elements
cards = driver.find_elements("xpath", "//*[contains(@class,'PropertyCard')]")
print(f"PropertyCards visible: {len(cards)}")

driver.quit()