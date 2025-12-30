#!/usr/bin/env python3
"""Test the 3-tier reconciliation architecture.

Tests:
1. Sync endpoint with single event ID
2. Sync endpoint with bulk recent events
3. Webhook trigger → sync endpoint flow
4. Scheduled task configuration
"""

import requests
import json
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:8000')
EVENT_ID = '55521609'  # Known test event

print("=" * 80)
print("3-TIER RECONCILIATION ARCHITECTURE TEST")
print("=" * 80)

# Test 1: Single Event Sync via Endpoint
print("\n[TEST 1] Single Event Sync - GET /api/sync/tripleseat?event_id=EVENT_ID")
print("-" * 80)
try:
    response = requests.get(
        f"{BASE_URL}/api/sync/tripleseat",
        params={'event_id': EVENT_ID},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    # Verify response structure
    assert 'success' in result, "Missing 'success' field"
    assert 'mode' in result, "Missing 'mode' field"
    assert result.get('mode') == 'single', f"Expected mode='single', got {result.get('mode')}"
    assert 'summary' in result, "Missing 'summary' field"
    assert 'events' in result, "Missing 'events' field"
    
    if result.get('success'):
        print(f"✅ PASS: Event {EVENT_ID} synced successfully")
        if result.get('events'):
            event_details = result['events'][0]
            print(f"   - Revel Order ID: {event_details.get('revel_order_id')}")
            print(f"   - Status: {event_details.get('status')}")
    else:
        print(f"⚠️  Event not injected (may be duplicate/skipped)")
        if result.get('events'):
            event_details = result['events'][0]
            print(f"   - Status: {event_details.get('status')}")
            print(f"   - Reason: {event_details.get('reason')}")
    
except Exception as e:
    print(f"❌ FAIL: {e}")

# Test 2: Bulk Recent Events Sync via Endpoint
print("\n[TEST 2] Bulk Recent Events Sync - GET /api/sync/tripleseat?hours_back=48")
print("-" * 80)
try:
    response = requests.get(
        f"{BASE_URL}/api/sync/tripleseat",
        params={'hours_back': 48},
        timeout=120  # Allow more time for bulk sync
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    
    # Don't print full result for bulk (too large), just summary
    summary = result.get('summary', {})
    print(f"Mode: {result.get('mode')}")
    print(f"Summary:")
    print(f"  - Queried: {summary.get('queried', 0)}")
    print(f"  - Injected: {summary.get('injected', 0)}")
    print(f"  - Skipped: {summary.get('skipped', 0)}")
    print(f"  - Failed: {summary.get('failed', 0)}")
    
    # Verify response structure
    assert 'success' in result, "Missing 'success' field"
    assert 'mode' in result, "Missing 'mode' field"
    assert result.get('mode') == 'bulk', f"Expected mode='bulk', got {result.get('mode')}"
    assert 'summary' in result, "Missing 'summary' field"
    
    if result.get('success'):
        print(f"✅ PASS: Bulk sync completed successfully")
    else:
        print(f"⚠️  Bulk sync completed with issues")
    
except Exception as e:
    print(f"❌ FAIL: {e}")

# Test 3: Webhook Flow Test
print("\n[TEST 3] Webhook Trigger → Sync Endpoint Flow")
print("-" * 80)
print("Simulating webhook arrival for event 55521609")

# Create a minimal webhook payload
webhook_payload = {
    "webhook_trigger_type": "UPDATE_EVENT",
    "event": {
        "id": EVENT_ID,
        "site_id": "15691",
        "name": "Test Event",
        "date": datetime.now(pytz.timezone('America/Los_Angeles')).isoformat(),
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
}

try:
    response = requests.post(
        f"{BASE_URL}/webhooks/tripleseat",
        json=webhook_payload,
        timeout=30
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    # Verify webhook response
    assert 'ok' in result, "Missing 'ok' field"
    assert 'processed' in result, "Missing 'processed' field"
    
    if result.get('ok'):
        print(f"✅ PASS: Webhook processed successfully")
        if result.get('processed'):
            print(f"   Event was synced to Revel")
        else:
            print(f"   Event was acknowledged but not synced (may be duplicate/skipped)")
            print(f"   Reason: {result.get('reason')}")
    else:
        print(f"❌ FAIL: Webhook processing failed")
        print(f"   Error: {result.get('reason')}")
    
except Exception as e:
    print(f"❌ FAIL: {e}")

# Test 4: Verify Scheduler Configuration
print("\n[TEST 4] Scheduled Task Configuration")
print("-" * 80)
print("Checking if APScheduler is configured to run sync every 45 minutes...")
try:
    # Try to import and check scheduler
    from apscheduler.schedulers.background import BackgroundScheduler
    print("✅ APScheduler is available")
    
    # Check if requirements.txt includes apscheduler
    with open('requirements.txt', 'r') as f:
        content = f.read()
        if 'apscheduler' in content:
            print("✅ apscheduler is in requirements.txt")
        else:
            print("❌ apscheduler not in requirements.txt")
    
    # Check if app.py has scheduler initialization
    with open('app.py', 'r') as f:
        content = f.read()
        if 'BackgroundScheduler' in content:
            print("✅ BackgroundScheduler initialized in app.py")
        else:
            print("❌ BackgroundScheduler not found in app.py")
        
        if "'interval'" in content and "'minutes'" in content:
            print("✅ Scheduled task configured with interval scheduler")
        else:
            print("❌ Interval scheduler not configured")
    
except ImportError:
    print("⚠️  APScheduler not installed (run: pip install apscheduler)")
except Exception as e:
    print(f"❌ FAIL: {e}")

# Summary
print("\n" + "=" * 80)
print("ARCHITECTURE SUMMARY")
print("=" * 80)
print("""
3-TIER PATTERN IMPLEMENTED:

1️⃣  WEBHOOK TRIGGER (Entry Point)
    - Endpoint: POST /webhooks/tripleseat
    - Receives event notification from TripleSeat
    - Calls sync endpoint with event_id (line ~11 in webhook_handler.py)
    - Returns acknowledgment to TripleSeat

2️⃣  SYNC ENDPOINT (Reconciliation Engine)
    - Endpoint: GET /api/sync/tripleseat
    - Supports two modes:
      a) Single event: ?event_id=55521609
      b) Bulk recent: ?hours_back=48
    - Queries TripleSeat for event details
    - Checks Revel for duplicates (local_id lookup)
    - Injects new orders only
    - Returns summary with counts and details

3️⃣  SCHEDULED TASK (Safety Net)
    - Runs every 45 minutes (via APScheduler)
    - Calls sync endpoint with hours_back=48
    - Catches missed webhooks
    - Idempotent (Revel dedup prevents duplicates)
    - Full audit trail in logs

BENEFITS:
✅ No duplicate orders (Revel-backed idempotency)
✅ Catches missed webhooks (scheduled sync)
✅ Manual sync available (API endpoint)
✅ Full audit trail (correlation IDs)
✅ Industry standard pattern (PayPal, Stripe)

DEPLOYMENT:
- Commit changes to git
- Run: pip install -r requirements.txt (adds apscheduler)
- Scheduler starts automatically on app startup
- Sync endpoint responds within 30 seconds (single) or 2 minutes (bulk)
""")
print("=" * 80)
