#!/usr/bin/env python3
"""
Agoda 酒店数据抓取工具 v2
通过完整交互流程：打开首页 → 点击搜索 → 输入城市 → 选择城市 → 设置日期 → 搜索 → 抓取
"""
import os
import sqlite3
import time
import re
import random
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ========== 配置 ==========
CITY = "武汉"
CHECKIN_DAYS = 35
STAY_NIGHTS = 1
ROOMS = 1
ADULTS = 2
CURRENCY = "CNY"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hotels.db")
EXCEL_PATH = os.path.join(BASE_DIR, f"hotels_{CITY}.xlsx")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

MIN_DELAY = 2.0
MAX_DELAY = 4.0

CHECKIN_DATE = (datetime.now() + timedelta(days=CHECKIN_DAYS)).strftime("%Y-%m-%d")
CHECKOUT_DATE = (datetime.now() + timedelta(days=CHECKIN_DAYS + STAY_NIGHTS)).strftime("%Y-%m-%d")

# 用于日期选择
CHECKIN_DAY = int((datetime.now() + timedelta(days=CHECKIN_DAYS)).strftime("%d"))
CHECKIN_MONTH = (datetime.now() + timedelta(days=CHECKIN_DAYS)).month
CHECKIN_YEAR = (datetime.now() + timedelta(days=CHECKIN_DAYS)).year
CHECKOUT_DAY = int((datetime.now() + timedelta(days=CHECKIN_DAYS + STAY_NIGHTS)).strftime("%d"))

print(f"入住日期: {CHECKIN_DATE}")
print(f"离店日期: {CHECKOUT_DATE}")
print(f"城市: {CITY}, {ROOMS}间, {ADULTS}成人, 币种: {CURRENCY}")


def setup_driver():
    """初始化 Chrome 浏览器"""
    chrome_options = Options()
    chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--lang=zh-CN")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

    chromedriver_path = os.path.join(BASE_DIR, "chromedriver.exe")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def random_delay(min_s=MIN_DELAY, max_s=MAX_DELAY):
    time.sleep(random.uniform(min_s, max_s))


