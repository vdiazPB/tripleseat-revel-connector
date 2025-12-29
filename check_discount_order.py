#!/usr/bin/env python3
"""Check the actual order in Revel API."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('REVEL_API_KEY')
api_secret = os.getenv('REVEL_API_SECRET')
domain = os.getenv('REVEL_DOMAIN', 'pinkboxdoughnuts.revelup.com')

base_url = f"https://{domain}"
headers = {
    'API-AUTHENTICATION': f'{api_key}:{api_secret}',
    'Content-Type': 'application/json'
}

order_id = '10683804'

print(f"\nChecking Order {order_id}...")

url = f"{base_url}/resources/Order/{order_id}/"

response = requests.get(url, headers=headers)
order = response.json()

print(f"  Subtotal: ${order.get('subtotal')}")
print(f"  Discount Amount: ${order.get('discount_amount')}")
print(f"  Final Total: ${order.get('final_total')}")
print(f"  Closed: {order.get('closed')}")
print(f"  Printed: {order.get('printed')}")
