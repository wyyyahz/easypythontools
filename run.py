#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agoda 酒店数据全量抓取 - 优化版 (Selenium DOM版)

核心策略：
1. 按价格区间分段搜索,每个区间滚动加载全部酒店
2. 从 DOM 提取数据,使用 data-propertyid 去重
3. 合并所有区间结果

对比旧版改进:
- 使用 Agoda 原生价格分段,从121个减少到26个
- 每个区间充分滚动加载(直到稳定)
- 正确的 CSS 选择器和 data-propertyid 提取
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import time
import os
from datetime import datetime, timedelta

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def extract_hotels_from_dom(driver):
    """从 DOM 提取酒店数据,返回 JSON 字符串"""
    return driver.execute_script("""
    // 只取顶级容器(propertyContainer),避免嵌套子元素重复
    const containers = document.querySelectorAll('[class*="PropertyCard__propertyContainer"]');
    const results = [];
    const seen = new Set();

    containers.forEach(container => {
        const propId = container.getAttribute('data-propertyid') || '';
        if (!propId) return;
        // 全局去重
        if (seen.has(propId)) return;
        seen.add(propId);

        const text = container.textContent;
        const html = container.innerHTML;

        // 酒店名称
        let name = '';
        const nameEl = container.querySelector('[class*=hotelName] h3');
        if (nameEl) name = nameEl.textContent.trim();
        if (!name) name = container.querySelector('[class*=hotelName]')?.textContent?.trim() || '';
        if (!name || name.length < 2) return;

        // Agoda评分
        let rating = null;
        const ratingEl = container.querySelector('[class*=reviewScoreAndText]');
        if (ratingEl) {
            const m = ratingEl.textContent.trim().match(/(\\d+\\.?\\d*)/);
            if (m) rating = parseFloat(m[1]);
        }

        // 评价数
        let reviewCount = 0;
        const countEl = container.querySelector('[class*=reviewScoreElem]');
        if (countEl) {
            const m = countEl.textContent.match(/(\\d+)/);
            if (m) reviewCount = parseInt(m[1]);
        }

        // 星级
        let starRating = null;
        const starText = text.match(/(\\d+)\\s*星/);
        if (starText) starRating = parseInt(starText[1]);

        // 最低价 - 找 RMB 后的数字
        let price = null;
        // 在 footer 区域找价格
        const footer = container.querySelector('[class*=PropertyCard__footer]');
        const footerText = footer ? footer.textContent : text;
        const priceMatch = footerText.match(/RMB\\s*(\\d{1,3}(?:,\\d{3})*|\\d{2,5})/);
        if (priceMatch) {
            price = parseInt(priceMatch[1].replace(/,/g, ''));
        }

        // 区域
        let area = '';
        const areaEl = container.querySelector('[class*=BadgeStyled]');
        if (areaEl) area = areaEl.textContent.trim();

        results.push({
            '酒店ID': propId,
            '酒店名称': name,
            '区域': area,
            'Agoda评分': rating,
            '评价数': reviewCount,
            '星级': starRating,
            '最低价(CNY)': price,
            '可订状态': ''
        });
    });
    return JSON.stringify(results);
    """)


def scroll_to_load_all(driver, max_scrolls=50, wait=2.0):
    """滚动页面直到所有酒店加载完成,返回总卡片数"""
    prev_count = 0
    stable_rounds = 0

    for s in range(max_scrolls):
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(wait)

        count = driver.execute_script(
            'return document.querySelectorAll(\'[class*="PropertyCard__propertyContainer"]\').length'
        )
        if count != prev_count:
            prev_count = count
            stable_rounds = 0
        else:
            stable_rounds += 1
            if stable_rounds >= 5:
                break
    return prev_count


def log(msg):
    print(msg, flush=True)


