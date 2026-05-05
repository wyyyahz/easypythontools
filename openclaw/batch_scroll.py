#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch scroll and load all Agoda Wuhan hotels"""
import time
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=== Agoda 武汉酒店全量抓取 ===")
    
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(options=options)
    
    try:
        url = ("https://www.agoda.cn/search?city=5818&checkin=2026-06-05"
               "&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY")
        print(f"打开页面: {url}")
        driver.get(url)
        
        # Wait for initial load
        print("等待初始加载...")
        time.sleep(10)
        
        total_clicks = 0
        max_clicks = 500
        no_change = 0
        last_count = 0
        
        print("开始批量加载...")
        
        while total_clicks < max_clicks:
            try:
                current = len(driver.find_elements(By.CSS_SELECTOR, "a[href*='/hotel/wuhan-cn']"))
            except:
                current = last_count
            
            if current != last_count:
                print(f"  [{total_clicks}] {current} 家酒店 (+{current-last_count})")
                last_count = current
                no_change = 0
            else:
                no_change += 1
            
            if no_change >= 10:
                print(f"  停止: {no_change}次无变化")
                break
            
            # Scroll to bottom
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            except:
                pass
            time.sleep(0.5)
            
            # Find and click the load more button
            found = False
            for selector in [
                "//*[contains(text(), '加载更多住宿')]",
                "//*[contains(text(), '加载更多')]",
                "//button[contains(text(), '加载')]",
                "//div[contains(text(), '加载更多')]"
            ]:
                try:
                    els = driver.find_elements(By.XPATH, selector)
                    for el in els:
                        try:
                            if el.is_displayed():
                                driver.execute_script("arguments[0].click();", el)
                                found = True
                                total_clicks += 1
                                break
                        except:
                            continue
                    if found:
                        break
                except:
                    continue
            
            if not found:
                # Try all buttons
                try:
                    for btn in driver.find_elements(By.TAG_NAME, "button"):
                        try:
                            if btn.is_displayed() and ('加载' in btn.text):
                                driver.execute_script("arguments[0].click();", btn)
                                found = True
                                total_clicks += 1
                                break
                        except:
                            continue
                except:
                    pass
            
            if not found:
                time.sleep(1)
        
        print(f"\n加载完成! 点击{total_clicks}次, {last_count}家酒店")
        
        # Extract data
        print("提取数据...")
        hotels_json = driver.execute_script("""
            const seen = new Set();
            const hotels = [];
            document.querySelectorAll('a[href*="/hotel/wuhan-cn"]').forEach(link => {
                const text = link.textContent.trim();
                if (text.length < 20) return;
                const pm = text.match(/RMB\\s*([0-9,]+)/);
                const rm = text.match(/([0-9]\\.[0-9])/);
                const sm = text.match(/Rating\\s*([0-9]+)\\s*out of/);
                let name = '';
                const lines = text.split('\\n').map(l=>l.trim()).filter(l=>l.length>3);
                for (const l of lines) {
                    if (l.includes('酒店')||l.includes('客栈')||l.includes('民宿')||
                        l.includes('宾馆')||l.includes('公寓')||l.includes('旅馆')||
                        l.includes('RETURN')||l.includes('Luojia')||l.includes('Fashion')) {
                        name = l; break;
                    }
                }
                if (!name) name = lines[0]||'';
                if (name.includes('广告')) name = name.split('广告').pop();
                const cn = name.replace(/^[0-9]+\\s*/,'').trim();
                if (seen.has(cn)||cn.length<4) return;
                seen.add(cn);
                hotels.push({
                    name: cn,
                    stars: sm ? sm[1]+'/5星' : '',
                    rating: rm ? parseFloat(rm[1]) : null,
                    price: pm ? parseInt(pm[1].replace(/,/g,'')) : null,
                    url: link.href
                });
            });
            return JSON.stringify({count: hotels.length, hotels: hotels});
        """)
        
        data = json.loads(hotels_json)
        out_path = os.path.join(BASE_DIR, "hotels_data.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Take screenshot
        try:
            driver.save_screenshot(os.path.join(BASE_DIR, "agoda_result.png"))
        except:
            pass
        
        print(f"\n完成! 共{data['count']}家酒店")
        print(f"数据: {out_path}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
