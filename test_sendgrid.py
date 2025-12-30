#!/usr/bin/env python3
"""Test SendGrid email sending."""

import os
from dotenv import load_dotenv
load_dotenv()

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

api_key = os.getenv('SENDGRID_API_KEY')
sender = os.getenv('TRIPLESEAT_EMAIL_SENDER')
recipients_str = os.getenv('TRIPLESEAT_EMAIL_RECIPIENTS')

print("Testing SendGrid Email Configuration")
print("=" * 70)
print(f"API Key configured: {bool(api_key)}")
print(f"API Key starts with: {api_key[:10] if api_key else 'MISSING'}...")
print(f"Sender: {sender}")
print(f"Recipients: {recipients_str}")

if not api_key or not sender or not recipients_str:
    print("\n[ERROR] Missing email configuration!")
    exit(1)

recipients = [r.strip() for r in recipients_str.split(',')]

try:
    print("\nSending test email...")
    sg = SendGridAPIClient(api_key)
    
    message = Mail(
        from_email=sender,
        to_emails=recipients,
        subject="Test Email from Triple Seat Connector",
        html_content="<h2>This is a test email</h2><p>If you received this, SendGrid is working!</p>"
    )
    
    response = sg.send(message)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.body}")
    
    if response.status_code == 202:
        print("\n[SUCCESS] Email sent successfully!")
    else:
        print(f"\n[ERROR] Unexpected response code: {response.status_code}")
        
except Exception as e:
    print(f"\n[ERROR] Failed to send email: {e}")
    import traceback
    traceback.print_exc()
