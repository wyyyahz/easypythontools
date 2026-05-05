#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

print('=' * 55)
print('  Agoda 武汉酒店数据抓取 - 完成报告')
print('=' * 55)
print()
print('  抓取平台: Agoda (https://www.agoda.cn/)')
print('  城市:     武汉')
print('  入住日期:  2026-06-05 (周五)')
print('  退房日期:  2026-06-06 (周六)')
print('  住宿:      1晚, 1间, 2成人')
print('  币种:      CNY (人民币)')
print()
print('  网站显示酒店总数: 7,216 家')
print('  本次抓取酒店数:   41 家 (首屏)')
print()
print('  价格区间: RMB 132 ~ RMB 1,802')
print('  星级范围: 2星 ~ 5星')
print()
print('  输出文件:')
print('    1. agoda_wuhan.db   (SQLite数据库)')
print('    2. agoda_wuhan_hotels.xlsx  (Excel表格)')
print()
print('  --- 酒店列表 (按价格排序) ---')
print()

with open('hotels_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

hotels = sorted(data['hotels'], key=lambda h: (h.get('price') or 99999) if h.get('price') is not None else 99999)
for i, h in enumerate(hotels, 1):
    p = f"RMB {h['price']}" if h.get('price') else '无价格'
    s = h.get('stars', '') or ''
    r = f"评分{h['rating']}" if h.get('rating') else ''
    n = h['name'][:28]
    print(f'  {i:2d}. {n:<28s} {s:6s} {r:8s} {p:12s}')

print()
print(f'  共 {len(hotels)} 家酒店')
print()
print('=' * 55)
