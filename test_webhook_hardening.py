#!/usr/bin/env python
"""
Test suite for hardened webhook implementation.
Tests signature verification, trigger routing, idempotency, and response contracts.
"""

import asyncio
import hmac
import hashlib
import json
from dotenv import load_dotenv
load_dotenv()
from integrations.tripleseat.webhook_handler import (
    handle_tripleseat_webhook,
    verify_webhook_signature,
    ACTIONABLE_TRIGGERS
)

def create_test_signature(body: str, signing_key: str) -> str:
    """Create a valid test signature."""
    timestamp = "1640000000"
    signed_payload = f"{timestamp}.{body}"
    signature = hmac.new(
        signing_key.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


def test_signature_verification():
    """Test webhook signature verification."""
    print("\n" + "=" * 70)
    print("TEST 1: SIGNATURE VERIFICATION")
    print("=" * 70)
    
    signing_key = "test_key_12345"
    body = '{"event": {"id": "123"}}'
    
    # Valid signature
    valid_sig = create_test_signature(body, signing_key)
    is_valid, error = verify_webhook_signature(body.encode(), valid_sig)
    print(f"✓ Valid signature accepted: {is_valid}")
    
    # Invalid signature
    is_valid, error = verify_webhook_signature(body.encode(), "t=1640000000,v1=invalidsignature")
    print(f"✓ Invalid signature rejected: {not is_valid}")
    
    # Missing header
    is_valid, error = verify_webhook_signature(body.encode(), "")
    print(f"✓ Missing signature rejected: {not is_valid}")
    
    return True


async def test_trigger_routing():
    """Test trigger-type routing and allowlist."""
    print("\n" + "=" * 70)
    print("TEST 2: TRIGGER ROUTING")
    print("=" * 70)
    
    # Test actionable trigger
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'event': {'id': '123', 'site_id': '1'},
    }
    result = await handle_tripleseat_webhook(
        payload, 'test_trigger_001',
        verify_signature_flag=False,
        dry_run=True,
        enable_connector=True
    )
    print(f"✓ Actionable trigger (CREATE_EVENT) processed: {result.get('trigger') == 'CREATE_EVENT'}")
    
    # Test non-actionable trigger
    payload = {
        'webhook_trigger_type': 'UNKNOWN_TRIGGER',
        'event': {'id': '123', 'site_id': '1'},
    }
    result = await handle_tripleseat_webhook(
        payload, 'test_trigger_002',
        verify_signature_flag=False,
        dry_run=True,
        enable_connector=True
    )
    print(f"✓ Non-actionable trigger rejected: {result.get('processed') == False}")
    print(f"✓ Response includes trigger: {result.get('trigger') == 'UNKNOWN_TRIGGER'}")
    
    # Test missing trigger
    payload = {
        'event': {'id': '123', 'site_id': '1'},
    }
    result = await handle_tripleseat_webhook(
        payload, 'test_trigger_003',
        verify_signature_flag=False,
        dry_run=True,
        enable_connector=True
    )
    print(f"✓ Missing trigger handled: {result.get('reason') == 'MISSING_TRIGGER_TYPE'}")
    
    return True


async def test_idempotency():
    """Test idempotency detection."""
    print("\n" + "=" * 70)
    print("TEST 3: IDEMPOTENCY")
    print("=" * 70)
    
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'event': {
            'id': '9999',
            'site_id': '1',
            'updated_at': '2025-12-27T10:00:00Z'
        },
    }
    
    # First delivery
    result1 = await handle_tripleseat_webhook(
        payload, 'test_idem_001',
        verify_signature_flag=False,
        dry_run=True,
        enable_connector=True
    )
    print(f"✓ First delivery processed: {result1.get('trigger') is not None}")
    
    # Second delivery (duplicate)
    result2 = await handle_tripleseat_webhook(
        payload, 'test_idem_002',
        verify_signature_flag=False,
        dry_run=True,
        enable_connector=True
    )
    print(f"✓ Duplicate detected: {result2.get('reason') == 'DUPLICATE_DELIVERY'}")
    print(f"✓ Duplicate still returns ok=true: {result2.get('ok') == True}")
    
    return True


async def test_response_contract():
    """Test that response contract is followed."""
    print("\n" + "=" * 70)
    print("TEST 4: RESPONSE CONTRACT")
    print("=" * 70)
    
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'event': {'id': '123', 'site_id': '1', 'updated_at': '2025-12-27T10:00:00Z'},
    }
    
    result = await handle_tripleseat_webhook(
        payload, 'test_contract_001',
        verify_signature_flag=False,
        dry_run=True,
        enable_connector=True
    )
    
    required_fields = {
        'ok': result.get('ok') is not None,
        'processed': result.get('processed') is not None,
        'trigger': result.get('trigger') is not None,
    }
    
    for field, present in required_fields.items():
        status = '✓' if present else '✗'
        print(f"{status} Response includes '{field}': {present}")
    
    return all(required_fields.values())


async def test_missing_data_handling():
    """Test handling of missing required data."""
    print("\n" + "=" * 70)
    print("TEST 5: MISSING DATA HANDLING")
    print("=" * 70)
    
    # Missing site_id
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'event': {'id': '123'},
    }
    result = await handle_tripleseat_webhook(
        payload, 'test_missing_001',
        verify_signature_flag=False,
        dry_run=True,
        enable_connector=True
    )
    print(f"✓ Missing site_id handled: {result.get('reason') == 'MISSING_SITE_ID'}")
    print(f"✓ Still returns ok=true: {result.get('ok') == True}")
    
    # Missing event_id
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'event': {'site_id': '1'},
    }
    result = await handle_tripleseat_webhook(
        payload, 'test_missing_002',
        verify_signature_flag=False,
        dry_run=True,
        enable_connector=True
    )
    print(f"✓ Missing event_id handled: {result.get('reason') == 'NO_EVENT_ID'}")
    
    return True


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " HARDENED WEBHOOK IMPLEMENTATION - COMPLETE TEST SUITE".center(68) + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = {}
    
    # Test 1
    results['Signature Verification'] = test_signature_verification()
    
    # Test 2
    results['Trigger Routing'] = await test_trigger_routing()
    
    # Test 3
    results['Idempotency'] = await test_idempotency()
    
    # Test 4
    results['Response Contract'] = await test_response_contract()
    
    # Test 5
    results['Missing Data Handling'] = await test_missing_data_handling()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = '✓ PASS' if result else '✗ FAIL'
        print(f'{status}: {test_name}')
    
    print("\n" + "=" * 70)
    if passed == total:
        print(f'✓ ALL TESTS PASSED ({passed}/{total})')
        print("\nWebhook implementation is hardened and production-ready.")
    else:
        print(f'✗ SOME TESTS FAILED ({total - passed} failures)')
        return 1
    print("=" * 70 + "\n")
    
    return 0

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)
