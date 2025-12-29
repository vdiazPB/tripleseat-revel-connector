#!/usr/bin/env python3
"""Check historical orders to understand discount structure."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

# Get a sample of recent orders to find one with a discount
resp = requests.get(f'{base_url}/resources/Order/?limit=50', headers=headers)
orders = resp.json()

print('\nLooking for orders with discounts...')
print('=' * 70)

found_with_discount = False
for order in orders.get('results', []):
    discount = order.get('discount_amount')
    is_disc = order.get('is_discounted')
    
    # Look for any order with discount > 0
    if discount and float(discount) > 0:
        order_id = order.get('id')
        print(f'\nFound order with discount!')
        print(f'Order ID: {order_id}')
        print(f'  discount_amount: {discount}')
        print(f'  is_discounted: {is_disc}')
        print(f'  subtotal: {order.get("subtotal")}')
        print(f'  final_total: {order.get("final_total")}')
        print(f'  discount field: {order.get("discount")}')
        print(f'  closed: {order.get("closed")}')
        print(f'  printed: {order.get("printed")}')
        
        # Get full details
        detail_resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
        detail = detail_resp.json()
        
        print(f'\n  Applied Discounts:')
        for d in detail.get('applied_discounts', []):
            print(f'    - {d.get("name")}: ${float(d.get("discount_amount", 0)):.2f}')
        
        print()
        found_with_discount = True
        break

if not found_with_discount:
    print('No orders with discounts found in recent 50 orders')
    print('This might mean discounts are not commonly used, or we need a different field')

print('=' * 70)
