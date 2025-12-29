#!/usr/bin/env python3
"""Test order creation with Triple Seat pricing."""

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

from integrations.revel.api_client import RevelAPIClient

print("\n" + "=" * 70)
print("CREATING ORDER WITH TRIPLE SEAT PRICING")
print("=" * 70 + "\n")

# Create client
client = RevelAPIClient()

# Order with Triple Seat custom pricing
# Note: These prices are what Triple Seat charged, not Revel's default product prices
order_data = {
    'establishment': '4',
    'local_id': 'ts_order_20251228_001',
    'notes': 'Triple Seat Event - Custom Pricing',
    'items': [
        {
            'product_id': 579,  # TRIPLE OG
            'quantity': 12,
            'price': 1.50,  # Triple Seat custom price (different from Revel's default)
        },
        {
            'product_id': 571,  # MAPLE BAR
            'quantity': 8,
            'price': 1.75,  # Triple Seat custom price
        },
        {
            'product_id': 611,  # Another product
            'quantity': 5,
            'price': 2.25,  # Triple Seat custom price
        }
    ],
    'discount_amount': 5.00,  # Discount from Triple Seat
    'payment_amount': 45.25,  # Total payment (12*1.50 + 8*1.75 + 5*2.25 - 5.00 = 45.25)
}

print("Order Details:")
print(f"  Establishment: {order_data['establishment']}")
print(f"  Local ID: {order_data['local_id']}")
print(f"  Notes: {order_data['notes']}")
print(f"\nItems with Triple Seat Pricing:")
for item in order_data['items']:
    product_id = item['product_id']
    qty = item['quantity']
    price = item['price']
    total = qty * price
    print(f"  - Product {product_id}: {qty}x @ ${price:.2f} = ${total:.2f}")

discount = order_data['discount_amount']
payment = order_data['payment_amount']
print(f"\nPricing Summary:")
print(f"  Subtotal: ${(12*1.50 + 8*1.75 + 5*2.25):.2f}")
print(f"  Discount: -${discount:.2f}")
print(f"  Final Total: ${payment:.2f}")

print("\n" + "-" * 70)
print("Creating order in Revel...")
print("-" * 70 + "\n")

# Create the order
created_order = client.create_order(order_data)

if created_order:
    order_id = created_order.get('id')
    print(f"\nSUCCESS: Order created!\n")
    print(f"Order ID: {order_id}")
    print(f"Order URI: {created_order.get('resource_uri')}")
    print(f"Final Total: ${created_order.get('final_total')}")
    print(f"Items in order: {len(created_order.get('items', []))}")
    
    if created_order.get('closed'):
        print(f"\n✅ Order is CLOSED and ready to appear in Revel UI")
    if created_order.get('printed'):
        print(f"✅ Order is marked as PRINTED")
        
    print(f"\n" + "=" * 70)
    print(f"Search for order ID {order_id} in Revel Order History")
    print(f"=" * 70)
else:
    print(f"\nFAILED: Order was not created")

print("\nDone!")
