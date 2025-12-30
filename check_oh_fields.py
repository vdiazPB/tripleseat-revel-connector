import os, requests, json
from dotenv import load_dotenv
load_dotenv()

h = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
b = f"https://{os.getenv('REVEL_DOMAIN')}"

# Get the OrderHistory record
oh = requests.get(f"{b}/resources/OrderHistory/6765269/", headers=h).json()

print("OrderHistory 6765269 - All fields:")
for k, v in sorted(oh.items()):
    if isinstance(v, str) and len(v) > 80:
        print(f"  {k}: {v[:80]}...")
    else:
        print(f"  {k}: {v}")
