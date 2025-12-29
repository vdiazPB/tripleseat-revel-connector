#!/usr/bin/env python3
"""Check the structure of the discount-applied order"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_DOMAIN = os.getenv('REVEL_DOMAIN')

if not REVEL_API_KEY or not REVEL_DOMAIN:
    print("❌ Missing REVEL_API_KEY or REVEL_DOMAIN environment variables")
    exit(1)

base_url = f'https://{REVEL_DOMAIN}'
headers = {'Authorization': f'APIAuthentication api_key="{REVEL_API_KEY}"'}

order_id = 10684169
url = f'{base_url}/resources/Order/{order_id}/'
print(f"Fetching: {url}")
print(f"Headers: Authorization: {headers.get('Authorization')[:30]}...")
resp = requests.get(url, headers=headers)

print(f"Status: {resp.status_code}")
print(f"Raw Response: {repr(resp.text[:500])}")

if resp.status_code == 200:
    order = resp.json()
    print('\nORDER 10684169 - KEY FIELDS')
    print('=' * 70)
    print(f"ID: {order.get('id')}")
    print(f"Subtotal: {order.get('subtotal')}")
    print(f"Discount Amount: {order.get('discount_amount')}")
    print(f"Final Total: {order.get('final_total')}")
    print(f"Applied Discounts: {order.get('applied_discounts')}")
else:
    print(f"❌ Error fetching order")
