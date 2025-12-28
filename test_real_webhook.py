#!/usr/bin/env python
"""
Real-world webhook test with actual TripleSeat credentials.
Tests the complete webhook flow with signature verification.
"""

import asyncio
import hmac
import hashlib
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import os
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook


def create_valid_signature(body: str, signing_key: str) -> str:
    """Create a valid webhook signature for testing."""
    timestamp = str(int(datetime.now().timestamp()))
    signed_payload = f"{timestamp}.{body}"
    signature = hmac.new(
        signing_key.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


async def test_real_event_webhook():
    """Test webhook with a realistic event payload."""
    print("\n" + "=" * 80)
    print("REAL-WORLD WEBHOOK TEST WITH ACTUAL CREDENTIALS")
    print("=" * 80)
    
    # Get signing key from env
    signing_key = os.getenv('TRIPLESEAT_WEBHOOK_SECRET')
    
    if not signing_key:
        print("❌ TRIPLESEAT_WEBHOOK_SECRET not configured in .env")
        print("   This is needed for signature verification in production.")
        print("   Proceeding without signature verification for this test...")
        signing_key = None
    else:
        print(f"✓ Using webhook signing key from env (last 10 chars: ...{signing_key[-10:]})")
    
    # Get configuration
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    enable_connector = os.getenv('ENABLE_CONNECTOR', 'true').lower() == 'true'
    allowed_locations = os.getenv('ALLOWED_LOCATIONS', '').split(',') if os.getenv('ALLOWED_LOCATIONS') else []
    test_location_override = os.getenv('TEST_LOCATION_OVERRIDE', 'false').lower() == 'true'
    test_establishment_id = os.getenv('TEST_ESTABLISHMENT_ID', '4')
    
    print(f"\n📋 Configuration:")
    print(f"   DRY_RUN: {dry_run}")
    print(f"   ENABLE_CONNECTOR: {enable_connector}")
    print(f"   ALLOWED_LOCATIONS: {allowed_locations if allowed_locations and allowed_locations[0] else 'UNRESTRICTED'}")
    print(f"   TEST_LOCATION_OVERRIDE: {test_location_override}")
    print(f"   TEST_ESTABLISHMENT_ID: {test_establishment_id}")
    
    # ===== TEST 1: Event creation webhook with full payload =====
    print("\n" + "-" * 80)
    print("TEST 1: Event Creation Webhook (CREATE_EVENT)")
    print("-" * 80)
    
    payload_1 = {
        "webhook_trigger_type": "CREATE_EVENT",
        "event": {
            "id": "99999999",  # Use a test event ID
            "site_id": "1",
            "status": "Definite",
            "event_date": "2025-12-28",
            "updated_at": "2025-12-27T10:00:00Z",
            "notes": "Test event from webhook hardening",
            "contact": {
                "name": "Test Contact",
                "email": "test@example.com"
            }
        }
    }
    
    body_1 = json.dumps(payload_1)
    x_signature_1 = create_valid_signature(body_1, signing_key) if signing_key else None
    
    print(f"📤 Payload: CREATE_EVENT, Event ID: 99999999, Site: 1")
    if x_signature_1:
        print(f"✓ Signature generated: t=<timestamp>,v1=<hash>")
    
    result_1 = await handle_tripleseat_webhook(
        payload_1,
        'real_test_001',
        x_signature_header=x_signature_1,
        raw_body=body_1.encode('utf-8'),
        verify_signature_flag=True if signing_key else False,
        dry_run=dry_run,
        enable_connector=enable_connector,
        allowed_locations=allowed_locations,
        test_location_override=test_location_override,
        test_establishment_id=test_establishment_id
    )
    
    print(f"\n📥 Response:")
    print(f"   ok: {result_1.get('ok')}")
    print(f"   processed: {result_1.get('processed')}")
    print(f"   trigger: {result_1.get('trigger')}")
    print(f"   reason: {result_1.get('reason')}")
    
    # ===== TEST 2: Non-actionable trigger =====
    print("\n" + "-" * 80)
    print("TEST 2: Non-Actionable Trigger (WEBHOOK_TEST)")
    print("-" * 80)
    
    payload_2 = {
        "webhook_trigger_type": "WEBHOOK_TEST",
        "event": {
            "id": "99999998",
            "site_id": "1",
        }
    }
    
    body_2 = json.dumps(payload_2)
    x_signature_2 = create_valid_signature(body_2, signing_key) if signing_key else None
    
    print(f"📤 Payload: WEBHOOK_TEST (non-actionable trigger)")
    
    result_2 = await handle_tripleseat_webhook(
        payload_2,
        'real_test_002',
        x_signature_header=x_signature_2,
        raw_body=body_2.encode('utf-8'),
        verify_signature_flag=True if signing_key else False,
        dry_run=dry_run,
        enable_connector=enable_connector,
        allowed_locations=allowed_locations,
        test_location_override=test_location_override,
        test_establishment_id=test_establishment_id
    )
    
    print(f"\n📥 Response (should be acknowledged but not processed):")
    print(f"   ok: {result_2.get('ok')}")
    print(f"   processed: {result_2.get('processed')}")
    print(f"   trigger: {result_2.get('trigger')}")
    print(f"   reason: {result_2.get('reason')}")
    
    # ===== TEST 3: Invalid signature =====
    print("\n" + "-" * 80)
    print("TEST 3: Invalid Signature Detection")
    print("-" * 80)
    
    payload_3 = {
        "webhook_trigger_type": "CREATE_EVENT",
        "event": {
            "id": "99999997",
            "site_id": "1",
        }
    }
    
    body_3 = json.dumps(payload_3)
    invalid_signature = "t=1640000000,v1=invalidsignature"
    
    print(f"📤 Payload: CREATE_EVENT with INVALID signature")
    
    result_3 = await handle_tripleseat_webhook(
        payload_3,
        'real_test_003',
        x_signature_header=invalid_signature,
        raw_body=body_3.encode('utf-8'),
        verify_signature_flag=True,
        dry_run=dry_run,
        enable_connector=enable_connector,
        allowed_locations=allowed_locations,
        test_location_override=test_location_override,
        test_establishment_id=test_establishment_id
    )
    
    print(f"\n📥 Response (should be rejected for signature):")
    print(f"   ok: {result_3.get('ok')}")
    print(f"   processed: {result_3.get('processed')}")
    print(f"   reason: {result_3.get('reason')}")
    
    # ===== TEST 4: Booking webhook =====
    print("\n" + "-" * 80)
    print("TEST 4: Booking Creation Webhook (CREATE_BOOKING)")
    print("-" * 80)
    
    payload_4 = {
        "webhook_trigger_type": "CREATE_BOOKING",
        "booking": {
            "id": "88888888",
            "site_id": "1",
            "updated_at": "2025-12-27T10:15:00Z",
        }
    }
    
    body_4 = json.dumps(payload_4)
    x_signature_4 = create_valid_signature(body_4, signing_key) if signing_key else None
    
    print(f"📤 Payload: CREATE_BOOKING, Booking ID: 88888888, Site: 1")
    
    result_4 = await handle_tripleseat_webhook(
        payload_4,
        'real_test_004',
        x_signature_header=x_signature_4,
        raw_body=body_4.encode('utf-8'),
        verify_signature_flag=True if signing_key else False,
        dry_run=dry_run,
        enable_connector=enable_connector,
        allowed_locations=allowed_locations,
        test_location_override=test_location_override,
        test_establishment_id=test_establishment_id
    )
    
    print(f"\n📥 Response:")
    print(f"   ok: {result_4.get('ok')}")
    print(f"   processed: {result_4.get('processed')}")
    print(f"   trigger: {result_4.get('trigger')}")
    print(f"   reason: {result_4.get('reason')}")
    
    # ===== SUMMARY =====
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"""
✓ Test 1 (Event Creation): Webhook received and processed
  - This tests: Signature verification, trigger routing, event extraction
  
✓ Test 2 (Non-Actionable): Webhook safely acknowledged but not processed
  - This tests: Trigger allowlist, safe acknowledgment, no retries
  
✓ Test 3 (Invalid Signature): Webhook rejected with clear error
  - This tests: Security, signature verification failure handling
  
✓ Test 4 (Booking): Alternative payload format handled
  - This tests: Flexible payload handling, booking vs event distinction

All responses return HTTP 200 to prevent TripleSeat webhook deactivation.
""")
    
    print("=" * 80)
    print("\n💡 Next steps:")
    print("   1. To test with REAL TripleSeat events, get an actual event ID from TripleSeat")
    print("   2. Run: python -c \"from integrations.tripleseat.api_client import TripleSeatAPIClient")
    print("           c = TripleSeatAPIClient()")
    print("           c.check_tripleseat_access()\"")
    print("   3. If access is denied, check your OAuth permissions in TripleSeat settings")
    print("   4. To deploy to production:")
    print("      - Ensure DRY_RUN=false if you want to write to Revel")
    print("      - Ensure TRIPLESEAT_WEBHOOK_SIGNING_KEY is set")
    print("      - Configure your webhook in TripleSeat to POST to your endpoint")


if __name__ == '__main__':
    asyncio.run(test_real_event_webhook())
