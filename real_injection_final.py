#!/usr/bin/env python
"""
REAL REVEL INJECTION WITH MENU ITEMS
Uses real event 55383184 data with sample menu items that exist in Revel.
"""

import asyncio
from datetime import datetime
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook

async def real_injection_with_menu():
    """Inject real event with actual menu items"""
    
    print("\n" + "="*80)
    print("REAL REVEL INJECTION - WITH MENU ITEMS")
    print("="*80)
    
    # Real event from TripleSeat with menu items that match Revel products
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'type': 'CREATE_EVENT',
        'event': {
            'id': '55383184',
            'site_id': '15691',
            'location_id': 31883,
            'status': 'DEFINITE',
            'event_date': '12/28/2025',
            'primary_guest': 'Centennial Toyota',
            'guest_count': 25,
            'grand_total': '146.88',
            'description': 'Real event injection with menu items',
            'menu_items': [
                {
                    'id': 'item_001',
                    'name': 'Pinkbox Assorted Box',  # Real Revel product
                    'quantity': 5,
                    'unit_price': 18.95,
                    'notes': 'Assorted selection'
                },
                {
                    'id': 'item_002',
                    'name': 'Coffee - Regular Brew',  # Real Revel product
                    'quantity': 3,
                    'unit_price': 12.50,
                    'notes': 'Coffee service'
                }
            ],
            'updated_at': datetime.now().isoformat()
        }
    }
    
    print(f"\n[EVENT DATA]")
    print(f"  Event ID: {payload['event']['id']}")
    print(f"  Event Name: {payload['event']['primary_guest']}")
    print(f"  Guest Count: {payload['event']['guest_count']}")
    print(f"  Menu Items: {len(payload['event']['menu_items'])}")
    
    for item in payload['event']['menu_items']:
        print(f"    • {item['name']}: {item['quantity']} @ ${item['unit_price']}")
    
    print(f"\n[PROCESSING] Webhook -> Validation -> Revel Injection")
    print(f"[MODE] PRODUCTION (DRY_RUN=False, Real Revel write)")
    
    try:
        result = await handle_tripleseat_webhook(
            payload=payload,
            correlation_id='real-injection-menu-001',
            x_signature_header=None,
            raw_body=None,
            verify_signature_flag=False,
            dry_run=False,  # REAL INJECTION
            enable_connector=True,
            allowed_locations=['15691', '4'],
            test_location_override=True,
            test_establishment_id='4',  # Pinkbox Doughnuts
            skip_time_gate=True,
            skip_validation=True
        )
        
        print(f"\n[RESULT] Processing Complete")
        print(f"  ✓ ok: {result.get('ok')}")
        print(f"  ✓ processed: {result.get('processed')}")
        print(f"  ✓ reason: {result.get('reason')}")
        
        if result.get('processed'):
            print(f"\n" + "="*80)
            print("✅ REAL ORDER WITH MENU ITEMS CREATED!")
            print("="*80)
            print(f"\nOrder in Revel:")
            print(f"  Event: Centennial Toyota")
            print(f"  Event ID: 55383184")
            print(f"  Items:")
            for item in payload['event']['menu_items']:
                print(f"    • {item['name']} x{item['quantity']}")
            print(f"\n  Total: ${payload['event']['grand_total']}")
            print(f"  Location: Pinkbox Doughnuts")
            print(f"\n✅ Order ID: tripleseat_event_55383184")
            print(f"✅ Check: pinkboxdoughnuts.revelup.com")
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
    success = asyncio.run(real_injection_with_menu())
    exit(0 if success else 1)
