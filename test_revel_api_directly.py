#!/usr/bin/env python
"""Direct test of Revel API client to see URL construction."""

from dotenv import load_dotenv
load_dotenv()

from integrations.revel.api_client import RevelAPIClient

print("\n=== Testing Revel API Client ===\n")

# Create client (logs will show domain/base_url)
client = RevelAPIClient()

print(f"Client created successfully")
print(f"API Key (last 8): {client.api_key[-8:] if client.api_key else 'MISSING'}")
print(f"API Secret (last 8): {client.api_secret[-8:] if client.api_secret else 'MISSING'}")

# Try to fetch products
print("\nTesting get_products_by_establishment(4)...")
products = client.get_products_by_establishment('4')
print(f"Result: {len(products)} products fetched")

if products:
    print(f"First product: {products[0].get('name', 'N/A')}")
else:
    print("No products returned (expected for test - API may have failed)")

print("\nTesting get_order()...")
order = client.get_order('test_order_id', '4')
print(f"Order check result: {order}")

print("\nDone!")
