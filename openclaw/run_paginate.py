#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paginate using the fresh API body"""
import json, urllib.request, time, sys, os
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, 'api_body.json'), 'r') as f:
    template = json.loads(f.read())

template['variables']['CitySearchRequest']['searchRequest']['filterRequest']['rangeFilters'] = []

HEADERS = {
    'Content-Type':'application/json','Accept':'*/*',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'AG-LANGUAGE-LOCALE':'zh-cn','AG-CID':'-1','AG-PAGE-TYPE-ID':'103','AG-REQUEST-ATTEMPT':'1',
}

ALL = []
SEEN = set()
page, token = 1, None

print("Paginating fresh session...")

while page <= 150:
    req = json.loads(json.dumps(template))
    req['variables']['CitySearchRequest']['searchRequest']['page'] = {'pageSize': 50, 'pageNumber': page}
    if token:
        req['variables']['CitySearchRequest']['searchRequest']['page']['pageToken'] = token
    
    data = json.dumps(req).encode('utf-8')
    r = urllib.request.Request('https://www.agoda.cn/graphql/search', data=data, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(r, timeout=30)
        result = json.loads(resp.read().decode())
        
        props = result.get('data',{}).get('citySearch',{}).get('properties') or []
        token = result.get('data',{}).get('citySearch',{}).get('searchEnrichment',{}).get('pageToken')
        
        if not props:
            if page > 1:
                break
            page += 1
            continue
        
        for p in props:
            info = p.get('content',{}).get('informationSummary') or {}
            reviews = p.get('content',{}).get('reviews',{})
            pricing = p.get('pricing') or {}
            name = info.get('localeName') or info.get('defaultName') or ''
            if not name or name in SEEN:
                continue
            SEEN.add(name)
            
            price = None
            try:
                for o in (pricing.get('offers') or []):
                    for r in (o.get('roomOffers') or []):
                        for pr in (r.get('room',{}).get('pricing') or []):
                            d = pr.get('price',{}).get('perBook',{}).get('inclusive',{}).get('display')
                            if d:
                                price = round(d)
                                break
                        if price: break
                    if price: break
            except:
                pass
            
            rating = None
            try:
                rating = reviews.get('cumulative',{}).get('score')
            except:
                pass
            
            location = ''
            addr = info.get('address') or {}
            if addr.get('area'):
                location = addr['area'].get('name', '')
            if not location and addr.get('city'):
                location = addr['city'].get('name', '')
            
            ALL.append({'name': name, 'rating': rating, 'price': price, 'location': location})
        
        token_str = 'yes' if token else 'no'
        print(f"  Page {page}: {len(props)} props, {len(ALL)} total, token: {token_str}")
        
        if not token:
            break
        page += 1
        time.sleep(0.15)
        
    except urllib.error.HTTPError as e:
        print(f"  Page {page}: HTTP {e.code}")
        if page > 2:
            break
        page += 1
        time.sleep(2)
    except Exception as e:
        print(f"  Page {page}: {type(e).__name__}: {e}")
        if page > 2:
            break
        page += 1
        time.sleep(2)

print(f"\nTotal: {len(ALL)} hotels")

# Save
with open(os.path.join(BASE, 'hotels_all.json'), 'w', encoding='utf-8') as f:
    json.dump({'count': len(ALL), 'hotels': ALL}, f, ensure_ascii=False, indent=2)

prices = [h['price'] for h in ALL if h['price'] is not None]
ratings = [h['rating'] for h in ALL if h['rating'] is not None]
if prices:
    print(f"Price: RMB {min(prices):,} ~ RMB {max(prices):,}, Avg: RMB {sum(prices)/len(prices):.0f}")
if ratings:
    print(f"Rating: {min(ratings):.1f} ~ {max(ratings):.1f}")
