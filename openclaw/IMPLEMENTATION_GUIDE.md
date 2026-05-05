# Agoda 武汉酒店 7,214 家全量抓取 — 自建实现方案

## 方案概述

核心思路：**多实例 + 多参数 + 代理轮换**。每个独立的 Chrome 实例 = 独立的 Agoda session = 不同的酒店子集。

## 环境要求

```bash
# 必须能访问 GitHub（下载 ChromeDriver）
pip install selenium webdriver-manager undetected-chromedriver requests

# 或者用 Playwright（自带浏览器，推荐）
pip install playwright
playwright install chromium

# 代理支持
pip install selenium-wire
```

## 方案一：多排序 + 多日期 + 代理轮换（推荐）

### 步骤

#### 1. 获取完整 API 请求体模板

这是我们最关键的发现。用以下方法捕获：

```python
# capture_api_body.py
import asyncio, json
from playwright.async_api import async_playwright

async def capture_body():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 拦截 API 请求
        api_body = None
        async def intercept_request(request):
            nonlocal api_body
            if 'graphql/search' in request.url:
                api_body = request.post_data
        
        page.on('request', intercept_request)
        
        await page.goto('https://www.agoda.cn/search?city=5818'
                       '&checkin=2026-06-05&checkout=2026-06-06'
                       '&los=1&rooms=1&adults=2&children=0&currency=CNY')
        await page.wait_for_timeout(5000)
        
        if api_body:
            with open('api_template.json', 'w', encoding='utf-8') as f:
                f.write(api_body)
            print(f'Captured: {len(api_body)} bytes')
        
        await browser.close()

asyncio.run(capture_body())
```

#### 2. 用模板进行分页请求

```python
# paginate.py
import json, requests, time

HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

def get_all_hotels(template_path, cookie_str):
    """使用模板 + cookie 获取该 session 下所有酒店"""
    with open(template_path, 'r') as f:
        template = json.loads(f.read())
    
    # 移除价格过滤
    template['variables']['CitySearchRequest']['searchRequest']['filterRequest']['rangeFilters'] = []
    
    all_hotels = []
    seen = set()
    token = None
    page = 1
    
    cookies = {}
    for c in cookie_str.split('; '):
        if '=' in c:
            k, v = c.split('=', 1)
            cookies[k] = v
    
    while page <= 150:
        req = json.loads(json.dumps(template))
        req['variables']['CitySearchRequest']['searchRequest']['page'] = {
            'pageSize': 50, 'pageNumber': page
        }
        if token:
            req['variables']['CitySearchRequest']['searchRequest']['page']['pageToken'] = token
        
        resp = requests.post(
            'https://www.agoda.cn/graphql/search',
            json=req, headers=HEADERS, cookies=cookies, timeout=30
        )
        
        if resp.status_code != 200:
            break
        
        data = resp.json()
        props = data.get('data', {}).get('citySearch', {}).get('properties', [])
        token = data.get('data', {}).get('citySearch', {}).get('searchEnrichment', {}).get('pageToken')
        
        if not props:
            break
        
        for p in props:
            info = p.get('content', {}).get('informationSummary', {})
            name = info.get('localeName') or info.get('defaultName') or ''
            if not name or name in seen:
                continue
            seen.add(name)
            
            # 提取价格
            price = None
            try:
                for o in (p.get('pricing', {}).get('offers', [])):
                    for r in (o.get('roomOffers', [])):
                        for pr in (r.get('room', {}).get('pricing', [])):
                            d = pr.get('price', {}).get('perBook', {}).get('inclusive', {}).get('display')
                            if d:
                                price = round(d)
                                break
                        if price: break
                    if price: break
            except: pass
            
            # 提取评分
            rating = None
            try:
                rating = p.get('content', {}).get('reviews', {}).get('cumulative', {}).get('score')
            except: pass
            
            # 提取位置
            location = ''
            addr = info.get('address') or {}
            if addr.get('area'):
                location = addr['area'].get('name', '')
            
            all_hotels.append({
                'name': name,
                'rating': rating,
                'price': price,
                'location': location
            })
        
        if not token:
            break
        
        page += 1
        time.sleep(0.15)  # 频率控制
    
    return all_hotels
```

#### 3. 多实例并行抓取（核心）

