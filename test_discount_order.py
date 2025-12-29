#!/usr/bin/env python3
"""Test order with correct discount calculation."""

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

from integrations.revel.api_client import RevelAPIClient

print("\n" + "=" * 70)
print("CREATE ORDER WITH CORRECTED DISCOUNT")
print("=" * 70 + "\n")

client = RevelAPIClient()

# Order with correct pricing
order_data = {
    'establishment': '4',
    'local_id': 'ts_order_20251228_discount',
    'notes': 'Test Order - Discount Applied',
    'items': [
        {
            'product_id': 579,
            'quantity': 10,
            'price': 2.00,  # $20.00 subtotal
        },
        {
            'product_id': 571,
            'quantity': 5,
            'price': 3.00,  # $15.00 subtotal
        }
    ],
    'discount_amount': 5.00,  # $5 discount
    'payment_amount': 30.00,  # $20 + $15 - $5 = $30
}

print("Order with Discount:")
print(f"  Item 1: 10x @ $2.00 = $20.00")
print(f"  Item 2: 5x @ $3.00 = $15.00")
print(f"  Subtotal: $35.00")
print(f"  Discount: -$5.00")
print(f"  Final Total: $30.00")

print("\nCreating order...")
created_order = client.create_order(order_data)

if created_order:
    order_id = created_order.get('id')
    print(f"\n✅ SUCCESS!")
    print(f"Order ID: {order_id}")
    print(f"Subtotal: ${created_order.get('subtotal')}")
    print(f"Discount: ${created_order.get('discount_amount')}")
    print(f"Final Total: ${created_order.get('final_total')}")
    print(f"Closed: {created_order.get('closed')}")
    print(f"\nSearch for Order {order_id} in Revel Order History")
else:
    print(f"\n❌ FAILED")

print("\nDone!")
