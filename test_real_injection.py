#!/usr/bin/env python
"""
Real test with actual TripleSeat event and Revel injection.
This will fetch a real event from TripleSeat and inject it into Revel.
"""

import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook


async def test_real_injection():
    """Test with real TripleSeat event and Revel injection."""
    print("\n" + "=" * 80)
    print("REAL TRIPLESEAT EVENT + REVEL INJECTION TEST")
    print("=" * 80)
    
    # Get settings
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    enable_connector = os.getenv('ENABLE_CONNECTOR', 'true').lower() == 'true'
    
    print(f"\n⚠️  CONFIG:")
    print(f"   DRY_RUN: {dry_run} {'(writes to Revel)' if not dry_run else '(preview only)'}")
    print(f"   ENABLE_CONNECTOR: {enable_connector}")
    
    if not enable_connector:
        print("\n❌ ENABLE_CONNECTOR is false. Set to true to proceed.")
        return
    
    # Test 1: List available events
    print("\n" + "-" * 80)
    print("STEP 1: Check TripleSeat API Access")
    print("-" * 80)
    
    client = TripleSeatAPIClient()
    has_access = client.check_tripleseat_access()
    
    if not has_access:
        print("\n❌ No access to TripleSeat API")
        print("   Your OAuth token may lack read permissions.")
        print("   Check your TripleSeat OAuth app settings.")
        return
    
    print("✓ TripleSeat API access verified")
    
    # Test 2: Get a real event
    print("\n" + "-" * 80)
    print("STEP 2: Fetch Real Event from TripleSeat")
    print("-" * 80)
    
    # You can change this to a real event ID from your TripleSeat account
    event_id = input("\nEnter a TripleSeat event ID to test (or press Enter for 55521609): ").strip()
    if not event_id:
        event_id = "55521609"
    
    print(f"\nFetching event {event_id}...")
    event_data, failure_type = client.get_event_with_status(event_id)
    
    if not event_data:
        print(f"❌ Could not fetch event {event_id}")
        print(f"   Failure type: {failure_type}")
        print("\n   Try with a different event ID from your TripleSeat account.")
        return
    
    event = event_data.get('event', {})
    print(f"✓ Event fetched successfully")
    print(f"   ID: {event.get('id')}")
    print(f"   Status: {event.get('status')}")
    print(f"   Date: {event.get('event_date')}")
    print(f"   Site: {event.get('site_id')}")
    
    # Test 3: Run webhook flow
    print("\n" + "-" * 80)
    print("STEP 3: Run Webhook Handler (Validation → Time Gate → Revel Injection)")
    print("-" * 80)
    
    webhook_payload = {
        "webhook_trigger_type": "CREATE_EVENT",
        "event": event
    }
    
    print("\nProcessing webhook...")
    
    result = await handle_tripleseat_webhook(
        webhook_payload,
        'real_injection_test',
        verify_signature_flag=False,
        dry_run=dry_run,
        enable_connector=enable_connector,
        allowed_locations=['1', '4'],  # Allow all
        test_location_override=True,
        test_establishment_id='4'
    )
    
    print(f"\n📥 Result:")
    print(f"   ok: {result.get('ok')}")
    print(f"   processed: {result.get('processed')}")
    print(f"   trigger: {result.get('trigger')}")
    print(f"   reason: {result.get('reason')}")
    
    if result.get('authorization_status') == 'DENIED':
        print(f"\n⚠️  Event is not accessible via OAuth")
        print(f"   (Permission issue with this event in TripleSeat)")
    
    if result.get('ok') and result.get('processed'):
        print(f"\n✅ SUCCESS: Event was injected into Revel!")
    elif result.get('ok'):
        print(f"\n⏭️  Event was acknowledged but not processed")
        print(f"   Reason: {result.get('reason')}")
    else:
        print(f"\n❌ Event processing failed")
        print(f"   Reason: {result.get('reason')}")


if __name__ == '__main__':
    asyncio.run(test_real_injection())
