#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Use Chrome DevTools Protocol to capture the Agoda API request body.
1. Connect to existing browser via CDP
2. Open a new tab with network throttling (slow 3G)
3. Capture the graphql/search request body
4. Save it for later use
"""
import asyncio
import json
import urllib.request
import websockets

WS_URLS = {}  # tab_id -> ws_url

async def get_tabs():
    resp = urllib.request.urlopen('http://127.0.0.1:18800/json', timeout=5)
    tabs = json.loads(resp.read())
    result = {}
    for t in tabs:
        tid = t['id']
        ws = t['webSocketDebuggerUrl']
        url = t.get('url', '')
        result[tid] = {'ws': ws, 'url': url, 'title': t.get('title', '')}
    return result

async def send_cmd(ws, cmd_id, method, params=None):
    msg = {'id': cmd_id, 'method': method}
    if params:
        msg['params'] = params
    await ws.send(json.dumps(msg))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get('id') == cmd_id:
            return resp

async def capture_api_body():
    tabs = await get_tabs()
    
    # Find an existing Agoda tab to use as template
    agoda_tab = None
    for tid, info in tabs.items():
        if 'agoda.cn' in info['url']:
            agoda_tab = tid
            # Get its cookies
            ws_url = info['ws']
            break
    
    if not agoda_tab:
        print("No Agoda tab found")
        return
    
    print(f"Using tab: {agoda_tab}")
    print(f"WS URL: {ws_url}")
    
    # Connect to the tab
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        # Enable Network domain
        await send_cmd(ws, 1, 'Network.enable')
        print("Network domain enabled")
        
        # Get cookies from the page
        result = await send_cmd(ws, 2, 'Network.getAllCookies')
        cookies = result.get('result', {}).get('cookies', [])
        cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
        print(f"Got {len(cookies)} cookies")
        
        # Set up request interception for graphql/search
        await send_cmd(ws, 3, 'Network.setRequestInterception', {
            'patterns': [{
                'urlPattern': '*graphql/search*',
                'interceptionStage': 'HeadersReceived'
            }]
        })
        print("Request interception set")
        
        # Navigate to a fresh price bracket URL
        nav_url = ('https://www.agoda.cn/search?city=5818&checkin=2026-06-05'
                   '&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0'
                   '&currency=CNY&priceFrom=0&priceTo=50&priceCur=CNY&t=' + str(asyncio.get_event_loop().time()))
        
        print(f"Navigating to: {nav_url[:80]}...")
        
        # Listen for the request
        captured_body = None
        
        async def listen():
            nonlocal captured_body
            while True:
                try:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                    method = msg.get('method', '')
                    
                    if method == 'Network.requestIntercepted':
                        interception_id = msg['params']['interceptionId']
                        request = msg['params'].get('request', {})
                        
                        # Check if there's post data
                        post_data = request.get('postData', '')
                        if post_data and 'graphql' in post_data:
                            captured_body = post_data
                            print(f"\nCAPTURED! Body length: {len(post_data)}")
                        
                        # Continue the request
                        await send_cmd(ws, 100 + msg['id'], 'Network.continueInterceptedRequest', {
                            'interceptionId': interception_id
                        })
                        
                        if captured_body:
                            break
                    
                    elif method == 'Network.requestWillBeSent':
                        req = msg['params'].get('request', {})
                        if 'graphql/search' in req.get('url', ''):
                            post_data = req.get('postData', '')
                            if post_data:
                                captured_body = post_data
                                print(f"\nCAPTURED from requestWillBeSent! Body length: {len(post_data)}")
                                break
                    
                except asyncio.TimeoutError:
                    print("Timeout waiting for request")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break
        
        # Start navigation and listen simultaneously
        nav_task = asyncio.create_task(send_cmd(ws, 10, 'Page.navigate', {'url': nav_url}))
        listen_task = asyncio.create_task(listen())
        
        await asyncio.gather(nav_task, listen_task)
        
        if captured_body:
            # Save the body to a file
            with open('api_body.json', 'w', encoding='utf-8') as f:
                f.write(captured_body)
            print(f"\nSaved! Body preview: {captured_body[:200]}")
            
            # Check if it has price filter
            parsed = json.loads(captured_body)
            filters = parsed.get('variables',{}).get('CitySearchRequest',{}).get('searchRequest',{}).get('filterRequest',{})
            print(f"Has rangeFilters: {len(filters.get('rangeFilters',[]))}")
            print(f"Has ContentSummaryRequest: {'ContentSummaryRequest' in parsed.get('variables',{})}")
        else:
            print("\nFailed to capture API body")

asyncio.run(capture_api_body())
