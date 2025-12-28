#!/usr/bin/env python
"""
REAL REVEL INJECTION - SIMPLIFIED TEST
Injects real order directly into Revel from webhook payload
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Test order creation directly in Revel
def test_revel_order_creation():
    """Test creating a real order in Revel POS"""
    
    print("\n" + "="*80)
    print("DIRECT REVEL ORDER CREATION TEST")
    print("="*80)
    
    from integrations.revel.injection import inject_order
    
    # Create a test event that will be injected into Revel
    event_id = "test_tripleseat_event_001"
    
    print(f"\n[TEST] Creating order for event: {event_id}")
    print(f"[TEST] Destination: Revel POS (Location: Test/4)")
    print(f"[TEST] Mode: REAL INJECTION (will write to Revel)")
    
    try:
        # Call injection directly
        result = inject_order(
            event_id=event_id,
            correlation_id="real-injection-001",
            dry_run=False,  # REAL INJECTION
            enable_connector=True,
            test_location_override=True,
            test_establishment_id="4"
        )
        
        print(f"\n[RESULT] Injection Complete")
        print(f"  Success: {result.success}")
        print(f"  Error: {result.error}")
        
        if result.success:
            print(f"\n✅ SUCCESS: Order created in Revel!")
            print(f"\n  Order Details:")
            if result.order_details:
                for key, value in result.order_details.items():
                    print(f"    {key}: {value}")
            return True
        else:
            print(f"\n⚠️  Order creation failed: {result.error}")
            if "event data" in str(result.error).lower():
                print("\n   Note: The injection function needs TripleSeat event data.")
                print("   In production, this comes from the webhook payload.")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_revel_dry_run():
    """Test with DRY_RUN to see what would happen"""
    
    print("\n" + "="*80)
    print("DRY RUN: ORDER CREATION SIMULATION")
    print("="*80)
    
    from integrations.revel.injection import inject_order
    
    event_id = "test_tripleseat_event_002"
    
    print(f"\n[TEST] Simulating order for event: {event_id}")
    print(f"[TEST] Mode: DRY RUN (no Revel write)")
    
    try:
        result = inject_order(
            event_id=event_id,
            correlation_id="dry-run-injection-001",
            dry_run=True,  # DRY RUN
            enable_connector=True,
            test_location_override=True,
            test_establishment_id="4"
        )
        
        print(f"\n[RESULT] Injection Simulation Complete")
        print(f"  Success: {result.success}")
        print(f"  Error: {result.error}")
        
        if result.success:
            print(f"\n✅ DRY RUN PASSED: Order would be created")
            return True
        else:
            print(f"\n⚠️  Simulation failed: {result.error}")
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
    print("║" + "REVEL POS INJECTION TESTS".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    print("\n\n[STEP 1/2] Testing with DRY_RUN...")
    dry_run_ok = test_revel_dry_run()
    
    print("\n\n[STEP 2/2] Testing REAL REVEL INJECTION...")
    real_ok = test_revel_order_creation()
    
    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nDry-Run Test: {'✅ PASSED' if dry_run_ok else '⚠️  See details above'}")
    print(f"Real Injection Test: {'✅ PASSED' if real_ok else '⚠️  See details above'}")
    
    print("\n" + "-"*80)
    if real_ok:
        print("\n✅ REAL REVEL INJECTION SUCCESSFUL!")
        print("\nOrder should now be visible in:")
        print("  1. Revel POS dashboard")
        print("  2. Order management system")
        print("  3. Kitchen display system (if configured)")
    else:
        print("\n⚠️  Injection did not complete successfully")
        print("\nThis is normal if event data is not available from TripleSeat API.")
        print("In production, the webhook payload provides all event data needed.")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
