#!/usr/bin/env python3
"""Check order 10685143 status"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
REVEL_DOMAIN = os.getenv('REVEL_DOMAIN')

base_url = f'https://{REVEL_DOMAIN}'
headers = {
    'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'
}

order_id = 10685143
url = f'{base_url}/resources/Order/{order_id}/'

resp = requests.get(url, headers=headers)

if resp.status_code == 200:
    order = resp.json()
    print("ORDER 10685143:")
    print("="*70)
    print(f"Created By: {order.get('created_by')}")
    print(f"Updated By: {order.get('updated_by')}")
    print(f"Subtotal: ${order.get('subtotal'):.2f}")
    print(f"Discount Amount: ${order.get('discount_amount'):.2f}")
    print(f"Discount Reason: '{order.get('discount_reason')}'")
    print(f"Final Total: ${order.get('final_total'):.2f}")
    print(f"Has OrderHistory: {bool(order.get('orderhistory'))}")
    print()
    print("Applied Discounts:")
    for d in order.get('applied_discounts', []):
        print(f"  - {d.get('name')}: ${d.get('discount_amount')}")
