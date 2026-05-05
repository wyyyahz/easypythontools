#!/usr/bin/env python3
"""
Agoda 酒店数据抓取工具 v3
"""
import os, sqlite3, time, re, random
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

CITY = "武汉"
CITY_ID = "5818"
CHECKIN_DAYS = 35
STAY_NIGHTS = 1
ROOMS = 1
ADULTS = 2
CURRENCY = "CNY"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hotels.db")
EXCEL_PATH = os.path.join(BASE_DIR, f"hotels_{CITY}.xlsx")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

CHECKIN_DATE = (datetime.now() + timedelta(days=CHECKIN_DAYS)).strftime("%Y-%m-%d")
CHECKOUT_DATE = (datetime.now() + timedelta(days=CHECKIN_DAYS + STAY_NIGHTS)).strftime("%Y-%m-%d")
print(f"入住:{CHECKIN_DATE} 离店:{CHECKOUT_DATE} {CITY} {ROOMS}间{ADULTS}人 {CURRENCY}")

# 非酒店名称过滤
BAD_NAMES = [
    "本站仅剩", "仅剩", "只剩", "特别推荐", "Domestic Deal", "查看",
    "RETURN HOME", "我们只剩",
]


def setup_driver():
    opts = Options()
    opts.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=zh-CN")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36")
    svc = Service(os.path.join(BASE_DIR, "chromedriver.exe"))
    d = webdriver.Chrome(service=svc, options=opts)
    d.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return d


