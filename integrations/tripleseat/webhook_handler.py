import logging
from fastapi import Request, HTTPException
import hmac
import hashlib
import os
from integrations.tripleseat.validation import validate_event
from integrations.tripleseat.time_gate import check_time_gate
from integrations.revel.injection import inject_order
from emailer.sendgrid_emailer import send_success_email, send_failure_email

logger = logging.getLogger(__name__)

async def handle_tripleseat_webhook(request: Request):
    """Handle incoming Triple Seat webhook."""
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get('X-TripleSeat-Signature')

    # Verify signature
    if not verify_signature(body, signature):
        logger.error("Invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse payload
    payload = await request.json()
    logger.info("Payload parsed")

    # Extract event_id
    event = payload.get("event", {})
    event_id = event.get("id")

    if not event_id:
        logger.error("No event_id in payload")
        return

    site_id = event.get("site_id")
    logger.info(f"Location resolved: {site_id}")

    logger.info(f"Processing Triple Seat event {event_id}")

    # Run pipeline
    try:
        # STEP 1: Validation
        validation_result = validate_event(event_id)
        if not validation_result.is_valid:
            logger.info(f"Event {event_id} failed validation: {validation_result.reason}")
            return  # Silent exit

        # STEP 2: Time Gate
        time_gate_result = check_time_gate(event_id)
        if time_gate_result == "PROCEED":
            logger.info("Time gate: OPEN")
        else:
            logger.info(f"Time gate: CLOSED ({time_gate_result})")
            return  # Silent exit

        # STEP 3: Revel Injection
        injection_result = inject_order(event_id)
        if not injection_result.success:
            logger.error(f"Event {event_id} injection failed: {injection_result.error}")
            send_failure_email(event_id, injection_result.error)
            return

        # STEP 4: Success Email
        send_success_email(event_id, injection_result.order_details)

        logger.info(f"Event {event_id} processed successfully")

    except Exception as e:
        logger.error(f"Pipeline failed for event {event_id}: {e}")
        send_failure_email(event_id, str(e))

def verify_signature(body: bytes, signature: str) -> bool:
    """Verify Triple Seat webhook signature."""
    signing_secret = os.getenv('TRIPLESEAT_SIGNING_SECRET')
    if not signing_secret:
        logger.error("TRIPLESEAT_SIGNING_SECRET not set")
        return False

    expected_signature = hmac.new(
        signing_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
