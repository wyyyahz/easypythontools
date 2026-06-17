#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test clicking price filter buttons and see if results change"""
import sys, os, time, json, re
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    # Get initial results
    def get_hotel_count():
        """Get number of hotel containers and total from page"""
        containers = driver.execute_script("return document.querySelectorAll('[class*=\"PropertyCard__propertyContainer\"]').length")
        body = driver.find_element(By.TAG_NAME, 'body').text
        m = re.search(r'(\d+)\s*个住宿', body)
        total = int(m.group(1)) if m else 0
        return containers, total

    c1, t1 = get_hotel_count()
    print(f"Before filter: {c1} containers, page claims {t1} total")

    # Get the first hotel ID before filtering
    first_before = driver.execute_script("""
    const c = document.querySelector('[class*="PropertyCard__propertyContainer"]');
    return c ? c.getAttribute('data-propertyid') : 'NONE';
    """)
    print(f"First hotel ID: {first_before}")

    # Find and click a price filter button (e.g., RMB80 - RMB100)
    print("\nLooking for price filter buttons...")
    buttons = driver.execute_script("""
    const buttons = document.querySelectorAll('button');
    const result = [];
    buttons.forEach((btn, i) => {
        const text = (btn.textContent || '').trim();
        if (text.includes('RMB') && (text.includes('-') || text.includes('+'))) {
            result.push({idx: i, text: text.substring(0, 40), displayed: btn.offsetParent !== null});
        }
    });
    return result;
    """)
    for b in buttons:
        print(f"  Button #{b['idx']}: '{b['text']}' displayed={b['displayed']}")

    # Click the first specific price range button
    if buttons:
        target_text = buttons[2]['text']  # RMB50 - RMB70 or similar
        print(f"\nClicking: {target_text}")

        # Find button by text and click
        clicked = driver.execute_script("""
        const buttons = document.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.textContent.includes('RMB') && btn.textContent.includes('-')) {
                btn.click();
                return btn.textContent.trim();
            }
        }
        return 'NOT FOUND';
        """)
        print(f"Clicked: {clicked}")

        # Wait for page to update
        time.sleep(8)

        c2, t2 = get_hotel_count()
        first_after = driver.execute_script("""
        const c = document.querySelector('[class*="PropertyCard__propertyContainer"]');
        return c ? c.getAttribute('data-propertyid') : 'NONE';
        """)
        print(f"\nAfter filter: {c2} containers, page claims {t2} total")
        print(f"First hotel ID: {first_after}")

        # Check if results changed
        if first_before != first_after:
            print("SUCCESS: Results changed after clicking filter!")
        elif c1 != c2 or t1 != t2:
            print("PARTIAL: Counts changed but first hotel same")
        else:
            print("NO CHANGE: Filter click had no effect")
            # Body text to verify
            body = driver.find_element(By.TAG_NAME, 'body').text
            print(f"Body sample: {body[:500]}")

    # Try clicking the "筛选" filter button first to open panel
    print("\n\nTrying via filter panel...")
    driver.get(url)  # reset
    time.sleep(8)

    # Click 筛选 button
    filter_btn = driver.find_element(By.XPATH, "//button[contains(text(), '筛选')]")
    filter_btn.click()
    time.sleep(3)
    print("Clicked 筛选 button")

    # Now see if price filter buttons are available in the panel
    panel_btns = driver.execute_script("""
    const btns = document.querySelectorAll('button, a, span, div');
    const result = [];
    btns.forEach((btn, i) => {
        const text = (btn.textContent || '').trim();
        if (text.includes('RMB') && (text.includes('-') || text.includes('+'))) {
            result.push({idx: i, tag: btn.tagName, text: text.substring(0, 40), displayed: btn.offsetParent !== null});
        }
    });
    return result;
    """)
    print(f"Price buttons in panel: {len(panel_btns)}")
    for b in panel_btns[:10]:
        print(f"  <{b['tag']}> '{b['text']}' displayed={b['displayed']}")

except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()
finally:
    driver.quit()
