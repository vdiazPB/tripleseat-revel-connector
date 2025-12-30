#!/usr/bin/env python3
"""Debug script to check the billing invoice structure from Triple Seat API"""
import os
import json
from dotenv import load_dotenv
from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.tripleseat.oauth1 import OAuth1Session

load_dotenv()

# Initialize API client
client = TripleSeatAPIClient()

# Use the test event ID
event_id = 55597622

print(f"\n{'='*80}")
print(f"FETCHING EVENT {event_id} FROM TRIPLE SEAT API")
print(f"{'='*80}\n")

try:
    # Fetch full event details
    event_data = client.get_event(event_id)
    
    if event_data and 'event' in event_data:
        event = event_data['event']
        
        # Look for documents
        documents = event.get('documents', [])
        print(f"Total documents: {len(documents)}\n")
        
        for idx, doc in enumerate(documents):
            print(f"Document {idx + 1}:")
            print(f"  Type: {doc.get('type')}")
            print(f"  Name: {doc.get('name')}")
            print(f"\n  Full document structure:")
            print(json.dumps(doc, indent=4))
            print(f"\n  {'='*76}\n")
        
        # Look specifically for billing_invoice
        billing_invoice = next((doc for doc in documents if doc.get("type") == "billing_invoice"), None)
        
        if billing_invoice:
            print(f"\n{'='*80}")
            print(f"BILLING INVOICE DETAILS:")
            print(f"{'='*80}\n")
            print(json.dumps(billing_invoice, indent=2))
            
            # Check key fields
            print(f"\nKey fields in billing_invoice:")
            print(f"  - total: {billing_invoice.get('total')}")
            print(f"  - subtotal: {billing_invoice.get('subtotal')}")
            print(f"  - amount_due: {billing_invoice.get('amount_due')}")
            print(f"  - estimated_amount_due: {billing_invoice.get('estimated_amount_due')}")
            print(f"  - paid: {billing_invoice.get('paid')}")
            print(f"  - balance: {billing_invoice.get('balance')}")
            print(f"  - balance_due: {billing_invoice.get('balance_due')}")
            print(f"  - remaining_balance: {billing_invoice.get('remaining_balance')}")
            print(f"  - status: {billing_invoice.get('status')}")
            
            # Show all keys
            print(f"\nAll keys in billing_invoice:")
            for key in sorted(billing_invoice.keys()):
                value = billing_invoice[key]
                if not isinstance(value, (dict, list)):
                    print(f"  - {key}: {value}")
        else:
            print("No billing_invoice document found!")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
