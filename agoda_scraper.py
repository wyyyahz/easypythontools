#!/usr/bin/env python3
"""
Agoda 酒店数据抓取工具
抓取指定城市的酒店列表并保存到本地数据库和 Excel
"""
import json
import os
import sqlite3
import time
import re
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException, ElementClickInterceptedException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ========== 配置 ==========
CITY = "武汉"
CHECKIN_DAYS = 35  # 约1个月后
STAY_NIGHTS = 1
ROOMS = 1
ADULTS = 2
CURRENCY = "CNY"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hotels.db")
EXCEL_PATH = os.path.join(BASE_DIR, f"hotels_{CITY}.xlsx")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

# 抓取间隔（秒）- 不要太快
MIN_DELAY = 2
MAX_DELAY = 4

# ========== 计算日期 ==========
CHECKIN_DATE = (datetime.now() + timedelta(days=CHECKIN_DAYS)).strftime("%Y-%m-%d")
CHECKOUT_DATE = (datetime.now() + timedelta(days=CHECKIN_DAYS + STAY_NIGHTS)).strftime("%Y-%m-%d")

print(f"入住日期: {CHECKIN_DATE}")
print(f"离店日期: {CHECKOUT_DATE}")
print(f"城市: {CITY}, {ROOMS}间, {ADULTS}成人, 币种: {CURRENCY}")


def setup_driver():
    """初始化 Chrome 浏览器"""
    chrome_options = Options()
    chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    # 反检测设置
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")

    # 设置中文语言
    chrome_options.add_argument("--lang=zh-CN")
    chrome_options.add_argument("--accept-lang=zh-CN")

    # User-Agent
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

    # 使用本地 ChromeDriver
    chromedriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromedriver.exe")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def random_delay(min_s=MIN_DELAY, max_s=MAX_DELAY):
    """随机延迟模拟人类行为"""
    import random
    time.sleep(random.uniform(min_s, max_s))


def init_database():
    """初始化 SQLite 数据库"""
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
    # 清空旧数据（每次重新抓取）
    cursor.execute("DELETE FROM hotels WHERE city = ?", (CITY,))
    conn.commit()
    return conn


def ensure_dir(path):
    """确保目录存在"""
    if not os.path.exists(path):
        os.makedirs(path)


def wait_and_find(driver, by, selector, timeout=15, multiple=False):
    """等待元素出现并返回"""
    try:
        if multiple:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((by, selector))
            )
            return driver.find_elements(by, selector)
        else:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            return element
    except TimeoutException:
        print(f"  [超时] 未找到元素: {selector}")
        return None if not multiple else []


def safe_click(driver, element):
    """安全点击元素（尝试多种方式）"""
    try:
        element.click()
    except ElementClickInterceptedException:
        try:
            driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            print(f"  [点击失败] {e}")


