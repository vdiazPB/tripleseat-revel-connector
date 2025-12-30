#!/usr/bin/env python3
"""Check all fields of a specific order to understand status."""

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

# Check the last fully-paid order we created
order_id = '10686007'

print(f"\nChecking Order {order_id}...")
print("=" * 70)

resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
if resp.status_code == 200:
    order = resp.json()
    
    # Print all fields
    print("\nAll Order Fields:")
    print("-" * 70)
    for key in sorted(order.keys()):
        value = order[key]
        print(f"{key}: {value}")
else:
    print(f"Error: {resp.status_code}")
    print(resp.text[:500])