```python
# distributed_scraper.py
"""
在 10+ 台机器（或 Docker 容器）上运行以下流程：

每个实例：
1. 启动全新 Chrome（新 user-data-dir）
2. 获取 Agoda session cookie
3. 用不同的排序参数抓取
4. 保存结果到共享存储

参数组合（每个实例用一种）：
"""

PARAM_COMBINATIONS = [
    # 排序方式
    {'sortField': 'Ranking', 'sortOrder': 'Desc'},
    {'sortField': 'Price', 'sortOrder': 'Asc'},
    {'sortField': 'Price', 'sortOrder': 'Desc'},
    {'sortField': 'ReviewScore', 'sortOrder': 'Desc'},
    {'sortField': 'StarRating', 'sortOrder': 'Desc'},
    
    # 入住日期（20+ 个日期）
    {'checkIn': '2026-06-05', 'checkOut': '2026-06-06'},
    {'checkIn': '2026-06-12', 'checkOut': '2026-06-13'},
    # ... 每个月的第一个周末
    
    # 住客配置
    {'rooms': 1, 'adults': 1, 'children': 0},
    {'rooms': 1, 'adults': 2, 'children': 0},
    {'rooms': 1, 'adults': 3, 'children': 0},
    {'rooms': 2, 'adults': 2, 'children': 0},
    
    # 住宿类型
    {'productType': 1},  # 酒店
    {'productType': 2},  # 民宿公寓
]

# 每个组合约产出 300~500 家酒店
# 20 个实例 × 500 家 = 10,000 家（覆盖 7,214 绰绰有余）
```

#### 4. Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11

RUN pip install playwright && playwright install chromium

COPY scraper.py /app/
WORKDIR /app

# 每个容器用不同的 INSTANCE_ID（0~19）
ENV INSTANCE_ID=0
CMD ["python", "scraper.py"]
```

```yaml
# docker-compose.yml
version: '3'
services:
  scraper-{0..19}:
    build: .
    environment:
      - INSTANCE_ID={i}
      - PROXY=http://proxy-{i}:8080  # 每个实例不同代理
    volumes:
      - ./output:/app/output
```

## 方案二：Property ID 批量探测

### 原理
Agoda 的酒店 ID 是顺序增长的。从已知 ID 范围扫描，用 `propertySummary` API 验证归属城市。

### 已知 ID 范围（从已抓取的 2,502 家中提取）
```
最小 ID: ~2,600,000
最大 ID: ~260,000,000
```

### 实现

```python
# id_scanner.py
"""
扫描 property ID 范围，找到所有武汉酒店。
"""
import requests, json, time

# 用已知的武汉酒店 ID 训练一个范围模型
KNOWN_IDS = [26069441, ...]  # 从已有数据提取

# 在范围内分批扫描
BATCH_SIZE = 100
START_ID = 1000000
END_ID = 300000000
STEP = 50000  # 每隔 5 万扫一个点，找到密度区域后密集扫描

def check_property(property_id):
    """检查某个 ID 是否属于武汉酒店"""
    url = f'https://www.agoda.cn/api/gw/property/{property_id}/summary'
    # 或使用 graphql/propertySummary 端点
    resp = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0...',
        'Referer': 'https://www.agoda.cn/'
    })
    if resp.status_code == 200:
        data = resp.json()
        city_id = data.get('cityId') or data.get('address', {}).get('cityId')
        return city_id == 5818  # 武汉
    return False
```

## 方案三：直接调用 Booking Holdings 的公开 API

Agoda 隶属于 Booking Holdings。Booking 有面向合作伙伴的 API：
- https://developers.booking.com/
- 需要申请 API key
- 可以查询酒店列表、价格、可用性
- 是最正规的获取全量数据的方式

## 时间预估

| 方案 | 准备时间 | 抓取时间 | 难度 |
|------|---------|---------|------|
| 多实例 Docker | 1-2 天 | 30 分钟 | ⭐⭐⭐ |
| Property ID 扫描 | 1 天 | 2-5 小时 | ⭐⭐⭐⭐ |
| Booking API | 1-2 周（申请） | 即时 | ⭐⭐ |

## 关键经验教训

1. **千万不要用单机爬 Agoda** — 会被封 IP
2. **每个实例必须用独立 user-data-dir** — 否则 session 冲突
3. **排序参数是最有效的"换数据"手段** — 比换日期有效 100 倍
4. **API 请求体必须从浏览器实时捕获** — 不能手动构造（约 30KB，结构极复杂）
5. **频率控制很重要** — 建议每次请求间隔 150ms 以上
6. **PageToken 机制** — 每个 session 约 30~50 页后 Token 失效，需要换 session

## 最终输出格式

```python
import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = '武汉酒店列表'

# 写入表头
headers = ['序号', '酒店名称', '用户评分', '最低价(CNY)', '区域位置']
for i, h in enumerate(headers, 1):
    ws.cell(row=1, column=i, value=h)

# 按价格排序写入
hotels_sorted = sorted(all_hotels, key=lambda x: x['price'] or 99999)
for idx, hotel in enumerate(hotels_sorted, 1):
    ws.cell(row=idx+1, column=1, value=idx)
    ws.cell(row=idx+1, column=2, value=hotel['name'])
    ws.cell(row=idx+1, column=3, value=hotel['rating'])
    ws.cell(row=idx+1, column=4, value=hotel['price'])
    ws.cell(row=idx+1, column=5, value=hotel['location'])

wb.save('agoda_wuhan_7214_hotels.xlsx')
```

---

以上方案需要**至少一台能访问 GitHub 的服务器**来安装依赖。这个环境网络受限做不到，但你那边应该可以。加油 💪