def search_hotels(driver):
    """在 Agoda 上搜索酒店"""
    print("\n=== 步骤1: 打开 Agoda 首页 ===")
    driver.get("https://www.agoda.cn/")
    random_delay(3, 5)

    # 处理可能出现的登录/弹窗
    try:
        # 关闭可能的弹窗
        close_buttons = driver.find_elements(By.XPATH,
            "//*[contains(@class,'close')] | //*[contains(@class,'dismiss')] | //button[contains(text(),'关闭')] | //button[contains(text(),'不')]")
        for btn in close_buttons[:3]:
            try:
                safe_click(driver, btn)
                random_delay(0.5, 1)
            except:
                pass
    except:
        pass

    # 点击搜索框 - Agoda 的搜索框
    print("  输入城市: 武汉")
    search_box_selectors = [
        "//input[@placeholder and contains(@placeholder, '目的地')]",
        "//input[@placeholder and contains(@placeholder, '城市')]",
        "//input[@placeholder and contains(@placeholder, '酒店')]",
        "//input[@data-element-name='search-box']",
        "//input[contains(@class, 'SearchBox')]",
        "//input[@id='textInput']",
        "//input[@aria-label='搜索']",
        "//div[contains(@class,'SearchBox')]//input",
        "//div[contains(@data-selenium,'search')]//input",
    ]

    search_input = None
    for sel in search_box_selectors:
        try:
            elements = driver.find_elements(By.XPATH, sel)
            if elements:
                search_input = elements[0]
                print(f"  找到搜索框: {sel}")
                break
        except:
            continue

    if not search_input:
        print("  [警告] 未找到标准搜索框，尝试直接打开搜索页...")
        # 直接尝试打开搜索 URL
        search_url = f"https://www.agoda.cn/search?city=16958&checkIn={CHECKIN_DATE}&checkOut={CHECKOUT_DATE}&rooms={ROOMS}&adults={ADULTS}&currency={CURRENCY}"
        driver.get(search_url)
        random_delay(5, 8)
        return True

    search_input.clear()
    random_delay(0.5, 1)
    search_input.send_keys(CITY)
    random_delay(2, 3)

    # 选择下拉建议中的城市
    print("  选择城市建议")
    suggestion_selectors = [
        "//*[contains(@data-element-name,'suggestion')]//*[contains(text(),'武汉')]",
        "//*[contains(@class,'suggestion')]//*[contains(text(),'武汉')]",
        "//*[contains(@class,'autocomplete')]//*[contains(text(),'武汉')]",
        "//li[contains(.,'武汉')]",
        "//div[contains(.,'武汉') and (@role='option' or @role='presentation')]",
        "//*[@data-element-name='search-suggestion-item' and contains(.,'武汉')]",
    ]

    suggestion_clicked = False
    for sel in suggestion_selectors:
        try:
            suggestions = driver.find_elements(By.XPATH, sel)
            if suggestions:
                safe_click(driver, suggestions[0])
                suggestion_clicked = True
                print(f"  已选择城市建议: {sel}")
                random_delay(1.5, 2.5)
                break
        except:
            continue

    if not suggestion_clicked:
        print("  [警告] 未找到城市建议，按 Enter 继续")
        search_input.send_keys(Keys.RETURN)
        random_delay(3, 5)

    # 设置日期 - 处理日期选择器
    print(f"  设置日期: {CHECKIN_DATE} ~ {CHECKOUT_DATE}")
    random_delay(1, 2)

    # 尝试直接通过URL参数设置日期
    try:
        current_url = driver.current_url
        if "checkIn" not in current_url and "checkin" not in current_url:
            print("  尝试通过 URL 设置日期参数...")
            # 获取城市ID
            city_match = re.search(r'city=(\d+)', current_url)
            if city_match:
                city_id = city_match.group(1)
            else:
                # 从页面提取城市信息
                city_id = ""

            # Agoda 接受 URL 参数
            search_url = f"https://www.agoda.cn/search?city={city_id}&checkIn={CHECKIN_DATE}&checkOut={CHECKOUT_DATE}&rooms={ROOMS}&adults={ADULTS}&currency={CURRENCY}"
            driver.get(search_url)
            random_delay(5, 8)
            print(f"  已加载搜索页面")
            return True
    except:
        pass

    # 搜索按钮
    print("  点击搜索按钮")
    search_btn_selectors = [
        "//button[@type='submit']",
        "//button[contains(text(),'搜索')]",
        "//button[contains(@class,'search')]",
        "//*[@data-element-name='search-button']",
        "//*[@role='button' and contains(text(),'搜索')]",
    ]

    for sel in search_btn_selectors:
        try:
            btn = wait_and_find(driver, By.XPATH, sel, timeout=3)
            if btn:
                safe_click(driver, btn)
                print(f"  已点击搜索按钮")
                random_delay(5, 7)
                return True
        except:
            continue

    print("  [警告] 未找到搜索按钮，尝试提交表单")
    try:
        search_input.send_keys(Keys.RETURN)
        random_delay(5, 7)
    except:
        pass

    return True


