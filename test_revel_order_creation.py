#!/usr/bin/env python
"""Test Revel order creation directly."""

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

from integrations.revel.api_client import RevelAPIClient

print("\n=== Testing Revel Order Creation ===\n")

# Create client
client = RevelAPIClient()

# Sample order data - similar to what the webhook would create
order_data = {
    'establishment': '4',
    'local_id': 'test_order_12345',
    'notes': 'Test Order - Direct API Test',
    'items': [
        {
            'product_id': 579,  # TRIPLE OG
            'quantity': 6,
            'price': 10.20,  # $1.70 per doughnut
        },
        {
            'product_id': 571,  # MAPLE BAR
            'quantity': 4,
            'price': 6.80,  # $1.70 per doughnut
        }
    ],
    'discount_amount': 0,
    'payment_amount': 17.00,
}

print("Creating order with data:")
print(f"  Establishment: {order_data['establishment']}")
print(f"  Local ID: {order_data['local_id']}")
print(f"  Items: {len(order_data['items'])}")
print(f"  Payment Amount: ${order_data['payment_amount']}")
print()

# Create the order
created_order = client.create_order(order_data)

if created_order:
    print(f"\n✅ ORDER CREATED SUCCESSFULLY!")
    print(f"Order ID: {created_order.get('id')}")
    print(f"Order URI: {created_order.get('resource_uri')}")
    print(f"Items created: {len(created_order.get('items', []))}")
    print(f"\nFull response:")
    import json
    print(json.dumps(created_order, indent=2, default=str))
else:
    print(f"\n❌ FAILED TO CREATE ORDER")

print("\nDone!")
