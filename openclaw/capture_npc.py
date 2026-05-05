#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capture NPC endpoint"""
import asyncio, json, urllib.request, websockets, sys
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    resp = json.loads(urllib.request.urlopen('http://127.0.0.1:18800/json', timeout=5).read())
    
    target = None
    for t in resp:
        if 'hotel/wuhan-cn' in t.get('url',''):
            target = t
            break
    
    if not target:
        print('No hotel detail tab found')
        return
    
    tid = target['id']
    print(f'Tab: {tid}')
    
    tws = target['webSocketDebuggerUrl']
    async with websockets.connect(tws, max_size=20_000_000) as ws:
        await ws.send(json.dumps({'id':1,'method':'Network.enable'}))
        try: await asyncio.wait_for(ws.recv(), timeout=3)
        except: pass
        
        captured = None
        async def listen():
            nonlocal captured
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=20)
                m = json.loads(raw)
                if m.get('method') == 'Network.requestWillBeSent':
                    rq = m['params'].get('request', {})
                    url = rq.get('url', '')
                    if 'graphql/npc' in url:
                        pd = rq.get('postData', '')
                        if pd:
                            captured = {'url': url, 'body': pd[:2000]}
                            return
        
        await ws.send(json.dumps({'id':2,'method':'Page.reload'}))
        try: await asyncio.wait_for(listen(), timeout=20)
        except asyncio.TimeoutError:
            print('Timeout')
        except Exception as e:
            print(f'Error: {e}')
    
    if captured:
        print(f"URL: {captured['url']}")
        print(f"Body: {captured['body']}")
    else:
        print('Not captured')

asyncio.run(main())
