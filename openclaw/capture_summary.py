#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capture propertySummary endpoint from search results page"""
import asyncio, json, urllib.request, websockets, sys, os
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))

# Start a fresh Chrome and navigate to search results
proc = None
try:
    import subprocess
    chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    proc = subprocess.Popen([chrome, '--remote-debugging-port=19300',
        '--user-data-dir=D:\\temp_summary', '--no-first-run', '--no-default-browser-check',
        '--disable-sync', '--headless=new'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    import time
    time.sleep(4)
    
    info = json.loads(urllib.request.urlopen('http://127.0.0.1:19300/json/version', timeout=5).read())
    bws = info['webSocketDebuggerUrl']
    
    async def main():
        async with websockets.connect(bws, max_size=20_000_000) as bws_conn:
            await bws_conn.send(json.dumps({'id':1,'method':'Target.createTarget','params':{'url':'about:blank'}}))
            r = json.loads(await bws_conn.recv())
            tid = r['result']['targetId']
            tws = f'ws://127.0.0.1:19300/devtools/page/{tid}'
        
        captured_bodies = []
        
        async with websockets.connect(tws, max_size=20_000_000) as ws:
            await ws.send(json.dumps({'id':1,'method':'Network.enable'}))
            try: await asyncio.wait_for(ws.recv(), timeout=3)
            except: pass
            
            async def listen():
                while True:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=30)
                        m = json.loads(raw)
                        if m.get('method') == 'Network.requestWillBeSent':
                            rq = m['params'].get('request', {})
                            url = rq.get('url', '')
                            pd = rq.get('postData', '')
                            
                            if 'propertySummary' in url and pd:
                                captured_bodies.append(pd[:500])
                                if len(captured_bodies) >= 3:
                                    return
                            elif 'graphql/search' in url and pd:
                                # Save the search body too
                                with open(os.path.join(BASE, 'api_body_search.json'), 'w') as f:
                                    f.write(pd)
                                print(f'Saved search body ({len(pd)} bytes)')
                    except asyncio.TimeoutError:
                        return
                    except:
                        pass
            
            # Navigate to search results
            nav_url = ('https://www.agoda.cn/search?city=5818&checkin=2026-06-05'
                       '&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY')
            await ws.send(json.dumps({'id':2,'method':'Page.navigate','params':{'url': nav_url}}))
            
            try: await asyncio.wait_for(listen(), timeout=30)
            except: pass
            
            # Scroll to trigger more loads
            for i in range(3):
                await ws.send(json.dumps({'id':3+i,'method':'Runtime.evaluate',
                    'params':{'expression':'window.scrollBy(0,1000)'}}))
                try: await asyncio.wait_for(ws.recv(), timeout=2)
                except: pass
                await asyncio.sleep(2)
            
            # Listen a bit more for propertySummary
            try:
                await asyncio.wait_for(listen(), timeout=15)
            except:
                pass
        
        if captured_bodies:
            print(f'Captured {len(captured_bodies)} propertySummary calls')
            for i, b in enumerate(captured_bodies):
                print(f'\n--- Call {i+1} ---')
                print(b[:800])
        else:
            print('No propertySummary calls captured')
    
    asyncio.run(main())

finally:
    if proc:
        try: proc.kill()
        except: pass
