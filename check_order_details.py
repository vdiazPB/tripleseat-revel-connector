import os, requests, json
from dotenv import load_dotenv
load_dotenv()

h = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
b = f"https://{os.getenv('REVEL_DOMAIN')}"

# Get the working order (10684118)
o = requests.get(f"{b}/resources/Order/10684118/", headers=h).json()

print("Working Order 10684118 - All fields:")
for k, v in sorted(o.items()):
    if isinstance(v, str) and len(v) > 80:
        print(f"  {k}: {v[:80]}...")
    else:
        print(f"  {k}: {v}")
