#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test - single bracket"""
import json, time, urllib.request, sys, os
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, 'api_body.json'), 'r') as f:
    T = json.load(f)

H = {'Content-Type':'application/json','Accept':'*/*',
     'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
     'AG-LANGUAGE-LOCALE':'zh-cn','AG-CID':'-1','AG-PAGE-TYPE-ID':'103','AG-REQUEST-ATTEMPT':'1'}

def call(frm, to, page=1, token=None):
    req = json.loads(json.dumps(T))
    req['variables']['CitySearchRequest']['searchRequest']['filterRequest']['rangeFilters'][0]['ranges'] = [{'from': float(frm), 'to': float(to) + 0.49}]
    req['variables']['CitySearchRequest']['searchRequest']['page'] = {'pageSize': 50, 'pageNumber': page}
    if token: req['variables']['CitySearchRequest']['searchRequest']['page']['pageToken'] = token
    
    data = json.dumps(req).encode('utf-8')
    r = urllib.request.Request('https://www.agoda.cn/graphql/search', data=data, headers=H)
    resp = urllib.request.urlopen(r, timeout=30)
    return json.loads(resp.read().decode())

print("Testing bracket 0-50...")
data = call(0, 50)
props = data.get('data',{}).get('citySearch',{}).get('properties',[])
token = data.get('data',{}).get('citySearch',{}).get('searchEnrichment',{}).get('pageToken')
t = data.get('data',{}).get('citySearch',{}).get('searchResult',{}).get('searchInfo',{}).get('totalCount',0)
print(f"Properties: {len(props)}, Token: {'yes' if token else 'no'}, Total: {t}")
if props:
    print(f"First: {props[0].get('content',{}).get('informationSummary',{}).get('localeName','?')}")
    print(f"Price check: {props[0].get('pricing',{}).get('offers',[{}])[0].get('roomOffers',[{}])[0].get('room',{}).get('pricing',[{}])[0].get('price',{}).get('perBook',{}).get('inclusive',{}).get('display','N/A')}")

print("\nTesting bracket 0-20...")
data2 = call(0, 20)
props2 = data2.get('data',{}).get('citySearch',{}).get('properties',[])
print(f"Properties: {len(props2)}")
if props2:
    print(f"First: {props2[0].get('content',{}).get('informationSummary',{}).get('localeName','?')}")

print("\nTesting bracket 50-100...")
data3 = call(50, 100)
props3 = data3.get('data',{}).get('citySearch',{}).get('properties',[])
print(f"Properties: {len(props3)}")
if props3:
    print(f"First: {props3[0].get('content',{}).get('informationSummary',{}).get('localeName','?')}")

print("\nDone!")
