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

print("Testing Supply It locations endpoint...\n")
print(f"URL: {url}")
print(f"Auth: {bool(api_key)} / {bool(username)}\n")

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f'Status Code: {resp.status_code}')
    print(f'Response Size: {len(resp.text)} bytes\n')
    
    if resp.status_code == 200:
        data = resp.json()
        
        # Check structure
        if isinstance(data, dict):
            print("Response is a dictionary with keys:", list(data.keys()))
            if 'data' in data:
                locations = data['data']
                print(f"Using 'data' key - found {len(locations)} locations\n")
            else:
                locations = data
                print(f"No 'data' key - using root - found {len(data)} items\n")
        elif isinstance(data, list):
            locations = data
            print(f"Response is a list - found {len(locations)} locations\n")
        else:
            print("Unexpected response type:", type(data))
            locations = []
        
        # Print summary
        print("Location Summary:")
        print("Code | Name | ID | Status")
        print("-" * 70)
        for loc in locations:
            code = loc.get('Code', 'N/A')
            name = loc.get('Name', 'N/A')
            loc_id = loc.get('ID', 'N/A')
            status = loc.get('LocationStatus', 'N/A')
            print(f"{code:>5} | {name:<35} | {loc_id:<5} | {status}")
        
        print(f"\nTotal: {len(locations)} locations")
        
        # Look for anything with "special" in the name
        print("\nSearching for 'special' in location names:")
        found = False
        for loc in locations:
            name = loc.get('Name', '').lower()
            code = loc.get('Code', '').lower()
            if 'special' in name or 'special' in code:
                print(f"  Found: {loc.get('Code')} - {loc.get('Name')} (ID: {loc.get('ID')})")
                found = True
        if not found:
            print("  No locations with 'special' in the name")
            
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
