#!/usr/bin/env python3
"""List all products in JERA Special Events location."""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integrations.supplyit.api_client import SupplyItAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def main():
    load_dotenv()
    
    api_key = os.getenv('JERA_API_KEY')
    api_user = os.getenv('JERA_API_USERNAME')
    
    if not api_key or not api_user:
        print("❌ Missing JERA_API_KEY or JERA_API_USERNAME in .env")
        sys.exit(1)
    
    client = SupplyItAPIClient()
    
    # Get Special Events location
    location = client.get_location_by_code('8')
    if not location:
        print("❌ Location code '8' not found")
        sys.exit(1)
    
    location_id = location.get('ID') or location.get('id')
    print(f"[OK] Special Events location: ID {location_id}")
    print()
    
    # Get all products for this location
    print("Fetching products...")
    try:
        import requests
        url = f"{os.getenv('SUPPLYIT_API_BASE')}/locations/{location_id}/products"
        headers = {
            'Authorization': api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Api-User': api_user
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch products: HTTP {response.status_code}")
            sys.exit(1)
        
        data = response.json()
        products = data if isinstance(data, list) else data.get('products', [])
        
        print(f"Found {len(products)} products:\n")
        print(f"{'Name':<40} {'ID':<10} {'SKU':<15} {'Active':<10}")
        print("-" * 75)
        
        for product in products:
            # Handle both camelCase and PascalCase keys
            name = (product.get('Name') or product.get('name') or 'Unknown')[:37]
            pid = product.get('ID') or product.get('id') or 'N/A'
            sku = (product.get('SKU') or product.get('sku') or '')[:12]
            active_val = product.get('Active') or product.get('active') or False
            active = 'Yes' if active_val else 'No'
            print(f"{name:<40} {str(pid):<10} {sku:<15} {active:<10}")
        
        print("\n" + "=" * 75)
        print(f"Total products: {len(products)}")
        
    except Exception as e:
        print(f"❌ Error fetching products: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
