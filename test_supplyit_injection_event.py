#!/usr/bin/env python3
"""
Test script to inject the event into Supply It with DEFINITE status.
"""
import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook


async def test_supplyit_injection():
    """Test injecting event 55521609 into Supply It with DEFINITE status."""
    
    print("=" * 70)
    print("TEST: SUPPLY IT ORDER INJECTION")
    print("=" * 70)
    print()
    
    # Create test webhook payload with DEFINITE status (actual event status)
    webhook_payload = {
        "webhook_trigger_type": "STATUS_CHANGE_EVENT",
        "event": {
            "id": 55521609,
            "name": "Jon Ponder",
            "event_date": "12/28/2025",
            "event_date_iso8601": "2025-12-28",
            "status": "DEFINITE",  # For Supply It routing
            "site_id": 15691,
            "event_start": "12/28/2025 6:00 PM",
            "event_end": "12/28/2025 6:15 PM",
            "updated_at": "12/28/2025 12:56 PM"
        }
    }
    
    print("Webhook payload (DEFINITE status → Supply It):")
    print(json.dumps(webhook_payload, indent=2))
    print()
    
    print("=" * 70)
    print("Processing webhook...")
    print("=" * 70)
    print()
    
    try:
        # Handle the webhook
        result = await handle_tripleseat_webhook(
            webhook_payload,
            correlation_id="test-event-supplyit",
            x_signature_header=None,
            raw_body=json.dumps(webhook_payload).encode(),
            verify_signature_flag=False,
            dry_run=False,
            enable_connector=True,
            allowed_locations=['4', '15691'],
            test_location_override=None,
            test_establishment_id=None
        )
        
        print()
        print("=" * 70)
        print("RESULT")
        print("=" * 70)
        print(f"Success: {result.get('success', False)}")
        print(f"Message: {result.get('message', 'No message')}")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
        if result.get('processed'):
            print(f"Processed: {result.get('processed')}")
        print()
        
    except Exception as e:
        logger.exception(f"Error during webhook processing: {e}")
        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)
        print(f"Failed with exception: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_supplyit_injection())
