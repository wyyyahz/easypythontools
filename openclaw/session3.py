#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Session 3: paginate and merge"""
import json, urllib.request, time, sys, os
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, 'hotels_all.json'), 'r', encoding='utf-8') as f:
    ALL = json.load(f)['hotels']
SEEN = set(h['name'] for h in ALL)
print(f"Before: {len(ALL)}")

with open(os.path.join(BASE, 'api_body3.json'), 'r') as f:
    t = json.loads(f.read())
t['variables']['CitySearchRequest']['searchRequest']['filterRequest']['rangeFilters'] = []

H = {'Content-Type':'application/json','Accept':'*/*','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','AG-LANGUAGE-LOCALE':'zh-cn','AG-CID':'-1','AG-PAGE-TYPE-ID':'103','AG-REQUEST-ATTEMPT':'1'}
p, tk, nc = 1, None, 0

while p <= 150:
    r = json.loads(json.dumps(t))
    r['variables']['CitySearchRequest']['searchRequest']['page'] = {'pageSize': 50, 'pageNumber': p}
    if tk: r['variables']['CitySearchRequest']['searchRequest']['page']['pageToken'] = tk
    try:
        d = json.loads(urllib.request.urlopen(urllib.request.Request('https://www.agoda.cn/graphql/search',data=json.dumps(r).encode('utf-8'),headers=H),timeout=30).read().decode())
        ps = d.get('data',{}).get('citySearch',{}).get('properties') or []
        tk = d.get('data',{}).get('citySearch',{}).get('searchEnrichment',{}).get('pageToken')
        if not ps:
            if p > 1: break
            p += 1; continue
        for x in ps:
            info = x.get('content',{}).get('informationSummary') or {}
            n = info.get('localeName') or info.get('defaultName') or ''
            if not n or n in SEEN: continue
            SEEN.add(n)
            pr = None
            try:
                for o in (x.get('pricing',{}).get('offers') or []):
                    for r in (o.get('roomOffers') or []):
                        for pp in (r.get('room',{}).get('pricing') or []):
                            d = pp.get('price',{}).get('perBook',{}).get('inclusive',{}).get('display')
                            if d: pr = round(d); break
                        if pr: break
                    if pr: break
            except: pass
            ra = None
            try: ra = x.get('content',{}).get('reviews',{}).get('cumulative',{}).get('score')
            except: pass
            ALL.append({'name': n, 'rating': ra, 'price': pr})
            nc += 1
        if not tk: break
        p += 1; time.sleep(0.15)
    except: break

print(f"New: {nc}, Total: {len(ALL)}")
with open(os.path.join(BASE, 'hotels_all.json'), 'w', encoding='utf-8') as f:
    json.dump({'count': len(ALL), 'hotels': ALL}, f, ensure_ascii=False, indent=2)
pr = [h['price'] for h in ALL if h['price']]
if pr: print(f"Price: RMB {min(pr):,} ~ RMB {max(pr):,}")
