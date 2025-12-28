# TripleSeat OAuth Troubleshooting Guide

## Current Status
✅ **OAuth Token Fetch**: Working  
✅ **Token Scopes**: Includes `events:read`, `bookings:read`, `locations:read`  
❌ **API Access**: Returns 401 "Token resource owner not found"

## The Problem
The OAuth token is valid and has the correct scopes, but TripleSeat API rejects it with:
```
{"error": "Token resource owner not found"}
```

This means: **The OAuth application is not linked to a user account with API permissions.**

## Solutions

### Solution 1: Link OAuth App to User Account (RECOMMENDED)

1. Go to **TripleSeat Admin Panel**
2. Go to **Settings** → **API & Integrations** → **OAuth Applications**
3. Find your app: `k2AjxXq3kP_VHXGN6TeVSnkq-HNn1QXiSr7UiH9tm34`
4. Look for "Resource Owner" or "Account" field
5. **Select your user account** (the one with API permissions)
6. Save changes
7. Test API again

### Solution 2: Grant Delegated Permissions

1. In the same OAuth app settings
2. Look for "Delegated Permissions" or "Scopes"
3. Check these boxes:
   - ✓ Read Events
   - ✓ Read Bookings  
   - ✓ Read Locations
   - ✓ Read Orders
   - ✓ Read Accounts
4. Save and test

### Solution 3: Create Service Account

If the above doesn't work:
1. Create a new **Service Account** or **API User** in TripleSeat
2. Link the OAuth app to that account
3. Grant that account API permissions
4. Try again

## Verification

After making changes, run this test:

```bash
python -c "
import os
with open('.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key] = value

from integrations.tripleseat.oauth import clear_token_cache, get_access_token
from integrations.tripleseat.api_client import TripleSeatAPIClient

# Clear cache and get fresh token
clear_token_cache()
token = get_access_token()

# Test API
api_client = TripleSeatAPIClient()
response = api_client.session.get(
    api_client.base_url + '/v1/locations.json',
    headers={'Authorization': 'Bearer ' + token}
)

print(f'Status: {response.status_code}')
if response.status_code == 200:
    print('✅ OAuth is working!')
    print(f'Locations: {len(response.json().get(\"locations\", []))}')
else:
    print('❌ Still failing')
    print(f'Error: {response.json()}')
"
```

## If Still Not Working

Contact TripleSeat Support:
- **Issue**: OAuth Client `k2AjxXq3kP_VHXGN6TeVSnkq-HNn1QXiSr7UiH9tm34` returns 401 "Token resource owner not found"
- **Context**: Token has correct scopes but API rejects it
- **Question**: How do I link an OAuth app to a user account for API access?

## Reference
- OAuth Token Status: ✅ Working
- Token Scopes: ✅ Correct (events:read, bookings:read, locations:read, etc.)
- API Connection: ✅ Working
- OAuth App Linking: ❌ Needs configuration
