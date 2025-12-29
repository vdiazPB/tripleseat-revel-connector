#!/usr/bin/env python3
"""Verify if order 10684169 actually exists in Revel API"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
REVEL_DOMAIN = os.getenv('REVEL_DOMAIN')

if not all([REVEL_API_KEY, REVEL_API_SECRET, REVEL_DOMAIN]):
    print("❌ Missing environment variables")
    exit(1)

base_url = f'https://{REVEL_DOMAIN}'
headers = {
    'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'
}

# Try to fetch order 10684169
order_id = 10684169
url = f'{base_url}/resources/Order/{order_id}/'

print(f"Checking if order {order_id} exists...")
print(f"URL: {url}")
print()

resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    order = resp.json()
    print(f"✅ ORDER FOUND!")
    print(f"  ID: {order.get('id')}")
    print(f"  Subtotal: {order.get('subtotal')}")
    print(f"  Discount Amount: {order.get('discount_amount')}")
    print(f"  Final Total: {order.get('final_total')}")
    print(f"  Closed: {order.get('closed')}")
    print(f"  Printed: {order.get('printed')}")
    print(f"  Local ID: {order.get('local_id')}")
elif resp.status_code == 404:
    print(f"❌ ORDER NOT FOUND (404)")
    print(f"   The order was never created in Revel")
else:
    print(f"❌ Error: {resp.status_code}")
    print(f"   {resp.text[:300]}")
