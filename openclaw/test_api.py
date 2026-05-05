#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Agoda API with full cookies and complete request body"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

cookies = {
    'agoda.user.03': 'UserId=83133924-5561-46c1-979d-dd87b2787ff1',
    'agoda.prius': 'PriusID=0&PointsMaxTraffic=Agoda',
    'agoda.attr.fe': '-1|||qh2m5g1dpcspuvayxtah05eg|2026-05-05T11:58:20|False|2026-06-04T11:58:20|R61+DJI/BefynMe8',
    '_ga': 'GA1.2.832944308.1777957234',
    '_gid': 'GA1.2.1537966440.1777957234',
    'agoda.version.03': 'CookieId=f2ddaba6-6cfa-4229-9634-85458d77284e&DLang=zh-cn&CurLabel=CNY&CuLang=8',
    'agoda.analytics': 'Id=-1911203617507896738&Signature=830278978184623154&Expiry=1777966050971',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Origin': 'https://www.agoda.cn',
    'Referer': 'https://www.agoda.cn/search?city=5818',
    'AG-LANGUAGE-LOCALE': 'zh-cn',
    'AG-CID': '-1',
    'AG-PAGE-TYPE-ID': '103',
    'AG-REQUEST-ATTEMPT': '1',
    'x-gate-meta': 'gw21',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

body = {
    "operationName": "citySearch",
    "variables": {
        "CitySearchRequest": {
            "cityId": 5818,
            "searchRequest": {
                "searchCriteria": {
                    "bookingDate": "2026-05-05T05:00:00.000Z",
                    "checkInDate": "2026-06-05T00:00:00.000Z",
                    "los": 1, "rooms": 1, "adults": 2, "children": 0,
                    "childAges": [], "ratePlans": [1],
                    "featureFlagRequest": {
                        "fiveStarDealOfTheDay": True, "isAllowBookOnRequest": False,
                        "showUnAvailable": True, "showRemainingProperties": True,
                        "isMultiHotelSearch": False, "enableAgencySupplyForPackages": True,
                        "isFlexibleMultiRoomSearch": False, "enablePageToken": True,
                        "flags": [
                            {"feature": "FamilyChildFriendlyPopularFilter", "enable": True},
                            {"feature": "FamilyChildFriendlyPropertyTypeFilter", "enable": True},
                            {"feature": "FamilyMode", "enable": False}
                        ]
                    },
                    "isUserLoggedIn": False, "currency": "CNY", "travellerType": "Couple",
                    "isAPSPeek": False, "enableOpaqueChannel": False,
                    "sorting": {"sortField": "Ranking", "sortOrder": "Desc"},
                    "requiredBasis": "PRPN", "requiredPrice": "AllInclusive",
                    "suggestionLimit": 0, "synchronous": False,
                    "isRoomSuggestionRequested": False, "isAPORequest": False,
                    "hasAPOFilter": False, "isAllowBookOnRequest": True,
                    "localCheckInDate": "2026-06-05"
                },
                "searchContext": {
                    "locale": "zh-cn", "cid": -1, "origin": "CN",
                    "platform": 4, "deviceTypeId": 1,
                    "experiments": {"forceByExperiment": []},
                    "isRetry": False, "showCMS": False,
                    "storeFrontId": 3, "pageTypeId": 103,
                    "endpointSearchType": "CitySearch",
                },
                "filterRequest": {"idsFilters": [], "rangeFilters": [], "textFilters": []},
                "matrixGroup": [
                    {"matrixGroup": "StarRating", "size": 100},
                    {"matrixGroup": "AccommodationType", "size": 100},
                ],
                "page": {"pageSize": 10, "pageNumber": 1},
                "searchHistory": [], "isTrimmedResponseRequested": False,
                "extraHotels": {"extraHotelIds": [], "enableFiltersForExtraHotels": False},
                "highlyRatedAgodaHomesRequest": {
                    "numberOfAgodaHomes": 30, "minimumReviewScore": 7.5,
                    "minimumReviewCount": 3,
                    "accommodationTypes": [28,29,30,102,103,106,107,108,109,110,114,115,120,131],
                    "sortVersion": 0
                },
                "featuredPulsePropertiesRequest": {"numberOfPulseProperties": 15},
                "rankingRequest": {"isNhaKeywordSearch": False, "isPulseRankingBoost": False},
                "searchDetailRequest": {"priceHistogramBins": 30},
            }
        }
    }
}

url = 'https://www.agoda.cn/graphql/search'
s = requests.Session()
s.cookies.update(cookies)
resp = s.post(url, json=body, headers=headers, timeout=20)
print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    data = resp.json()
    props = data.get('data',{}).get('citySearch',{}).get('properties',[])
    token = data.get('data',{}).get('citySearch',{}).get('searchEnrichment',{}).get('pageToken')
    total = data.get('data',{}).get('citySearch',{}).get('searchResult',{}).get('searchInfo',{}).get('totalCount',0)
    print(f'OK! Properties: {len(props)}, Token: {"yes" if token else "no"}, Total: {total}')
    if props:
        info = props[0].get('content',{}).get('informationSummary',{})
        print(f'First: {info.get("localeName","?")}')
else:
    txt = resp.text
    print(f'Error: {txt[:500]}')
    # Try without some cookies
    print('\nRetrying with minimal cookies...')
    s2 = requests.Session()
    s2.cookies.update({'agoda.user.03': cookies['agoda.user.03']})
    resp2 = s2.post(url, json=body, headers=headers, timeout=20)
    print(f'Status: {resp2.status_code}, Body: {resp2.text[:200]}')
