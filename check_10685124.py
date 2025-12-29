#!/usr/bin/env python3
"""Check order 10685124 status"""
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

order_id = 10685124
url = f'{base_url}/resources/Order/{order_id}/'

resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}\n")

if resp.status_code == 200:
    order = resp.json()
    print("ORDER 10685124 - KEY FIELDS:")
    print("="*70)
    print(f"ID: {order.get('id')}")
    print(f"Created By: {order.get('created_by')}")
    print(f"Updated By: {order.get('updated_by')}")
    print(f"Subtotal: {order.get('subtotal')}")
    print(f"Discount Amount: {order.get('discount_amount')}")
    print(f"Discount Reason: {order.get('discount_reason')}")
    print(f"Final Total: {order.get('final_total')}")
    print(f"OrderHistory Records: {order.get('orderhistory')}")
    print(f"Has History: {order.get('has_history')}")
    print()
    print("Applied Discounts:")
    for d in order.get('applied_discounts', []):
        print(f"  - {d.get('name')}: ${d.get('discount_amount')}")
