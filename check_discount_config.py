#!/usr/bin/env python3
"""Check Discount resource configuration."""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

# Get the Triple Seat Discount resource
resp = requests.get(f'{base_url}/resources/Discount/3358/', headers=headers)
discount = resp.json()

print('\nTriple Seat Discount (ID 3358) Configuration:')
print('=' * 70)
print(json.dumps(discount, indent=2, default=str))
print('=' * 70)