def extract_hotel_data(driver, hotel_element):
    """从单个酒店元素提取数据"""
    data = {"name": "", "address": "", "rating": 0, "stars": 0, "min_price": 0}

    # 酒店名称 - 多种选择器
    name_selectors = [
        ".//h3[contains(@class,'name')]",
        ".//h3[contains(@data-selenium,'hotel-name')]",
        ".//*[contains(@data-selenium,'hotel-name')]",
        ".//*[contains(@data-element-name,'hotel-name')]",
        ".//a[contains(@class,'name')]",
        ".//span[contains(@class,'name')]",
        ".//div[contains(@class,'name')]",
        ".//h3",
        ".//*[@data-testid='hotel-name']",
    ]
    for sel in name_selectors:
        try:
            el = hotel_element.find_elements(By.XPATH, sel)
            if el:
                data["name"] = el[0].text.strip()
                if data["name"]:
                    break
        except:
            continue

    # 酒店地址
    addr_selectors = [
        ".//*[contains(@data-selenium,'address')]",
        ".//*[contains(@class,'address')]",
        ".//*[contains(@data-element-name,'address')]",
        ".//span[contains(@class,'address')]",
        ".//div[contains(@class,'address')]",
    ]
    for sel in addr_selectors:
        try:
            el = hotel_element.find_elements(By.XPATH, sel)
            if el and el[0].text.strip():
                data["address"] = el[0].text.strip()
                break
        except:
            continue

    # 评分
    rating_selectors = [
        ".//*[contains(@data-selenium,'rating')]",
        ".//*[contains(@class,'rating')]",
        ".//*[contains(@data-element-name,'rating')]",
        ".//*[contains(@class,'score')]",
        ".//span[contains(@class,'review')]",
    ]
    for sel in rating_selectors:
        try:
            el = hotel_element.find_elements(By.XPATH, sel)
            if el:
                text = el[0].text.strip()
                # 提取数字评分
                rating_match = re.search(r'(\d+\.?\d*)', text)
                if rating_match:
                    data["rating"] = float(rating_match.group(1))
                break
        except:
            continue

    # 星级
    star_selectors = [
        ".//*[contains(@data-selenium,'star')]",
        ".//*[contains(@class,'star')]",
        ".//*[contains(@data-element-name,'star')]",
        ".//*[contains(@alt,'star')]",
        ".//i[contains(@class,'star')]",
        ".//*[name()='svg' and contains(@class,'star')]",
    ]
    for sel in star_selectors:
        try:
            el = hotel_element.find_elements(By.XPATH, sel)
            if el:
                # 计算星的数量（可能用图标表示）
                stars_el = hotel_element.find_elements(By.XPATH,
                    ".//*[contains(@class,'star') and not(contains(@class,'outline')) and not(contains(@class,'empty'))]")
                if len(stars_el) > 0:
                    data["stars"] = len(stars_el)
                else:
                    text = el[0].text.strip()
                    star_match = re.search(r'(\d+)\s*星', text)
                    if star_match:
                        data["stars"] = int(star_match.group(1))
                break
        except:
            continue

    # 价格
    price_selectors = [
        ".//*[contains(@data-selenium,'price')]",
        ".//*[contains(@class,'price')]",
        ".//*[contains(@data-element-name,'price')]",
        ".//*[contains(@class,'finalPrice')]",
        ".//*[contains(@class,'displayPrice')]",
    ]
    for sel in price_selectors:
        try:
            el = hotel_element.find_elements(By.XPATH, sel)
            if el:
                text = el[0].text.strip()
                # 提取数字价格
                price_match = re.search(r'([\d,]+\.?\d*)', text.replace(',', ''))
                if price_match:
                    data["min_price"] = float(price_match.group(1).replace(',', ''))
                break
        except:
            continue

    # 获取酒店URL
    try:
        link = hotel_element.find_elements(By.XPATH, ".//a[contains(@href,'hotel')]")
        if link:
            href = link[0].get_attribute("href")
            if href:
                data["url"] = href
    except:
        pass

    return data


def load_all_hotels(driver):
    """滚动页面加载所有酒店"""
    print("\n=== 步骤3: 加载所有酒店列表 ===")

    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_attempts = 30
    no_new_hotels_count = 0

    while scroll_attempts < max_attempts and no_new_hotels_count < 5:
        # 滚动到底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        random_delay(2, 4)

        # 点击"查看更多"或"加载更多"按钮
        try:
            load_more = driver.find_elements(By.XPATH,
                "//*[contains(text(),'更多') or contains(text(),'加载') or contains(text(),'Show more')]")
            for btn in load_more:
                if btn.is_displayed():
                    safe_click(driver, btn)
                    print("  点击了加载更多按钮")
                    random_delay(2, 3)
        except:
            pass

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_new_hotels_count += 1
        else:
            no_new_hotels_count = 0

        last_height = new_height
        scroll_attempts += 1
        print(f"  滚动加载中... ({scroll_attempts}/{max_attempts})")

    print(f"  完成加载，共尝试 {scroll_attempts} 次滚动")
    random_delay(2, 3)


