#!/usr/bin/env python3
"""Test webhook processing directly without FastAPI server."""

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

import json
import asyncio
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook

# Test webhook payload with realistic Triple Seat data
payload = {
    "webhook_trigger_type": "STATUS_CHANGE_EVENT",
    "event": {
        "id": 99999999,  # Use unique event ID for each test
        "name": "Test Customer",
        "phone": "(702) 555-0123",
        "event_date": "12/28/2025",
        "event_date_iso8601": "2025-12-28",
        "status": "DEFINITE",
        "site_id": 4,  # Use Revel establishment 4
        "event_start": "12/28/2025 6:00 PM",
        "event_end": "12/28/2025 6:15 PM",
        "updated_at": "12/28/2025 12:56 PM",
        "items": [
            {
                "id": 579,
                "name": "TRIPLE OG",
                "quantity": 5,
                "price": 2.00,
                "item_type": "product"
            }
        ]
    }
}

print("\n" + "=" * 70)
print("DIRECT WEBHOOK TEST")
print("=" * 70)
print(f"\nPayload:")
print(json.dumps(payload, indent=2))

print("\n" + "-" * 70)
print("Processing webhook...")
print("-" * 70 + "\n")

# Process the webhook directly with a test correlation ID
async def test():
    result = await handle_tripleseat_webhook(
        payload, 
        "test-12345",
        test_location_override=True,
        test_establishment_id="4"
    )
    return result

result = asyncio.run(test())

print("\n" + "=" * 70)
print("RESULT")
print("=" * 70)
if isinstance(result, dict):
    print(f"Success: {result.get('success')}")
    if result.get('order_id'):
        print(f"Order ID: {result.get('order_id')}")
    if result.get('error'):
        print(f"Error: {result.get('error')}")
else:
    print(f"Result: {result}")
print("=" * 70)
