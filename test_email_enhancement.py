#!/usr/bin/env python3
"""
Test script to verify email enhancements (event date, location, items).
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Mock order details class
class MockOrderDetails:
    def __init__(self):
        self.revel_order_id = "10690923"
        self.subtotal = 157.52
        self.discount = 0.00
        self.final_total = 157.52
        self.payment_type = "Triple Seat"
        self.items = [
            {
                'name': 'Glazed Dozen',
                'quantity': 1,
                'price': 157.52
            },
            {
                'name': 'Coffee - Medium',
                'quantity': 2,
                'price': 5.50
            }
        ]


def test_email():
    """Test sending an email with new enhancements."""
    
    # Check environment variables
    api_key = os.getenv('SENDGRID_API_KEY')
    sender = os.getenv('TRIPLESEAT_EMAIL_SENDER')
    recipients_str = os.getenv('TRIPLESEAT_EMAIL_RECIPIENTS')
    
    print("=" * 60)
    print("EMAIL TEST SETUP")
    print("=" * 60)
    print(f"[OK] SendGrid API Key: {'SET' if api_key else 'NOT SET'}")
    print(f"[OK] Email Sender: {sender or 'NOT SET'}")
    print(f"[OK] Email Recipients: {recipients_str or 'NOT SET'}")
    print()
    
    if not api_key or not sender or not recipients_str:
        print("[ERROR] Missing email configuration!")
        print("Please ensure SENDGRID_API_KEY, TRIPLESEAT_EMAIL_SENDER, and TRIPLESEAT_EMAIL_RECIPIENTS are set in .env")
        return False
    
    try:
        print("=" * 60)
        print("SENDING TEST EMAIL")
        print("=" * 60)
        
        from emailer.sendgrid_emailer import send_success_email
        
        # Create mock order details
        order_details = MockOrderDetails()
        event_id = "55558872"  # Using the event from your logs
        
        print(f"Event ID: {event_id}")
        print(f"Order Details:")
        print(f"  - Revel Order ID: {order_details.revel_order_id}")
        print(f"  - Subtotal: ${order_details.subtotal:.2f}")
        print(f"  - Discount: ${order_details.discount:.2f}")
        print(f"  - Final Total: ${order_details.final_total:.2f}")
        print(f"  - Items: {len(order_details.items)} item(s)")
        for item in order_details.items:
            print(f"    • {item['name']} - Qty: {item['quantity']}, Price: ${item['price']:.2f}")
        print()
        
        # Send the email
        print("Sending email...")
        send_success_email(event_id, order_details, correlation_id="TEST-EMAIL")
        
        print("[OK] Email sent successfully!")
        print()
        print("=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
        print(f"Check your email inbox ({recipients_str})")
        print("The email should include:")
        print("  [OK] Event Date (formatted as 'January 15, 2025')")
        print("  [OK] Revel Location (from establishment mapping)")
        print("  [OK] Items table with Name, Qty, Price columns")
        print("  [OK] Order Summary section")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send email")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_email()
    sys.exit(0 if success else 1)
