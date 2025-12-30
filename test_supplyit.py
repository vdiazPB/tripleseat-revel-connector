#!/usr/bin/env python3
"""
Test script to verify Supply It (JERA) API integration.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_supplyit_connection():
    """Test Supply It API connection and basic operations."""
    
    print("=" * 60)
    print("SUPPLY IT (JERA) API TEST")
    print("=" * 60)
    print()
    
    # Check environment variables
    api_key = os.getenv('JERA_API_KEY')
    username = os.getenv('JERA_API_USERNAME')
    api_base = os.getenv('SUPPLYIT_API_BASE', 'https://api.supplyit.com/api/v2')
    
    print("Configuration:")
    print(f"  API Base: {api_base}")
    print(f"  API Key: {'SET' if api_key else 'NOT SET'}")
    print(f"  Username: {username if username else 'NOT SET'}")
    print()
    
    if not api_key or not username:
        print("[ERROR] Missing JERA_API_KEY or JERA_API_USERNAME")
        return False
    
    try:
        from integrations.supplyit.api_client import SupplyItAPIClient
        
        print("=" * 60)
        print("STEP 1: Initialize Supply It Client")
        print("=" * 60)
        client = SupplyItAPIClient()
        print("[OK] Client initialized")
        print()
        
        print("=" * 60)
        print("STEP 2: Get Locations by Code")
        print("=" * 60)
        locations = client.get_location_by_code("8")
        
        if locations:
            print(f"[OK] Found location code '8' (PB Special Events):")
            print(f"  ID: {locations.get('ID')}")
            print(f"  Name: {locations.get('Name')}")
            print(f"  Code: {locations.get('Code')}")
            print(f"  Status: {locations.get('LocationStatus')}")
            location_id = locations.get('ID')
        else:
            print("[WARNING] Location code '8' not found")
            print("  This may indicate:")
            print("  - Location doesn't exist in Supply It")
            print("  - API credentials are invalid")
            return False
        
        print()
        print("=" * 60)
        print("STEP 3: Get Sample Products")
        print("=" * 60)
        
        # Try to get a common product
        product = client.get_product_by_name(location_id, "Glazed Dozen")
        if product:
            print(f"[OK] Found product 'Glazed Dozen':")
            print(f"  ID: {product.get('ID')}")
            print(f"  Name: {product.get('Name')}")
            print(f"  Code: {product.get('Code')}")
        else:
            print("[INFO] Product 'Glazed Dozen' not found (expected - may have different name)")
            print("  Supply It products may need to be mapped from TripleSeat items")
        
        print()
        print("=" * 60)
        print("STEP 4: Test Order Creation (Dry Run)")
        print("=" * 60)
        
        # Build a test order
        test_order = {
            "Location": {
                "ID": location_id,
                "Name": "Special Events"
            },
            "Contact": {
                "Name": "Test Contact"
            },
            "OrderDate": "2025-12-29T00:00:00",
            "OrderItems": [
                {
                    "Product": {
                        "ID": 1,  # Use a dummy product ID for testing
                        "Name": "Test Product"
                    },
                    "UnitsOrdered": 1,
                    "UnitPrice": 10.00
                }
            ],
            "OrderNotes": "Test order from connector",
            "OrderStatus": "Open"
        }
        
        print("Test order structure:")
        import json
        print(json.dumps(test_order, indent=2))
        print()
        print("[INFO] In production, this order would be created in Supply It")
        print("[INFO] Test complete - supply It connection is working")
        
        print()
        print("=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print("[OK] Supply It API is accessible")
        print("[OK] Special Events location exists")
        print("[OK] Authentication headers configured correctly")
        print()
        print("Next steps:")
        print("1. Deploy webhook to production")
        print("2. Send DEFINITE status event from TripleSeat")
        print("3. Monitor logs for Supply It order creation")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_supplyit_connection()
    sys.exit(0 if success else 1)
