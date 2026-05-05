#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CDP - Capture Agoda API request body, v2"""
import asyncio, json, urllib.request, websockets, sys
sys.stdout.reconfigure(encoding='utf-8')

async def capture():
    # Get an Agoda tab
    resp = urllib.request.urlopen('http://127.0.0.1:18800/json', timeout=5)
    tabs = json.loads(resp.read())
    
    target = None
    for t in tabs:
        if 'agoda.cn/search' in t.get('url',''):
            target = t
            break
    
    if not target:
        print("No Agoda tab found")
        return None
    
    ws_url = target['webSocketDebuggerUrl']
    print(f"Tab: {target['id']}")
    
    captured = {'body': None}
    
    async with websockets.connect(ws_url, max_size=20_000_000) as ws:
        # Enable Network
        await ws.send(json.dumps({'id':1,'method':'Network.enable'}))
        await ws.recv()  # ack
        
        # Get cookies
        await ws.send(json.dumps({'id':2,'method':'Network.getAllCookies'}))
        ack = json.loads(await ws.recv())
        cookies = ack.get('result',{}).get('cookies',[])
        print(f"Cookies: {len(cookies)}")
        
        # Navigate to price bracket URL
        nav_url = ('https://www.agoda.cn/search?city=5818&checkin=2026-06-05'
                   '&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0'
                   '&currency=CNY&priceFrom=0&priceTo=50&priceCur=CNY&cdp=1')
        
        # Track pending commands
        pending = {}
        
        async def message_loop():
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=20)
                    msg = json.loads(raw)
                    mid = msg.get('id')
                    method = msg.get('method', '')
                    
                    # Handle response to a command
                    if mid is not None and mid in pending:
                        pending[mid].set_result(msg)
                        del pending[mid]
                        continue
                    
                    # Handle network events
                    if method == 'Network.requestWillBeSent':
                        req = msg['params'].get('request', {})
                        url = req.get('url', '')
                        if 'graphql/search' in url:
                            post_data = req.get('postData', '')
                            if post_data and len(post_data) > 500:
                                print(f"\n>>> CAPTURED API BODY! Length: {len(post_data)}")
                                captured['body'] = post_data
                                return
                    
                    elif method == 'Network.responseReceived':
                        resp_url = msg['params'].get('request', {}).get('url', '')
                        if 'graphql/search' in resp_url:
                            print(f"  API response received (but body already captured?)")
                    
                except asyncio.TimeoutError:
                    print("Message loop timeout")
                    return
                except Exception as e:
                    print(f"Msg loop error: {e}")
                    return
        
        def send_cmd(method, params=None):
            nonlocal pending
            import uuid
            mid = int(uuid.uuid4().int % 1000000)
            msg = {'id': mid, 'method': method}
            if params:
                msg['params'] = params
            pending[mid] = asyncio.get_event_loop().create_future()
            asyncio.ensure_future(ws.send(json.dumps(msg)))
            return pending[mid]
        
        # Start the message loop
        loop_task = asyncio.create_task(message_loop())
        
        # Send navigation command
        nav_future = send_cmd('Page.navigate', {'url': nav_url})
        
        # Wait for either capture or timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(loop_task, return_exceptions=True),
                timeout=25
            )
        except asyncio.TimeoutError:
            print("Timeout")
        
        body = captured['body']
        if body:
            with open('api_body.json', 'w', encoding='utf-8') as f:
                f.write(body)
            
            # Parse and show info
            parsed = json.loads(body)
            v = parsed.get('variables',{}).get('CitySearchRequest',{}).get('searchRequest',{})
            filters = v.get('filterRequest',{}).get('rangeFilters',[])
            has_csr = 'ContentSummaryRequest' in parsed.get('variables',{})
            print(f"\nBody info:")
            print(f"  Length: {len(body)}")
            print(f"  Has price filter: {len(filters) > 0}")
            if filters:
                print(f"  Filter: {filters}")
            print(f"  Has ContentSummaryRequest: {has_csr}")
            return body
        
        print("Failed to capture API body")
        return None

result = asyncio.run(capture())
