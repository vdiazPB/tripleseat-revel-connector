"""Full integration test with working order creation."""
from dotenv import load_dotenv
load_dotenv()

import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

# Import after dotenv
from integrations.revel.injection import inject_order

# Force TEST MODE with DRY_RUN=false for real injection
os.environ['DRY_RUN'] = 'false'
os.environ['TEST_LOCATION_OVERRIDE'] = 'true'
os.environ['TEST_ESTABLISHMENT_ID'] = '4'

print("="*60)
print("FULL INTEGRATION TEST - REAL ORDER INJECTION")
print("="*60)
print(f"DRY_RUN: {os.getenv('DRY_RUN')}")
print(f"TEST_LOCATION_OVERRIDE: {os.getenv('TEST_LOCATION_OVERRIDE')}")
print(f"TEST_ESTABLISHMENT_ID: {os.getenv('TEST_ESTABLISHMENT_ID')}")
print()

# Test webhook payload with items that exist in Revel
test_payload = {
    "event": {
        "id": 999999,
        "site_id": "test-site",
        "name": "Integration Test Event"
    },
    "items": [
        {"name": "HOT COFFEE PREMIUM ROAST", "quantity": 2},
        {"name": "APPLE JUICE", "quantity": 1},
    ],
    "documents": []
}

print("Test payload:")
print(f"  Items: {[item['name'] for item in test_payload['items']]}")
print()

print("="*60)
print("INJECTING ORDER...")
print("="*60)

result = inject_order(
    event_id="integration_test_001",
    correlation_id="test-001",
    dry_run=False,  # REAL INJECTION
    test_location_override=True,
    test_establishment_id="4",
    webhook_payload=test_payload
)

print()
print("="*60)
print("RESULT")
print("="*60)
print(f"Success: {result.success}")
if result.error:
    print(f"Error: {result.error}")
if result.order_details:
    print(f"Order Details: {result.order_details}")
