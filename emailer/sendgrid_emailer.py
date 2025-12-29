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

        subject = f"Triple Seat Event Injected — Event #{event_id}"

        html_content = f"""
        <h2>Triple Seat Event Successfully Injected</h2>
        <p><strong>Event ID:</strong> {event_id}</p>
        <p><strong>Event Date:</strong> {event.get('event_date', 'Unknown')}</p>
        <p><strong>Revel Location:</strong> {establishment}</p>
        <p><strong>Revel Order ID:</strong> {order_details.revel_order_id}</p>
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