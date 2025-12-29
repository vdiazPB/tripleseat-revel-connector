#!/usr/bin/env python3
"""Create order and properly apply discount using AppliedDiscountOrder."""

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

import os
import requests
import uuid
from datetime import datetime, timezone

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

now = datetime.now(timezone.utc).isoformat()

# Create a test order
order_data = {
    'closed': False,
    'establishment': '/enterprise/Establishment/4/',
    'created_by': '/enterprise/User/209/',
    'updated_by': '/enterprise/User/209/',
    'created_at': '/resources/PosStation/4/',
    'last_updated_at': '/resources/PosStation/4/',
    'local_id': 'applied_discount_test_' + str(uuid.uuid4())[:8],
    'notes': 'Testing AppliedDiscountOrder',
}

print('\n1. Creating order...')
resp = requests.post(f'{base_url}/resources/Order/', headers=headers, json=order_data)
if resp.status_code not in [200, 201]:
    print(f'   FAILED: {resp.status_code}')
    print(resp.text)
else:
    order = resp.json()
    order_id = order.get('id')
    order_uri = order.get('resource_uri')
    print(f'   ✅ Order {order_id} created')
    
    # Add item
    print('2. Adding item...')
    item_data = {
        'order': order_uri,
        'product': '/resources/Product/579/',
        'quantity': 5,
        'price': 2.00,
    }
    resp = requests.post(f'{base_url}/resources/OrderItem/', headers=headers, json=item_data)
    if resp.status_code in [200, 201]:
        print(f'   ✅ Item added')
    
    # Try to create AppliedDiscountOrder directly
    print('3. Creating AppliedDiscountOrder...')
    applied_discount_data = {
        'order': order_uri,
        'discount': '/resources/Discount/3358/',
        'discount_amount': 2.50,  # Set the amount here!
        'uuid': str(uuid.uuid4()),
    }
    resp = requests.post(f'{base_url}/resources/AppliedDiscountOrder/', headers=headers, json=applied_discount_data)
    print(f'   Status: {resp.status_code}')
    if resp.status_code in [200, 201]:
        applied = resp.json()
        print(f'   ✅ Applied Discount created')
        print(f'      Amount: {applied.get("discount_amount")}')
    else:
        print(f'   ❌ Failed: {resp.text[:200]}')
    
    # Check order
    print('4. Checking order...')
    resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
    order = resp.json()
    print(f'   discount_amount: {order.get("discount_amount")}')
    print(f'   final_total: {order.get("final_total")}')
    print(f'   Applied Discounts:')
    for d in order.get('applied_discounts', []):
        print(f'     - {d.get("name")}: ${float(d.get("discount_amount", 0)):.2f}')
    
    print(f'\n   ORDER ID: {order_id}')
