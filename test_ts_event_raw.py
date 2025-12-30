#!/usr/bin/env python3
"""Test script to query TripleSeat events API and get full raw JSON"""

import json
from dotenv import load_dotenv
from integrations.tripleseat.api_client import TripleSeatAPIClient

# Load environment variables
load_dotenv()

# Test event ID
EVENT_ID = 55521609

print(f"\n{'='*80}")
print(f"Testing TripleSeat Events API - Event {EVENT_ID}")
print(f"{'='*80}\n")

# Initialize client with OAuth 1.0
try:
    client = TripleSeatAPIClient()
    print("✅ OAuth 1.0 client initialized\n")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    exit(1)

# Fetch event
try:
    url = f"{client.base_url}/v1/events/{EVENT_ID}"
    print(f"Requesting: {url}\n")
    
    response = client.session.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}\n")
    
    if response.status_code == 200:
        event_data = response.json()
        print("✅ Successfully fetched event!\n")
        print("Full Raw JSON Response:")
        print("="*80)
        print(json.dumps(event_data, indent=2))
        print("="*80)
        
        # Show key fields
        event = event_data.get('event', {})
        print(f"\n📋 Key Fields:")
        print(f"   Event ID: {event.get('id')}")
        print(f"   Event Name: {event.get('name')}")
        print(f"   Event Date: {event.get('event_date')}")
        print(f"   Status: {event.get('status')}")
        print(f"   Site ID: {event.get('site_id')}")
        print(f"   Number of Items: {len(event.get('items', []))}")
        print(f"   Number of Documents: {len(event.get('documents', []))}")
        
        # Show documents
        if event.get('documents'):
            print(f"\n📄 Documents:")
            for doc in event.get('documents', []):
                print(f"   - Type: {doc.get('type')}, URL: {doc.get('view_url')[:80]}...")
    else:
        print(f"❌ Failed to fetch event: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
