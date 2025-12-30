#!/usr/bin/env python3
"""
Check event data structure for booking ID and items.
"""
import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from integrations.tripleseat.api_client import TripleSeatAPIClient

event_id = 55521609

ts_client = TripleSeatAPIClient()
event_data = ts_client.get_event(event_id)

print("=" * 70)
print("EVENT DATA STRUCTURE")
print("=" * 70)
print()

# Check key fields
if event_data:
    event = event_data.get('event', {})
    print(f"Event keys: {list(event.keys())}")
    print()
    
    print(f"booking_id: {event.get('booking_id')}")
    print(f"items: {event.get('items', [])}")
    print(f"menu_items: {event.get('menu_items', [])}")
    print()
    
    # Check documents
    documents = event_data.get('documents', [])
    print(f"documents: {len(documents)} documents found")
    for i, doc in enumerate(documents):
        print(f"  [{i}] type={doc.get('type')}, name={doc.get('name')}")
    print()
    
    # Check root level items
    print(f"Root level items: {event_data.get('items', [])}")
    print()
    
    # Full data (first 1000 chars)
    print("Full response (first 1000 chars):")
    print(json.dumps(event_data, indent=2, default=str)[:1000])
