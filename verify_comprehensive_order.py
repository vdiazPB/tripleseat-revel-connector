#!/usr/bin/env python3
"""Verify the comprehensive order in Revel."""

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

import os
import requests

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = "https://pinkboxdoughnuts.revelup.com"
headers = {
    "API-AUTHENTICATION": f"{REVEL_API_KEY}:{REVEL_API_SECRET}"
}

# Fetch order 10683828
order_id = 10683828
print(f"\nVerifying Order {order_id}...")
print("=" * 70)

order_response = requests.get(
    f"{base_url}/resources/Order/{order_id}/",
    headers=headers
)

if order_response.status_code == 200:
    order = order_response.json()
    
    print(f"\nOrder Details:")
    print(f"  ID: {order.get('id')}")
    print(f"  Local ID: {order.get('local_id')}")
    print(f"  Status: {'CLOSED' if order.get('closed') else 'OPEN'}")
    
    print(f"\nFinancial Details:")
    print(f"  Subtotal: ${order.get('subtotal', 0):.2f}")
    print(f"  Discount Amount: ${order.get('discount_amount', 0):.2f}")
    print(f"  Final Total: ${order.get('final_total', 0):.2f}")
    
    # Verify items
    print(f"\nItems ({len(order.get('items', []))} items):")
    for item in order.get('items', []):
        print(f"  - Product {item.get('product')} qty={item.get('quantity')}")
        print(f"    Price: ${item.get('price', 0):.2f}, Initial: ${item.get('initial_price', 0):.2f}")
    
    # Check flags
    print(f"\nFlags:")
    print(f"  Closed: {order.get('closed')}")
    print(f"  Printed: {order.get('printed')}")
    
    print(f"\n" + "=" * 70)
    expected_subtotal = 24*1.25 + 12*1.50 + 3*4.99
    expected_discount = 10.00
    expected_final = expected_subtotal - expected_discount
    
    subtotal_ok = abs(order.get('subtotal', 0) - expected_subtotal) < 0.01
    discount_ok = abs(order.get('discount_amount', 0) - expected_discount) < 0.01
    final_ok = abs(order.get('final_total', 0) - expected_final) < 0.01
    closed_ok = order.get('closed') == True
    printed_ok = order.get('printed') == True
    
    if subtotal_ok and discount_ok and final_ok and closed_ok and printed_ok:
        print("✅ ORDER VERIFIED - All values correct!")
    else:
        print("⚠️  Some fields don't match expected values")
        if not subtotal_ok:
            print(f"   Subtotal mismatch: got {order.get('subtotal')}, expected {expected_subtotal}")
        if not discount_ok:
            print(f"   Discount mismatch: got {order.get('discount_amount')}, expected {expected_discount}")
        if not final_ok:
            print(f"   Final mismatch: got {order.get('final_total')}, expected {expected_final}")
        if not closed_ok:
            print(f"   Closed flag: {order.get('closed')}, expected True")
        if not printed_ok:
            print(f"   Printed flag: {order.get('printed')}, expected True")
    
    print("=" * 70)
else:
    print(f"ERROR: {order_response.status_code}")
    print(order_response.text)

print("\n✅ Done! Check Revel Order History for order #{}\n".format(order_id))
