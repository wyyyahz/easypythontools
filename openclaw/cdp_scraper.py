#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Agoda hotel scraper using Chrome DevTools Protocol.
Connects to the existing browser debugging port (ws://127.0.0.1:18800).
"""
import asyncio
import json
import os
import re
import websockets

BASE = os.path.dirname(os.path.abspath(__file__))
WS_URL = "ws://127.0.0.1:18800/devtools/page/3262B396DF121E2625461D5C90774AC2"

PRICE_BRACKETS = [
    (0, 50), (50, 70), (70, 80), (80, 100), (100, 120), (120, 150),
    (150, 190), (190, 230), (230, 280), (280, 350), (350, 430), (430, 520),
    (520, 640), (640, 790), (790, 970), (970, 1190), (1190, 1470),
    (1470, 1810), (1810, 2220), (2220, 2730), (2730, 3350), (3350, 100000)
]

ALL_HOTELS = []
SEEN_NAMES = set()

async def send_cmd(ws, cmd):
    await ws.send(json.dumps(cmd))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == cmd.get("id"):
            return resp

async def navigate(ws, url):
    cmd = {"id": 1, "method": "Page.navigate", "params": {"url": url}}
    return await send_cmd(ws, cmd)

async def evaluate(ws, js, cmd_id=2):
    cmd = {"id": cmd_id, "method": "Runtime.evaluate", 
           "params": {"expression": js, "returnByValue": True}}
    resp = await send_cmd(ws, cmd)
    result = resp.get("result", {}).get("result", {})
    if "value" in result:
        return result["value"]
    if "exceptionDetails" in result:
        return {"error": result["exceptionDetails"]}
    return result

async def wait_for_page(ws, timeout=10):
    """Wait for page to finish loading"""
    import time
    start = time.time()
    while time.time() - start < timeout:
        result = await evaluate(ws, 
            "document.readyState === 'complete' ? 'complete' : 'loading'", 100)
        if result == 'complete':
            # Also wait for content to render
            await asyncio.sleep(3)
            return True
        await asyncio.sleep(1)
    return False

async def extract_hotels(ws):
    """Extract all visible hotel data from current page"""
    js = """
    (() => {
        const seen = new Set();
        const hotels = [];
        document.querySelectorAll('a[href*="/hotel/wuhan-cn"]').forEach(link => {
            const text = link.textContent.trim();
            if (text.length < 20) return;
            const pm = text.match(/RMB\\s*([0-9,]+)/);
            const rm = text.match(/([0-9]\\.[0-9])/);
            const sm = text.match(/Rating\\s*([0-9]+)\\s*out of/);
            let name = '';
            const lines = text.split('\\n').map(l=>l.trim()).filter(l=>l.length>3);
            for (const l of lines) {
                if (l.includes('\\u9152\\u5e97')||l.includes('\\u5ba2\\u6808')||l.includes('\\u6c11\\u5bbf')||
                    l.includes('\\u5bbe\\u9986')||l.includes('\\u516c\\u5bd3')||l.includes('\\u65c5\\u9986')||
                    l.includes('Hostel')||l.includes('Hotel')||l.includes('Apartment')||
                    l.includes('Accommodation')||l.includes('RETURN')||l.includes('Luojia')) {
                    name = l; break;
                }
            }
            if (!name) {
                for (const l of lines) {
                    if (!l.includes('RMB')&&!l.includes('tooltip')&&!l.includes('Rating')&&l.length>5) {
                        name=l; break;
                    }
                }
            }
            const cn = name.replace(/^[0-9]+\\s*/,'').trim();
            if (!cn||cn.length<3||seen.has(cn)) return;
            seen.add(cn);
            hotels.push({
                name: cn,
                stars: sm ? sm[1]+'/5\\u661f' : '',
                rating: rm ? parseFloat(rm[1]) : null,
                price: pm ? parseInt(pm[1].replace(/,/g,'')) : null
            });
        });
        return JSON.stringify({count: hotels.length, hotels: hotels});
    })()
    """
    result = await evaluate(ws, js, 200)
    if isinstance(result, str):
        return json.loads(result)
    return {"count": 0, "hotels": []}

async def scrape_bracket(ws, from_price, to_price):
    url = (f"https://www.agoda.cn/search?city=5818&checkin=2026-06-05"
           f"&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0"
           f"&currency=CNY&priceFrom={from_price}&priceTo={to_price}&priceCur=CNY")
    
    print(f"  Navigating to {url}")
    await navigate(ws, url)
    
    loaded = await wait_for_page(ws)
    if not loaded:
        print(f"  Page load timeout")
        return 0
    
    result = await extract_hotels(ws)
    new_hotels = 0
    for h in result.get("hotels", []):
        name = h["name"]
        # Clean name
        name = re.sub(r'Rating.*$', '', name)
        name = re.sub(r'tooltip.*$', '', name)
        name = name.replace('特别推荐', '').replace('Domestic Deal', '').strip()
        if not name or len(name) < 3 or name in SEEN_NAMES:
            continue
        SEEN_NAMES.add(name)
        h["name"] = name
        ALL_HOTELS.append(h)
        new_hotels += 1
    
    print(f"  Bracket {from_price}-{to_price}: {result['count']} visible, {new_hotels} new (total: {len(ALL_HOTELS)})")
    return new_hotels

async def main():
    print(f"Connecting to {WS_URL}")
    async with websockets.connect(WS_URL) as ws:
        print("Connected! Starting scrape...\n")
        
        for idx, (frm, to) in enumerate(PRICE_BRACKETS, 1):
            print(f"\n[{idx}/{len(PRICE_BRACKETS)}] Price bracket: RMB {frm} - {to}")
            try:
                await scrape_bracket(ws, frm, to)
            except Exception as e:
                print(f"  Error: {e}")
                # Try to reconnect
                break
            await asyncio.sleep(1)
        
        # Save results
        output = {"count": len(ALL_HOTELS), "hotels": ALL_HOTELS}
        out_path = os.path.join(BASE, "hotels_all.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*50}")
        print(f"Done! Total: {len(ALL_HOTELS)} unique hotels")
        print(f"Saved to: {out_path}")

if __name__ == "__main__":
    asyncio.run(main())
