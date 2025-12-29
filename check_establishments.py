#!/usr/bin/env python3
"""Check which establishment/location an order belongs to"""
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

# Check both a working order and a new order
for order_id in [10684118, 10685039]:
    print(f"\n{'='*60}")
    print(f"ORDER {order_id}")
    print('='*60)
    
    url = f'{base_url}/resources/Order/{order_id}/'
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        order = resp.json()
        establishment_uri = order.get('establishment')
        print(f"Establishment URI: {establishment_uri}")
        
        # Extract establishment ID from URI
        if establishment_uri:
            est_id = establishment_uri.split('/')[-2]
            print(f"Establishment ID: {est_id}")
            
            # Try to get establishment details
            est_url = f'{base_url}{establishment_uri}'
            est_resp = requests.get(est_url, headers=headers)
            if est_resp.status_code == 200:
                est_data = est_resp.json()
                print(f"Establishment Name: {est_data.get('name')}")
