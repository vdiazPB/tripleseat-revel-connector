#!/usr/bin/env python3
"""Test different JERA API endpoints to understand the structure."""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('JERA_API_KEY')
api_user = os.getenv('JERA_API_USERNAME')
base_url = os.getenv('SUPPLYIT_API_BASE', 'https://app.supplyit.com/api/v2')

if not api_key or not api_user:
    print("Missing credentials")
    sys.exit(1)

headers = {
    'Authorization': api_key,
    'X-Api-User': api_user,
    'Accept': 'application/json'
}

# Test different endpoints
endpoints = [
    '/products',
    '/locations',
    '/locations/27139',
    '/locations/27139/products',
]

for endpoint in endpoints:
    url = f"{base_url}{endpoint}"
    print(f"\nGET {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {resp.status_code}")
        if resp.status_code < 400:
            data = resp.json()
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:5]}")
                if 'products' in data:
                    print(f"  Products count: {len(data['products'])}")
                    if data['products']:
                        print(f"  First product keys: {list(data['products'][0].keys())}")
                        print(f"  First product: {data['products'][0]}")
            elif isinstance(data, list):
                print(f"  List length: {len(data)}")
                if data:
                    if isinstance(data[0], dict):
                        print(f"  First item keys: {list(data[0].keys())}")
                    print(f"  First item: {str(data[0])[:100]}")
        else:
            print(f"  Error: {resp.text[:200]}")
    except Exception as e:
        print(f"  Exception: {e}")
