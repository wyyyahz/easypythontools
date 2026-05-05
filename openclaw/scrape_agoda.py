#!/usr/bin/env python3
"""
Agoda 武汉酒店数据爬取脚本
- 目标: https://www.agoda.cn/
- 城市: 武汉
- 入住: 2026-06-05, 退房: 2026-06-06 (1晚)
- 1间, 2成人, 币种 CNY
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import re
import sqlite3
import os

# ============ CONFIG ============
CHECK_IN = "2026-06-05"
CHECK_OUT = "2026-06-06"
CITY = "武汉"
CITY_CODE = "10335"  # Wuhan city code on Agoda
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agoda_wuhan.db")

# ============ DATABASE ============
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_name TEXT,
            address TEXT,
            rating REAL,
            star_rating TEXT,
            lowest_price REAL,
            currency TEXT,
            url TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def save_hotels(conn, hotels):
    c = conn.cursor()
    for h in hotels:
        c.execute("""
            INSERT OR IGNORE INTO hotels (hotel_name, address, rating, star_rating, lowest_price, currency, url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            h.get('name', ''),
            h.get('address', ''),
            h.get('rating'),
            h.get('star_rating', ''),
            h.get('price'),
            h.get('currency', 'CNY'),
            h.get('url', '')
        ))
    conn.commit()
    print(f"  ✓ 已保存 {len(hotels)} 家酒店到数据库")

# ============ SCRAPER ============
def scrape_agoda():
    print("=" * 60)
    print(f"Agoda 武汉酒店数据抓取")
    print(f"入住: {CHECK_IN} → 退房: {CHECK_OUT}")
    print("=" * 60)

    # Initialize database
    conn = init_db()

    # Initialize undetected Chrome driver
    print("\n[1/5] 启动浏览器...")
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=zh-CN")
    
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # Step 1: Navigate to Agoda search URL
        print("[2/5] 加载搜索结果页...")
        search_url = (
            f"https://www.agoda.cn/search"
            f"?city={CITY_CODE}"
            f"&checkIn={CHECK_IN}"
            f"&checkOut={CHECK_OUT}"
            f"&rooms=1"
            f"&adults=2"
            f"&children=0"
            f"&currency=CNY"
            f"&languageCode=zh-cn"
        )
        driver.get(search_url)
        
        # Wait for results to load (or error page)
        time.sleep(8)
        
        # Take screenshot for debugging
        driver.save_screenshot(os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_search.png"))
        
        # Check if there's an error
        page_text = driver.page_source
        
        # Try to wait for hotel cards to appear
        print("[3/5] 等待酒店列表加载...")
        try:
            # Wait for hotel card elements or price elements
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-selenium='hotel-item'], .HotelCard, [class*='hotel'], [class*='property-card'], [class*='PropertyCard']"))
            )
        except TimeoutException:
            print("  ⚠ 酒店卡片未直接出现，尝试等待更久或检查页面...")
            time.sleep(5)
        
        # Scroll down to load more results
        print("[4/5] 滚动加载更多...")
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(2)
        
        # Extract hotel data using JavaScript
        print("[5/5] 提取酒店数据...")
        
        hotels_data = driver.execute_script("""
            const hotels = [];
            
            // Try to find hotel cards using various selectors
            const cardSelectors = [
                '[data-selenium="hotel-item"]',
                '[class*="HotelCard"]', 
                '[class*="PropertyCard"]',
                '[class*="hotel-card"]',
                '[class*="property-card"]',
                '[data-testid="hotel-card"]',
                'article',
                '[class*="Listing"]',
                '[class*="SearchResult"]'
            ];
            
            let cards = [];
            for (const selector of cardSelectors) {
                const found = document.querySelectorAll(selector);
                if (found.length > 0) {
                    cards = found;
                    console.log('Found cards with:', selector);
                    break;
                }
            }
            
            // If no structured cards found, try extracting from the raw page
            if (cards.length === 0) {
                // Try to find any element with hotel name
                const allElements = document.querySelectorAll('*');
                const textItems = [];
                for (const el of allElements) {
                    if (el.children.length === 0 && el.textContent.trim().length > 2) {
                        textItems.push(el.textContent.trim());
                    }
                }
                return {cards: [], rawTexts: textItems.slice(0, 200)};
            }
            
            for (const card of cards) {
                const hotel = {};
                
                // Hotel name
                const nameEl = card.querySelector('[data-selenium="hotel-name"], [class*="hotel-name"], [class*="hotelName"], h3, [class*="title"]');
                hotel.name = nameEl ? nameEl.textContent.trim() : '';
                
                // Address
                const addrEl = card.querySelector('[data-selenium="hotel-address"], [class*="address"], [class*="location"]');
                hotel.address = addrEl ? addrEl.textContent.trim() : '';
                
                // Rating
                const ratingEl = card.querySelector('[data-selenium="rating"], [class*="rating"], [class*="score"]');
                const ratingText = ratingEl ? ratingEl.textContent.trim() : '';
                const ratingMatch = ratingText.match(/([0-9]\\.[0-9])/);
                hotel.rating = ratingMatch ? parseFloat(ratingMatch[1]) : null;
                
                // Star rating
                const starEl = card.querySelector('[class*="star"], [data-selenium="star-rating"]');
                hotel.star_rating = starEl ? starEl.textContent.trim() : '';
                
                // Price
                const priceEl = card.querySelector('[data-selenium="display-price"], [class*="price"], [class*="finalPrice"], [data-element-name="final-price"]');
                hotel.price = priceEl ? priceEl.textContent.trim() : '';
                
                // URL
                const linkEl = card.querySelector('a');
                hotel.url = linkEl ? linkEl.href : '';
                
                hotels.push(hotel);
            }
            
            return {cards: hotels, total: hotels.length};
        """)
        
        print(f"  JS返回数据: {json.dumps(hotels_data, ensure_ascii=False)[:500]}")
        
        # Try another approach - get all elements with prices
        print("\n尝试备用提取方法...")
        all_text = driver.find_elements(By.XPATH, "//*[contains(text(), '¥') or contains(text(), 'CNY') or contains(text(), '￥')]")
        price_elements = []
        for el in all_text[:20]:
            try:
                price_elements.append(el.text)
            except:
                pass
        
        print(f"  找到 {len(price_elements)} 个价格元素")
        
        # Save raw page source for analysis
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "page_source.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("  ✓ 页面源码已保存到 page_source.html")
        
        # Take final screenshot
        driver.save_screenshot(os.path.join(os.path.dirname(os.path.abspath(__file__)), "result.png"))
        
        return hotels_data, driver.page_source

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        print("\n关闭浏览器...")
        driver.quit()
        conn.close()

if __name__ == "__main__":
    result, source = scrape_agoda()
    if result:
        print(f"\n✓ 抓取完成!")
    else:
        print(f"\n✗ 抓取失败，请检查 debug 截图")
