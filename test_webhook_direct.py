"""
Test webhook processing directly without FastAPI server
"""
import logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')

from dotenv import load_dotenv
load_dotenv()

import json
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook

# Test webhook payload with realistic Triple Seat data
payload = {
    "webhook_trigger_type": "STATUS_CHANGE_EVENT",
    "event": {
        "id": 55521609,
        "name": "Jon Ponder",
        "phone": "(555) 123-4567",
        "event_date": "12/28/2025",
        "event_date_iso8601": "2025-12-28",
        "status": "DEFINITE",
        "site_id": 15691,
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
    "event": {
        "id": 55521609,
        "name": "Jon Ponder",
        "event_date": "12/28/2025",
        "event_date_iso8601": "2025-12-28",
        "status": "DEFINITE",
        "site_id": 15691,
        "event_start": "12/28/2025 6:00 PM",
        "event_end": "12/28/2025 6:15 PM",
        "event_start_utc": "2025-12-29T02:00:00Z",
        "event_end_utc": "2025-12-29T02:15:00Z",
        "updated_at": "12/28/2025 1:03 PM",
        "items": []
    }
}

async def test():
    print("Testing webhook handler directly...")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    result = await handle_tripleseat_webhook(
        payload=payload,
        correlation_id="test-local-123",
        x_signature_header=None,  # Skip signature verification for local test
        raw_body=None,
        verify_signature_flag=False,  # Disable signature check locally
        dry_run=False,
        enable_connector=True,
        allowed_locations=['4', '15691'],
        test_location_override=True,
        test_establishment_id='4',
        skip_time_gate=False,
        skip_validation=True  # Skip validation to test injection
    )
    
    print("\n" + "="*60)
    print("WEBHOOK RESULT:")
    print("="*60)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(test())
