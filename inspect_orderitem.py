#!/usr/bin/env python3
"""Check OrderItem structure to see if discount goes there."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

# Get items from our recent order
order_id = 10683890
resp = requests.get(f'{base_url}/resources/OrderItem/?order=/resources/Order/{order_id}/', headers=headers)
items = resp.json()

print(f'\nOrderItem structure for order {order_id}:')
print('=' * 70)

if items.get('results'):
    for item in items.get('results', []):
        print(f'\nItem ID: {item.get("id")}')
        # Print all keys to see what fields exist
        for key in sorted(item.keys()):
            if not key.startswith('_'):
                value = item.get(key)
                # Skip long values
                if isinstance(value, (str, int, float, bool, type(None))):
                    print(f'  {key}: {value}')
else:
    print('No items found')

print('\n' + '=' * 70)
print('Looking for any discount-related fields on OrderItem...')
print('=' * 70)
