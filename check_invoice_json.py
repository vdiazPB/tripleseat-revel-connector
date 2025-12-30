#!/usr/bin/env python3
import json

with open('webhook_event_55521609.json') as f:
    data = json.load(f)

docs = data.get('event', {}).get('documents', [])
print(f"Total documents: {len(docs)}\n")

for doc in docs:
    doc_type = doc.get('type')
    if doc_type == 'billing_invoice':
        print("BILLING INVOICE KEYS:")
        for key in sorted(doc.keys()):
            val = doc[key]
            if isinstance(val, (str, int, float, bool)):
                print(f"  {key}: {val}")
            elif isinstance(val, dict):
                print(f"  {key}: <dict with {len(val)} keys>")
            elif isinstance(val, list):
                print(f"  {key}: <list with {len(val)} items>")
        
        print("\nINVOICE FINANCIAL DATA:")
        print(f"  total: {doc.get('total')}")
        print(f"  subtotal: {doc.get('subtotal')}")
        print(f"  amount_due: {doc.get('amount_due')}")
        print(f"  estimated_amount_due: {doc.get('estimated_amount_due')}")
        print(f"  grand_total: {doc.get('grand_total')}")
        
        print("\nFull invoice data:")
        print(json.dumps(doc, indent=2))
