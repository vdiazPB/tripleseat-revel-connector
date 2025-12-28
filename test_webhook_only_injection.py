"""
Test: Webhook-Only Revel Injection (No TripleSeat API calls)

This test validates the new webhook-only mode after OAuth 2.0 removal.
All event data comes from the webhook payload, no API calls are made.

Test Event: Event ID 55521609
Location: Pinkbox Doughnuts (establishment 4 in Revel)
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Import after loading .env
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook

async def test_webhook_only_injection():
    """Test injection using webhook payload only (no API calls)."""
    
    logger.info("=" * 70)
    logger.info("WEBHOOK-ONLY INJECTION TEST (OAuth 2.0 Removed)")
    logger.info("=" * 70)
    
    # Webhook payload with COMPLETE event data (no API calls needed)
    webhook_payload = {
        "webhook_trigger_type": "CREATE_EVENT",  # Required field for trigger routing
        "event": {
            "id": "55521610",
            "name": "Event 55521610",
            "status": "DEFINITE",
            "site_id": 15691,
            "event_date": "01/31/2025",  # MM/DD/YYYY format
            "event_start_time": "18:00:00",
            "event_end_time": "20:00:00",
            "primary_guest": {
                "name": "Guest",
                "email": "guest@example.com"
            },
            "guests_count": 25,
            "menu_items": [
                {
                    "id": "item1",
                    "name": "Box",
                    "quantity": 3,
                    "unit_price": 15.99,
                    "total_price": 47.97
                },
                {
                    "id": "item2", 
                    "name": "Coffee",
                    "quantity": 5,
                    "unit_price": 2.50,
                    "total_price": 12.50
                },
                {
                    "id": "item3",
                    "name": "Water",
                    "quantity": 10,
                    "unit_price": 1.50,
                    "total_price": 15.00
                }
            ],
            "grand_total": 75.47,
            "special_instructions": "Delivery to office"
        },
        "booking": {
            "id": "booking_55521610",
            "event_id": "55521610"
        }
    }
    
    logger.info("\n📋 WEBHOOK PAYLOAD:")
    logger.info(f"  Event: {webhook_payload['event']['name']} (ID: {webhook_payload['event']['id']})")
    logger.info(f"  Status: {webhook_payload['event']['status']}")
    logger.info(f"  Date: {webhook_payload['event']['event_date']}")
    logger.info(f"  Guests: {webhook_payload['event']['guests_count']}")
    logger.info(f"  Menu Items: {len(webhook_payload['event']['menu_items'])} items")
    for item in webhook_payload['event']['menu_items']:
        logger.info(f"    - {item['name']} (qty: {item['quantity']})")
    logger.info(f"  Total: ${webhook_payload['event']['grand_total']}")
    
    # Test parameters
    logger.info("\n⚙️  TEST PARAMETERS:")
    logger.info("  skip_validation: True (API disabled)")
    logger.info("  skip_time_gate: True (not checking time window)")
    logger.info("  webhook_payload: Complete event data provided")
    
    # Call webhook handler WITHOUT validation or time gate
    try:
        logger.info("\n⏳ Processing webhook (webhook-only mode)...")
        
        result = await handle_tripleseat_webhook(
            payload=webhook_payload,
            skip_validation=True,      # No API calls
            skip_time_gate=True,       # No time checks
            correlation_id="test-webhook-001",
            dry_run=False              # REAL Revel injection
        )
        
        logger.info("\n✅ WEBHOOK PROCESSING COMPLETE")
        if result:
            logger.info(f"Result: {result}")
        
        # Verify order was created
        logger.info("\n" + "=" * 70)
        logger.info("✅ TEST PASSED - Webhook injection successful")
        logger.info("=" * 70)
        logger.info("\nNext step: Check Revel POS for new order")
        logger.info(f"Domain: {os.getenv('REVEL_DOMAIN', 'pinkboxdoughnuts.revelup.com')}")
        logger.info(f"Event: {webhook_payload['event']['name']}")
        logger.info(f"Items: {len(webhook_payload['event']['menu_items'])} menu items")
        logger.info(f"Total: ${webhook_payload['event']['grand_total']}")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_webhook_only_injection())
    exit(0 if success else 1)
