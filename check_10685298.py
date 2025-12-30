import os, requests, json
from dotenv import load_dotenv
load_dotenv()

h = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
b = f"https://{os.getenv('REVEL_DOMAIN')}"

# Check test order
o = requests.get(f"{b}/resources/Order/10685298/", headers=h).json()
print(f"Order 10685298:")
print(f"  has_history: {o.get('has_history')}")
print(f"  orderhistory: {o.get('orderhistory')}")
print(f"  closed: {o.get('closed')}")
print(f"  created_date: {o.get('created_date')}")
print(f"  updated_date: {o.get('updated_date')}")
