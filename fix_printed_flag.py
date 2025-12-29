#!/usr/bin/env python3
"""Verify finalize response - check if printed flag was set"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
REVEL_DOMAIN = os.getenv('REVEL_DOMAIN')

base_url = f'https://{REVEL_DOMAIN}'
headers = {
    'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}',
    'Content-Type': 'application/json'
}

order_id = 10684169
url = f'{base_url}/resources/Order/{order_id}/'

# Try to manually set printed = True
print("Attempting to set printed = True...")
finalize_data = {
    'printed': True,
}

resp = requests.patch(url, headers=headers, json=finalize_data)
print(f"Status: {resp.status_code}")

if resp.status_code in [200, 202]:
    order = resp.json()
    print(f"✅ Successfully updated order")
    print(f"  Printed: {order.get('printed')}")
    print(f"  Closed: {order.get('closed')}")
    print(f"  Discount Amount: {order.get('discount_amount')}")
    print(f"  Final Total: {order.get('final_total')}")
else:
    print(f"❌ Error: {resp.status_code}")
    print(f"   {resp.text[:500]}")
