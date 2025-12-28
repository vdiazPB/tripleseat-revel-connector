#!/usr/bin/env python
"""
REAL REVEL INJECTION TEST - WITH WEBHOOK PAYLOAD
Complete end-to-end test with actual order data
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def test_real_injection_with_payload():
    """
    Test real Revel injection with complete webhook payload.
    This is the most realistic test - webhook provides all event data.
    """
    
    print("\n" + "="*80)
    print("REAL REVEL INJECTION WITH WEBHOOK PAYLOAD")
    print("="*80)
    
    from integrations.revel.injection import inject_order
    
    # Complete event data as it would come from TripleSeat webhook
    event_id = "webhook_test_event_12345"
    
    webhook_payload = {
        'event': {
            'id': event_id,
            'site_id': '4',
            'primary_guest': 'Smith Family Event',
            'guest_count': 75,
            'menu_items': [
                {
                    'name': 'Pinkbox Assorted Donuts',
                    'quantity': 150,
                    'price_per_item': 0.75
                },
                {
                    'name': 'Coffee Service',
                    'quantity': 75,
                    'price_per_item': 2.50
                },
                {
                    'name': 'Juice & Beverages',
                    'quantity': 75,
                    'price_per_item': 1.50
                },
                {
                    'name': 'Fruit Platter',
                    'quantity': 1,
                    'price_per_item': 45.00
                }
            ],
            'status': 'Definite',
            'event_date': datetime.now().isoformat(),
            'setup_time': '7:00 AM',
            'event_time': '8:00 AM',
            'delivery_address': '123 Main St'
        },
        'booking': {
            'id': 'booking_88888',
            'primary_guest': 'John Smith',
            'guest_count': 75
        }
    }
    
    # Calculate totals
    total_items = sum(item['quantity'] for item in webhook_payload['event']['menu_items'])
    total_revenue = sum(item['quantity'] * item['price_per_item'] 
                       for item in webhook_payload['event']['menu_items'])
    
    print(f"\n[EVENT] {webhook_payload['event']['primary_guest']}")
    print(f"  Event ID: {event_id}")
    print(f"  Site ID: {webhook_payload['event']['site_id']}")
    print(f"  Guests: {webhook_payload['event']['guest_count']}")
    print(f"  Menu Items: {len(webhook_payload['event']['menu_items'])} items")
    print(f"  Total Items: {total_items} units")
    print(f"  Total Revenue: ${total_revenue:,.2f}")
    
    print(f"\n[MENU]")
    for item in webhook_payload['event']['menu_items']:
        print(f"  - {item['name']}: {item['quantity']} × ${item['price_per_item']:.2f}")
    
    print(f"\n[TEST] Mode: REAL INJECTION (DRY_RUN=False)")
    print(f"[TEST] Destination: Revel POS - Pinkbox Doughnuts")
    print(f"[TEST] Correlation ID: webhook-real-test-001")
    
    try:
        # Inject with webhook payload
        result = inject_order(
            event_id=event_id,
            correlation_id="webhook-real-test-001",
            dry_run=False,  # REAL INJECTION
            enable_connector=True,
            test_location_override=True,
            test_establishment_id="4",
            webhook_payload=webhook_payload  # Pass complete webhook data
        )
        
        print(f"\n[RESULT] Injection Complete")
        print(f"  Success: {result.success}")
        print(f"  Error: {result.error}")
        
        if result.success:
            print(f"\n✅ SUCCESS: Order created in Revel!")
            print(f"\n[ORDER DETAILS]")
            if result.order_details:
                print(json.dumps(result.order_details, indent=2))
            return True
        else:
            print(f"\n❌ FAILED: {result.error}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dry_run_with_payload():
    """Test with DRY_RUN to validate without writing to Revel"""
    
    print("\n" + "="*80)
    print("DRY-RUN INJECTION WITH WEBHOOK PAYLOAD")
    print("="*80)
    
    from integrations.revel.injection import inject_order
    
    event_id = "dry_run_test_event_67890"
    
    webhook_payload = {
        'event': {
            'id': event_id,
            'site_id': '4',
            'primary_guest': 'Corporate Catering',
            'guest_count': 200,
            'menu_items': [
                {'name': 'Pinkbox Assorted Donuts', 'quantity': 400, 'price_per_item': 0.75},
                {'name': 'Coffee & Tea Service', 'quantity': 200, 'price_per_item': 3.00},
                {'name': 'Fresh Fruit Platter', 'quantity': 2, 'price_per_item': 65.00},
                {'name': 'Bagel & Cream Cheese', 'quantity': 100, 'price_per_item': 1.50}
            ],
            'status': 'Definite',
            'event_date': datetime.now().isoformat()
        }
    }
    
    print(f"\n[EVENT] {webhook_payload['event']['primary_guest']}")
    print(f"  Guests: {webhook_payload['event']['guest_count']}")
    print(f"  Menu Items: {len(webhook_payload['event']['menu_items'])}")
    
    total_revenue = sum(item['quantity'] * item['price_per_item'] 
                       for item in webhook_payload['event']['menu_items'])
    print(f"  Total Value: ${total_revenue:,.2f}")
    
    print(f"\n[TEST] Mode: DRY RUN (validates but does not write)")
    
    try:
        result = inject_order(
            event_id=event_id,
            correlation_id="webhook-dry-run-001",
            dry_run=True,  # DRY RUN
            enable_connector=True,
            test_location_override=True,
            test_establishment_id="4",
            webhook_payload=webhook_payload
        )
        
        print(f"\n[RESULT] Injection Simulation Complete")
        print(f"  Success: {result.success}")
        print(f"  Error: {result.error}")
        
        if result.success:
            print(f"\n✅ DRY RUN PASSED: Order would be created")
            print(f"   (No actual write to Revel)")
            return True
        else:
            print(f"\n❌ Simulation failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "REAL REVEL INJECTION TESTS".center(78) + "║")
    print("║" + "With Complete Webhook Payload Data".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    print("\n[STEP 1/2] Testing with DRY_RUN...")
    dry_run_ok = test_dry_run_with_payload()
    
    print("\n\n[STEP 2/2] Testing REAL INJECTION...")
    real_ok = test_real_injection_with_payload()
    
    # Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\nDry-Run Test: {'✅ PASSED' if dry_run_ok else '❌ FAILED'}")
    print(f"Real Injection Test: {'✅ PASSED' if real_ok else '❌ FAILED'}")
    
    print("\n" + "-"*80)
    if real_ok:
        print("\n✅ REAL REVEL INJECTION SUCCESSFUL!")
        print("\nOrders are now in Revel POS and should be visible in:")
        print("  ✓ Revel Dashboard")
        print("  ✓ Order Management System")
        print("  ✓ Kitchen Display System")
        print("  ✓ Inventory (items deducted)")
        print("\nNext steps:")
        print("  1. Verify orders in Revel POS")
        print("  2. Check menu item quantities were correct")
        print("  3. Confirm pricing and totals")
        print("  4. Monitor fulfillment status")
    else:
        print("\n❌ INJECTION TESTS FAILED")
        print("\nPossible issues:")
        print("  - Revel API connection problem")
        print("  - Menu item mapping incomplete")
        print("  - Revel establishment configuration")
        print("  - API authentication issue")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
