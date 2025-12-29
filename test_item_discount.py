#!/usr/bin/env python3
"""Create an order and apply discount at ITEM level instead."""

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

import os
import requests
import json

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

# Create a simple order first
order_data = {
    'closed': False,
    'establishment': '/enterprise/Establishment/4/',
    'local_id': 'item_discount_test',
    'notes': 'Testing item-level discount',
}

print('\n1. Creating order...')
resp = requests.post(f'{base_url}/resources/Order/', headers=headers, json=order_data)
order = resp.json()
order_id = order.get('id')
order_uri = order.get('resource_uri')
print(f'   Order {order_id} created')

# Add item
item_data = {
    'order': order_uri,
    'product': '/resources/Product/579/',
    'quantity': 5,
    'price': 2.00,
}

print('2. Adding item...')
resp = requests.post(f'{base_url}/resources/OrderItem/', headers=headers, json=item_data)
item = resp.json()
item_id = item.get('id')
print(f'   Item {item_id} added')

# Apply discount at ORDER level like we do
print('3. Applying discount at order level...')
discount_data = {
    'discount': '/resources/Discount/3358/',
    'discount_amount': 2.50,
}
resp = requests.patch(f'{base_url}/resources/Order/{order_id}/', headers=headers, json=discount_data)
print(f'   Discount PATCH status: {resp.status_code}')

# Check what the order looks like now
print('4. Checking order after discount...')
resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
order = resp.json()
print(f'   discount_amount: {order.get("discount_amount")}')
print(f'   applied_discounts: {len(order.get("applied_discounts", []))} discounts')
for d in order.get('applied_discounts', []):
    print(f'     - {d.get("name")}: ${d.get("discount_amount")}')

print()
print('ORDER ID: {}'.format(order_id))
print()
