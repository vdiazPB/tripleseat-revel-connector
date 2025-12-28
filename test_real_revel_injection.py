#!/usr/bin/env python
"""
REAL REVEL INJECTION TEST
Tests actual injection into Revel POS with real event data
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook

async def test_real_injection():
    """
    Test real injection into Revel with actual event data.
    
    This creates a realistic TripleSeat event webhook and injects it into Revel.
    WARNING: This will attempt ACTUAL REVEL INJECTION (not dry-run by default).
    """
    
    print("\n" + "="*80)
    print("REAL REVEL INJECTION TEST")
    print("="*80)
    
    # Real-looking event data that should pass validation
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'type': 'CREATE_EVENT',
        'event': {
            'id': '54321',  # Real-looking event ID
            'site_id': '4',  # Allowed location
            'status': 'Definite',  # Required status
            'event_date': datetime.now().isoformat(),  # Today's date
            'primary_guest': 'John Doe',
            'guest_count': 50,
            'menu_items': [
                {
                    'name': 'Appetizer Platter',
                    'quantity': 2,
                    'price_per_item': 45.00
                },
                {
                    'name': 'Main Course Chicken',
                    'quantity': 40,
                    'price_per_item': 28.00
                },
                {
                    'name': 'Vegetarian Option',
                    'quantity': 10,
                    'price_per_item': 26.00
                },
                {
                    'name': 'Dessert Trio',
                    'quantity': 50,
                    'price_per_item': 12.00
                }
            ],
            'updated_at': datetime.now().isoformat()
        },
        'booking': {
            'id': '98765',
            'primary_guest': 'John Doe',
            'guest_count': 50,
            'updated_at': datetime.now().isoformat()
        }
    }
    
    print("\n[TEST] Event Data:")
    print(f"  Event ID: {payload['event']['id']}")
    print(f"  Site ID: {payload['event']['site_id']}")
    print(f"  Status: {payload['event']['status']}")
    print(f"  Guest Count: {payload['event']['guest_count']}")
    print(f"  Menu Items: {len(payload['event']['menu_items'])}")
    
    total_price = sum(item['quantity'] * item['price_per_item'] 
                     for item in payload['event']['menu_items'])
    print(f"  Total Value: ${total_price:,.2f}")
    
    print("\n[TEST] Processing webhook with REAL REVEL INJECTION...")
    print("        (DRY_RUN=False - will actually write to Revel)")
    
    try:
        # Process with real injection
        result = await handle_tripleseat_webhook(
            payload=payload,
            correlation_id='real-test-001',
            x_signature_header=None,  # No signature for test
            raw_body=None,
            verify_signature_flag=False,  # Skip signature verification for test
            dry_run=False,  # ACTUAL INJECTION
            enable_connector=True,
            allowed_locations=['4'],  # Allow location 4
            test_location_override=True,  # Use test location
            test_establishment_id='4'  # Test establishment
        )
        
        print("\n[RESULT] Webhook Processing Complete")
        print(f"  Status: {result.get('ok')}")
        print(f"  Processed: {result.get('processed')}")
        print(f"  Reason: {result.get('reason')}")
        print(f"  Trigger: {result.get('trigger')}")
        
        if result.get('processed'):
            print("\n✅ SUCCESS: Event was successfully processed and injected!")
        else:
            print(f"\n⚠️  NOT PROCESSED: {result.get('reason')}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {'ok': False, 'error': str(e)}


async def test_with_dry_run():
    """
    Test with DRY_RUN=True to see full pipeline without writing to Revel.
    """
    
    print("\n" + "="*80)
    print("DRY-RUN TEST (Full Pipeline, No Revel Write)")
    print("="*80)
    
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'event': {
            'id': '54322',
            'site_id': '4',
            'status': 'Definite',
            'event_date': datetime.now().isoformat(),
            'primary_guest': 'Jane Smith',
            'guest_count': 75,
            'menu_items': [
                {
                    'name': 'Gourmet Appetizers',
                    'quantity': 3,
                    'price_per_item': 65.00
                },
                {
                    'name': 'Prime Rib Main Course',
                    'quantity': 60,
                    'price_per_item': 45.00
                },
                {
                    'name': 'Vegan Entrée',
                    'quantity': 15,
                    'price_per_item': 42.00
                },
                {
                    'name': 'Champagne Dessert',
                    'quantity': 75,
                    'price_per_item': 18.00
                }
            ],
            'updated_at': datetime.now().isoformat()
        }
    }
    
    print("\n[TEST] Event Data:")
    print(f"  Event ID: {payload['event']['id']}")
    print(f"  Site ID: {payload['event']['site_id']}")
    print(f"  Guest Count: {payload['event']['guest_count']}")
    
    print("\n[TEST] Processing webhook with DRY_RUN=True...")
    print("        (Will execute full pipeline but skip Revel write)")
    
    try:
        result = await handle_tripleseat_webhook(
            payload=payload,
            correlation_id='dry-run-test-001',
            verify_signature_flag=False,
            dry_run=True,  # DRY RUN MODE
            enable_connector=True,
            allowed_locations=['4'],
            test_location_override=True,
            test_establishment_id='4'
        )
        
        print("\n[RESULT] Webhook Processing Complete")
        print(f"  Status: {result.get('ok')}")
        print(f"  Processed: {result.get('processed')}")
        print(f"  Reason: {result.get('reason')}")
        
        if result.get('processed'):
            print("\n✅ DRY RUN SUCCESSFUL: Pipeline executed fully (Revel write skipped)")
        else:
            print(f"\n⚠️  NOT PROCESSED: {result.get('reason')}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {'ok': False, 'error': str(e)}


async def main():
    """Run both tests."""
    
    print("\n\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "TRIPLESEAT-REVEL REAL INJECTION TESTS".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    # Test 1: DRY RUN (safe)
    dry_run_result = await test_with_dry_run()
    
    print("\n\n")
    
    # Test 2: REAL INJECTION
    real_result = await test_real_injection()
    
    # Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\nDry-Run Test: {'✅ PASSED' if dry_run_result.get('ok') else '❌ FAILED'}")
    print(f"Real Injection Test: {'✅ PASSED' if real_result.get('ok') else '⚠️  INCOMPLETE' if real_result.get('processed') else '❌ FAILED'}")
    
    if real_result.get('processed'):
        print("\n✅ REAL REVEL INJECTION SUCCESSFUL!")
        print("\nNext Steps:")
        print("  1. Check Revel POS for new order")
        print("  2. Verify menu items were correctly mapped")
        print("  3. Confirm pricing and guest count are accurate")
        print("  4. Check email notifications were sent")
    else:
        print(f"\n⚠️  Real injection did not complete: {real_result.get('reason')}")
        print("\nPossible causes:")
        print("  - Event data failed validation")
        print("  - Billing invoice missing in API response")
        print("  - Revel connection issue")
        print("  - Menu item mapping incomplete")


if __name__ == '__main__':
    asyncio.run(main())
