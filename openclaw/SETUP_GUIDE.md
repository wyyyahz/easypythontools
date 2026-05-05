# Agoda 武汉酒店全量抓取 — 环境搭建与运行指南

## 目录
1. [安装 Python](#1-安装-python)
2. [安装依赖包](#2-安装依赖包)
3. [准备文件](#3-准备文件)
4. [运行基础抓取脚本](#4-运行基础抓取脚本)
5. [进阶：多参数全量抓取](#5-进阶多参数全量抓取)
6. [常见问题](#6-常见问题)

---

## 1. 安装 Python

### 检查是否已安装
打开终端（CMD 或 PowerShell），输入：
```bash
python --version
```

如果显示版本号（如 `Python 3.11.5`），跳到第 2 步。

### 下载安装
1. 打开 https://www.python.org/downloads/
2. 下载 Python 3.11 或更高版本
3. 运行安装程序
4. **务必勾选** ☑ `Add Python to PATH`
5. 点 Install Now 完成安装

### 验证安装
```bash
python --version
```
输出示例：`Python 3.11.5`

---

## 2. 安装依赖包

### 设置国内镜像（加速下载）
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 安装 Playwright（推荐，自带浏览器）
```bash
pip install playwright
playwright install chromium
```

如果 `playwright install chromium` 下载慢，也可以只用 `requests`（不需要浏览器）：

```bash
pip install requests openpyxl
```

> **Playwright 方案**：自带浏览器，可以实时捕获最新的 API 请求体
> **Requests 方案**：直接用我们已捕获的 API 模板，不需要浏览器

### 全部依赖（一步安装）
```bash
pip install requests openpyxl playwright
playwright install chromium
```

---

## 3. 准备文件

在工作目录下放好这些文件：

| 文件 | 说明 | 来源 |
|------|------|------|
| `api_body.json` | API 请求体模板（已捕获） | 本目录已有 |
| `agoda_wuhan_hotels.xlsx` | 已抓取的 2,502 家酒店 | 本目录已有 |
| `scraper.py` | 抓取脚本（见下方） | 自己创建 |

### 创建抓取脚本

新建文件 `scraper.py`，复制以下代码：

```python
"""
Agoda 武汉酒店数据抓取脚本
使用方法：python scraper.py
"""
import json
import time
import requests
from openpyxl import Workbook

# ========== 配置 ==========
TEMPLATE_FILE = 'api_body.json'     # API 请求体模板
OUTPUT_FILE = 'agoda_wuhan_7k_hotels.xlsx'  # 输出 Excel

HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'AG-LANGUAGE-LOCALE': 'zh-cn',
    'AG-CID': '-1',
    'AG-PAGE-TYPE-ID': '103',
    'AG-REQUEST-ATTEMPT': '1',
}

API_URL = 'https://www.agoda.cn/graphql/search'

# 不同排序方式（每种返回不同的酒店子集）
SORT_CONFIGS = [
    {'sortField': 'Ranking', 'sortOrder': 'Desc', 'label': '默认排序'},
    {'sortField': 'Price', 'sortOrder': 'Asc', 'label': '价格从低到高'},
    {'sortField': 'Price', 'sortOrder': 'Desc', 'label': '价格从高到低'},
    {'sortField': 'ReviewScore', 'sortOrder': 'Desc', 'label': '评分从高到低'},
    {'sortField': 'StarRating', 'sortOrder': 'Desc', 'label': '星级从高到低'},
]

# 不同日期（更多日期 = 更多酒店）
DATE_CONFIGS = [
    ('2026-06-05', '2026-06-06'),
    ('2026-06-12', '2026-06-13'),
    ('2026-07-05', '2026-07-06'),
    ('2026-08-05', '2026-08-06'),
    ('2026-09-05', '2026-09-06'),
    ('2026-10-02', '2026-10-03'),
    ('2026-11-06', '2026-11-07'),
    ('2026-12-04', '2026-12-05'),
]


# ========== 核心函数 ==========

def load_template():
    """加载 API 请求体模板"""
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        return json.loads(f.read())


def scrape_hotels(sort_field, sort_order, check_in, check_out, label):
    """
    用指定的排序和日期抓取酒店数据
    
    参数:
        sort_field: 排序字段 (Ranking/Price/ReviewScore/StarRating)
        sort_order: 排序方向 (Asc/Desc)
        check_in: 入住日期 (YYYY-MM-DD)
        check_out: 退房日期 (YYYY-MM-DD)
        label: 日志标签
    
    返回:
        list: 酒店列表，每项包含 name/rating/price
    """
    template = load_template()
    
    # 设置排序
    template['variables']['CitySearchRequest']['searchRequest']['searchCriteria']['sorting'] = {
        'sortField': sort_field,
        'sortOrder': sort_order
    }
    
    # 设置日期
    template['variables']['CitySearchRequest']['searchRequest']['searchCriteria']['checkInDate'] = f'{check_in}T00:00:00.000Z'
    template['variables']['CitySearchRequest']['searchRequest']['searchCriteria']['localCheckInDate'] = check_in
    
    # 移除价格过滤（不加限制）
    template['variables']['CitySearchRequest']['searchRequest']['filterRequest']['rangeFilters'] = []
    
    hotels = []
    seen_names = set()
    page_token = None
    page_num = 1
    
    while page_num <= 150:
        # 复制模板并设置分页
        request_body = json.loads(json.dumps(template))
        request_body['variables']['CitySearchRequest']['searchRequest']['page'] = {
            'pageSize': 50,
            'pageNumber': page_num
        }
        if page_token:
            request_body['variables']['CitySearchRequest']['searchRequest']['page']['pageToken'] = page_token
        
        try:
            # 发送请求
            response = requests.post(
                API_URL,
                json=request_body,
                headers=HEADERS,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f'  [{label}] 请求失败: HTTP {response.status_code}')
                break
            
            data = response.json()
            properties = data.get('data', {}).get('citySearch', {}).get('properties', [])
            page_token = data.get('data', {}).get('citySearch', {}).get('searchEnrichment', {}).get('pageToken')
            
            if not properties:
                print(f'  [{label}] 第 {page_num} 页无数据')
                break
            
            # 提取酒店信息
            for prop in properties:
                info = prop.get('content', {}).get('informationSummary', {})
                name = info.get('localeName') or info.get('defaultName') or ''
                
                if not name or name in seen_names:
                    continue
                seen_names.add(name)
                
                # 提取价格
                price = None
                try:
                    for offer in (prop.get('pricing', {}).get('offers', [])):
                        for room_offer in (offer.get('roomOffers', [])):
                            for pricing in (room_offer.get('room', {}).get('pricing', [])):
                                display_price = pricing.get('price', {}).get('perBook', {}).get('inclusive', {}).get('display')
                                if display_price:
                                    price = round(display_price)
                                    break
                            if price:
                                break
                        if price:
                            break
                except:
                    pass
                
                # 提取评分
                rating = None
                try:
                    rating = prop.get('content', {}).get('reviews', {}).get('cumulative', {}).get('score')
                except:
                    pass
                
                # 提取位置
                location = ''
                addr = info.get('address') or {}
                if addr.get('area'):
                    location = addr['area'].get('name', '')
                if not location and addr.get('city'):
                    location = addr['city'].get('name', '')
                
                hotels.append({
                    'name': name,
                    'rating': rating,
                    'price': price,
                    'location': location
                })
            
            # 没有下一页 token 则退出
            if not page_token:
                break
            
            page_num += 1
            time.sleep(0.15)  # 频率控制，不要太快
            
        except requests.exceptions.Timeout:
            print(f'  [{label}] 第 {page_num} 页超时')
            if page_num > 2:
                break
            page_num += 1
            time.sleep(2)
            
        except Exception as e:
            print(f'  [{label}] 第 {page_num} 页错误: {e}')
            if page_num > 2:
                break
            page_num += 1
            time.sleep(2)
    
    return hotels


def save_to_excel(all_hotels, filename):
    """保存酒店数据到 Excel 文件"""
    
    # 按价格排序
    sorted_hotels = sorted(
        all_hotels,
        key=lambda x: (x['price'] or 999999) if x['price'] is not None else 999999
    )
    
    wb = Workbook()
    ws = wb.active
    ws.title = '武汉酒店列表'
    
    # 写表头
    headers = ['序号', '酒店名称', '用户评分', '最低价(CNY)', '区域位置']
    for i, header in enumerate(headers, 1):
        ws.cell(row=1, column=i, value=header)
    
    # 写数据
    for idx, hotel in enumerate(sorted_hotels, 1):
        row = idx + 1
        ws.cell(row=row, column=1, value=idx)
        ws.cell(row=row, column=2, value=hotel['name'])
        ws.cell(row=row, column=3, value=hotel['rating'])
        ws.cell(row=row, column=4, value=hotel['price'])
        ws.cell(row=row, column=5, value=hotel.get('location', ''))
    
    # 设置列宽
    ws.column_dimensions['A'].width = 6
    ws.column_dimensions['B'].width = 42
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 24
    
    # 冻结首行
    ws.freeze_panes = 'A2'
    
    wb.save(filename)
    print(f'  ✓ 已保存到 {filename}')


# ========== 主流程 ==========

def main():
    print('=' * 50)
    print('  Agoda 武汉酒店数据抓取')
    print('=' * 50)
    
    all_hotels = []
    seen_names = set()
    
    # 1. 遍历排序方式
    for sort_config in SORT_CONFIGS:
        sf = sort_config['sortField']
        so = sort_config['sortOrder']
        label = sort_config['label']
        
        print(f'\n▶ 排序方式: {label}')
        hotels = scrape_hotels(sf, so, '2026-06-05', '2026-06-06', label)
        
        new_count = 0
        for h in hotels:
            if h['name'] not in seen_names:
                seen_names.add(h['name'])
                all_hotels.append(h)
                new_count += 1
        
        print(f'  → 新增 {new_count} 家，累计 {len(all_hotels)} 家')
        time.sleep(0.5)
    
    # 2. 遍历不同日期（用默认排序）
    print(f'\n▶ 尝试不同日期...')
    for check_in, check_out in DATE_CONFIGS:
        label = f'{check_in} 至 {check_out}'
        hotels = scrape_hotels('Ranking', 'Desc', check_in, check_out, label)
        
        new_count = 0
        for h in hotels:
            if h['name'] not in seen_names:
                seen_names.add(h['name'])
                all_hotels.append(h)
                new_count += 1
        
        print(f'  → {label}: 新增 {new_count} 家，累计 {len(all_hotels)} 家')
        time.sleep(0.5)
    
    # 3. 输出结果
    print(f'\n{"=" * 50}')
    print(f'  抓取完成！共 {len(all_hotels)} 家酒店')
    print(f'{"=" * 50}')
    
    if all_hotels:
        save_to_excel(all_hotels, OUTPUT_FILE)
        
        # 统计数据
        prices = [h['price'] for h in all_hotels if h['price'] is not None]
        ratings = [h['rating'] for h in all_hotels if h['rating'] is not None]
        
        if prices:
            print(f'\n  价格区间: RMB {min(prices):,} ~ RMB {max(prices):,}')
            print(f'  平均价格: RMB {sum(prices) / len(prices):.0f}')
        if ratings:
            high_rated = sum(1 for r in ratings if r >= 9)
            print(f'  评分区间: {min(ratings):.1f} ~ {max(ratings):.1f}')
            print(f'  评分 ≥ 9.0: {high_rated}/{len(ratings)} ({high_rated*100//len(ratings)}%)')


if __name__ == '__main__':
    main()
```

---

## 4. 运行基础抓取脚本

### 第一步：放好文件
把 `api_body.json` 和 `scraper.py` 放在**同一个文件夹**里。

### 第二步：运行
```bash
cd 你的文件夹路径
python scraper.py
```

### 第三步：等待完成
- 脚本会自动遍历 5 种排序 + 8 个日期 = 13 种组合
- 每种组合约需 10~30 秒
- 总耗时约 3~5 分钟
- 完成后生成 `agoda_wuhan_7k_hotels.xlsx`

### 预期结果
```
首次运行（5 种排序，1 个日期）：约 2,000~2,500 家
完整运行（5 种排序 + 8 个日期）：约 2,500~3,000 家
```

---

## 5. 进阶：多参数全量抓取

如果基础脚本跑完后还需要更多酒店，可以修改 `scraper.py` 增加配置：

### 添加更多日期
在 `DATE_CONFIGS` 里添加更多日期组合：
```python
DATE_CONFIGS = [
    ('2026-06-05', '2026-06-06'),
    ('2026-06-12', '2026-06-13'),
    ('2026-06-19', '2026-06-20'),
    ('2026-06-26', '2026-06-27'),
    ('2026-07-03', '2026-07-04'),
    # ... 继续添加
    ('2026-12-18', '2026-12-19'),
]
```

### 添加不同住客配置
修改 `scrape_hotels` 调用时的参数：
```python
# 1 位成人
hotels = scrape_hotels('Ranking', 'Desc', '2026-06-05', '2026-06-06', '1位成人')

# 修改模板中的客人数量：
template['variables']['CitySearchRequest']['searchRequest']['searchCriteria']['adults'] = 1
```

### 多实例并行（最有效）
在**多台电脑**上同时运行此脚本，每台用不同的参数组合。结果合并去重即可。

---

## 6. 常见问题

### Q1: `ModuleNotFoundError: No module named 'requests'`
```bash
pip install requests
```

### Q2: `ModuleNotFoundError: No module named 'openpyxl'`
```bash
pip install openpyxl
```

### Q3: 请求返回 502 Bad Gateway
API 会话可能过期了。重新捕获 `api_body.json`：

```python
# capture_fresh_body.py
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        api_body = None
        async def on_request(request):
            nonlocal api_body
            if 'graphql/search' in request.url:
                api_body = request.post_data
        
        page.on('request', on_request)
        
        await page.goto('https://www.agoda.cn/search?city=5818'
                       '&checkin=2026-06-05&checkout=2026-06-06'
                       '&los=1&rooms=1&adults=2&children=0&currency=CNY')
        await page.wait_for_timeout(5000)
        
        if api_body:
            with open('api_body.json', 'w', encoding='utf-8') as f:
                f.write(api_body)
            print(f'已捕获 API 请求体 ({len(api_body)} 字节)')
        else:
            print('未捕获到 API 请求')
        
        await browser.close()

asyncio.run(main())
```

### Q4: 请求返回 400 无法解析
说明 API 请求体结构不对。用上面的 `capture_fresh_body.py` 重新捕获即可。

### Q5: 结果不够 7,214 家
这是正常的。单次运行只能拿到约 2,500~3,000 家。要拿全需要：
1. 在不同时间多跑几次（每次 session 不同，结果不同）
2. 用多台电脑同时跑
3. 合并所有结果去重

---

## 关键提醒

1. **频率控制** — 脚本已内置 150ms 延迟，不要改小
2. **IP 限制** — 如果频繁请求被封，换个 IP 或用代理
3. **请求体会过期** — 如果跑了几天后报错，重新捕获 `api_body.json`
4. **数据去重** — 脚本已自动按酒店名称去重，多次运行的结果可以直接合并
