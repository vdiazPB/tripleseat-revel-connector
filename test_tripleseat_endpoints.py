#!/usr/bin/env python3
"""Test TripleSeat API endpoints to find line items."""

import os
os.environ['CONSUMER_KEY'] = 'Whz3ADZ1VwNdSIssvh8jvCY2fmoPngT1b6Iuo5rX'
os.environ['CONSUMER_SECRET'] = 'VPZET8KoGih6FjsrU1KWYAI91Gz443cLMeNwvjKr'
os.environ['TRIPLESEAT_API_BASE'] = 'https://api.tripleseat.com'

from integrations.tripleseat.api_client import TripleSeatAPIClient
import json

event_id = "55521609"
client = TripleSeatAPIClient()

endpoints = [
    f"/v1/events/{event_id}/line_items",
    f"/v1/events/{event_id}/items",
]

print(f"\n{'='*80}")
print(f"Testing TripleSeat API endpoints for event {event_id}")
print(f"{'='*80}\n")

for endpoint in endpoints:
    try:
        url = f"{client.base_url}{endpoint}"
        print(f"Testing: {endpoint}")
        response = client.session.get(url, timeout=10)
        
        print(f"  Status: HTTP {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"  Response length: {len(response.text)} chars")
        print(f"  First 500 chars: {response.text[:500]}")
        print()
    except Exception as e:
        print(f"  ❌ Error: {e}\n")

print(f"{'='*80}")
