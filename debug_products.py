#!/usr/bin/env python3
"""Debug script to check Revel products for HEY BLONDIE and FUDGY WUDGY"""

import os
import sys
from integrations.revel.api_client import RevelAPIClient

# Initialize client
client = RevelAPIClient(
    domain=os.getenv('REVEL_DOMAIN'),
    api_key=os.getenv('REVEL_API_KEY'),
    default_user_id=1
)

# Get all products for establishment 4
products = client.get_products_by_establishment('4')

print(f"\n✅ Total products in establishment 4: {len(products)}\n")

# Search for HEY BLONDIE and FUDGY WUDGY
search_terms = ['HEY BLONDIE', 'FUDGY WUDGY', 'BLONDIE', 'FUDGY', 'BLONDE', 'WUDGY']

for term in search_terms:
    print(f"\n📍 Searching for products containing '{term}':")
    term_lower = term.lower()
    matches = [p for p in products if term_lower in p.get('name', '').lower()]
    
    if matches:
        for p in matches:
            print(f"   - ID: {p.get('id'):6} | Name: '{p.get('name')}' | Price: ${p.get('price', 0)}")
    else:
        print(f"   ❌ No matches")

# Show first 20 products to verify data
print(f"\n📋 First 20 products in establishment 4:")
for i, p in enumerate(products[:20], 1):
    print(f"   {i:2}. ID: {p.get('id'):6} | Name: '{p.get('name')}' | Price: ${p.get('price', 0)}")
