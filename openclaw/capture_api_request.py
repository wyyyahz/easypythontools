#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agoda API 请求拦截 - 获取正确的 price filter 格式
通过 Selenium DevTools 抓取页面上点击价格筛选后的 API 请求体
"""
import json, os, sys, time
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

service = Service(os.path.join(BASE, '..', 'chromedriver.exe'))
options = webdriver.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_argument('--window-size=1920,1080')

# Enable performance logging
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

driver = webdriver.Chrome(service=service, options=options)

try:
    url = ("https://www.agoda.cn/search?city=5818&checkin=2026-06-05"
           "&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY")
    print("打开页面...")
    driver.get(url)
    time.sleep(8)

    print("已加载，查找价格筛选按钮...")

    # Click 价格 (Price) filter to expand price brackets
    price_filter_clicked = False
    for selector in [
        "//span[contains(text(), '价格')]",
        "//div[contains(text(), '价格')]",
        "//*[contains(text(), 'RMB')]",
        "//span[contains(text(), 'RMB')]",
    ]:
        try:
            els = driver.find_elements(By.XPATH, selector)
            for el in els:
                if el.is_displayed():
                    driver.execute_script("arguments[0].click();", el)
                    price_filter_clicked = True
                    print(f"点击了: {el.text[:50]}")
                    time.sleep(2)
                    break
        except:
            continue
        if price_filter_clicked:
            break

    if not price_filter_clicked:
        print("未找到价格筛选按钮，尝试其他方式...")

    # Try clicking a specific price bracket (RMB80 - RMB100)
    print("尝试点击价格段 RMB80 - RMB100...")
    bracket_clicked = False
    for selector in [
        "//span[contains(text(), '80') and contains(text(), '100')]",
        "//*[contains(text(), 'RMB80')]",
        "//*[contains(text(), 'RMB 80')]",
        "//*[contains(text(), '80 -') and contains(text(), '100')]",
    ]:
        try:
            els = driver.find_elements(By.XPATH, selector)
            for el in els:
                if el.is_displayed():
                    driver.execute_script("arguments[0].click();", el)
                    bracket_clicked = True
                    print(f"点击了价格段: {el.text[:50]}")
                    time.sleep(3)
                    break
        except:
            continue
        if bracket_clicked:
            break

    if not bracket_clicked:
        print("未找到价格段按钮，尝试点击所有可见的价格文本...")
        for el in driver.find_elements(By.XPATH, "//*[contains(text(), 'RMB')]"):
            try:
                if el.is_displayed() and 'RMB' in el.text:
                    print(f"尝试点击: {el.text[:60]}")
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(2)
                    break
            except:
                continue

    # Wait more for API calls
    time.sleep(3)

    # Get performance logs
    print("\n获取网络请求日志...")
    logs = driver.get_log('performance')

    graphql_requests = []
    for entry in logs:
        try:
            log = json.loads(entry['message'])
            message = log.get('message', {})
            method = message.get('method', '')
            params = message.get('params', {})

            # Capture request bodies
            if method == 'Network.requestWillBeSent':
                req = params.get('request', {})
                url = req.get('url', '')
                if 'graphql/search' in url:
                    post_data = req.get('postData', '')
                    if post_data:
                        try:
                            body = json.loads(post_data)
                            graphql_requests.append(body)
                            # Check if it has rangeFilters
                            rf = body.get('variables', {}).get('CitySearchRequest', {}).get('searchRequest', {}).get('filterRequest', {}).get('rangeFilters', [])
                            print(f"  [{len(graphql_requests)}] GraphQL请求 到 {url}")
                            if rf:
                                print(f"    rangeFilters: {json.dumps(rf, ensure_ascii=False)[:300]}")
                            else:
                                print(f"    rangeFilters: 空")
                        except:
                            pass

            # Also capture responses to see the filter result
            if method == 'Network.responseReceived':
                resp = params.get('response', {})
                url = resp.get('url', '')
                if 'graphql/search' in url:
                    print(f"  GraphQL响应: {resp.get('status')} ({url[:80]})")

        except:
            continue

    # Save captured requests
    if graphql_requests:
        out_path = os.path.join(BASE, 'captured_requests.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(graphql_requests, f, ensure_ascii=False, indent=2)
        print(f"\n保存了 {len(graphql_requests)} 个请求到 {out_path}")

        # Show all unique rangeFilters formats found
        print("\n=== 发现的 rangeFilters 格式 ===")
        for i, req in enumerate(graphql_requests):
            rf = req.get('variables', {}).get('CitySearchRequest', {}).get('searchRequest', {}).get('filterRequest', {}).get('rangeFilters', [])
            print(f"  请求 {i+1}: {json.dumps(rf, ensure_ascii=False)[:200]}")
    else:
        print("\n未捕获到 GraphQL 请求！")
        # Try to get the page HTML to see what's there
        print("\n页面内容片段:")
        body = driver.find_element(By.TAG_NAME, 'body')
        print(body.text[:2000])

finally:
    driver.quit()
