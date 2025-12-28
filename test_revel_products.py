#!/usr/bin/env python
"""Direct test with logging enabled."""

import logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

from integrations.revel.api_client import RevelAPIClient

print("\n=== Testing Revel API Client with Logging ===\n")

# Create client (logs will show domain/base_url)
client = RevelAPIClient()

print(f"\nTesting get_products_by_establishment(4)...")
products = client.get_products_by_establishment('4')
print(f"Result: {len(products)} products fetched")

print("\nTesting resolve_product_by_name()...")
product = client.resolve_product_by_name('4', 'TRIPLE OG')
if product:
    print(f"✅ Found product: {product.get('name')} (ID: {product.get('id')})")
else:
    print("❌ Product 'TRIPLE OG' not found")

# Try some other names
for name in ['OG', 'MAPLE BAR', 'SUGA DADDY']:
    product = client.resolve_product_by_name('4', name)
    if product:
        print(f"✅ Found: {name} → {product.get('name')} (ID: {product.get('id')})")
    else:
        print(f"❌ Not found: {name}")

print("\nDone!")
