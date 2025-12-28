import requests
import json
import hmac
import hashlib
from datetime import datetime

# Webhook payload from previous test
webhook_payload = {
    "webhook_trigger_type": "STATUS_CHANGE_EVENT",
    "event": {
        "id": 55521609,
        "name": "Jon Ponder",
        "event_date": "12/28/2025",
        "event_date_iso8601": "2025-12-28",
        "status": "DEFINITE",
        "site_id": 15691,
        "event_start": "12/28/2025 6:00 PM",
        "event_end": "12/28/2025 6:15 PM",
        "updated_at": "12/28/2025 12:56 PM",
        "items": [
            {
                "id": 1,
                "name": "Dozen Assorted Doughnuts",
                "quantity": 2,
                "price": 19.99,
                "item_type": "catering_item"
            },
            {
                "id": 2,
                "name": "Coffee Service",
                "quantity": 1,
                "price": 29.99,
                "item_type": "catering_item"
            }
        ]
    }
}

# Generate signature
signing_key = "f58b124f06897ba9f4cbb3a4d74ab7ed46700ad5064d3abdf6c1993ca5a7746e"
timestamp = str(int(datetime.now().timestamp()))
body_str = json.dumps(webhook_payload)
signed_payload = f"{timestamp}.{body_str}"
signature = hmac.new(
    signing_key.encode('utf-8'),
    signed_payload.encode('utf-8'),
    hashlib.sha256
).hexdigest()

x_signature = f"t={timestamp},v1={signature}"

# Send webhook
url = "http://127.0.0.1:8000/webhooks/tripleseat"
headers = {
    "Content-Type": "application/json",
    "X-Signature": x_signature
}

print("Sending webhook to localhost:8000...")
print(f"Payload: {json.dumps(webhook_payload, indent=2)}")
print(f"X-Signature: {x_signature}")

response = requests.post(url, json=webhook_payload, headers=headers)
print(f"\nResponse Status: {response.status_code}")
print(f"Response Body: {response.json()}")
