#!/usr/bin/env python3
"""Get full order JSON and look for all discount-related fields."""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

order_id = 10683890
resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
order = resp.json()

print(f'\n\nFull Order {order_id} JSON:')
print('=' * 70)

# Find all discount-related fields
discount_fields = {}
for key, value in order.items():
    if 'discount' in key.lower() or key in ['subtotal', 'final_total', 'payment_total', 'total']:
        discount_fields[key] = value

print(json.dumps(discount_fields, indent=2, default=str))

print('\n' + '=' * 70)
print('All fields:')
for key in sorted(order.keys()):
    if order[key] is not None and not isinstance(order[key], (dict, list)):
        print(f'{key}: {order[key]}')
