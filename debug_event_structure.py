#!/usr/bin/env python3
"""Debug script to see full TripleSeat event structure."""

import json
import logging
from integrations.tripleseat.api_client import TripleSeatAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test with event 55521609
event_id = "55521609"

client = TripleSeatAPIClient()
event_data = client.get_event(event_id)

print("\n" + "="*80)
print(f"FULL EVENT STRUCTURE FOR EVENT {event_id}")
print("="*80)
print(json.dumps(event_data, indent=2))
print("="*80)

# Check what fields are available
if event_data:
    print("\nAVAILABLE FIELDS:")
    for key in sorted(event_data.keys()):
        value = event_data[key]
        if isinstance(value, (list, dict)):
            if isinstance(value, list):
                print(f"  - {key}: list with {len(value)} items")
                if value and isinstance(value[0], dict):
                    print(f"    First item keys: {list(value[0].keys())}")
            else:
                print(f"  - {key}: dict with keys {list(value.keys())}")
        else:
            print(f"  - {key}: {type(value).__name__} = {value}")
