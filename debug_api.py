#!/usr/bin/env python3
"""Debug Agoda GraphQL API response"""
import json, os, time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

BASE = os.path.dirname(os.path.abspath(__file__))
CHECKIN = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
CHECKOUT = (datetime.now() + timedelta(days=36)).strftime("%Y-%m-%d")
GRAPHQL_URL = "https://www.agoda.cn/graphql/search"

# Get cookies
opts = Options()
opts.binary_location = r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe"
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_argument("--no-sandbox")
opts.add_argument("--window-size=1280,800")
opts.add_argument("--lang=zh-CN")
opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

chromedriver = os.path.join(BASE, "chromedriver.exe")
driver = webdriver.Chrome(service=Service(chromedriver), options=opts)
driver.get(f"https://www.agoda.cn/search?city=16958&checkIn={CHECKIN}&checkOut={CHECKOUT}&rooms=1&adults=2&currency=CNY")
time.sleep(8)
cookies = {c['name']: c['value'] for c in driver.get_cookies()}
print(f"Cookies: {len(cookies)}")
driver.quit()

import requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Origin': 'https://www.agoda.cn',
    'Referer': f'https://www.agoda.cn/search?city=16958&checkIn={CHECKIN}&checkOut={CHECKOUT}&rooms=1&adults=2&currency=CNY',
    'AG-LANGUAGE-LOCALE': 'zh-cn',
    'AG-CID': '-1',
}

body = {
    "operationName": "citySearch",
    "variables": {
        "CitySearchRequest": {
            "cityId": 16958,
            "searchRequest": {
                "searchCriteria": {
                    "bookingDate": datetime.utcnow().strftime("%Y-%m-%dT05:00:00.000Z"),
                    "checkInDate": f"{CHECKIN}T00:00:00.000Z",
                    "los": 1, "rooms": 1, "adults": 2, "children": 0, "childAges": [],
                    "ratePlans": [1],
                    "featureFlagRequest": {"fiveStarDealOfTheDay": True, "isAllowBookOnRequest": False, "showUnAvailable": True, "showRemainingProperties": True, "isMultiHotelSearch": False, "enableAgencySupplyForPackages": True, "flags": [], "isFlexibleMultiRoomSearch": False, "enablePageToken": True},
                    "isUserLoggedIn": False, "currency": "CNY", "travellerType": "Couple",
                    "isAPSPeek": False, "enableOpaqueChannel": False,
                    "sorting": {"sortField": "Ranking", "sortOrder": "Desc"},
                    "requiredBasis": "PRPN", "requiredPrice": "AllInclusive",
                    "suggestionLimit": 0, "synchronous": False,
                    "isRoomSuggestionRequested": False, "isAPORequest": False, "hasAPOFilter": False,
                    "isAllowBookOnRequest": True, "localCheckInDate": CHECKIN
                },
                "searchContext": {
                    "locale": "zh-cn", "cid": -1, "origin": "CN", "platform": 4, "deviceTypeId": 1,
                    "experiments": {"forceByExperiment": []}, "isRetry": False, "showCMS": False,
                    "storeFrontId": 3, "pageTypeId": 103, "endpointSearchType": "CitySearch"
                },
                "filterRequest": {"idsFilters": [], "rangeFilters": [], "textFilters": []},
                "matrixGroup": [
                    {"matrixGroup": "StarRating", "size": 100},
                    {"matrixGroup": "AccommodationType", "size": 100},
                    {"matrixGroup": "HotelAreaId", "size": 100},
                ],
                "page": {"pageSize": 10, "pageNumber": 1},
                "searchHistory": [],
                "isTrimmedResponseRequested": False,
                "extraHotels": {"extraHotelIds": [], "enableFiltersForExtraHotels": False},
                "highlyRatedAgodaHomesRequest": {"numberOfAgodaHomes": 30, "minimumReviewScore": 7.5, "minimumReviewCount": 3, "accommodationTypes": [], "sortVersion": 0},
                "featuredPulsePropertiesRequest": {"numberOfPulseProperties": 15},
                "rankingRequest": {"isNhaKeywordSearch": False, "isPulseRankingBoost": False},
                "searchDetailRequest": {"priceHistogramBins": 30}
            }
        }
    }
}

resp = requests.post(GRAPHQL_URL, json=body, headers=headers, cookies=cookies, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Response size: {len(resp.text)}")
try:
    data = resp.json()
    s = json.dumps(data, ensure_ascii=False, indent=2)
    # Print first 3000 chars
    print(s[:3000])
except:
    print(resp.text[:2000])
