#!/usr/bin/env python3
"""Find a manually closed order in Revel to see how it's marked."""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
base_url = "https://pinkboxdoughnuts.revelup.com"
headers = {
    "API-AUTHENTICATION": f"{REVEL_API_KEY}:{REVEL_API_SECRET}"
}

# Get recent orders
print("\nFetching recent orders from Revel...")
resp = requests.get(f'{base_url}/resources/Order/?limit=20&ordering=-created_date', headers=headers)

if resp.status_code == 200:
    data = resp.json()
    orders = data.get('results', [])
    
    print(f"\nFound {len(orders)} recent orders")
    print("=" * 70)
    
    for order in orders[:10]:  # Show first 10
        order_id = order.get('id')
        closed = order.get('closed')
        open_field = order.get('open')
        remaining = order.get('remaining_due')
        final_total = order.get('final_total')
        
        print(f"\nOrder {order_id}:")
        print(f"  closed: {closed}")
        print(f"  open: {open_field}")
        print(f"  remaining_due: {remaining}")
        print(f"  final_total: {final_total}")
        print(f"  is_unpaid: {order.get('is_unpaid')}")
        print(f"  kitchen_status: {order.get('kitchen_status')}")
else:
    print(f"Error: {resp.status_code}")
