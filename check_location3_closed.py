#!/usr/bin/env python3
"""Check orders from location 3 to find a closed order and see what makes it closed."""

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

# Get recent orders from establishment 3
print("\nFetching orders from Establishment 3...")
print("=" * 70)

# Establishment 3 - try with just ID
resp = requests.get(
    f'{base_url}/resources/Order/?establishment=3&limit=50&ordering=-created_date', 
    headers=headers
)

if resp.status_code == 200:
    data = resp.json()
    orders = data.get('results', [])
    
    print(f"Found {len(orders)} orders from Establishment 3\n")
    
    # Look for closed orders
    closed_count = 0
    for order in orders:
        order_id = order.get('id')
        closed = order.get('closed')
        remaining = order.get('remaining_due')
        final_total = order.get('final_total')
        is_unpaid = order.get('is_unpaid')
        printed = order.get('printed')
        
        if closed:
            closed_count += 1
            print(f"\n[CLOSED] Order {order_id}:")
            print(f"  closed: {closed}")
            print(f"  remaining_due: {remaining}")
            print(f"  final_total: {final_total}")
            print(f"  is_unpaid: {is_unpaid}")
            print(f"  printed: {printed}")
            print(f"  created_date: {order.get('created_date')}")
            
            # Get full order details for this closed order
            print(f"\n  Full details of closed order {order_id}:")
            closed_resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
            if closed_resp.status_code == 200:
                closed_order = closed_resp.json()
                # Print key fields
                print(f"    - opened: {closed_order.get('opened')}")
                print(f"    - kitchen_status: {closed_order.get('kitchen_status')}")
                print(f"    - deleted: {closed_order.get('deleted')}")
                print(f"    - pos_mode: {closed_order.get('pos_mode')}")
                
            if closed_count >= 3:
                break
    
    if closed_count == 0:
        print("\nNo closed orders found in location 3. Showing all recent orders:")
        for order in orders[:10]:
            order_id = order.get('id')
            closed = order.get('closed')
            remaining = order.get('remaining_due')
            print(f"\nOrder {order_id}: closed={closed}, remaining_due={remaining}")
else:
    print(f"Error: {resp.status_code}")
    print(resp.text[:500])
