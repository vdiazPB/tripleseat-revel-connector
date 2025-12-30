import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.revel.mappings import get_revel_establishment

logger = logging.getLogger(__name__)

def send_success_email(event_id: str, order_details, correlation_id: str = None):
    """Send success notification email."""
    try:
        # Guard against None order_details
        if not order_details:
            logger.warning(f"[req-{correlation_id}] Skipping email: order_details is None for event {event_id}")
            return
            
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        sender = os.getenv('TRIPLESEAT_EMAIL_SENDER')
        recipients_str = os.getenv('TRIPLESEAT_EMAIL_RECIPIENTS')
        
        # Guard against missing email config
        if not sender or not recipients_str:
            logger.warning(f"[req-{correlation_id}] Skipping email: EMAIL_SENDER or EMAIL_RECIPIENTS not configured")
            return
            
        recipients = [r.strip() for r in recipients_str.split(',')]

        # Get event details
        ts_client = TripleSeatAPIClient()
        event_data = ts_client.get_event(event_id)
        event = event_data.get("event", {}) if event_data else {}
        site_id = event.get("site_id")

        establishment = get_revel_establishment(site_id) or "Unknown"

        # Format event date
        event_date = event.get('event_date', 'Unknown')
        if event_date and event_date != 'Unknown':
            from datetime import datetime
            date_str = str(event_date).strip()
            try:
                # First try MM/DD/YYYY format
                if '/' in date_str:
                    event_date = datetime.strptime(date_str, '%m/%d/%Y').strftime('%B %d, %Y')
                else:
                    # YYYY-MM-DD format
                    event_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
            except Exception as e:
                logger.debug(f"Could not parse event_date '{date_str}': {e}")
                event_date = 'Unknown'

        # Build items table
        items_html = ""
        if hasattr(order_details, 'items') and order_details.items:
            items_html = "<h3>Items Injected:</h3><table style='width:100%; border-collapse: collapse;'>"
            items_html += "<tr style='background-color: #f0f0f0;'><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Item</th><th style='border: 1px solid #ddd; padding: 8px; text-align: right;'>Qty</th><th style='border: 1px solid #ddd; padding: 8px; text-align: right;'>Price</th></tr>"
            for item in order_details.items:
                item_name = item.get('name', 'Unknown Item') if isinstance(item, dict) else str(item)
                item_qty = item.get('quantity', 1) if isinstance(item, dict) else 1
                item_price = item.get('price', 0) if isinstance(item, dict) else 0
                items_html += f"<tr><td style='border: 1px solid #ddd; padding: 8px;'>{item_name}</td><td style='border: 1px solid #ddd; padding: 8px; text-align: right;'>{item_qty}</td><td style='border: 1px solid #ddd; padding: 8px; text-align: right;'>${item_price:.2f}</td></tr>"
            items_html += "</table>"
        else:
            items_html = "<p><em>No items details available</em></p>"

        subject = f"Triple Seat Event Injected — Event #{event_id}"

        html_content = f"""
        <h2>Triple Seat Event Successfully Injected</h2>
        <p><strong>Event ID:</strong> {event_id}</p>
        <p><strong>Event Date:</strong> {event_date}</p>
        <p><strong>Revel Location:</strong> {establishment}</p>
        <p><strong>Revel Order ID:</strong> {order_details.revel_order_id}</p>
        
        {items_html}
        
        <h3>Order Summary:</h3>
        <p><strong>Subtotal:</strong> ${order_details.subtotal:.2f}</p>
        <p><strong>Discount:</strong> ${order_details.discount:.2f}</p>
        <p><strong>Final Total:</strong> ${order_details.final_total:.2f}</p>
        <p><strong>Payment Type:</strong> {order_details.payment_type or 'N/A'}</p>
        """

        message = Mail(
            from_email=sender,
            to_emails=recipients,
            subject=subject,
            html_content=html_content
        )

        sg.send(message)
        logger.info(f"[req-{correlation_id}] Success email sent for event {event_id}")

    except Exception as e:
        logger.error(f"[req-{correlation_id}] Failed to send success email: {e}")

def send_failure_email(event_id: str, error_reason: str, correlation_id: str = None):
    """Send failure notification email."""
    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        sender = os.getenv('TRIPLESEAT_EMAIL_SENDER')
        recipients_str = os.getenv('TRIPLESEAT_EMAIL_RECIPIENTS')
        
        # Guard against missing email config
        if not sender or not recipients_str:
            logger.warning(f"[req-{correlation_id}] Skipping email: EMAIL_SENDER or EMAIL_RECIPIENTS not configured")
            return
            
        recipients = [r.strip() for r in recipients_str.split(',')]

        subject = f"FAILED: Triple Seat Event Injection — Event #{event_id}"

        html_content = f"""
        <h2>Triple Seat Event Injection Failed</h2>
        <p><strong>Event ID:</strong> {event_id}</p>
        <p><strong>Failure Reason:</strong> {error_reason}</p>
        <p><strong>Timestamp:</strong> {os.getenv('CURRENT_TIME', 'Unknown')}</p>
        """

        message = Mail(
            from_email=sender,
            to_emails=recipients,
            subject=subject,
            html_content=html_content
        )

        sg.send(message)
        logger.info(f"[req-{correlation_id}] Failure email sent for event {event_id}")

    except Exception as e:
        logger.error(f"[req-{correlation_id}] Failed to send failure email: {e}")