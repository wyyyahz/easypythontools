# Agoda 武汉酒店全量数据抓取 — 技术交接文档

## 📋 当前成果

- **已抓取 2,502 家酒店**（占 Agoda 显示的 7,214 家的 35%）
- 输出文件：`agoda_wuhan_hotels.xlsx`、`agoda_wuhan.db`、`hotels_all.json`
- 价格范围：RMB 10 ~ 2,477
- 评分范围：2.0 ~ 10.0

## 🔧 技术栈与工具链

### 核心技术
1. **API 端点**: `https://www.agoda.cn/graphql/search`
   - Method: POST
   - Content-Type: application/json
   
2. **请求头（必须）**:
   ```
   AG-LANGUAGE-LOCALE: zh-cn
   AG-CID: -1
   AG-PAGE-TYPE-ID: 103
   AG-REQUEST-ATTEMPT: 1
   Content-Type: application/json
   User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
   ```

3. **认证方式**: Session cookie (`agoda.user.03` + `agoda.prius` + `ds` cookie)
   - Cookie 是 HTTP-only，无法通过 JS 读取或清除
   - 所有标签页共享同一個 `ds` session

### 获取完整请求体（关键步骤）
API 请求体约 30KB，结构极其复杂。无法手动构造——必须从浏览器加载页面时捕获。

**捕获方法（Chrome DevTools Protocol）**:
```python
# 1. 启动全新 Chrome 实例（必须用新 user-data-dir，零 cookie）
chrome --remote-debugging-port=18901 --user-data-dir=D:\temp_chrome

# 2. 通过 CDP 创建新标签页
# 3. 启用 Network 域
# 4. 导航到搜索 URL
# 5. 监听 Network.requestWillBeSent 事件
# 6. 捕获包含 graphql/search 的 postData
```

**成功使用的 Python 代码**（见 `cdp_capture2.py`）:
- 连接浏览器 WebSocket
- 创建 target → 导航 → 捕获请求体
- 保存到 `api_body.json`（约 30KB）

### 请求体关键字段
```json
{
  "operationName": "citySearch",
  "variables": {
    "CitySearchRequest": {
      "cityId": 5818,  // 武汉
      "searchRequest": {
        "searchCriteria": {
          "checkInDate": "2026-06-05T00:00:00.000Z",
          "los": 1, "rooms": 1, "adults": 2, "children": 0,
          "currency": "CNY",
          "sorting": {"sortField": "Ranking", "sortOrder": "Desc"},
          // ... 约 50+ 个字段
        },
        "searchContext": {
          "locale": "zh-cn", "cid": -1, "origin": "CN",
          // ... 会话标识
        },
        "filterRequest": {
          "rangeFilters": [{"filterKey": "Price", "ranges": [{"from": 0, "to": 50.49}]}]
          // ↑ 价格区间过滤（可选）
        },
        "page": {"pageSize": 50, "pageNumber": 1}
      }
    },
    "ContentSummaryRequest": { /* 必须包含此字段 */ }
  }
}
```

### 分页逻辑
```python
while page <= 150:
    req = 复制模板
    req.page = {pageSize: 50, pageNumber: page}
    if 有 pageToken: req.page.pageToken = pageToken
    
    resp = POST(url, json=req, headers=headers)
    data = resp.json()
    
    hotels = data.data.citySearch.properties  # 酒店列表
    next_token = data.data.citySearch.searchEnrichment.pageToken  # 下一页 token
    
    if not next_token: break  # 无更多数据
    page += 1
```

**限制**: 每个会话约 30~50 页（约 300~500 家酒店）后 token 失效

### 酒店数据提取
每个 property 对象包含:
```python
info = property.content.informationSummary
name = info.localeName          # 中文名
address = info.address.area.name  # 区域
reviews = property.content.reviews.cumulative
rating = reviews.score           # 评分
pricing = property.pricing
# 价格从 cheapest room offer 提取:
price = pricing.offers[0].roomOffers[0].room.pricing[0].price.perBook.inclusive.display
```

## 🎯 已尝试的参数组合（93 种）

