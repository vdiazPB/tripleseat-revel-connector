#!/usr/bin/env python3
"""Verify that created orders exist in Revel."""

import os
import requests
import base64
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

# Order IDs to check
order_ids = ['10683655', '10683658']

print("=" * 70)
print("VERIFYING ORDERS IN REVEL")
print("=" * 70)

for order_id in order_ids:
    print(f"\n📋 Order ID: {order_id}")
    print("-" * 70)
    
    url = f"{base_url}/resources/Order/{order_id}/"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            order = response.json()
            print(f"✅ Order found in Revel!")
            print(f"   Status: {response.status_code}")
            print(f"   Local ID: {order.get('local_id')}")
            print(f"   Establishment: {order.get('establishment')}")
            print(f"   Items: {len(order.get('items', []))}")
            print(f"   Notes: {order.get('notes')}")
            print(f"   Web Order: {order.get('web_order')}")
            print(f"   Opened: {order.get('opened')}")
            print(f"   Closed: {order.get('closed')}")
            print(f"   Final Total: ${order.get('final_total', 0)}")
            print(f"   Created Date: {order.get('created_date')}")
            
            # Check if order has items
            items = order.get('items', [])
            if items:
                print(f"\n   Items:")
                for item in items:
                    print(f"   - {item.get('product')} x{item.get('quantity')} @ ${item.get('price')}")
        else:
            print(f"❌ Order NOT found!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error fetching order: {e}")

print("\n" + "=" * 70)
print("CHECKING ESTABLISHMENT 4 ORDERS")
print("=" * 70)

# List all orders for establishment 4
url = f"{base_url}/resources/Order/"
params = {
    'establishment': '4',
    'limit': 100,
    'ordering': '-created_date'  # Most recent first
}

try:
    response = requests.get(url, headers=headers, params=params, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        orders = data.get('objects', [])
        print(f"\n✅ Found {len(orders)} orders in Establishment 4")
        
        print("\nMost recent orders:")
        for order in orders[:5]:  # Show top 5
            order_id = order.get('id')
            local_id = order.get('local_id')
            opened = order.get('opened')
            created = order.get('created_date', '')[:10]
            print(f"  - Order {order_id}: local_id={local_id}, opened={opened}, created={created}")
    else:
        print(f"\n❌ Failed to list orders: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Error listing orders: {e}")

print("\n" + "=" * 70)
