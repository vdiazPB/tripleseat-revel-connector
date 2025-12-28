#!/usr/bin/env python3
"""
TRIPLESEAT OAUTH PERMISSION FIX GUIDE

This script helps diagnose and fix OAuth read permission issues with TripleSeat.

The Problem:
- Your OAuth application has been created with client_id and client_secret
- BUT it was NOT granted read permissions on API endpoints
- TripleSeat OAuth apps are created WITHOUT permissions by default
- You must manually grant permissions in TripleSeat's admin panel

The Solution:
1. Log into TripleSeat as an admin (pinkbox account)
2. Go to Settings → API & Integrations → OAuth Applications
3. Find your application: "Revel Connector" (client_id: k2AjxXq3kP_VHXGN6TeVSnkq-HNn1QXiSr7UiH9tm34)
4. Edit the application and check these permissions:
   - ☑ Read Events
   - ☑ Read Bookings
   - ☑ Read Locations
   - ☑ Read Orders
5. Save the changes
6. The OAuth token will immediately have read permissions

Current Configuration:
"""

import os
import requests
import json

# Load environment
from dotenv import load_dotenv
load_dotenv()

client_id = os.getenv('TRIPLESEAT_OAUTH_CLIENT_ID')
client_secret = os.getenv('TRIPLESEAT_OAUTH_CLIENT_SECRET')

print("=" * 80)
print("TRIPLESEAT OAUTH PERMISSION DIAGNOSIS")
print("=" * 80)

print(f"\n📋 OAuth Application Details:")
print(f"   Client ID:     {client_id}")
print(f"   Client Secret: {client_secret[:20]}..." if client_secret else "   Client Secret: NOT SET")

print(f"\n🔍 Attempting to fetch OAuth token...")
data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret
}
headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

try:
    response = requests.post('https://api.tripleseat.com/oauth2/token', data=data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        print(f"   ✅ Token obtained successfully")
        print(f"   Token: {access_token[:20]}...")
        print(f"   Expires in: {token_data.get('expires_in', 'unknown')} seconds")
        
        # Now test read access
        print(f"\n📖 Testing read permissions...")
        
        test_endpoints = [
            ('locations', 'GET /v1/locations.json'),
            ('events', 'GET /v1/events/<event_id>.json'),
            ('orders', 'GET /v1/orders.json'),
        ]
        
        headers_auth = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Test locations endpoint (simplest, no ID required)
        response = requests.get('https://api.tripleseat.com/v1/locations.json', 
                               headers=headers_auth, 
                               timeout=5)
        
        if response.status_code == 200:
            print(f"   ✅ Read permission GRANTED for locations")
            data = response.json()
            print(f"      Returned {len(data) if isinstance(data, list) else '?'} locations")
        elif response.status_code == 401:
            print(f"   ❌ Read permission DENIED for locations (401 Unauthorized)")
            print(f"      This means your OAuth app is NOT granted read permissions")
            print(f"      📌 FIX: Log into TripleSeat and grant read permissions to your OAuth app")
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
    
    elif response.status_code == 401:
        print(f"   ❌ Token fetch failed: 401 Unauthorized")
        print(f"      Client ID or secret is invalid")
    else:
        error_msg = response.text
        try:
            error_data = response.json()
            error_msg = error_data.get('error', error_msg)
        except:
            pass
        print(f"   ❌ Token fetch failed: HTTP {response.status_code}")
        print(f"      Error: {error_msg}")

except requests.RequestException as e:
    print(f"   ❌ Connection error: {e}")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("""
1. Open TripleSeat in your browser
2. Log in with admin/manager credentials
3. Navigate to: Settings → API & Integrations → OAuth Applications
4. Find the application with Client ID: k2AjxXq3kP_VHXGN6TeVSnkq-HNn1QXiSr7UiH9tm34
5. Click 'Edit' and grant these permissions:
   ☑ Read Events
   ☑ Read Bookings  
   ☑ Read Locations
   ☑ Read Orders
6. Save the changes
7. Run this script again to verify permissions

Once permissions are granted in TripleSeat, your OAuth token will automatically
have read access to the API and the connector will work correctly.

⚠️  Note: This is a ONE-TIME configuration in TripleSeat. Once done, all future
    tokens will have these permissions.
""")
