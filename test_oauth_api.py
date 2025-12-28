import os
import json
from dotenv import load_dotenv
import requests

load_dotenv()

from integrations.tripleseat.oauth import get_access_token
from integrations.tripleseat.api_client import TripleSeatAPIClient

print('=' * 80)
print('TRIPLESEAT API TEST - OAuth 2.0')
print('=' * 80)
print()

# Initialize
api_client = TripleSeatAPIClient()
token = get_access_token()

print('Token obtained:', token[:30] + '...')
print('Base URL:', api_client.base_url)
print()

# Test 1: Check Access
print('Test 1: Check OAuth 2.0 Access')
print('-' * 40)
is_valid = api_client.check_tripleseat_access()
if is_valid:
    print('✅ OAuth 2.0 authentication is VALID')
else:
    print('❌ OAuth 2.0 authentication FAILED (401)')
print()

# Test 2: Get Event Details
print('Test 2: Get Event Details (ID: 12345)')
print('-' * 40)
event_data, status = api_client.get_event_with_status('12345')
if event_data:
    print(f'✅ Event retrieved successfully')
    print(f'   Event keys: {list(event_data.keys())[:5]}')
elif status == 'AUTHORIZATION_DENIED':
    print(f'❌ Authorization failed (401) - "Token resource owner not found"')
    print('   This requires OAuth app linking in TripleSeat admin')
else:
    print(f'❌ Failed with status: {status}')
print()

# Test 3: Direct API Request
print('Test 3: Direct API Request with Headers')
print('-' * 40)
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
url = f"{api_client.base_url}/v1/events?limit=1"
response = requests.get(url, headers=headers, timeout=10)
print(f'Status Code: {response.status_code}')
print(f'Content-Type: {response.headers.get("content-type")}')
if response.status_code == 200:
    print(f'✅ Response is valid JSON')
    data = response.json()
    print(f'   Response keys: {list(data.keys())}')
else:
    print(f'Response body: {response.text[:200]}')
print()

print('=' * 80)
print('API TEST COMPLETE')
print('=' * 80)
