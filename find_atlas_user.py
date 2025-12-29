#!/usr/bin/env python3
"""Search for all users and find atlas"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
REVEL_DOMAIN = os.getenv('REVEL_DOMAIN')

base_url = f'https://{REVEL_DOMAIN}'
headers = {
    'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'
}

# Get all users
print("Fetching all users...")
url = f'{base_url}/enterprise/User/'
params = {'limit': 500}

resp = requests.get(url, headers=headers, params=params)
print(f"Status: {resp.status_code}\n")

if resp.status_code == 200:
    data = resp.json()
    users = data.get('objects', [])
    
    print(f"Total users: {len(users)}\n")
    
    # Search for atlas
    print("="*70)
    print("USERS WITH 'atlas' IN USERNAME OR NAME:")
    print("="*70)
    
    found = False
    for user in users:
        username = user.get('username', '').lower()
        first_name = user.get('first_name', '').lower()
        last_name = user.get('last_name', '').lower()
        
        if 'atlas' in username or 'atlas' in first_name or 'atlas' in last_name:
            found = True
            print(f"\nID: {user.get('id')}")
            print(f"  Username: {user.get('username')}")
            print(f"  Name: {user.get('first_name')} {user.get('last_name')}")
            print(f"  Email: {user.get('email')}")
            print(f"  Is Active: {user.get('is_active')}")
    
    if not found:
        print("\nNo users found with 'atlas'")
        print("\n" + "="*70)
        print("ALL ACTIVE USERS:")
        print("="*70)
        for user in users:
            if user.get('is_active'):
                print(f"\nID: {user.get('id')} - {user.get('username')} ({user.get('first_name')} {user.get('last_name')})")
else:
    print(f"Error: {resp.status_code}")
