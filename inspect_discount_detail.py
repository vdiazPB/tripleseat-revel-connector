#!/usr/bin/env python3
"""Detailed discount inspection for recent orders."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

# Check our recent orders
test_orders = [10683848, 10683804, 10683755]

for order_id in test_orders:
    print(f'\n{"=" * 70}')
    print(f'Order {order_id}')
    print('=' * 70)
    
    resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
    
    if resp.status_code != 200:
        print(f'Failed to fetch: {resp.status_code}')
        continue
    
    order = resp.json()
    
    print(f'API Fields:')
    print(f'  subtotal: ${order.get("subtotal", 0):.2f}')
    print(f'  discount_amount: ${order.get("discount_amount", 0):.2f}')
    print(f'  final_total: ${order.get("final_total", 0):.2f}')
    print(f'  is_discounted: {order.get("is_discounted")}')
    print(f'  discount field: {order.get("discount")}')
    
    print(f'\nApplied Discounts:')
    for d in order.get('applied_discounts', []):
        discount_val = float(d.get('discount_amount', 0))
        print(f'  - {d.get("name")}: ${discount_val:.2f}')
    
    if not order.get('applied_discounts'):
        print('  (none)')
    
    print(f'\nOrder Items:')
    for item in order.get('items', []):
        print(f'  - Product {item.get("product")}: qty={item.get("quantity")}, price=${item.get("price", 0):.2f}')

print(f'\n{"=" * 70}')
print('Summary: Check Revel UI Order History for each order number above')
print('=' * 70)
