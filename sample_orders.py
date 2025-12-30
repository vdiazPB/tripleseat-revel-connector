#!/usr/bin/env python3
"""Get sample of orders to understand closed status."""

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

print("\nFetching sample orders...")

# Try with simple filter
resp = requests.get(f'{base_url}/resources/Order/?limit=5', headers=headers, timeout=5)

print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    print(f"Count: {data.get('meta', {}).get('total_count', 'unknown')}")
    
    orders = data.get('results', [])
    print(f"\nSample of {len(orders)} orders:")
    print("=" * 70)
    
    for order in orders:
        order_id = order.get('id')
        closed = order.get('closed')
        remaining = order.get('remaining_due')
        print(f"\nOrder {order_id}:")
        print(f"  closed: {closed}")
        print(f"  remaining_due: {remaining}")
else:
    print(f"Error: {resp.text[:300]}")
