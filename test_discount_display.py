#!/usr/bin/env python3
"""Test discount display - create and verify immediately."""

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

import os
import requests
from integrations.revel.api_client import RevelAPIClient

client = RevelAPIClient()

# Simple order with clear discount
order_data = {
    'establishment': '4',
    'local_id': 'Triple Seat 55521609',  # Use Triple Seat event format
    'notes': 'Discount Test Order',
    'customer_name': 'Jon Ponder',  # Customer name from Triple Seat
    'customer_phone': '(555) 123-4567',  # Customer phone from Triple Seat
    'items': [
        {
            'product_id': 579,  # TRIPLE OG
            'quantity': 5,
            'price': 2.00,  # 5 x $2 = $10
        },
    ],
    'discount_amount': 2.50,  # 25% off = $2.50 discount
    'payment_amount': 7.50,  # $10 - $2.50 = $7.50
}

print("\nDISCOUNT TEST ORDER")
print("=" * 70)
print("Items: 5x TRIPLE OG @ $2.00 = $10.00")
print("Discount: -$2.50")
print("Final Total: $7.50")
print("=" * 70 + "\n")

# Create order
created_order = client.create_order(order_data)

if created_order:
    order_id = created_order.get('id')
    print(f"\n[OK] Order {order_id} created\n")
    
    # Immediately verify via API
    print("Verifying via Revel API...")
    print("-" * 70)
    
    REVEL_API_KEY = os.getenv('REVEL_API_KEY')
    REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
    headers = {
        "API-AUTHENTICATION": f"{REVEL_API_KEY}:{REVEL_API_SECRET}"
    }
    
    base_url = "https://pinkboxdoughnuts.revelup.com"
    resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
    order = resp.json()
    
    print(f"Subtotal:        ${order.get('subtotal', 0):.2f}")
    print(f"Discount Amount: ${order.get('discount_amount', 0):.2f}")
    print(f"Final Total:     ${order.get('final_total', 0):.2f}")
    print(f"Is Discounted:   {order.get('is_discounted')}")
    print()
    print("Applied Discounts:")
    for d in order.get('applied_discounts', []):
        disc_amt = float(d.get('discount_amount', 0))
        print(f'  - {d.get("name")}: ${disc_amt:.2f}')
    
    print()
    print("=" * 70)
    print(f"NOW CHECK REVEL UI FOR ORDER #{order_id}")
    print("Look at Order History and check if discount shows")
    print("=" * 70)
else:
    print("[FAILED] Failed to create order")

print()
