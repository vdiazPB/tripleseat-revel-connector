#!/usr/bin/env python3
"""Debug WebOrders endpoints"""

import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('REVEL_API_KEY')
api_secret = os.getenv('REVEL_API_SECRET')
domain = os.getenv('REVEL_DOMAIN', 'pinkboxdoughnuts.revelup.com')

base_url = f"https://{domain}"
headers = {
    'API-AUTHENTICATION': f'{api_key}:{api_secret}',
    'Content-Type': 'application/json'
}

# Try different WebOrders endpoints
endpoints = [
    '/weborders/',
    '/weborders/menu/',
    '/resources/weborders/',
    '/specialresources/weborders/',
    '/weborders/4/cart/validate',
    '/specialresources/weborders/cart/validate',
]

for endpoint in endpoints:
    url = f"{base_url}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint}")
    print(f"Full URL: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        if response.status_code == 200:
            print("✅ Found!")
            print(f"Response preview: {response.text[:200]}")
        else:
            print(f"❌ Not found or error")
    except Exception as e:
        print(f"❌ Error: {e}")
