#!/usr/bin/env python3
"""Verify the new order appears in Revel."""

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

order_id = '10683701'

print("=" * 70)
print(f"CHECKING NEW ORDER: {order_id}")
print("=" * 70)

url = f"{base_url}/resources/Order/{order_id}/"

try:
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        order = response.json()
        print(f"\nOrder found!")
        print(f"  Local ID: {order.get('local_id')}")
        print(f"  Final Total: ${order.get('final_total')}")
        print(f"  Subtotal: ${order.get('subtotal')}")
        print(f"  Closed: {order.get('closed')}")
        print(f"  Printed: {order.get('printed')}")
        print(f"  Items: {len(order.get('items', []))}")
        
        if order.get('closed'):
            print(f"\n✅ ORDER SHOULD NOW APPEAR IN REVEL UI!")
        else:
            print(f"\n❌ Order not closed yet")
    else:
        print(f"Order not found: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
