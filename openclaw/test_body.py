#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the captured API body"""
import json, time, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('api_body.json', 'r') as f:
    template = json.load(f)

# Make first API call
req_data = json.loads(json.dumps(template))
req_data['variables']['CitySearchRequest']['searchRequest']['filterRequest']['rangeFilters'][0]['ranges'] = [{'from': 0.0, 'to': 50.49}]
req_data['variables']['CitySearchRequest']['searchRequest']['page'] = {'pageSize': 10, 'pageNumber': 1}

body = json.dumps(req_data).encode('utf-8')
url = 'https://www.agoda.cn/graphql/search'
headers = {
    'Content-Type': 'application/json', 'Accept': '*/*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'AG-LANGUAGE-LOCALE': 'zh-cn', 'AG-CID': '-1', 'AG-PAGE-TYPE-ID': '103',
    'AG-REQUEST-ATTEMPT': '1',
}

req = urllib.request.Request(url, data=body, headers=headers)
print('Making API call with captured body...')
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode())
props = data.get('data',{}).get('citySearch',{}).get('properties',[])
total = data.get('data',{}).get('citySearch',{}).get('searchResult',{}).get('searchInfo',{}).get('totalCount',0)
token = data.get('data',{}).get('citySearch',{}).get('searchEnrichment',{}).get('pageToken','')

token_yes = 'yes' if token else 'no'
print(f'OK! Hotels: {len(props)}, Total: {total}, Token: {token_yes}')
if props:
    info = props[0].get('content',{}).get('informationSummary',{})
    first_name = info.get('localeName','?')
    print(f'First: {first_name}')
