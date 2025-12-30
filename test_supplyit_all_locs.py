import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.getenv('JERA_API_KEY')
username = os.getenv('JERA_API_USERNAME')

url = 'https://app.supplyit.com/api/v2/locations'
headers = {
    'Authorization': api_key,
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
if username:
    headers['X-Api-User'] = username

try:
    resp = requests.get(url, headers=headers, timeout=5)
    print(f'Status Code: {resp.status_code}')
    
    if resp.status_code == 200:
        data = resp.json()
        
        # Check if response has 'data' key
        if isinstance(data, dict) and 'data' in data:
            locations = data['data']
        else:
            locations = data if isinstance(data, list) else []
        
        print(f'\nFull location list ({len(locations)} total):')
        print(json.dumps(locations, indent=2))
except Exception as e:
    print(f'Error: {e}')
