#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose DOM structure of Agoda search page"""
import sys, os, json, time, re
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
           "&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY"
           "&pf=100&pt=200")
    print(f"Loading: {url}")
    driver.get(url)
    time.sleep(10)

    # Save page source for analysis
    with open(os.path.join(SCRIPT_DIR, 'debug_page.html'), 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("Page source saved to debug_page.html")

    # Take screenshot
    ss_path = os.path.join(SCRIPT_DIR, 'debug_screenshot.png')
    driver.save_screenshot(ss_path)
    print(f"Screenshot saved: {ss_path}")

    # Check for iframes/shadow roots
    iframe_count = driver.execute_script('return document.querySelectorAll("iframe, frame").length')
    print(f"\n=== iFrames: {iframe_count} ===")

    # Page title
    print(f"Title: {driver.title}")

    # Count various elements to understand page structure
    print("\n=== Element counts ===")
    checks = [
        ('div', 'div'),
        ('a[href]', 'all links'),
        ('a[href*="hotel"]', 'hotel links'),
        ('a[href*="property"]', 'property links'),
        ('img', 'images'),
        ('h3', 'h3'),
        ('h2', 'h2'),
        ('h4', 'h4'),
        ('button', 'buttons'),
        ('[data-selenium]', 'data-selenium'),
        ('[class]', 'elements with class'),
    ]
    for sel, label in checks:
        cnt = driver.execute_script(f'return document.querySelectorAll("{sel}").length')
        print(f"  {label}: {cnt}")

    # Dump class names of all top-level children of body (first level)
    print("\n=== Top-level body children classes ===")
    classes = driver.execute_script("""
    const result = [];
    for (let i = 0; i < document.body.children.length; i++) {
        const el = document.body.children[i];
        const tag = el.tagName.toLowerCase();
        let cls = '';
        if (typeof el.className === 'string') cls = el.className;
        else if (el.className && el.className.baseVal) cls = el.className.baseVal;
        const text = (el.textContent || '').trim().substring(0, 60).replace(/\\n/g, ' ');
        result.push(tag + (cls ? '.' + cls.split(/\\s+/).filter(Boolean).join('.') : '') + ' | ' + text);
    }
    return result;
    """)
    for c in classes[:20]:
        print(f"  {c[:120]}")

    # Find the main content area
    print("\n=== Likely container divs (deep class analysis) ===")
    containers = driver.execute_script("""
    function getClasses(el, depth) {
        if (depth > 4) return [];
        const result = [];
        let cls = '';
        if (typeof el.className === 'string') cls = el.className;
        else if (el.className && el.className.baseVal) cls = el.className.baseVal;
        if (cls && cls.length > 5 && cls.length < 200) {
            if (cls.includes('ainer') || cls.includes('ontent') || cls.includes('esult') || cls.includes('ist') || cls.includes('rid') || cls.includes('ection') || cls.includes('ody')) {
                result.push({tag: el.tagName.toLowerCase(), class: cls, depth: depth, childCount: el.children.length, textLen: (el.textContent || '').length});
            }
        }
        for (let i = 0; i < Math.min(el.children.length, 10); i++) {
            result.push(...getClasses(el.children[i], depth + 1));
        }
        return result;
    }
    return getClasses(document.body, 0);
    """)
    for c in containers[:30]:
        print(f"  (d{c['depth']}) <{c['tag']}> .{c['class'][:80]} | children={c['childCount']} | text={c['textLen']}")

    # Check all CSS-classed elements that contain "hotel" or "property" or "card" in text
    print("\n=== Elements containing 'hotel' text ===")
    hotel_els = driver.execute_script("""
    const all = document.querySelectorAll('a, div, span, section');
    const result = [];
    all.forEach(el => {
        const text = (el.textContent || '').trim();
        if (text.length > 3 && text.length < 200 && /hotel/i.test(text)) {
            let cls = '';
            if (typeof el.className === 'string') cls = el.className;
            result.push({tag: el.tagName.toLowerCase(), class: cls.substring(0, 60), text: text.substring(0, 80)});
        }
    });
    return result.slice(0, 20);
    """)
    for h in hotel_els:
        print(f"  <{h['tag']}> .{h['class'][:50]} | {h['text']}")

    # Check for property cards using various approaches
    print("\n=== Longest text-containing divs (likely cards) ===")
    long_divs = driver.execute_script("""
    const divs = document.querySelectorAll('div');
    const items = [];
    divs.forEach(d => {
        const len = (d.textContent || '').trim().length;
        const childCount = d.children.length;
        if (len > 100 && childCount > 3 && childCount < 50) {
            let cls = '';
            if (typeof d.className === 'string') cls = d.className;
            items.push({class: cls.substring(0, 100), len: len, children: childCount});
        }
    });
    items.sort((a, b) => b.len - a.len);
    return items.slice(0, 30);
    """)
    for d in long_divs:
        print(f"  .{d['class'][:80]} | len={d['len']} | children={d['children']}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("\nDone")
