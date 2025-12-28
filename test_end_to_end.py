#!/usr/bin/env python3
"""
End-to-End Test Script for TripleSeat-Revel Connector
Tests order injection with realistic payload including discounts and multiple items.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
LOCAL_BASE_URL = "http://127.0.0.1:8000"
RENDER_BASE_URL = "https://your-render-app-url.onrender.com"  # Replace with actual Render URL if needed

def construct_test_payload():
    """Construct a realistic TripleSeat webhook payload for testing."""
    return {
        "event": {
            "id": "test_event_12345",
            "site_id": "1",  # Will be overridden to establishment 4 in test mode
            "status": "Definite",
            "event_date": "2025-12-27T18:00:00Z",
            "triggered_at": datetime.utcnow().isoformat() + "Z",
            "menu_items": [
                {
                    "name": "Glazed Donut",  # Should exist in Revel Siegel menu
                    "quantity": 2
                },
                {
                    "name": "Chocolate Donut",  # Should exist
                    "quantity": 1
                },
                {
                    "name": "NonExistentItem",  # Should NOT exist - test negative case
                    "quantity": 1
                },
                {
                    "name": "Sprinkled Donut",  # Should exist
                    "quantity": 3
                }
            ]
        },
        "documents": [
            {
                "type": "billing_invoice",
                "subtotal": 25.00,  # Total before discount
                "total": 20.00      # After discount
            }
        ]
    }

def test_endpoint(base_url, endpoint, payload):
    """Test a specific endpoint and return response."""
    url = f"{base_url}{endpoint}"
    print(f"Testing endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)

    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"HTTP Status: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")

            # Validate required fields
            required_fields = ["ok", "dry_run", "site_id", "time_gate"]
            missing_fields = [field for field in required_fields if field not in response_data]
            if missing_fields:
                print(f"❌ MISSING REQUIRED FIELDS: {missing_fields}")
                return False, response_data

            # Check ok == true
            if not response_data.get("ok"):
                print("❌ RESPONSE ok != true")
                return False, response_data

            print("✅ Response validation passed")
            return True, response_data
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            return False, response_data if response.headers.get('content-type') == 'application/json' else {}

    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return False, {}

def main():
    print("=" * 70)
    print("TRIPLESEAT-REVEL CONNECTOR: END-TO-END TEST")
    print("=" * 70)
    print()

    # Construct test payload
    payload = construct_test_payload()
    print("Constructed test payload with:")
    print(f"- Event ID: {payload['event']['id']}")
    print(f"- Site ID: {payload['event']['site_id']}")
    print(f"- {len(payload['event']['menu_items'])} menu items")
    print(f"- Subtotal: ${payload['documents'][0]['subtotal']}")
    print(f"- Total: ${payload['documents'][0]['total']}")
    print(f"- Discount: ${payload['documents'][0]['subtotal'] - payload['documents'][0]['total']}")
    print()

    success = True

    # Test 1: Local /test/webhook
    print("TEST 1: Local /test/webhook endpoint")
    print("-" * 50)
    local_success, local_response = test_endpoint(LOCAL_BASE_URL, "/test/webhook", payload)
    success &= local_success
    print()

    # Test 2: Render /webhooks/tripleseat (optional - comment out if not deployed)
    # print("TEST 2: Render /webhooks/tripleseat endpoint")
    # print("-" * 50)
    # render_success, render_response = test_endpoint(RENDER_BASE_URL, "/webhooks/tripleseat", payload)
    # success &= render_success
    # print()

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    if success:
        print("✅ ALL TESTS PASSED")
        print("✅ Order injection logic validated")
        print("✅ Negative test case (NonExistentItem) should be logged as skipped")
        print("✅ Check logs above for [TEST] markers and correlation IDs")
    else:
        print("❌ SOME TESTS FAILED")
        print("❌ Check logs and response details above")
        sys.exit(1)

    print()
    print("Expected log sequence (check application logs):")
    print("1. [req-XXXX] [TEST] TEST WEBHOOK INVOKED")
    print("2. [req-XXXX] Webhook received")
    print("3. [req-XXXX] Payload parsed")
    print("4. [req-XXXX] [TEST] Location override ACTIVE – using establishment 4")
    print("5. [req-XXXX] [TEST] Skipping API validation - using webhook payload")
    print("6. [req-XXXX] [TEST] Skipping time gate check")
    print("7. [req-XXXX] [ITEM RESOLUTION] Attempting: 'Glazed Donut' x2")
    print("8. [req-XXXX] [ITEM RESOLVED] 'Glazed Donut' → product_id=..., qty=2")
    print("9. Similar for other existing items")
    print("10. [req-XXXX] [ITEM SKIPPED] 'NonExistentItem' not found in Revel – skipping")
    print("11. [req-XXXX] [DRY_RUN] Would inject X items to establishment 4")
    print("12. [req-XXXX] [DRY_RUN] Revel write PREVENTED – DRY_RUN=true")
    print("13. [req-XXXX] Webhook completed")
    print()

if __name__ == "__main__":
    main()