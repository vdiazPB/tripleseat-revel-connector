import os, requests
from dotenv import load_dotenv
load_dotenv()

h = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
b = f"https://{os.getenv('REVEL_DOMAIN')}"

# Try various reporting-related endpoints
endpoints = [
    '/resources/ReportingSequence/',
    '/resources/OrderReporting/',
    '/resources/OrderSequence/',
]

for endpoint in endpoints:
    try:
        resp = requests.get(f"{b}{endpoint}", headers=h, params={'limit': 1})
        if resp.status_code == 200:
            data = resp.json()
            print(f"{endpoint}: Found - {len(data.get('results', []))} records")
        else:
            print(f"{endpoint}: {resp.status_code}")
    except:
        pass
