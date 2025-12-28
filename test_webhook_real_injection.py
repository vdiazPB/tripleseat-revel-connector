#!/usr/bin/env python
"""
REAL REVEL INJECTION TEST - Webhook-First Approach
Tests actual injection into Revel with webhook payload data
(No TripleSeat API calls needed)
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

from integrations.revel.injection import inject_order

async def test_direct_revel_injection():
    """
    Test DIRECT Revel injection using order data from webhook payload.
    This is what happens after webhook validation passes.
    """
    
    print("\n" + "="*80)
    print("DIRECT REVEL INJECTION TEST")
    print("="*80)
    
    # Simulated event data from TripleSeat webhook
    event_id = "test_event_12345"
    correlation_id = "injection-test-001"
    
    print(f"\n[TEST] Injecting Event: {event_id}")
    print(f"[TEST] Correlation ID: {correlation_id}")
    
    try:
        # Call the injection function directly
        # This simulates what happens after webhook validation passes
        result = inject_order(
            event_id=event_id,
            correlation_id=correlation_id,
            dry_run=False,  # REAL INJECTION
            enable_connector=True,
            test_location_override=True,
            test_establishment_id='4'
        )
        
        print(f"\n[RESULT] Injection Result:")
        print(f"  Success: {result.success}")
        print(f"  Error: {result.error}")
        print(f"  Order Details: {result.order_details}")
        
        if result.success:
            print(f"\n✅ SUCCESS: Order created in Revel!")
            print(f"   Order Details: {json.dumps(result.order_details, indent=2)}")
            return True
        else:
            print(f"\n⚠️  Injection failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_webhook_to_revel_full_pipeline():
    """
    Test full pipeline: Webhook → Validation → Revel Injection
    Uses webhook payload with all event data included.
    """
    
    print("\n" + "="*80)
    print("FULL WEBHOOK → REVEL PIPELINE TEST")
    print("="*80)
    
    from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook
    
    # Real webhook payload with COMPLETE event data
    # This is what TripleSeat actually sends
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'type': 'CREATE_EVENT',
        'event': {
            'id': '99999',
            'site_id': '4',
            'status': 'Definite',
            'event_date': datetime.now().isoformat(),
            'primary_guest': 'Test Customer',
            'guest_count': 50,
            'menu_items': [
                {
                    'id': 'item_001',
                    'name': 'Premium Appetizers',
                    'quantity': 2,
                    'price': 75.00,
                    'unit': 'serving'
                },
                {
                    'id': 'item_002',
                    'name': 'Grilled Chicken Breast',
                    'quantity': 30,
                    'price': 35.00,
                    'unit': 'plate'
                },
                {
                    'id': 'item_003',
                    'name': 'Pan Seared Salmon',
                    'quantity': 15,
                    'price': 42.00,
                    'unit': 'plate'
                },
                {
                    'id': 'item_004',
                    'name': 'Vegetarian Risotto',
                    'quantity': 5,
                    'price': 32.00,
                    'unit': 'plate'
                },
                {
                    'id': 'item_005',
                    'name': 'Chocolate Mousse Cups',
                    'quantity': 50,
                    'price': 8.00,
                    'unit': 'serving'
                }
            ],
            'dietary_restrictions': {
                'gluten_free': 5,
                'vegan': 3,
                'nut_allergy': 2
            },
            'special_notes': 'Early setup required. Client prefers plated service.',
            'setup_time': '5:00 PM',
            'event_time': '6:00 PM',
            'teardown_time': '10:00 PM',
            'updated_at': datetime.now().isoformat()
        },
        'booking': {
            'id': 'booking_88888',
            'primary_guest': 'Test Customer',
            'guest_count': 50,
            'contact_email': 'test@example.com',
            'contact_phone': '555-1234',
            'updated_at': datetime.now().isoformat()
        },
        'site_id': '4',
        'updated_at': datetime.now().isoformat()
    }
    
    print("\n[TEST] Webhook Payload Summary:")
    print(f"  Event ID: {payload['event']['id']}")
    print(f"  Site ID: {payload['event']['site_id']}")
    print(f"  Status: {payload['event']['status']}")
    print(f"  Guest Count: {payload['event']['guest_count']}")
    print(f"  Menu Items: {len(payload['event']['menu_items'])}")
    
    total_revenue = sum(item['quantity'] * item['price'] 
                       for item in payload['event']['menu_items'])
    print(f"  Total Revenue: ${total_revenue:,.2f}")
    
    print("\n[TEST] Processing webhook with REAL REVEL INJECTION...")
    print("        Pipeline: Signature → Trigger → Validation → TimeGate → Revel → Email")
    
    try:
        # Process webhook with real injection
        result = await handle_tripleseat_webhook(
            payload=payload,
            correlation_id='full-pipeline-test-001',
            x_signature_header=None,
            raw_body=None,
            verify_signature_flag=False,  # Skip signature for test
            dry_run=False,  # REAL INJECTION
            enable_connector=True,
            allowed_locations=['4'],
            test_location_override=True,
            test_establishment_id='4'
        )
        
        print(f"\n[RESULT] Pipeline Processing Complete")
        print(f"  Status: {result.get('ok')}")
        print(f"  Processed: {result.get('processed')}")
        print(f"  Reason: {result.get('reason')}")
        print(f"  Trigger: {result.get('trigger')}")
        
        if result.get('processed'):
            print(f"\n✅ SUCCESS: Webhook processed and order injected into Revel!")
            print(f"   Event {payload['event']['id']} is now in Revel POS")
            return True
        elif result.get('ok') and not result.get('processed'):
            print(f"\n⚠️  Webhook acknowledged but not processed")
            print(f"   Reason: {result.get('reason')}")
            return False
        else:
            print(f"\n❌ FAILED: {result.get('reason')}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_dry_run():
    """
    Test with DRY_RUN=True to validate the entire pipeline without writing to Revel.
    """
    
    print("\n" + "="*80)
    print("DRY-RUN TEST (Full Pipeline, No Revel Write)")
    print("="*80)
    
    from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook
    
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'event': {
            'id': '77777',
            'site_id': '4',
            'status': 'Definite',
            'event_date': datetime.now().isoformat(),
            'primary_guest': 'Test Customer 2',
            'guest_count': 100,
            'menu_items': [
                {'name': 'Appetizers', 'quantity': 3, 'price': 60.00},
                {'name': 'Prime Rib Main', 'quantity': 85, 'price': 65.00},
                {'name': 'Vegetarian', 'quantity': 15, 'price': 55.00},
                {'name': 'Dessert', 'quantity': 100, 'price': 15.00}
            ],
            'updated_at': datetime.now().isoformat()
        }
    }
    
    print(f"\n[TEST] Event: {payload['event']['id']}")
    print(f"[TEST] Guests: {payload['event']['guest_count']}")
    
    print("\n[TEST] Processing webhook with DRY_RUN=True...")
    
    try:
        result = await handle_tripleseat_webhook(
            payload=payload,
            correlation_id='dry-run-full-001',
            verify_signature_flag=False,
            dry_run=True,  # DRY RUN
            enable_connector=True,
            allowed_locations=['4'],
            test_location_override=True,
            test_establishment_id='4'
        )
        
        print(f"\n[RESULT] Pipeline Processing Complete")
        print(f"  Status: {result.get('ok')}")
        print(f"  Processed: {result.get('processed')}")
        print(f"  Reason: {result.get('reason')}")
        
        if result.get('processed'):
            print(f"\n✅ DRY RUN SUCCESSFUL: Full pipeline executed (Revel write skipped)")
            return True
        elif result.get('ok'):
            print(f"\n⚠️  Pipeline acknowledged: {result.get('reason')}")
            return False
        else:
            print(f"\n❌ FAILED: {result.get('reason')}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "TRIPLESEAT-REVEL REAL INJECTION TESTS".center(78) + "║")
    print("║" + "Webhook-First Approach (No TripleSeat API Calls)".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    # Test 1: Dry run (validates pipeline)
    print("\n\n[STEP 1/3] Validating full pipeline with DRY_RUN...")
    dry_run_ok = await test_with_dry_run()
    
    # Test 2: Full webhook to Revel pipeline
    print("\n\n[STEP 2/3] Testing full webhook → Revel pipeline...")
    pipeline_ok = await test_webhook_to_revel_full_pipeline()
    
    # Test 3: Direct injection (fallback test)
    print("\n\n[STEP 3/3] Testing direct Revel injection...")
    injection_ok = await test_direct_revel_injection()
    
    # Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\nDry-Run Test: {'✅ PASSED' if dry_run_ok else '❌ FAILED'}")
    print(f"Full Pipeline Test: {'✅ PASSED' if pipeline_ok else '⚠️  INCOMPLETE'}")
    print(f"Direct Injection Test: {'✅ PASSED' if injection_ok else '❌ FAILED'}")
    
    if pipeline_ok or injection_ok:
        print("\n✅ REAL REVEL INJECTION SUCCESSFUL!")
        print("\nNext Steps:")
        print("  1. Check Revel POS dashboard for new orders")
        print("  2. Verify menu items and pricing")
        print("  3. Check email notifications")
        print("  4. Monitor order status in Revel")
    else:
        print("\n⚠️  Real injection tests did not complete as expected")
        print("\nCheck logs for:")
        print("  - Revel connection status")
        print("  - API authentication")
        print("  - Event data validation")


if __name__ == '__main__':
    asyncio.run(main())
