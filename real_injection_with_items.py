#!/usr/bin/env python
"""
REAL REVEL INJECTION WITH ACTUAL EVENT DATA
Fetches real event 55383184 from TripleSeat including menu items,
then injects into Revel POS with actual products.
"""

import asyncio
from datetime import datetime
from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook

async def real_injection_with_event_data():
    """Fetch real event and inject with actual menu data"""
    
    print("\n" + "="*80)
    print("REAL REVEL INJECTION WITH ACTUAL EVENT DATA")
    print("="*80)
    
    event_id = '55383184'
    
    # Fetch the real event from TripleSeat
    print(f"\n[STEP 1] Fetching real event {event_id} from TripleSeat...")
    client = TripleSeatAPIClient()
    event_data, status = client.get_event_with_status(event_id)
    
    if not event_data:
        print(f"❌ Failed to fetch event: {status}")
        return False
    
    event = event_data.get('event', {})
    
    print(f"\n[EVENT DATA RETRIEVED]")
    print(f"  Event: {event.get('name', 'Unknown')}")
    print(f"  Event ID: {event.get('id')}")
    print(f"  Status: {event.get('status')}")
    print(f"  Site ID: {event.get('site_id')}")
    print(f"  Location: {event.get('location', {}).get('name', 'Unknown')}")
    print(f"  Guest Count: {event.get('guest_count', 'N/A')}")
    print(f"  Amount: ${event.get('grand_total', '0')}")
    
    # Extract menu items from the event
    print(f"\n[STEP 2] Extracting menu items from event...")
    
    # TripleSeat stores menu items in various places
    # Try to get from the event directly or from related records
    menu_items = event.get('menu_items', [])
    
    print(f"  Menu items found: {len(menu_items)}")
    for item in menu_items:
        print(f"    • {item.get('name', 'Unknown')}: {item.get('quantity', 0)}")
    
    # Create webhook payload with real data
    print(f"\n[STEP 3] Creating webhook payload with real event data...")
    
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'type': 'CREATE_EVENT',
        'event': {
            'id': str(event.get('id')),
            'site_id': str(event.get('site_id')),
            'location_id': event.get('location_id'),
            'status': event.get('status', 'DEFINITE'),
            'event_date': event.get('event_date'),
            'primary_guest': event.get('name'),
            'guest_count': event.get('guest_count', 0),
            'grand_total': event.get('grand_total'),
            'menu_items': menu_items,  # Include real menu items
            'updated_at': datetime.now().isoformat()
        }
    }
    
    print(f"\n[STEP 4] Sending webhook to Revel injection pipeline...")
    print(f"  Payload contains {len(menu_items)} menu items")
    print(f"  DRY_RUN: False (REAL injection)")
    print(f"  Skip validation: True (use payload data)")
    print(f"  Skip time gate: True (immediate injection)")
    
    try:
        result = await handle_tripleseat_webhook(
            payload=payload,
            correlation_id='real-injection-with-items-001',
            x_signature_header=None,
            raw_body=None,
            verify_signature_flag=False,
            dry_run=False,  # REAL INJECTION
            enable_connector=True,
            allowed_locations=['15691', '4'],
            test_location_override=True,  # Map to Pinkbox Doughnuts
            test_establishment_id='4',
            skip_time_gate=True,
            skip_validation=True
        )
        
        print(f"\n[RESULT] Webhook Processing Complete")
        print(f"  ✓ ok: {result.get('ok')}")
        print(f"  ✓ processed: {result.get('processed')}")
        print(f"  ✓ reason: {result.get('reason')}")
        
        if result.get('processed'):
            print(f"\n" + "="*80)
            print("✅ REAL ORDER CREATED IN REVEL!")
            print("="*80)
            print(f"\nOrder Details:")
            print(f"  Event ID: {event.get('id')}")
            print(f"  Event Name: {event.get('name')}")
            print(f"  Location: Pinkbox Doughnuts (establishment 4)")
            print(f"  Menu Items: {len(menu_items)}")
            print(f"  Amount: ${event.get('grand_total')}")
            print(f"\n✅ Check Revel POS: pinkboxdoughnuts.revelup.com")
            print(f"✅ Look for order: tripleseat_event_{event.get('id')}")
            return True
        else:
            print(f"\n⚠️  Order not created")
            print(f"  Reason: {result.get('reason')}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = asyncio.run(real_injection_with_event_data())
    exit(0 if success else 1)
