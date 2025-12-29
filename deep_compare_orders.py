#!/usr/bin/env python3
"""Deep comparison of working vs non-working order"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
REVEL_DOMAIN = os.getenv('REVEL_DOMAIN')

base_url = f'https://{REVEL_DOMAIN}'
headers = {
    'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'
}

# Working order vs new order
orders = {
    '10684118': 'WORKS (appears in Order History)',
    '10685039': 'NEW (not appearing)'
}

for order_id, note in orders.items():
    print(f"\n{'='*70}")
    print(f"ORDER {order_id} - {note}")
    print('='*70)
    
    url = f'{base_url}/resources/Order/{order_id}/'
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        order = resp.json()
        # Print all fields
        for key in sorted(order.keys()):
            value = order[key]
            if isinstance(value, (list, dict)):
                print(f"  {key}: {str(value)[:80]}...")
            else:
                print(f"  {key}: {value}")