def scrape_hotels(driver):
    """从搜索结果页面抓取酒店数据"""
    print("\n=== 步骤4: 提取酒店数据 ===")

    # 多个选择器尝试获取酒店列表容器
    hotel_container_selectors = [
        "//div[contains(@class,'hotel-list')]",
        "//div[contains(@data-selenium,'hotel-list')]",
        "//div[contains(@class,'SearchResult')]",
        "//div[@role='list']",
        "//div[contains(@class,'Listing')]",
        "//div[contains(@class,'PropertyCard')]/..",
        "//div[contains(@class,'hotel-card')]/..",
    ]

    # 单个酒店卡片的选择器
    hotel_card_selectors = [
        ".//div[contains(@class,'PropertyCard')]",
        ".//div[contains(@class,'hotel-card')]",
        ".//div[contains(@data-selenium,'hotel')]",
        ".//div[contains(@class,'Card') and contains(@class,'Hotel')]",
        ".//li[contains(@class,'hotel')]",
        ".//div[contains(@class,'listing')]",
        ".//*[@data-testid='hotel-card']",
    ]

    all_hotels = []

    # 尝试直接抓取
    for container_sel in hotel_container_selectors:
        try:
            containers = driver.find_elements(By.XPATH, container_sel)
            if containers:
                print(f"  找到酒店列表容器: {container_sel}")
                for card_sel in hotel_card_selectors:
                    try:
                        cards = containers[0].find_elements(By.XPATH, card_sel)
                        if cards:
                            print(f"  找到 {len(cards)} 个酒店卡片 (选择器: {card_sel})")
                            for card in cards:
                                data = extract_hotel_data(driver, card)
                                all_hotels.append(data)
                            if all_hotels:
                                return all_hotels
                    except:
                        continue
        except:
            continue

    # 如果上面的方法不行，直接找所有酒店卡片
    print("  [尝试] 直接查找所有酒店卡片...")
    for card_sel in hotel_card_selectors:
        try:
            cards = driver.find_elements(By.XPATH, card_sel.lstrip('.'))
            if cards:
                print(f"  直接找到 {len(cards)} 个酒店卡片")
                for card in cards:
                    data = extract_hotel_data(driver, card)
                    all_hotels.append(data)
                if all_hotels:
                    return all_hotels
        except:
            continue

    # 最后的备用方案：找所有含酒店名称的元素
    print("  [尝试] 备用方案 - 查找所有包含酒店信息的区块...")
    try:
        # 通用方法：查找所有大区块
        potential_cards = driver.find_elements(By.XPATH,
            "//*[@data-hotelid or @data-hotel-id or contains(@class,'PropertyCard') or contains(@class,'hotel-card')]")
        if not potential_cards:
            # 找所有包含"¥"价格和酒店名的区块
            potential_cards = driver.find_elements(By.XPATH,
                "//div[.//*[contains(text(),'¥')]]")

        print(f"  找到 {len(potential_cards)} 个潜在酒店区块")
        for card in potential_cards:
            data = extract_hotel_data(driver, card)
            if data["name"] or data["min_price"] > 0:
                all_hotels.append(data)
    except Exception as e:
        print(f"  备用方案失败: {e}")

    return all_hotels


def get_total_hotel_count(driver):
    """获取酒店总数"""
    print("\n=== 酒店总数 ===")
    count_selectors = [
        "//*[contains(text(),'共') and contains(text(),'家')]",
        "//*[contains(text(),'共') and contains(text(),'间')]",
        "//*[contains(text(),'个') and contains(text(),'结果')]",
        "//*[contains(@data-selenium,'result-count')]",
        "//*[contains(@class,'result-count')]",
        "//*[contains(@class,'resultCount')]",
    ]

    for sel in count_selectors:
        try:
            el = driver.find_elements(By.XPATH, sel)
            if el:
                text = el[0].text.strip()
                print(f"  找到计数: {text}")
                return text
        except:
            continue

    # 统计我们抓到的酒店数量
    print("  [提示] 未找到明确总数显示")
    return "未知"


def take_screenshots(driver):
    """截图保存"""
    ensure_dir(SCREENSHOT_DIR)

    # 全页截图
    print("\n=== 截图 ===")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 页面顶部截图（显示筛选条件）
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"agoda_{CITY}_{timestamp}.png")
    driver.save_screenshot(screenshot_path)
    print(f"  页面截图已保存: {screenshot_path}")

    return screenshot_path


