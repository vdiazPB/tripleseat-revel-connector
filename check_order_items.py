#!/usr/bin/env python3
"""Check order items for recent order."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

order_id = 10683848
resp = requests.get(f'{base_url}/resources/OrderItem/?order=/resources/Order/{order_id}/', headers=headers)
items_resp = resp.json()

print(f'\nItems for Order {order_id}:')
print('=' * 70)
if items_resp.get('results'):
    for item in items_resp.get('results', []):
        print('  - Product {}: qty={}, price=${:.2f}, initial_price=${:.2f}'.format(
            item.get('product'),
            item.get('quantity'),
            item.get('price', 0),
            item.get('initial_price', 0)
        ))
else:
    print('  (none found)')
print('=' * 70)
