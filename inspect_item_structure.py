#!/usr/bin/env python3
"""Inspect an OrderItem to see all available fields for discount."""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

# Get OrderItems for order 10683945
order_id = 10683945
resp = requests.get(f'{base_url}/resources/OrderItem/?limit=100', headers=headers)
items_list = resp.json()

print(f'\nSample OrderItem structure:')
print('=' * 70)

if items_list.get('results'):
    item = items_list.get('results')[0]
    print(json.dumps(item, indent=2, default=str)[:3000])
else:
    print('No items found')