def print_filter_info(driver):
    """打印当前筛选条件"""
    print("\n=== 当前筛选条件 ===")
    print(f"  平台: Agoda (agoda.cn)")
    print(f"  城市: {CITY}")
    print(f"  入住: {CHECKIN_DATE}")
    print(f"  离店: {CHECKOUT_DATE}")
    print(f"  住宿: {STAY_NIGHTS}晚")
    print(f"  房间: {ROOMS}间")
    print(f"  成人: {ADULTS}人")
    print(f"  币种: {CURRENCY}")
    print(f"  当前URL: {driver.current_url}")

    # 获取页面标题
    print(f"  页面标题: {driver.title}")


def save_to_excel(hotels, filename):
    """保存到 Excel"""
    print(f"\n=== 保存 Excel: {filename} ===")

    if not hotels:
        print("  [警告] 没有数据可保存")
        return

    df = pd.DataFrame(hotels)

    # 去重和排序
    if df.empty:
        print("  [警告] DataFrame 为空")
        return

    df = df.drop_duplicates(subset=["name"], keep="first")
    df = df.sort_values(by="min_price", ascending=True)

    # 重命名列
    df.columns = [
        "酒店名称", "地址", "评分", "星级", "最低价(CNY)",
        "详情链接", "抓取日期", "城市"
    ]

    df.to_excel(filename, index=False, engine="openpyxl")
    print(f"  已保存 {len(df)} 条酒店数据到 {filename}")


def main():
    """主流程"""
    print("=" * 60)
    print("Agoda 酒店数据抓取工具")
    print(f"抓取城市: {CITY}")
    print(f"抓取日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 初始化数据库
    conn = init_database()
    cursor = conn.cursor()

    driver = None
    try:
        # 启动浏览器
        driver = setup_driver()
        print("浏览器已启动")

        # 搜索酒店
        search_hotels(driver)

        # 等待搜索结果加载
        print("\n=== 步骤2: 等待搜索结果加载 ===")
        random_delay(5, 8)

        # 打印筛选条件信息
        print_filter_info(driver)

        # 截图
        take_screenshots(driver)

        # 获取总数
        total_count = get_total_hotel_count(driver)

        # 加载所有酒店
        load_all_hotels(driver)

        # 再次截图（加载后）
        take_screenshots(driver)

        # 抓取酒店数据
        hotels_data = scrape_hotels(driver)

        if not hotels_data:
            print("\n[错误] 没有抓取到任何酒店数据！")
            print("尝试保存页面源代码以供调试...")
            with open(os.path.join(BASE_DIR, "page_source.html"), "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("  页面源代码已保存到 page_source.html")
            return

        print(f"\n成功抓取到 {len(hotels_data)} 条酒店数据")

        # 保存到数据库
        print("\n=== 步骤5: 保存到数据库 ===")
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
        print(f"  已保存 {len(hotels_data)} 条数据到 {DB_PATH}")

        # 保存到 Excel
        save_to_excel(hotels_data, EXCEL_PATH)

        # 打印统计
        print("\n" + "=" * 60)
        print("抓取完成！统计信息：")
        print(f"  城市: {CITY}")
        print(f"  酒店总数: {total_count}")
        print(f"  成功抓取: {len(hotels_data)} 条")
        print(f"  数据库: {DB_PATH}")
        print(f"  Excel: {EXCEL_PATH}")
        print(f"  截图: {SCREENSHOT_DIR}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[错误] 抓取过程异常: {e}")
        import traceback
        traceback.print_exc()

        # 异常时截图保存
        if driver:
            try:
                ensure_dir(SCREENSHOT_DIR)
                error_ss = os.path.join(SCREENSHOT_DIR, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                driver.save_screenshot(error_ss)
                print(f"  错误截图已保存: {error_ss}")

                # 保存页面源码
                with open(os.path.join(BASE_DIR, "page_source_error.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("  页面源代码已保存到 page_source_error.html")
            except:
                pass

    finally:
        if driver:
            driver.quit()
        conn.close()
        print("\n浏览器已关闭，数据库连接已关闭")


if __name__ == "__main__":
    main()
