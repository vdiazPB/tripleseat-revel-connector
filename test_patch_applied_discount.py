#!/usr/bin/env python3
"""Test if we can patch AppliedDiscountOrder to set discount amount."""

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

import os
import requests

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

# Check order 10683890 and get its AppliedDiscountOrder ID
order_id = 10683890
resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
order = resp.json()

print(f'\nOrder {order_id} Applied Discounts:')
for d in order.get('applied_discounts', []):
    discount_uri = d.get('resource_uri')
    discount_id = d.get('id')
    current_amount = d.get('discount_amount')
    
    print(f'  Found AppliedDiscountOrder {discount_id}')
    print(f'    Current amount: {current_amount}')
    print(f'    URI: {discount_uri}')
    
    # Try to patch it with the correct amount
    print(f'  Patching with amount 2.50...')
    patch_data = {
        'discount_amount': 2.50,
    }
    resp = requests.patch(f'{base_url}{discount_uri}', headers=headers, json=patch_data)
    print(f'    Status: {resp.status_code}')
    
    if resp.status_code in [200, 202]:
        print(f'    ✅ Success')
        patched = resp.json()
        print(f'    New amount: {patched.get("discount_amount")}')
    else:
        print(f'    ❌ Failed: {resp.text[:200]}')

# Re-check the order
print(f'\nRe-checking order {order_id}...')
resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
order = resp.json()
print(f'  discount_amount: {order.get("discount_amount")}')
print(f'  final_total: {order.get("final_total")}')
