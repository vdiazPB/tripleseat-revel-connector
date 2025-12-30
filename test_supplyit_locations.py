import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('JERA_API_KEY')
username = os.getenv('JERA_API_USERNAME')

print(f'API Key configured: {bool(api_key)}')
if api_key:
    print(f'API Key starts with: {api_key[:20]}...')
print(f'Username: {username}')

# Test list locations
url = 'https://app.supplyit.com/api/v2/locations'
headers = {
    'Authorization': api_key,
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
if username:
    headers['X-Api-User'] = username

print(f'\nTesting endpoint: {url}')
print(f'Request headers: {list(headers.keys())}')

try:
    resp = requests.get(url, headers=headers, timeout=5)
    print(f'Status Code: {resp.status_code}')
    
    if resp.status_code == 200:
        data = resp.json()
        print('\n✅ Success! Got locations')
        
        # Check if response has 'data' key
        if isinstance(data, dict) and 'data' in data:
            locations = data['data']
        else:
            locations = data if isinstance(data, list) else []
        
        print(f'\nTotal locations: {len(locations)}')
        print('\nLocation list:')
        for loc in locations:
            if isinstance(loc, dict):
                loc_code = loc.get('Code', loc.get('code', 'N/A'))
                loc_name = loc.get('Name', loc.get('name', 'N/A'))
                loc_id = loc.get('ID', loc.get('id', 'N/A'))
                print(f'  - {loc_code} | {loc_name} (ID: {loc_id})')
            else:
                print(f'  - {loc}')
    else:
        print(f'❌ Status {resp.status_code}')
        print(f'Response: {resp.text[:500]}')
except Exception as e:
    print(f'❌ Error: {type(e).__name__}: {e}')