def run(city_id=5818, city_name='武汉',
        checkin='2026-06-01', los=1, adults=2):
    checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
    checkout = (checkin_date + timedelta(days=los)).strftime('%Y-%m-%d')

    # Agoda 原生价格分段(与页面筛选一致)
    brackets = [
        (0, 20), (20, 30), (30, 40), (40, 50),
        (50, 70), (70, 80), (80, 100),
        (100, 120), (120, 150), (150, 180), (180, 220), (220, 280), (280, 340), (340, 410),
        (410, 510), (510, 620), (620, 770), (770, 940),
        (940, 1160), (1160, 1420), (1420, 1740), (1740, 2140), (2140, 2630), (2630, 3230),
        (3230, 5000), (5000, 99999),
    ]

    total_brackets = len(brackets)
    log(f'\n{"="*60}')
    log(f'  Agoda {city_name} 酒店全量抓取 v2 (优化版)')
    log(f'  入住: {checkin}, {los}晚, {adults}位成人')
    log(f'  价格分段: {total_brackets} (Agoda原生区间)')
    log(f'{"="*60}')

    # 启动浏览器
    log('  启动浏览器...')
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
    log('  浏览器就绪')

    all_hotels = []
    seen_ids = set()
    start_ts = time.time()

    try:
        for idx, (price_from, price_to) in enumerate(brackets, 1):
            pf = int(price_from)
            pt = int(price_to) if price_to < 99999 else 99999

            url = (f'https://www.agoda.cn/search?city={city_id}'
                   f'&checkin={checkin}&checkout={checkout}'
                   f'&los={los}&rooms=1&adults={adults}&children=0&currency=CNY'
                   f'&pf={pf}&pt={pt}')

            driver.get(url)
            time.sleep(6)

            # 滚动加载全部酒店
            card_count = scroll_to_load_all(driver, max_scrolls=40, wait=2.5)

            # 提取酒店
            result = extract_hotels_from_dom(driver)
            bracket_hotels = json.loads(result) if result else []

            new_count = 0
            for h in bracket_hotels:
                hid = h['酒店ID']
                if hid not in seen_ids:
                    seen_ids.add(hid)
                    all_hotels.append(h)
                    new_count += 1

            elapsed = time.time() - start_ts
            avg = elapsed / idx
            remaining = avg * (total_brackets - idx)
            eta = time.strftime('%M:%S', time.gmtime(remaining))
            log(f'  [{idx:>2}/{total_brackets}] ¥{pf:>4}-{pt:<5}: 页={card_count:>3} +新={new_count:>3} 累计={len(all_hotels):>4} ETA:{eta}')

    finally:
        driver.quit()

    elapsed_total = time.time() - start_ts
    log(f'\n{"="*60}')
    if all_hotels:
        df = pd.DataFrame(all_hotels)
        if '最低价(CNY)' in df.columns:
            df = df.sort_values('最低价(CNY)', na_position='last').reset_index(drop=True)

        filename = f'Agoda_{city_name}_酒店_{checkin}_最终.xlsx'
        df.to_excel(filename, index=False, engine='openpyxl')

        log(f'  完成! 共 {len(df)} 家酒店, 用时 {elapsed_total:.0f}秒')
        log(f'  保存到: {filename}')

        df_score = df[df['Agoda评分'].notna()]
        df_price = df[df['最低价(CNY)'].notna()]
        if len(df_score) > 0:
            log(f'  平均评分: {df_score["Agoda评分"].mean():.1f} (基于{len(df_score)}家)')
        if len(df_price) > 0:
            prices = df_price['最低价(CNY)']
            log(f'  价格: {prices.min():.0f} ~ {prices.max():.0f}, 均价 {prices.mean():.0f}')

        if len(df_score) > 0:
            log(f'\n  评分前20名:')
            for _, row in df.nlargest(20, 'Agoda评分').iterrows():
                name_s = row['酒店名称'][:30]
                ps = f'{row["最低价(CNY)"]:.0f}' if row['最低价(CNY)'] else '-'
                ss = f'{row["Agoda评分"]:.1f}' if row['Agoda评分'] else '-'
                log(f'    {row["酒店ID"][:10]:>10s} | {name_s} | {ss} | {ps}')

        json_name = f'Agoda_{city_name}_酒店_{checkin}.json'
        with open(json_name, 'w', encoding='utf-8') as f:
            json.dump({'count': len(df), 'hotels': all_hotels}, f, ensure_ascii=False, indent=2)
        log(f'  JSON: {json_name}')
    else:
        log('  未抓取到数据')
    log(f'{"="*60}')


if __name__ == '__main__':
    run(
        city_id=5818,
        city_name='武汉',
        checkin='2026-06-05',
        los=1,
        adults=2
    )
