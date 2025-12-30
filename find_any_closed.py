#!/usr/bin/env python3
"""Find any closed order across all establishments."""

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

# Get all orders and look for closed ones
print("\nSearching for closed orders across all establishments...")
print("=" * 70)

resp = requests.get(f'{base_url}/resources/Order/?ordering=-id', headers=headers)

if resp.status_code == 200:
    data = resp.json()
    orders = data.get('results', [])
    
    closed_orders = [o for o in orders if o.get('closed')]
    
    print(f"Found {len(closed_orders)} closed orders out of {len(orders)} total\n")
    
    if closed_orders:
        # Show the first few closed orders
        for i, order in enumerate(closed_orders[:5]):
            order_id = order.get('id')
            est_uri = order.get('establishment')
            remaining = order.get('remaining_due')
            final_total = order.get('final_total')
            is_unpaid = order.get('is_unpaid')
            printed = order.get('printed')
            deleted = order.get('deleted')
            
            print(f"\nClosed Order {order_id}:")
            print(f"  establishment: {est_uri}")
            print(f"  remaining_due: {remaining}")
            print(f"  final_total: {final_total}")
            print(f"  is_unpaid: {is_unpaid}")
            print(f"  printed: {printed}")
            print(f"  deleted: {deleted}")
            
            # Get full details
            detail_resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
            if detail_resp.status_code == 200:
                o = detail_resp.json()
                print(f"  opened: {o.get('opened')}")
                print(f"  kitchen_status: {o.get('kitchen_status')}")
                print(f"  version: {o.get('version')}")
    else:
        print("No closed orders found!")
        print("\nShowing sample of recent orders:")
        for order in orders[:10]:
            order_id = order.get('id')
            closed = order.get('closed')
            remaining = order.get('remaining_due')
            est = order.get('establishment')
            print(f"  Order {order_id}: closed={closed}, remaining_due={remaining}, est={est}")
else:
    print(f"Error: {resp.status_code}")
