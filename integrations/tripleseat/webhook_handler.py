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

# In-memory idempotency cache (site_id + event_id + triggered_at)
# Production systems should use Redis or similar for distributed idempotency
idempotency_cache = {}

async def handle_tripleseat_webhook(
    payload: dict, 
    correlation_id: str, 
    verify_signature_flag: bool = True,
    dry_run: bool = True,
    allowed_locations: list = None,
    test_location_override: bool = False,
    test_establishment_id: str = "4"
):
    """Handle incoming Triple Seat webhook."""
    logger.info(f"[req-{correlation_id}] Webhook received")
    logger.info(f"[req-{correlation_id}] Payload parsed")

    # Extract event_id
    event = payload.get("event", {})
    event_id = event.get("id")
    site_id = event.get("site_id")
    triggered_at = event.get("triggered_at", "")  # For idempotency

    # Defensive validation
    if not site_id:
        logger.error(f"[req-{correlation_id}] Missing or invalid site_id")
        raise HTTPException(status_code=400, detail="Missing or invalid site_id")

    logger.info(f"[req-{correlation_id}] Location resolved: {site_id}")

    # Idempotency check
    if event_id and triggered_at:
        idempotency_key = f"{site_id}:{event_id}:{triggered_at}"
        if idempotency_key in idempotency_cache:
            logger.info(f"[req-{correlation_id}] Duplicate event detected (idempotency): {idempotency_key}")
            return {
                "ok": True,
                "acknowledged": True,
                "reason": "DUPLICATE_EVENT",
                "site_id": site_id,
                "dry_run": dry_run
            }

    # ALLOWED_LOCATIONS safety lock
    if allowed_locations and allowed_locations[0]:  # If configured
        allowed_locations_clean = [loc.strip() for loc in allowed_locations]
        if str(site_id) not in allowed_locations_clean:
            logger.warning(f"[req-{correlation_id}] Site {site_id} NOT in ALLOWED_LOCATIONS: {allowed_locations_clean}")
            return {
                "ok": True,
                "acknowledged": True,
                "reason": "LOCATION_NOT_ALLOWED",
                "site_id": site_id,
                "dry_run": dry_run
            }

    if not event_id:
        logger.error(f"[req-{correlation_id}] No event_id in payload")
        return {
            "ok": False,
            "dry_run": dry_run,
            "site_id": site_id,
            "time_gate": "UNKNOWN"
        }

    # Run pipeline
    try:
        # STEP 1: Validation (SKIP in test mode - use webhook payload directly)
        if test_location_override:
            logger.info(f"[req-{correlation_id}] [TEST MODE] Skipping API validation - using webhook payload")
            validation_passed = True
        else:
            validation_result = validate_event(event_id, correlation_id)
            validation_passed = validation_result.is_valid
            if not validation_passed:
                logger.info(f"[req-{correlation_id}] Event {event_id} failed validation: {validation_result.reason}")
                return {
                    "ok": False,
                    "dry_run": dry_run,
                    "site_id": site_id,
                    "time_gate": "UNKNOWN"
                }

        # STEP 2: Time Gate (SKIP in test mode)
        if test_location_override:
            logger.info(f"[req-{correlation_id}] [TEST MODE] Skipping time gate check")
            time_gate_status = "BYPASSED"
        else:
            time_gate_result = check_time_gate(event_id, correlation_id)
            if time_gate_result == "PROCEED":
                logger.info(f"[req-{correlation_id}] Time gate: OPEN")
                time_gate_status = "OPEN"
            else:
                logger.info(f"[req-{correlation_id}] Time gate: CLOSED ({time_gate_result})")
                time_gate_status = "CLOSED"
                return {
                    "ok": True,
                    "dry_run": dry_run,
                    "site_id": site_id,
                    "time_gate": time_gate_status
                }

        # STEP 3: Revel Injection
        injection_result = inject_order(
            event_id, 
            correlation_id, 
            dry_run=dry_run,
            test_location_override=test_location_override,
            test_establishment_id=test_establishment_id,
            webhook_payload=payload  # Pass webhook payload for test mode
        )
        if not injection_result.success:
            logger.error(f"[req-{correlation_id}] Event {event_id} injection failed: {injection_result.error}")
            send_failure_email(event_id, injection_result.error, correlation_id)
            return {
                "ok": False,
                "dry_run": dry_run,
                "site_id": site_id,
                "time_gate": time_gate_status
            }

        # STEP 4: Success Email
        send_success_email(event_id, injection_result.order_details, correlation_id)

        # Register idempotency on success
        if event_id and triggered_at:
            idempotency_key = f"{site_id}:{event_id}:{triggered_at}"
            idempotency_cache[idempotency_key] = True
            logger.info(f"[req-{correlation_id}] Idempotency registered: {idempotency_key}")

        logger.info(f"[req-{correlation_id}] Webhook completed")

        return {
            "ok": True,
            "dry_run": dry_run,
            "site_id": site_id,
            "time_gate": time_gate_status
        }

    except Exception as e:
        logger.error(f"[req-{correlation_id}] Pipeline failed for event {event_id}: {e}")
        send_failure_email(event_id, str(e), correlation_id)
        return {
            "ok": False,
            "dry_run": dry_run,
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
