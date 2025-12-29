#!/usr/bin/env python3
"""Check and override discount amount for order 10684061."""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

order_id = 10684061

# Get the order
resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
order = resp.json()

print(f'\nOrder {order_id}:')
print('=' * 70)
print(f'discount_amount on Order: {order.get("discount_amount")}')
print()

# Get the AppliedDiscountOrder
if order.get('applied_discounts'):
    for d in order.get('applied_discounts', []):
        discount_uri = d.get('resource_uri')
        discount_id = d.get('id')
        current_amount = d.get('discount_amount')
        
        print(f'AppliedDiscountOrder {discount_id}:')
        print(f'  Current amount: {current_amount}')
        print(f'  URI: {discount_uri}')
        print()
        
        # Try different approaches to set the amount
        # Approach 1: Try to PATCH with simple data
        print(f'Attempting to update discount amount to 2.50...')
        
        # Method 1: Direct PATCH
        update_data = {
            'discount_amount': 2.50,
        }
        resp = requests.patch(f'{base_url}{discount_uri}', headers=headers, json=update_data)
        print(f'  PATCH status: {resp.status_code}')
        if resp.status_code in [200, 201, 202]:
            print(f'  ✅ Success!')
            updated = resp.json()
            print(f'  New amount: {updated.get("discount_amount")}')
        else:
            print(f'  ❌ Failed')
            if resp.status_code != 401:
                print(f'  Response: {resp.text[:300]}')

# Re-check the order
print()
print('Re-checking order...')
resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
order = resp.json()
print(f'Order discount_amount: {order.get("discount_amount")}')
for d in order.get('applied_discounts', []):
    print(f'AppliedDiscountOrder amount: {d.get("discount_amount")}')

print()
print('=' * 70)
