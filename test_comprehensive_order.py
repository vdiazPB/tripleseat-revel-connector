#!/usr/bin/env python3
"""Test another order - comprehensive test with all features."""

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

from integrations.revel.api_client import RevelAPIClient

print("\n" + "=" * 70)
print("COMPREHENSIVE ORDER TEST")
print("=" * 70 + "\n")

client = RevelAPIClient()

# Realistic Triple Seat catering order
order_data = {
    'establishment': '4',
    'local_id': 'tripleseat_event_12345',
    'notes': 'Corporate Event Catering - TripleSeat',
    'items': [
        {
            'product_id': 579,  # TRIPLE OG
            'quantity': 24,
            'price': 1.25,
        },
        {
            'product_id': 571,  # MAPLE BAR
            'quantity': 12,
            'price': 1.50,
        },
        {
            'product_id': 611,  # Coffee
            'quantity': 3,
            'price': 4.99,
        }
    ],
    'discount_amount': 10.00,  # Corporate discount
    'payment_amount': 52.97,  # (24*1.25 + 12*1.50 + 3*4.99) - 10.00 = final total
}

subtotal = 24*1.25 + 12*1.50 + 3*4.99
final = subtotal - 10.00

print("Corporate Event Order:")
print(f"  Event Name: Corporate Event Catering - TripleSeat")
print(f"  Items:")
print(f"    - 24x TRIPLE OG @ $1.25 = $30.00")
print(f"    - 12x MAPLE BAR @ $1.50 = $18.00")
print(f"    - 3x Coffee Service @ $4.99 = $14.97")
print(f"  Subtotal: ${subtotal:.2f}")
print(f"  Corporate Discount: -$10.00")
print(f"  Final Total: ${final:.2f}")

print("\nCreating order in Revel...")
print("-" * 70 + "\n")

created_order = client.create_order(order_data)

if created_order:
    order_id = created_order.get('id')
    print(f"\n" + "=" * 70)
    print(f"SUCCESS - Order Created!")
    print(f"=" * 70)
    print(f"\nOrder ID: {order_id}")
    print(f"Order URI: {created_order.get('resource_uri')}")
    print(f"\nFinancial Summary:")
    print(f"  Subtotal: ${subtotal:.2f}")
    print(f"  Discount: -$10.00")
    print(f"  Final Total: ${final:.2f}")
    print(f"\nStatus:")
    print(f"  Closed: {created_order.get('closed')}")
    print(f"  Printed: {created_order.get('printed')}")
    print(f"  Items: {len(created_order.get('items', []))}")
    
    print(f"\n" + "=" * 70)
    print(f"Search for Order {order_id} in Revel Order History")
    print(f"=" * 70)
else:
    print(f"\nFAILED - Order was not created")

print("\nDone!")
