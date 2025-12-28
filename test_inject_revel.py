#!/usr/bin/env python
"""
Direct Revel injection test with complete event payload.
Skips TripleSeat API call - uses webhook payload directly.
"""

import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook


async def test_revel_injection():
    """Test real Revel injection with complete event payload."""
    print("\n" + "=" * 80)
    print("DIRECT REVEL INJECTION TEST")
    print("=" * 80)
    
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    enable_connector = os.getenv('ENABLE_CONNECTOR', 'true').lower() == 'true'
    
    print(f"\n⚙️  Configuration:")
    print(f"   DRY_RUN: {dry_run} {'(preview only)' if dry_run else '(WRITES TO REVEL)'}")
    print(f"   ENABLE_CONNECTOR: {enable_connector}")
    
    if not enable_connector:
        print("\n❌ Set ENABLE_CONNECTOR=true in .env")
        return
    
    if dry_run:
        print("\n⚠️  DRY_RUN=true - This will NOT write to Revel")
        print("   Set DRY_RUN=false to actually create orders in Revel")
    
    # Complete event payload with all required data
    # This bypasses TripleSeat API and tests injection directly
    webhook_payload = {
        "webhook_trigger_type": "CREATE_EVENT",
        "event": {
            "id": "test_event_" + os.urandom(4).hex(),
            "site_id": "4",
            "status": "Definite",
            "event_date": "2025-12-28",
            "updated_at": "2025-12-27T12:00:00Z",
            "contact": {
                "name": "Test Customer",
                "email": "test@example.com",
                "phone": "555-0123"
            },
            "notes": "Test event for Revel injection"
        },
        "documents": [
            {
                "type": "billing_invoice",
                "is_closed": True,
                "total": 100.00
            }
        ],
        "payments": [
            {
                "amount": 100.00
            }
        ],
        "menu_items": [
            {
                "name": "Dozen Glazed Donuts",
                "quantity": 1
            },
            {
                "name": "Half Dozen Chocolate",
                "quantity": 1
            }
        ]
    }
    
    event_id = webhook_payload['event']['id']
    
    print(f"\n📋 Test Event:")
    print(f"   ID: {event_id}")
    print(f"   Site: {webhook_payload['event']['site_id']}")
    print(f"   Status: {webhook_payload['event']['status']}")
    print(f"   Date: {webhook_payload['event']['event_date']}")
    print(f"   Items: {len(webhook_payload['menu_items'])} menu items")
    print(f"   Total: ${webhook_payload['documents'][0]['total']}")
    
    # Run webhook handler - this triggers the full pipeline including Revel injection
    print(f"\n🔄 Processing webhook (validation → time gate → Revel injection)...")
    
    result = await handle_tripleseat_webhook(
        webhook_payload,
        'direct_revel_test',
        verify_signature_flag=False,
        dry_run=dry_run,
        enable_connector=enable_connector,
        allowed_locations=['4'],
        test_location_override=True,
        test_establishment_id='4'
    )
    
    print(f"\n📊 Result:")
    print(f"   ok: {result.get('ok')}")
    print(f"   processed: {result.get('processed')}")
    print(f"   trigger: {result.get('trigger')}")
    print(f"   reason: {result.get('reason')}")
    
    print("\n" + "=" * 80)
    
    if result.get('ok') and result.get('processed'):
        print("✅ SUCCESS - Event was processed and injected to Revel!")
        if dry_run:
            print("\n⚠️  DRY_RUN=true so the order was NOT actually created.")
            print("   Set DRY_RUN=false to create real orders in Revel.")
    elif result.get('ok'):
        print(f"⏭️  Event was acknowledged but not processed")
        print(f"   Reason: {result.get('reason')}")
    else:
        print(f"❌ Processing failed")
        print(f"   Reason: {result.get('reason')}")
    
    print("=" * 80)


if __name__ == '__main__':
    asyncio.run(test_revel_injection())
