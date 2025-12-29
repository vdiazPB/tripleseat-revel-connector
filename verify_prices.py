#!/usr/bin/env python3
"""Verify order items have correct Triple Seat prices."""

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

order_id = '10683736'

print("=" * 70)
print(f"VERIFYING TRIPLE SEAT PRICES IN ORDER {order_id}")
print("=" * 70)

url = f"{base_url}/resources/Order/{order_id}/"

try:
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        order = response.json()
        items = order.get('items', [])
        
        print(f"\nOrder: {order_id}")
        print(f"  Final Total: ${order.get('final_total')}")
        print(f"  Items: {len(items)}")
        
        print(f"\nItem Details:")
        for i, item in enumerate(items, 1):
            print(f"\n  Item {i}:")
            print(f"    Product: {item.get('product')}")
            print(f"    Quantity: {item.get('quantity')}")
            print(f"    Price: ${item.get('price')}")
            print(f"    Initial Price: ${item.get('initial_price')}")
            print(f"    Price to Display: ${item.get('price_to_display')}")
            
            if item.get('price') == item.get('price_to_display'):
                print(f"    ✅ Price override successful!")
            else:
                print(f"    ⚠️ Price mismatch")
    else:
        print(f"Error: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
