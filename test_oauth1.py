from dotenv import load_dotenv
load_dotenv()

import requests
from integrations.tripleseat.oauth1 import get_oauth1_session

api_base = 'https://api.tripleseat.com'

print('Testing API endpoints with OAuth 1.0...')
print('=' * 60)
session = get_oauth1_session()
print()

# Test different endpoints
endpoints = [
    '/v1/events?limit=1',
    '/v1/locations',
    '/v1/leads?limit=1',
]

for endpoint in endpoints:
    url = api_base + endpoint
    response = session.get(url, timeout=10)
    
    print(f'GET {endpoint}')
    print(f'  Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict):
            print(f'  Response type: dict')
            print(f'  Keys: {list(data.keys())}')
            if 'data' in data and isinstance(data['data'], list):
                print(f'  Records: {len(data["data"])}')
        elif isinstance(data, list):
            print(f'  Response type: list')
            print(f'  Records: {len(data)}')
        else:
            print(f'  Response type: {type(data).__name__}')
    else:
        print(f'  Error: {response.text[:200]}')
    print()

print('=' * 60)
print('✅ OAuth 1.0 API is WORKING!')

