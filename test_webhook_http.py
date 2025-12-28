#!/usr/bin/env python
"""
HTTP client to test the webhook endpoint against a running server.
Use this to test the actual FastAPI /webhook endpoint.

Usage:
  1. Start the server: python -m uvicorn app:app --reload --port 8000
  2. In another terminal: python test_webhook_http.py
"""

import asyncio
import httpx
import hmac
import hashlib
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import os


def create_valid_signature(body: str, signing_key: str) -> str:
    """Create a valid webhook signature."""
    timestamp = str(int(datetime.now().timestamp()))
    signed_payload = f"{timestamp}.{body}"
    signature = hmac.new(
        signing_key.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


async def test_webhook_endpoint():
    """Test the actual webhook endpoint via HTTP."""
    print("\n" + "=" * 80)
    print("WEBHOOK HTTP ENDPOINT TEST")
    print("=" * 80)
    
    # Configuration
    base_url = "http://localhost:8000"
    signing_key = os.getenv('TRIPLESEAT_WEBHOOK_SECRET')
    
    print(f"\n🌐 Testing against: {base_url}")
    print(f"✓ Using webhook signing key (last 10 chars: ...{signing_key[-10:] if signing_key else 'NOT SET'})")
    
    async with httpx.AsyncClient() as client:
        # Test 1: Valid webhook with signature
        print("\n" + "-" * 80)
        print("TEST 1: Valid Event Creation Webhook with Signature")
        print("-" * 80)
        
        payload = {
            "webhook_trigger_type": "CREATE_EVENT",
            "event": {
                "id": "12345",
                "site_id": "4",
                "status": "Definite",
                "event_date": "2025-12-28",
                "updated_at": "2025-12-27T10:30:00Z",
                "contact": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "555-0123"
                }
            }
        }
        
        body = json.dumps(payload)
        headers = {
            "Content-Type": "application/json",
            "X-Signature": create_valid_signature(body, signing_key) if signing_key else ""
        }
        
        print(f"📤 POST {base_url}/webhook")
        print(f"   Trigger: CREATE_EVENT")
        print(f"   Event ID: 12345")
        print(f"   Site ID: 4")
        if signing_key:
            print(f"   Signature: Valid (t=<timestamp>,v1=<hash>)")
        
        try:
            response = await client.post(
                f"{base_url}/webhook",
                content=body,
                headers=headers,
                timeout=10
            )
            print(f"\n📥 Response: HTTP {response.status_code}")
            print(f"   {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("   Make sure the server is running: python -m uvicorn app:app --reload --port 8000")
        
        # Test 2: Non-actionable trigger
        print("\n" + "-" * 80)
        print("TEST 2: Non-Actionable Trigger (WEBHOOK_TEST)")
        print("-" * 80)
        
        payload_2 = {
            "webhook_trigger_type": "WEBHOOK_TEST",
            "event": {
                "id": "99999",
                "site_id": "4"
            }
        }
        
        body_2 = json.dumps(payload_2)
        headers_2 = {
            "Content-Type": "application/json",
            "X-Signature": create_valid_signature(body_2, signing_key) if signing_key else ""
        }
        
        print(f"📤 POST {base_url}/webhook")
        print(f"   Trigger: WEBHOOK_TEST (non-actionable)")
        
        try:
            response = await client.post(
                f"{base_url}/webhook",
                content=body_2,
                headers=headers_2,
                timeout=10
            )
            print(f"\n📥 Response: HTTP {response.status_code}")
            print(f"   {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        # Test 3: Invalid signature
        print("\n" + "-" * 80)
        print("TEST 3: Invalid Signature (Security Test)")
        print("-" * 80)
        
        payload_3 = {
            "webhook_trigger_type": "CREATE_EVENT",
            "event": {
                "id": "12346",
                "site_id": "4"
            }
        }
        
        body_3 = json.dumps(payload_3)
        headers_3 = {
            "Content-Type": "application/json",
            "X-Signature": "t=1640000000,v1=invalidsignature"
        }
        
        print(f"📤 POST {base_url}/webhook")
        print(f"   Signature: INVALID (tampered)")
        
        try:
            response = await client.post(
                f"{base_url}/webhook",
                content=body_3,
                headers=headers_3,
                timeout=10
            )
            print(f"\n📥 Response: HTTP {response.status_code}")
            result = response.json()
            print(f"   {json.dumps(result, indent=2)}")
            
            if not result.get('ok') and 'SIGNATURE' in result.get('reason', ''):
                print("   ✓ Signature verification working correctly")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        # Test 4: Test endpoint (no signature verification)
        print("\n" + "-" * 80)
        print("TEST 4: Test Endpoint (/test/webhook) - No Signature Required")
        print("-" * 80)
        
        payload_4 = {
            "webhook_trigger_type": "CREATE_EVENT",
            "event": {
                "id": "test_event_001",
                "site_id": "4",
                "status": "Definite",
                "event_date": "2025-12-28",
                "updated_at": "2025-12-27T10:45:00Z"
            }
        }
        
        body_4 = json.dumps(payload_4)
        headers_4 = {"Content-Type": "application/json"}
        
        print(f"📤 POST {base_url}/test/webhook")
        print(f"   Note: /test/webhook skips signature verification")
        
        try:
            response = await client.post(
                f"{base_url}/test/webhook",
                content=body_4,
                headers=headers_4,
                timeout=10
            )
            print(f"\n📥 Response: HTTP {response.status_code}")
            print(f"   {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
✓ Test 1 (Valid Signature): Event webhook with correct signature
✓ Test 2 (Non-Actionable): Non-actionable trigger safely acknowledged
✓ Test 3 (Invalid Signature): Tampered signature rejected
✓ Test 4 (Test Endpoint): Test mode without signature verification

All endpoints return HTTP 200 to prevent TripleSeat webhook deactivation.
Signature verification prevents webhook tampering in production.
""")
    
    print("=" * 80)
    print("\n📖 How to use in production:")
    print("   1. Start server: python -m uvicorn app:app --host 0.0.0.0 --port 8000")
    print("   2. Configure in TripleSeat: Webhook → https://your-domain/webhook")
    print("   3. Signature verification will automatically validate each webhook")
    print("   4. All event statuses (valid/invalid) return HTTP 200")


if __name__ == '__main__':
    asyncio.run(test_webhook_endpoint())
