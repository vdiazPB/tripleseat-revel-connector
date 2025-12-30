#!/usr/bin/env python3
"""Check raw response bodies from endpoints"""

from dotenv import load_dotenv
from integrations.tripleseat.api_client import TripleSeatAPIClient

load_dotenv()

EVENT_ID = 55521609
BOOKING_ID = 52511006

client = TripleSeatAPIClient()
print(f"\nChecking endpoint response bodies\n")

endpoints = [
    f"/v1/events/{EVENT_ID}/items",
    f"/v1/events/{EVENT_ID}/line_items",
    f"/v1/bookings/{BOOKING_ID}/items",
    f"/v1/bookings/{BOOKING_ID}/line_items",
    f"/v1/events/{EVENT_ID}/documents",
]

for endpoint in endpoints:
    url = f"{client.base_url}{endpoint}"
    print(f"[{endpoint}]")
    
    try:
        response = client.session.get(url, timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Length: {len(response.text)} bytes")
        print(f"  Content-Type: {response.headers.get('content-type')}")
        print(f"  Body: '{response.text[:200]}'")
        print()
    except Exception as e:
        print(f"  Error: {e}\n")
