#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch process: for each price bracket URL, open in new tab, extract, save
"""
import json, os, time, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))

BRACKETS = [
    (0,20),(20,30),(30,40),(40,50),(50,60),(60,70),(70,80),
    (80,100),(100,120),(120,150),(150,180),(180,210),(210,260),
    (260,310),(310,380),(380,460),(460,550),(550,670),(670,810),
    (810,980),(980,1180),(1180,1430),(1430,1730),(1730,2100)
]

# Start from bracket index
START_IDX = 1  # Already did bracket 0 (0-20)

for idx in range(START_IDX, len(BRACKETS)):
    frm, to = BRACKETS[idx]
    url = f"https://www.agoda.cn/search?city=5818&checkin=2026-06-05&checkout=2026-06-06&los=1&rooms=1&adults=2&children=0&currency=CNY&priceFrom={frm}&priceTo={to}&priceCur=CNY"
    
    print(f"\n[{idx+1}/{len(BRACKETS)}] Bracket RMB {frm}-{to}")
    print(f"  Open: {url}")
    
    # This would require browser tool calls - just print for now
    print(f"  Next: open tab, wait 10s, extract, close tab")
    
print("\nDone planning. Run manually or write a browser script.")
