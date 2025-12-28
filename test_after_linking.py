from dotenv import load_dotenv
load_dotenv()

from integrations.tripleseat.oauth import clear_token_cache
clear_token_cache()
print("Token cache cleared")

# Now test the API
from integrations.tripleseat.api_client import TripleSeatAPIClient

api_client = TripleSeatAPIClient()
print("\nTesting API with fresh token...")

# Test 1: Check Access
print("Test 1 - OAuth Access")
print("-" * 40)
is_valid = api_client.check_tripleseat_access()
if is_valid:
    print("✅ OAuth 2.0 authentication VALID")
else:
    print("❌ OAuth 2.0 authentication FAILED (401)")

# Test 2: Get Event
print("\nTest 2 - Get Event (ID: 12345)")
print("-" * 40)
event_data, status = api_client.get_event_with_status('12345')
if event_data:
    print(f"✅ Event retrieved successfully")
    print(f"   Status code: 200")
    print(f"   Event keys: {list(event_data.keys())[:5]}")
else:
    print(f"❌ Failed with status: {status}")

print("\nDone!")