def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            address TEXT,
            rating REAL,
            stars INTEGER,
            min_price REAL,
            currency TEXT DEFAULT 'CNY',
            url TEXT,
            scrape_date TEXT,
            city TEXT
        )
    """)
    cursor.execute("DELETE FROM hotels WHERE city = ?", (CITY,))
    conn.commit()
    return conn


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def safe_click(driver, element):
    try:
        element.click()
    except ElementClickInterceptedException:
        try:
            driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            print(f"  [点击失败] {e}")


def search_hotels(driver):
    """在 Agoda 上通过完整交互流程搜索酒店"""
    print("\n=== 步骤1: 打开 Agoda 首页 ===")
    driver.get("https://www.agoda.cn/")
    random_delay(4, 6)

    # --- 点击搜索框打开搜索面板 ---
    print("  点击搜索框...")
    try:
        search_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="TextSearch"]'))
        )
        safe_click(driver, search_btn)
    except TimeoutException:
        print("  [超时] 未找到搜索框，尝试备用方法...")
        driver.get(f"https://www.agoda.cn/search?city=16958&checkIn={CHECKIN_DATE}&checkOut={CHECKOUT_DATE}&rooms={ROOMS}&adults={ADULTS}&currency={CURRENCY}")
        random_delay(5, 8)
        print("  已直接加载搜索页，但城市ID可能不正确")
        return True

    random_delay(2, 3)

    # --- 输入城市 ---
    print(f"  输入城市: {CITY}")
    try:
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="text" and @placeholder]'))
        )
        search_input.clear()
        random_delay(0.5, 1)
        # 逐个字符输入
        for ch in CITY:
            search_input.send_keys(ch)
            random_delay(0.1, 0.2)
        random_delay(2, 3)
    except TimeoutException:
        print("  [超时] 未找到搜索输入框")
        return False

    # --- 选择城市建议 ---
    print("  选择城市建议...")
    try:
        # 等待包含城市的建议项出现
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.XPATH, f'//strong[contains(text(), "{CITY}")]'))
        )
        items = driver.find_elements(By.XPATH, f'//strong[contains(text(), "{CITY}")]')
        if items:
            # 点击包含城市的 li 或 option 元素
            city_option = items[0].find_element(By.XPATH, './ancestor::li | ./ancestor::div[@role="option"]')
            safe_click(driver, city_option)
            print("  已选择城市")
        else:
            print("  [警告] 未找到城市选项，按 Enter")
            search_input.send_keys(Keys.RETURN)
        random_delay(2, 3)
    except TimeoutException:
        print("  [超时] 城市建议未出现，尝试按 Enter")
        try:
            search_input.send_keys(Keys.RETURN)
        except:
            pass
        random_delay(2, 3)

    # --- 设置入住/离店日期 ---
    print(f"  设置日期: {CHECKIN_DATE} ~ {CHECKOUT_DATE}")
    try:
        # 点击日期选择器
        date_pickers = driver.find_elements(By.CSS_SELECTOR, '[data-testid="DatePickerComponent"]')
        if not date_pickers:
            date_pickers = driver.find_elements(By.XPATH, '//div[@data-component="DatePickerComponent"]')
        if not date_pickers:
            date_pickers = driver.find_elements(By.XPATH, '//*[contains(@data-testid, "Date")]')

        if date_pickers:
            safe_click(driver, date_pickers[0])
            random_delay(2, 3)

            # 在日期选择器中选择正确的日期
            # 先尝试通过数据属性直接设置
            try:
                # 看能不能直接通过JS设置日期
                driver.execute_script(f"""
                    var startDate = document.querySelector('[data-section="startDate"]');
                    var endDate = document.querySelector('[data-section="endDate"]');
                    if (startDate) startDate.setAttribute('data-date', '{CHECKIN_DATE}');
                    if (endDate) endDate.setAttribute('data-date', '{CHECKOUT_DATE}');
                """)
            except:
                pass

            # 点击对应的日期数字
            # 需要先找到正确的月份面板，然后点击日期
            try:
                # 导航到正确的年月
                current_year = datetime.now().year
                current_month = datetime.now().month

                # 需要点击"下一月"按钮的次数
                months_diff = (CHECKIN_YEAR - current_year) * 12 + (CHECKIN_MONTH - current_month)

                for _ in range(months_diff):
                    next_btns = driver.find_elements(By.XPATH,
                        '//button[contains(@aria-label, "Next") or contains(@aria-label, "下") or contains(@class, "next")]')
                    if next_btns:
                        safe_click(driver, next_btns[0])
                        random_delay(0.5, 1)
                    else:
                        break

                random_delay(1, 2)

                # 点击入住日期
                day_elems = driver.find_elements(By.XPATH,
                    f'//div[contains(@class, "Day") or contains(@class, "day")]//*[text()="{CHECKIN_DAY}"] | '
                    f'//button[contains(@class, "Day") or contains(@class, "day")]//*[text()="{CHECKIN_DAY}"] | '
                    f'//td[contains(text(), "{CHECKIN_DAY}")]')
                for d in day_elems:
                    try:
                        if d.is_displayed():
                            safe_click(driver, d)
                            print(f"  选择了入住日: {CHECKIN_DAY}")
                            random_delay(1, 2)
                            break
                    except:
                        continue
            except Exception as e:
                print(f"  日期选择出错: {e}")
        else:
            print("  [警告] 未找到日期选择器")
    except Exception as e:
        print(f"  日期设置出错: {e}")

    # --- 点击搜索按钮 ---
    print("  点击搜索按钮...")
    try:
        submit_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="SearchButton"]'))
        )
        safe_click(driver, submit_btn)
        print("  已点击搜索")
        random_delay(5, 8)
    except TimeoutException:
        print("  [超时] 未找到搜索按钮，尝试找其他按钮...")
        btns = driver.find_elements(By.XPATH, '//button[contains(text(), "搜索")]')
        if btns:
            safe_click(driver, btns[0])
            random_delay(5, 8)
        else:
            print("  [警告] 无法提交搜索")

    # 等待搜索结果页面加载
    try:
        WebDriverWait(driver, 15).until(
            lambda d: 'search' in d.current_url.lower() or 'hotel' in d.current_url.lower()
        )
    except:
        pass

    print(f"  当前URL: {driver.current_url}")
    return True


def scroll_to_load_all(driver):
    """滚动加载所有酒店"""
    print("\n=== 加载所有酒店 ===")
    last_height = driver.execute_script("return document.body.scrollHeight")
    max_attempts = 30
    no_change = 0

    for i in range(max_attempts):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        random_delay(2.5, 4)

        # 尝试点击"显示更多"按钮
        try:
            more_btns = driver.find_elements(By.XPATH,
                "//*[contains(text(),'显示更多') or contains(text(),'Show more') or contains(@class,'load-more')]")
            for btn in more_btns:
                if btn.is_displayed():
                    safe_click(driver, btn)
                    random_delay(2, 3)
        except:
            pass

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_change += 1
            if no_change >= 3:
                print(f"  页面不再增长，停止滚动")
                break
        else:
            no_change = 0

        last_height = new_height
        print(f"  滚动加载中... ({i + 1}/{max_attempts})")

    # 滚回顶部
    driver.execute_script("window.scrollTo(0, 0);")
    random_delay(1, 2)


def extract_hotel_info(hotel_el):
    """从酒店卡片元素提取信息（基于 data-element-name 属性）"""
    data = {"name": "", "address": "", "rating": 0, "stars": 0, "min_price": 0}

    # --- 酒店名称 (来自 info-section 的第一个文本) ---
    try:
        info_section = hotel_el.find_elements(By.XPATH,
            './/*[@data-element-name="ssr-property-card-info-section"]')
        if info_section:
            text = info_section[0].text.strip()
            # 名称是第一行，在换行符之前
            first_line = text.split('\n')[0].strip()
            if first_line and len(first_line) > 2:
                data["name"] = first_line
    except:
        pass

    # --- 地址/位置 (ssr-property-card-area) ---
    try:
        area_els = hotel_el.find_elements(By.XPATH,
            './/*[@data-element-name="ssr-property-card-area"]')
        if area_els:
            data["address"] = area_els[0].text.strip()
    except:
        pass

    # --- 评分 (ssr-property-card-reviews) ---
    try:
        review_els = hotel_el.find_elements(By.XPATH,
            './/*[@data-element-name="ssr-property-card-reviews"]')
        if review_els:
            text = review_els[0].text.strip()
            nums = re.findall(r'(\d+\.?\d*)', text)
            if nums:
                val = float(nums[0])
                if 1 <= val <= 10:
                    data["rating"] = val
    except:
        pass

    # --- 星级 (ssr-property-card-rating, e.g. "Rating 4 out of 5") ---
    try:
        star_els = hotel_el.find_elements(By.XPATH,
            './/*[@data-element-name="ssr-property-card-rating"]')
        if star_els:
            text = star_els[0].text.strip()
            # 匹配 "Rating X out of 5" 或 "X out of 5" 或中文 "星级为X"
            star_match = re.search(r'(\d+)\s*out\s*of\s*5', text, re.IGNORECASE)
            if star_match:
                data["stars"] = int(star_match.group(1))
    except:
        pass

    # --- 价格 (fpc-room-price) ---
    try:
        price_els = hotel_el.find_elements(By.XPATH,
            './/*[@data-element-name="fpc-room-price"]')
        if price_els:
            text = price_els[0].text.strip()
            nums = re.findall(r'([\d,]+\.?\d*)', text.replace(',', ''))
            if nums:
                for n in nums:
                    val = float(n.replace(',', ''))
                    if val > 10:  # 排除 RMB 等文本
                        data["min_price"] = val
                        break
    except:
        pass

    # --- 酒店链接 ---
    try:
        links = hotel_el.find_elements(By.XPATH,
            ".//a[contains(@href,'hotel') or contains(@href,'property')]")
        for link in links:
            href = link.get_attribute("href")
            if href and 'agoda' in href.lower():
                data["url"] = href
                break
    except:
        pass

    # 备用：从 HTML 正则提取价格（如果上面的方法没找到）
    if data["min_price"] == 0:
        html = hotel_el.get_attribute("outerHTML") or ""
        # 匹配 "RMB 1,234" 模式
        rmbs = re.findall(r'RMB\s*([\d,]+\.?\d*)', html)
        if rmbs:
            try:
                data["min_price"] = float(rmbs[0].replace(',', ''))
            except:
                pass

    return data


def scrape_hotels(driver):
    """抓取酒店列表数据"""
    print("\n=== 抓取酒店数据 ===")
    all_hotels = []

    # 多个选择器尝试获取酒店卡片
    card_selectors = [
        "//div[contains(@class,'PropertyCard')]",
        "//div[contains(@data-selenium,'hotel')]",
        "//div[contains(@class,'hotel-card')]",
        "//*[@data-testid='hotel-card']",
    ]

    found_cards = []
    for sel in card_selectors:
        try:
            cards = driver.find_elements(By.XPATH, sel)
            # 过滤出包含 info-section 的有效酒店卡片
            valid = []
            for c in cards:
                try:
                    info = c.find_elements(By.XPATH,
                        './/*[@data-element-name="ssr-property-card-info-section"]')
                    price = c.find_elements(By.XPATH,
                        './/*[@data-element-name="fpc-room-price"]')
                    if info or price:
                        valid.append(c)
                except:
                    continue
            if valid:
                print(f"  选择器 '{sel}' 找到 {len(valid)} 个有效酒店卡片（共 {len(cards)} 个元素）")
                found_cards = valid
                break
        except:
            continue

    if not found_cards:
        print("  [尝试] 备用方案：查找所有大区块...")
        # 找所有包含价格的区块
        potential = driver.find_elements(By.XPATH,
            "//div[.//*[contains(text(), '¥') or contains(text(), '￥')]]")
        for p in potential:
            text = p.text.strip()
            if text and len(text) > 10:
                found_cards.append(p)
        print(f"  备用方案找到 {len(found_cards)} 个区块")

    print(f"\n  正在提取 {len(found_cards)} 个卡片的信息...")
    seen_names = set()
    for i, card in enumerate(found_cards):
        try:
            data = extract_hotel_info(card)
            if data["name"] and data["name"] not in seen_names:
                seen_names.add(data["name"])
                all_hotels.append(data)
            elif not data["name"] and data["min_price"] > 0:
                # 无名但有价格
                all_hotels.append(data)
        except Exception as e:
            print(f"  卡片 {i} 提取失败: {e}")
            continue

        if (i + 1) % 20 == 0:
            print(f"  已处理 {i + 1}/{len(found_cards)} 个卡片...")

    return all_hotels


def take_screenshots(driver):
    """截图"""
    ensure_dir(SCREENSHOT_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 全页截图
    ss_path = os.path.join(SCREENSHOT_DIR, f"agoda_{CITY}_{timestamp}.png")
    driver.save_screenshot(ss_path)
    print(f"  截图: {ss_path}")
    return ss_path


def print_filter_info(driver):
    """打印筛选条件"""
    print("\n" + "=" * 50)
    print("当前筛选条件:")
    print(f"  平台: Agoda (agoda.cn)")
    print(f"  城市: {CITY}")
    print(f"  入住: {CHECKIN_DATE}")
    print(f"  离店: {CHECKOUT_DATE}")
    print(f"  住宿: {STAY_NIGHTS}晚")
    print(f"  房间: {ROOMS}间")
    print(f"  成人: {ADULTS}人")
    print(f"  币种: {CURRENCY}")
    print(f"  URL: {driver.current_url}")
    print(f"  标题: {driver.title}")
    print("=" * 50)


def get_total_hotel_count(driver):
    """获取酒店总数"""
    count_selectors = [
        "//*[contains(text(),'共') and (contains(text(),'家') or contains(text(),'间') or contains(text(),'个'))]",
        "//*[contains(@data-selenium,'result-count')]",
        "//*[contains(@class,'resultCount')]",
        "//*[contains(@class,'PropertyCount')]",
        "//*[contains(@data-element-name,'result-count')]",
    ]
    for sel in count_selectors:
        try:
            el = driver.find_elements(By.XPATH, sel)
            if el:
                text = el[0].text.strip()
                print(f"  酒店总数: {text}")
                return text
        except:
            continue
    return "未知"


def save_to_excel(hotels, filename):
    """保存到 Excel"""
    print(f"\n保存 Excel: {filename}")
    if not hotels:
        print("  [警告] 无数据")
        return

    df = pd.DataFrame(hotels)
    if df.empty:
        print("  无数据")
        return

    df = df.drop_duplicates(subset=["name"], keep="first")
    df = df.sort_values(by="min_price", ascending=True)

    # 重命名列
    column_map = {
        "name": "酒店名称",
        "address": "地址",
        "rating": "评分",
        "stars": "星级",
        "min_price": "最低价(CNY)",
    }
    if "url" in df.columns:
        column_map["url"] = "详情链接"

    # 只选择存在的列
    cols = [c for c in column_map.keys() if c in df.columns]
    df = df[cols].rename(columns=column_map)

    df.to_excel(filename, index=False, engine="openpyxl")
    print(f"  已保存 {len(df)} 条数据到 {filename}")


def main():
    print("=" * 60)
    print("Agoda 酒店数据抓取工具 v2")
    print(f"城市: {CITY}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = init_database()
    cursor = conn.cursor()

    driver = None
    try:
        driver = setup_driver()
        print("浏览器已启动")

        # 搜索
        ok = search_hotels(driver)
        if not ok:
            print("[错误] 搜索失败，终止")
            return

        # 等待结果加载
        print("\n等待搜索结果完全加载...")
        random_delay(8, 12)

        # 打印筛选条件
        print_filter_info(driver)

        # 截图（搜索结果页含筛选条件）
        take_screenshots(driver)

        # 获取总数
        total_count = get_total_hotel_count(driver)

        # 滚动加载所有酒店
        scroll_to_load_all(driver)

        # 再次截图
        take_screenshots(driver)

        # 抓取数据
        hotels_data = scrape_hotels(driver)

        if not hotels_data:
            print("\n[错误] 未抓取到酒店数据！")
            # 保存页面源码
            with open(os.path.join(BASE_DIR, "page_source_debug.html"), "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("  页面已保存到 page_source_debug.html")
            return

        print(f"\n成功抓取 {len(hotels_data)} 条酒店数据")

        # 保存到数据库
        print("\n保存到数据库...")
        for hotel in hotels_data:
            cursor.execute("""
                INSERT INTO hotels (name, address, rating, stars, min_price, currency, url, scrape_date, city)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hotel.get("name", ""),
                hotel.get("address", ""),
                hotel.get("rating", 0),
                hotel.get("stars", 0),
                hotel.get("min_price", 0),
                CURRENCY,
                hotel.get("url", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                CITY
            ))
        conn.commit()
        print(f"  数据库: {DB_PATH} ({len(hotels_data)} 条)")

        # 保存到 Excel
        save_to_excel(hotels_data, EXCEL_PATH)

        # 统计
        print("\n" + "=" * 60)
        print("抓取完成！")
        print(f"  城市: {CITY}")
        print(f"  总数: {total_count}")
        print(f"  抓取: {len(hotels_data)} 条")
        print(f"  数据库: {DB_PATH}")
        print(f"  Excel: {EXCEL_PATH}")
        print(f"  截图: {SCREENSHOT_DIR}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
        if driver:
            try:
                ensure_dir(SCREENSHOT_DIR)
                driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
                with open(os.path.join(BASE_DIR, "page_source_error.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
            except:
                pass
    finally:
        if driver:
            driver.quit()
        conn.close()
        print("已完成")


if __name__ == "__main__":
    main()
