#!/usr/bin/env python3
"""Test products endpoint with location code header."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('JERA_API_KEY')
api_user = os.getenv('JERA_API_USERNAME')
base_url = 'https://app.supplyit.com/api/v2'

headers = {
    'Authorization': api_key,
    'X-Api-User': api_user,
    'X-Supplyit-LocationCode': '8',  # Special Events location code
    'Accept': 'application/json'
}

print("Fetching products for location code '8' (Special Events)...")
resp = requests.get(f'{base_url}/products', headers=headers, timeout=10)
print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    products = resp.json()
    print(f'\nFound {len(products)} products:\n')
    print(f"{'Name':<50} {'ID':<10} {'Code':<15}")
    print("-" * 75)
    for p in products:
        name = (p.get('Name') or 'Unknown')[:47]
        pid = p.get('ID') or 'N/A'
        code = (p.get('Code') or '')[:12]
        print(f"{name:<50} {str(pid):<10} {code:<15}")
else:
    print(f'Error: {resp.text[:300]}')
