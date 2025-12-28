#!/usr/bin/env python
"""
PRODUCTION WEBHOOK INJECTION
Sends a real webhook to your app to trigger actual Revel POS injection.
Event ID: 55383184 (from your TripleSeat account)
"""

import asyncio
import json
from datetime import datetime
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook

async def trigger_real_injection():
    """Send a real webhook for Event 55383184 to trigger Revel injection"""
    
    print("\n" + "="*80)
    print("PRODUCTION WEBHOOK INJECTION - Event ID: 55383184")
    print("="*80)
    
    # Real event payload - minimal data to trigger injection
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'type': 'CREATE_EVENT',
        'event': {
            'id': '55383184',
            'site_id': '15691',  # Real site ID from your TripleSeat
            'status': 'DEFINITE',
            'event_date': '12/27/2025',
            'primary_guest': 'Centennial Toyota',
            'guest_count': 0,
            'description': 'Real production injection',
            'menu_items': [],
            'location_id': 31883,
            'grand_total': '146.88',
            'updated_at': datetime.now().isoformat()
        }
    }
    
    print(f"\n[PRODUCTION] Sending Real Webhook")
    print(f"  Event ID: {payload['event']['id']}")
    print(f"  Event Name: {payload['event']['primary_guest']}")
    print(f"  Site ID: {payload['event']['site_id']}")
    print(f"  Status: {payload['event']['status']}")
    print(f"  Trigger: {payload['webhook_trigger_type']}")
    
    print(f"\n[PROCESSING] Webhook -> Validation -> Revel Injection")
    print(f"[MODE] PRODUCTION (DRY_RUN=False, Real Revel write)")
    
    try:
        # Send to real webhook handler (NO TEST MODE)
        result = await handle_tripleseat_webhook(
            payload=payload,
            correlation_id='prod-injection-001',
            x_signature_header=None,  # Skip signature for direct injection
            raw_body=None,
            verify_signature_flag=False,  # Webhook verification skipped
            dry_run=False,  # PRODUCTION: Real Revel injection
            enable_connector=True,
            allowed_locations=['15691', '4'],  # Your actual location + test
            test_location_override=True,  # USE TEST LOCATION MAPPING
            test_establishment_id='4',  # Pinkbox Doughnuts
            skip_time_gate=True,  # Time gate check bypassed for immediate injection
            skip_validation=True  # Skip validation (use payload data directly)
        )
        
        print(f"\n[RESULT] Webhook Processing Complete")
        print(f"  ✓ ok: {result.get('ok')}")
        print(f"  ✓ processed: {result.get('processed')}")
        print(f"  ✓ reason: {result.get('reason')}")
        print(f"  ✓ trigger: {result.get('trigger')}")
        
        if result.get('processed'):
            print(f"\n" + "="*80)
            print("✅ REAL INJECTION SUCCESSFUL!")
            print("="*80)
            print(f"\nOrder has been created in Revel POS:")
            print(f"  • Event: {payload['event']['primary_guest']}")
            print(f"  • Event ID: {payload['event']['id']}")
            print(f"  • Domain: pinkboxdoughnuts.revelup.com")
            print(f"  • Status: INJECTED")
            return True
        else:
            print(f"\n⚠️  Injection not processed")
            print(f"  Reason: {result.get('reason')}")
            print(f"\nThis could be due to:")
            print(f"  - Menu items not found for resolution")
            print(f"  - Location not in allowed list")
            print(f"  - Event validation failed")
            return result.get('ok', False)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = asyncio.run(trigger_real_injection())
    exit(0 if success else 1)
