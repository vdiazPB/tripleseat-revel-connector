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

async def handle_tripleseat_webhook(payload: dict, correlation_id: str, verify_signature_flag: bool = True):
    """Handle incoming Triple Seat webhook."""
    logger.info(f"[req-{correlation_id}] Webhook received")
    logger.info(f"[req-{correlation_id}] Payload parsed")

    # Extract event_id
    event = payload.get("event", {})
    event_id = event.get("id")
    site_id = event.get("site_id")

    # Defensive validation
    if not site_id:
        logger.error(f"[req-{correlation_id}] Missing or invalid site_id")
        raise HTTPException(status_code=400, detail="Missing or invalid site_id")

    logger.info(f"[req-{correlation_id}] Location resolved: {site_id}")

    if not event_id:
        logger.error(f"[req-{correlation_id}] No event_id in payload")
        return {
            "ok": False,
            "dry_run": os.getenv('DRY_RUN', 'false').lower() == 'true',
            "site_id": site_id,
            "time_gate": "UNKNOWN"
        }

    # Run pipeline
    try:
        # STEP 1: Validation
        validation_result = validate_event(event_id, correlation_id)
        if not validation_result.is_valid:
            logger.info(f"[req-{correlation_id}] Event {event_id} failed validation: {validation_result.reason}")
            return {
                "ok": False,
                "dry_run": os.getenv('DRY_RUN', 'false').lower() == 'true',
                "site_id": site_id,
                "time_gate": "UNKNOWN"
            }

        # STEP 2: Time Gate
        time_gate_result = check_time_gate(event_id, correlation_id)
        if time_gate_result == "PROCEED":
            logger.info(f"[req-{correlation_id}] Time gate: OPEN")
            time_gate_status = "OPEN"
        else:
            logger.info(f"[req-{correlation_id}] Time gate: CLOSED ({time_gate_result})")
            time_gate_status = "CLOSED"
            return {
                "ok": True,
                "dry_run": os.getenv('DRY_RUN', 'false').lower() == 'true',
                "site_id": site_id,
                "time_gate": time_gate_status
            }

        # STEP 3: Revel Injection
        injection_result = inject_order(event_id, correlation_id)
        if not injection_result.success:
            logger.error(f"[req-{correlation_id}] Event {event_id} injection failed: {injection_result.error}")
            send_failure_email(event_id, injection_result.error, correlation_id)
            return {
                "ok": False,
                "dry_run": os.getenv('DRY_RUN', 'false').lower() == 'true',
                "site_id": site_id,
                "time_gate": time_gate_status
            }

        # STEP 4: Success Email
        send_success_email(event_id, injection_result.order_details, correlation_id)

        logger.info(f"[req-{correlation_id}] Webhook completed")

        return {
            "ok": True,
            "dry_run": os.getenv('DRY_RUN', 'false').lower() == 'true',
            "site_id": site_id,
            "time_gate": time_gate_status
        }

    except Exception as e:
        logger.error(f"[req-{correlation_id}] Pipeline failed for event {event_id}: {e}")
        send_failure_email(event_id, str(e), correlation_id)
        return {
            "ok": False,
            "dry_run": os.getenv('DRY_RUN', 'false').lower() == 'true',
            "site_id": site_id,
            "time_gate": "UNKNOWN"
        }

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