def sd(a=2, b=4):
    time.sleep(random.uniform(a, b))


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS hotels (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, address TEXT,
        rating REAL, stars INTEGER, min_price REAL, currency TEXT DEFAULT 'CNY',
        url TEXT, scrape_date TEXT, city TEXT)""")
    conn.execute("DELETE FROM hotels WHERE city=?", (CITY,))
    conn.commit()
    return conn


def ensure_dir(p):
    if not os.path.exists(p):
        os.makedirs(p)


def click(d, el):
    try:
        el.click()
    except ElementClickInterceptedException:
        d.execute_script("arguments[0].click();", el)


def search_hotels(d):
    print("\n[1/4] 打开武汉搜索页...")
    url = (f"https://www.agoda.cn/search?city={CITY_ID}"
           f"&checkin={CHECKIN_DATE}&checkout={CHECKOUT_DATE}"
           f"&los=1&rooms={ROOMS}&adults={ADULTS}&currency={CURRENCY}")
    print(f"  URL: {url}")
    d.get(url)
    sd(6, 9)
    print(f"  标题: {d.title} | URL: {d.current_url}")
    return True


def get_loaded_count(d):
    try:
        return len(d.find_elements(By.XPATH, "//div[contains(@class,'PropertyCard')]"))
    except:
        return 0


def scroll_all(d):
    print("\n[2/4] 滚动加载全部酒店...")
    total_text = ""
    try:
        for el in d.find_elements(By.XPATH, "//*[contains(text(),'共')]"):
            t = el.text.strip()
            if any(c.isdigit() for c in t):
                total_text = t
                break
    except:
        pass
    print(f"  页面计数: {total_text or '未找到'}")

    last_h = d.execute_script("return document.body.scrollHeight")
    no_chg = 0
    for i in range(300):
        d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sd(1.5, 2.5)
        try:
            for btn in d.find_elements(By.XPATH, "//*[contains(text(),'显示更多') or contains(@class,'load-more')]"):
                if btn.is_displayed():
                    click(d, btn)
                    sd(1.5, 2.5)
        except:
            pass
        if (i + 1) % 5 == 0:
            loaded = get_loaded_count(d)
            print(f"  滚动 {i+1}/300 - 已加载 {loaded} 家", end="\r")
        new_h = d.execute_script("return document.body.scrollHeight")
        if new_h == last_h:
            no_chg += 1
            if no_chg >= 5:
                loaded = get_loaded_count(d)
                if i > 10:  # 至少滚了几次
                    print(f"\n  页面停止增长, 已加载 {loaded} 家")
                    break
        else:
            no_chg = 0
        last_h = new_h

    loaded = get_loaded_count(d)
    print(f"\n  最终加载: {loaded} 家")
    d.execute_script("window.scrollTo(0, 0);")
    sd(1, 2)


def is_valid_hotel_name(name):
    """判断是否为有效酒店名称"""
    if not name or len(name) < 3:
        return False
    name_lower = name.lower()
    for bad in BAD_NAMES:
        if bad.lower() in name_lower:
            return False
    # 跳过纯促销文本
    promo = ["仅剩", "只剩", "特别推荐", "查看", "广告", "赞助"]
    if any(p in name for p in promo):
        return False
    return True


def extract(card):
    """从酒店卡片提取数据"""
    data = {"name": "", "address": "", "rating": 0, "stars": 0, "min_price": 0}
    text = card.text.strip()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return data

    # === 酒店名称: 查找第一个像酒店名的行 ===
    skip_pat = [
        r'^[\d,.RMB￥¥$€]+$', r'^\(', r'^[a-zA-Z\s]{1,3}$',
        '星级', '条评论', '评论', 'RMB', '每晚含税',
        '仅剩', '只剩', '本站', '已减', '已省', '特别推荐',
        '广告', '赞助',
    ]
    for line in lines:
        bad = False
        for pat in skip_pat:
            if re.match(pat, line) or (len(pat) > 3 and pat in line):
                bad = True
                break
        if not bad and len(line) >= 2:
            data["name"] = line
            break

    # === 星级: 从文本中找 "星级为N" 或 "Rating N out of 5" ===
    for line in lines:
        m = re.search(r'星级[为:：]?\s*(\d+)', line)
        if m:
            data["stars"] = int(m.group(1))
            break
    if data["stars"] == 0:
        m = re.search(r'(\d+)\s*out\s*of\s*5', text)
        if m:
            data["stars"] = int(m.group(1))

    # === 地址: 含地址关键词的行 ===
    addr_kw = ['路', '大道', '街', '商圈', '广场', 'CBD', '步行街', '位于']
    for line in lines:
        if line != data["name"] and '星级' not in line and '评论' not in line \
                and any(kw in line for kw in addr_kw) and not re.match(r'^[\d,.RMB￥$€]+$', line):
            data["address"] = line
            break

    # === 评分: 匹配 X.X 分数 ===
    for line in lines:
        # "9.6 非常好", "8.5 棒" 等模式
        m = re.search(r'(10(?:\.0)?|[0-9]\.[0-9])\s*', line)
        if m:
            v = float(m.group(1))
            # 确保不是价格或年份
            if 1.0 <= v <= 10.0 and not re.match(r'^\d{4}\s*$', line):
                data["rating"] = v
                break

    # === 价格 ===
    try:
        pr = card.find_elements(By.XPATH, './/*[@data-element-name="fpc-room-price"]')
        if pr:
            for n in re.findall(r'([\d,]+\.?\d*)', pr[0].text.replace(',', '')):
                v = float(n.replace(',', ''))
                if v > 10:
                    data["min_price"] = v
                    break
    except:
        pass
    if data["min_price"] == 0:
        m = re.findall(r'RMB\s*([\d,]+\.?\d*)', card.get_attribute("outerHTML") or "")
        if m:
            try:
                data["min_price"] = float(m[0].replace(',', ''))
            except:
                pass

    # === URL ===
    try:
        for a in card.find_elements(By.XPATH, ".//a[contains(@href,'hotel')]"):
            h = a.get_attribute("href")
            if h:
                data["url"] = h
                break
    except:
        pass

    return data


def scrape(d):
    print("\n[3/4] 抓取酒店数据...")
    cards = d.find_elements(By.XPATH, "//div[contains(@class,'PropertyCard')]")
    valid = [c for c in cards if c.text.strip() and len(c.text.strip()) > 15]
    print(f"  有效卡片: {len(valid)}/{len(cards)}")

    seen, results = set(), []
    for i, card in enumerate(valid):
        try:
            d2 = extract(card)
            name = d2["name"]
            if is_valid_hotel_name(name) and name not in seen:
                seen.add(name)
                results.append(d2)
            elif not name and d2["min_price"] > 0:
                pass  # 跳过无名酒店
        except:
            continue
        if (i + 1) % 50 == 0:
            print(f"  处理中: {i+1}/{len(valid)}")

    print(f"  提取到 {len(results)} 家酒店")
    return results


def screenshot(d):
    ensure_dir(SCREENSHOT_DIR)
    p = os.path.join(SCREENSHOT_DIR, f"agoda_{CITY}_{datetime.now():%Y%m%d_%H%M%S}.png")
    d.save_screenshot(p)
    print(f"  截图: {p}")


def print_info(d):
    print("\n" + "=" * 50)
    print("筛选条件:")
    print(f"  平台: Agoda | 城市: {CITY}")
    print(f"  入住: {CHECKIN_DATE} | 离店: {CHECKOUT_DATE}")
    print(f"  1晚 {ROOMS}间 {ADULTS}人 | 币种: {CURRENCY}")
    print(f"  URL: {d.current_url}")
    print("=" * 50)


def save_excel(hotels, path):
    print(f"\n[4/4] 保存 Excel: {path}")
    if not hotels:
        return print("  无数据")
    df = pd.DataFrame(hotels)
    df = df.drop_duplicates(subset=["name"], keep="first")
    df = df.sort_values("min_price")
    cmap = {"name": "酒店名称", "address": "地址", "rating": "评分",
            "stars": "星级", "min_price": "最低价(CNY)"}
    if "url" in df.columns:
        cmap["url"] = "详情链接"
    cols = [c for c in cmap if c in df.columns]
    df[cols].rename(columns=cmap).to_excel(path, index=False, engine="openpyxl")
    print(f"  已保存 {len(df)} 条")


def main():
    print("=" * 60)
    print(f"Agoda 酒店抓取 | {CITY} | {datetime.now():%Y-%m-%d %H:%M}")
    print("=" * 60)

    conn = init_db()
    cur = conn.cursor()
    d = None
    try:
        d = setup_driver()
        search_hotels(d)
        sd(8, 12)
        print_info(d)
        screenshot(d)
        scroll_all(d)
        screenshot(d)
        hotels = scrape(d)

        if not hotels:
            print("ERROR: 未抓取到数据")
            with open(os.path.join(BASE_DIR, "page_source_debug.html"), "w", encoding="utf-8") as f:
                f.write(d.page_source)
            return

        for h in hotels:
            cur.execute("INSERT INTO hotels (name,address,rating,stars,min_price,currency,url,scrape_date,city) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (h.get("name",""), h.get("address",""), h.get("rating",0), h.get("stars",0),
                         h.get("min_price",0), CURRENCY, h.get("url",""),
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"), CITY))
        conn.commit()

        save_excel(hotels, EXCEL_PATH)

        valid_prices = [h["min_price"] for h in hotels if h["min_price"] > 0]
        ratings = [h["rating"] for h in hotels if h["rating"] > 0]
        stars_list = [h["stars"] for h in hotels if h["stars"] > 0]

        print("\n" + "=" * 60)
        print("抓取完成！统计:")
        print(f"  酒店: {len(hotels)} 家")
        print(f"  价格: ¥{int(min(valid_prices))} ~ ¥{int(max(valid_prices))}" if valid_prices else "  价格: N/A")
        print(f"  平均: ¥{int(sum(valid_prices)/len(valid_prices))}" if valid_prices else "")
        print(f"  有评分: {len(ratings)}/{len(hotels)}")
        print(f"  有星级: {len(stars_list)}/{len(hotels)}")
        print(f"  数据库: {DB_PATH}")
        print(f"  Excel: {EXCEL_PATH}")
        print(f"  截图: {SCREENSHOT_DIR}")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        if d:
            try:
                ensure_dir(SCREENSHOT_DIR)
                d.save_screenshot(os.path.join(SCREENSHOT_DIR, f"error_{datetime.now():%Y%m%d_%H%M%S}.png"))
            except:
                pass
    finally:
        if d:
            d.quit()
        conn.close()
        print("完成")


if __name__ == "__main__":
    main()
