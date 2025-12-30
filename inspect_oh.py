import os, requests, json
from dotenv import load_dotenv
load_dotenv()

h = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
b = f"https://{os.getenv('REVEL_DOMAIN')}"

# Get working order's OrderHistory
oh_list = requests.get(f"{b}/resources/OrderHistory/", headers=h, params={'order__id': '10684118'}).json()
print(f"Found {len(oh_list.get('results', []))} OrderHistory records")

if oh_list.get('results'):
    oh = oh_list['results'][0]
    print('\nOrderHistory fields:')
    for k, v in sorted(oh.items()):
        print(f'  {k}: {v}')
