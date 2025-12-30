import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('JERA_API_KEY')
username = os.getenv('JERA_API_USERNAME')

print(f'API Key configured: {bool(api_key)}')
if api_key:
    print(f'API Key (first 20 chars): {api_key[:20]}...')
print(f'Username: {username}')

# Test simple request
url = 'https://supplyit.jeraconcepts.com/api/v2/locations'
headers = {
    'X-API-Key': api_key,
    'X-API-Username': username
}

print(f'\nTesting endpoint: {url}')
print(f'Request headers: {list(headers.keys())}')

try:
    resp = requests.get(url, headers=headers, timeout=5)
    print(f'Status Code: {resp.status_code}')
    print(f'Response: {resp.text[:500]}')
    
    if resp.status_code == 200:
        print('\n✅ Success! API credentials are working')
    elif resp.status_code == 403:
        print('\n❌ 403 Forbidden - Check API key and username')
    elif resp.status_code == 401:
        print('\n❌ 401 Unauthorized - Authentication failed')
except Exception as e:
    print(f'❌ Error: {type(e).__name__}: {e}')
