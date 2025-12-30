import os, requests
from dotenv import load_dotenv
load_dotenv()

h = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
b = f"https://{os.getenv('REVEL_DOMAIN')}"

# Get working order to see reporting_id
o = requests.get(f"{b}/resources/Order/10684118/", headers=h).json()
print(f"Working order 10684118 reporting_id: {o.get('reporting_id')}")

# Try to get the next available reporting number
# Check a few recent orders to see the pattern
orders = requests.get(f"{b}/resources/Order/", headers=h, params={'limit': 1, 'ordering': '-id'}).json()
if orders.get('results'):
    print(f"\nLatest order reporting_id: {orders['results'][0].get('reporting_id')}")
