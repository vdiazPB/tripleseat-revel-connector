#!/usr/bin/env python3
"""Compare several specific orders to understand what makes them 'closed'."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
base_url = "https://pinkboxdoughnuts.revelup.com"
headers = {
    "API-AUTHENTICATION": f"{REVEL_API_KEY}:{REVEL_API_SECRET}"
}

# Check specific orders we know exist
order_ids = ['10686007', '10685991', '10685962']

print("\nChecking specific orders...")
print("=" * 70)

for order_id in order_ids:
    resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
    
    if resp.status_code == 200:
        order = resp.json()
        
        print(f"\nOrder {order_id}:")
        print(f"  closed: {order.get('closed')}")
        print(f"  opened: {order.get('opened')}")
        print(f"  remaining_due: {order.get('remaining_due')}")
        print(f"  is_unpaid: {order.get('is_unpaid')}")
        print(f"  final_total: {order.get('final_total')}")
        print(f"  printed: {order.get('printed')}")
        print(f"  deleted: {order.get('deleted')}")
        print(f"  kitchen_status: {order.get('kitchen_status')}")
    else:
        print(f"\nOrder {order_id}: Error {resp.status_code}")
