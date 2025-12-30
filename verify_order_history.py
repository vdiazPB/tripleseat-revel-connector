#!/usr/bin/env python3
"""Verify that orders appear in Revel Order History and check their status."""

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

# Check our recent test orders
test_order_ids = ['10686007', '10685991', '10685962']

print("\n" + "=" * 70)
print("CHECKING IF ORDERS APPEAR IN REVEL ORDER HISTORY")
print("=" * 70)

for order_id in test_order_ids:
    print(f"\nOrder {order_id}:")
    
    # Get the order
    resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
    if resp.status_code == 200:
        order = resp.json()
        
        # Check if it has Order History records
        orderhistory_uris = order.get('orderhistory', [])
        
        print(f"  In Order History: {len(orderhistory_uris) > 0}")
        print(f"  Order History records: {orderhistory_uris}")
        print(f"  closed: {order.get('closed')}")
        print(f"  remaining_due: {order.get('remaining_due')}")
        print(f"  is_unpaid: {order.get('is_unpaid')}")
        
        # Check the OrderHistory details if it exists
        if orderhistory_uris:
            hist_uri = orderhistory_uris[0]
            hist_resp = requests.get(f'{base_url}{hist_uri}', headers=headers)
            if hist_resp.status_code == 200:
                hist = hist_resp.json()
                print(f"\n  OrderHistory Details:")
                print(f"    - opened: {hist.get('opened')}")
                print(f"    - closed: {hist.get('closed')}")
    else:
        print(f"  Error: {resp.status_code}")
