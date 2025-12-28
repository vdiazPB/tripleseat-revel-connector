#!/usr/bin/env python
"""Test APIClient token fetch"""

import os
from dotenv import load_dotenv

load_dotenv()

ck = os.getenv('CONSUMER_KEY')
cs = os.getenv('CONSUMER_SECRET')

print(f'CONSUMER_KEY loaded: {bool(ck)}')
print(f'CONSUMER_SECRET loaded: {bool(cs)}')

from integrations.tripleseat.api_client import TripleSeatAPIClient

client = TripleSeatAPIClient()
print(f'Client ID: {client.client_id}')
print(f'Client Secret: {client.client_secret}')

try:
    token = client._get_access_token()
    print(f'SUCCESS: {token[:20]}...')
except Exception as e:
    print(f'FAILED: {e}')
    import traceback
    traceback.print_exc()
