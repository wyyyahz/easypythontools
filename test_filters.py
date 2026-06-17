#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find price filter buttons on the page"""
import sys, os, time, json
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
    time.sleep(8)

    # Find all clickable price filter elements
    filters = driver.execute_script("""
    const result = [];
    // Look for elements containing RMB price ranges
    const all = document.querySelectorAll('span, div, button, a, label');
    const pricePattern = /RMB\\s*\\d+\\s*-\\s*RMB\\s*\\d+|RMB\\s*\\d+\\s*-\\s*\\d+/;
    all.forEach(el => {
        const text = (el.textContent || '').trim();
        if (pricePattern.test(text) && text.length < 40) {
            let cls = '';
            if (typeof el.className === 'string') cls = el.className;
            const tag = el.tagName.toLowerCase();
            const isClickable = el.onclick || el.tagName === 'BUTTON' || el.tagName === 'A' || el.getAttribute('role') === 'button' || el.getAttribute('tabindex');
            result.push({
                tag,
                text: text.substring(0, 40),
                class: cls.substring(0, 80),
                clickable: !!isClickable,
                tabIndex: el.getAttribute('tabindex') || '',
                role: el.getAttribute('role') || '',
                parentTag: el.parentElement ? el.parentElement.tagName.toLowerCase() : ''
            });
        }
    });
    return result;
    """)

    print(f"Found {len(filters)} price filter elements:")
    for f in filters[:30]:
        print(f"  <{f['tag']}> '{f['text']:30s}' clickable={f['clickable']} role={f['role']} parent=<{f['parentTag']}>")

    # Also find the "筛选" (filter) button which opens the filter panel
    print("\n=== Filter panel elements ===")
    filter_btns = driver.execute_script("""
    const result = [];
    const all = document.querySelectorAll('span, div, button, a');
    all.forEach(el => {
        const text = (el.textContent || '').trim();
        if (text === '筛选' || text === 'Filter' || text === '价格' || text === 'Price') {
            let cls = '';
            if (typeof el.className === 'string') cls = el.className;
            result.push({
                tag: el.tagName.toLowerCase(),
                text: text,
                class: cls.substring(0, 100),
                rect: el.getBoundingClientRect(),
                clickable: !!(el.onclick || el.tagName === 'BUTTON' || el.tagName === 'A')
            });
        }
    });
    return result;
    """)
    for f in filter_btns[:10]:
        r = f['rect']
        print(f"  <{f['tag']}> '{f['text']}' | class={f['class'][:60]} | pos=({r['x']:.0f},{r['y']:.0f})x({r['width']:.0f},{r['height']:.0f}) | clickable={f['clickable']}")

    # Check the price budget section
    print("\n=== Budget section ===")
    budget = driver.execute_script("""
    const all = document.querySelectorAll('div, section');
    for (const el of all) {
        const text = (el.textContent || '').trim();
        if (text.includes('设置预算') || text.includes('预算')) {
            let cls = '';
            if (typeof el.className === 'string') cls = el.className;
            return {
                tag: el.tagName.toLowerCase(),
                class: cls.substring(0, 120),
                html: el.outerHTML.substring(0, 2000)
            };
        }
    }
    return 'NOT FOUND';
    """)
    if isinstance(budget, dict):
        print(f"  Tag: <{budget['tag']}> class={budget['class']}")
        print(f"  HTML: {budget['html']}")
    else:
        print(f"  {budget}")

except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()
finally:
    driver.quit()
