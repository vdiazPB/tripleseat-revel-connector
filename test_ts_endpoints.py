#!/usr/bin/env python3
"""Test different TripleSeat endpoints to find items data"""

import json
from dotenv import load_dotenv
from integrations.tripleseat.api_client import TripleSeatAPIClient

load_dotenv()

EVENT_ID = 55521609
BOOKING_ID = 52511006

client = TripleSeatAPIClient()
print(f"\nTesting TripleSeat API Endpoints for Event {EVENT_ID}\n")
print("=" * 80)

# Test different potential endpoints
endpoints = [
    f"/v1/events/{EVENT_ID}",
    f"/v1/events/{EVENT_ID}/items",
    f"/v1/events/{EVENT_ID}/line_items",
    f"/v1/events/{EVENT_ID}/menu_items",
    f"/v1/bookings/{BOOKING_ID}",
    f"/v1/bookings/{BOOKING_ID}/items",
    f"/v1/bookings/{BOOKING_ID}/line_items",
    f"/v1/events/{EVENT_ID}/documents",
]

for endpoint in endpoints:
    url = f"{client.base_url}{endpoint}"
    print(f"\n[TEST] {endpoint}")
    print(f"  URL: {url}")
    
    try:
        response = client.session.get(url, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ SUCCESS - Response type: {type(data).__name__}")
            
            # Try to identify items
            if isinstance(data, dict):
                if 'items' in data:
                    print(f"    Found 'items' key with {len(data['items'])} items")
                if 'line_items' in data:
                    print(f"    Found 'line_items' key with {len(data['line_items'])} items")
                if 'menu_items' in data:
                    print(f"    Found 'menu_items' key with {len(data['menu_items'])} items")
                
                # Show first 500 chars
                preview = json.dumps(data, indent=2)[:500]
                print(f"    Preview:\n{preview}...\n")
        else:
            print(f"  Status: {response.status_code} - {response.reason}")
            
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