| 策略 | 参数 | 结果 | 新增 |
|------|------|------|------|
| 默认排序 | sortField=Ranking | 570 家 | 570 |
| 价格升序 | sortField=Price, sortOrder=Asc | +1,591 | 1,591 |
| 价格降序 | sortField=Price, sortOrder=Desc | +260 | 1,851 |
| 评分降序 | sortField=ReviewScore | 0 | 1,851 |
| 距离升序 | sortField=Distance | 0 | 1,851 |
| 星级降序 | sortField=StarRating | +11 | 1,862 |
| 20 个商圈过滤 | idsFilters=[{type:HotelAreaId, id:X}] | 0 新增 | 1,862 |
| 4 个不同日期 | 6/12, 7/5, 8/5, 9/5 | +59 | 2,491 |
| 60 个日期×房型组合 | 20 日期 × 3 房型 | +11 | **2,502** |

## 💡 获取剩余 4,712 家的建议

### 问题分析
剩余酒店不在搜索 API 的返回范围内。可能是：
1. **季节性下架** — 特定日期不可订的酒店不显示
2. **不同 API 通道** — `graphql/propertySummary`、`graphql/npc` 等其他端点
3. **分类差异** — 民宿/公寓/旅馆使用不同的 productType

### 推荐方案

#### 方案 A：Property ID 扫描（推荐）
利用 Agoda 的 `graphql/npc` 或 `graphql/propertySummary` 端点，按 property ID 逐个查询。

1. 获取已知酒店 IDs 的范围（从已有 2,502 家中提取）
2. 在 ID 范围内批量扫描，过滤 cityId=5818 的酒店
3. 每个有效 ID 返回详细信息
4. 预计耗时：扫描 100 万个 ID 约需 10 小时（单线程）

#### 方案 B：全量目录爬取
使用 Scrapy + Playwright 爬取 Agoda 武汉酒店目录页：
1. 从城市页 `https://www.agoda.cn/zh-cn/city/wuhan-cn.html` 出发
2. 遍历所有区域/价格/星级筛选项组合
3. 抓取每个组合下的酒店列表
4. 合并去重

#### 方案 C：Selenium Grid + 多 IP 轮换
分布式部署：
1. 准备 10+ 个代理 IP
2. 每个 IP 启动独立 Chrome 实例（新 user-data-dir）
3. 每个实例获取独立 `ds` session
4. 每个 session 可获取 ~500 家
5. 16 个 session 即可覆盖 7,214 家

### 环境准备
```bash
# 必须能够访问 GitHub（下载 ChromeDriver）
pip install selenium webdriver-manager undetected-chromedriver

# 或直接使用 Playwright（自带浏览器）
pip install playwright
playwright install chromium

# 代理池（可选）
pip install scrapy scrapy-rotating-proxies
```

## 📁 工作目录文件清单

```
D:\kaifa\openclaw\.openclaw\workspace\
├── agoda_wuhan_hotels.xlsx    # 最终 Excel（2,502 家）
├── agoda_wuhan.db             # SQLite 数据库
├── hotels_all.json            # JSON 原始数据
├── api_body.json               # 捕获的 API 请求体模板（30KB）
├── api_body_fresh.json         # 最新捕获的请求体
│
├── cdp_capture.py / _2.py     # CDP 捕获脚本
├── full_scraper_v4.py         # 多价格区间抓取
├── multi_sort.py / _2.py      # 多排序抓取
├── multi_session.py / _2.py   # 多会话抓取
├── mass_scraper.py            # 大规模多参数抓取
├── date_scraper.py            # 多日期抓取
├── area_scraper.py            # 商圈过滤抓取
│
├── save_excel.py              # Excel 导出
├── merge_final.py             # 数据合并
└── fresh_session.py           # 新会话框架
```

## 📊 关键发现

1. Agoda 搜索 API 每个独立 session 返回约 500 家酒店
2. 改变 **sorting** 参数可以获取完全不同的酒店子集（最关键发现）
3. `ds` cookie 是 HTTP-only 且跨标签页共享，必须重启浏览器才能换 session
4. 全新 Chrome 实例（新 user-data-dir）= 全新 session
5. Headless 模式不影响 CDP 捕获
6. API 请求体无法手动构造，必须从浏览器实时捕获

---
*交接文档完毕。如有问题请联系。*
