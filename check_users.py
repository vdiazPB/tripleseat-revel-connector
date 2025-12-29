#!/usr/bin/env python3
"""Check user details"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
REVEL_DOMAIN = os.getenv('REVEL_DOMAIN')

base_url = f'https://{REVEL_DOMAIN}'
headers = {
    'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'
}

# Check both users
for user_id in [209, 21955]:
    print(f"\n{'='*60}")
    print(f"USER {user_id}")
    print('='*60)
    
    url = f'{base_url}/enterprise/User/{user_id}/'
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        user = resp.json()
        print(f"Name: {user.get('first_name')} {user.get('last_name')}")
        print(f"Email: {user.get('email')}")
        print(f"Username: {user.get('username')}")
        print(f"Is Active: {user.get('is_active')}")
        print(f"Is Staff: {user.get('is_staff')}")
        print(f"Is Superuser: {user.get('is_superuser')}")
    else:
        print(f"Error: {resp.status_code}")
