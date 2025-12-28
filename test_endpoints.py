from dotenv import load_dotenv
load_dotenv()

import requests
import os
import json

client_id = os.getenv('TRIPLESEAT_OAUTH_CLIENT_ID')
client_secret = os.getenv('TRIPLESEAT_OAUTH_CLIENT_SECRET')
token_url = os.getenv('TRIPLESEAT_OAUTH_TOKEN_URL')
api_base = os.getenv('TRIPLESEAT_API_BASE')

# Get token
data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': 'read write'
}
token_resp = requests.post(token_url, data=data)
token = token_resp.json()['access_token']

print('Testing API endpoints with Bearer token...')
print(f'Token: {token[:30]}...')
print()

# Test different endpoints
endpoints = [
    '/v1/events?limit=1',
    '/v1/locations',
    '/v1/leads?limit=1',
]

for endpoint in endpoints:
    url = api_base + endpoint
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)
    
    print(f'GET {endpoint}')
    print(f'  Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print(f'  Response keys: {list(data.keys())}')
        if 'data' in data:
            print(f'  Records: {len(data["data"])}')
    else:
        print(f'  Error: {response.text[:200]}')
    print()
