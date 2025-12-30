#!/usr/bin/env python3
"""Test setting kitchen_status to close an order."""

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

# Get one of our test orders
order_id = '10686007'

print(f"\nChecking order {order_id} BEFORE updating kitchen_status...")
resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
if resp.status_code == 200:
    order = resp.json()
    print(f"  closed: {order.get('closed')}")
    print(f"  kitchen_status: {order.get('kitchen_status')}")

# Try setting kitchen_status to 1 (usually means "completed/closed")
print(f"\nUpdating kitchen_status to 1...")
update_data = {'kitchen_status': 1}
resp = requests.patch(f'{base_url}/resources/Order/{order_id}/', headers=headers, json=update_data)
print(f"Status: {resp.status_code}")

if resp.status_code in [200, 202]:
    print("Update successful!")
    print(f"\nChecking order AFTER update...")
    resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
    if resp.status_code == 200:
        order = resp.json()
        print(f"  closed: {order.get('closed')}")
        print(f"  kitchen_status: {order.get('kitchen_status')}")
else:
    print(f"Error: {resp.status_code}")
    print(resp.text[:300])
