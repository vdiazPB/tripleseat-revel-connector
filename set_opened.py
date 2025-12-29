#!/usr/bin/env python3
"""Try setting opened=True on order 10684977"""
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

order_id = 10684977
url = f'{base_url}/resources/Order/{order_id}/'

print(f"Setting opened=True on order {order_id}...")
resp = requests.patch(url, headers=headers, json={'opened': True})
print(f"Status: {resp.status_code}")

if resp.status_code in [200, 202]:
    order = resp.json()
    print(f"✅ Updated!")
    print(f"  Opened: {order.get('opened')}")
    print(f"  Closed: {order.get('closed')}")
    print(f"  Printed: {order.get('printed')}")
else:
    print(f"❌ Error: {resp.status_code}")
    print(resp.text[:300])
