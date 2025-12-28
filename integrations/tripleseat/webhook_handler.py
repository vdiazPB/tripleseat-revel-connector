import logging
from fastapi import Request, HTTPException
import hmac
import hashlib
import os
from typing import Dict, Any, Optional, Tuple
from integrations.tripleseat.validation import validate_event
from integrations.tripleseat.time_gate import check_time_gate
from integrations.revel.injection import inject_order
from emailer.sendgrid_emailer import send_success_email, send_failure_email

logger = logging.getLogger(__name__)

"""
WEBHOOK PROCESSING STRATEGY

1. PAYLOAD-FIRST: Webhook delivery includes full event/booking data
   - Event: payload["event"] with status, date, site_id, items, etc.
   - Booking: payload["booking"] with guest info, pricing, etc.
   
2. API ONLY IF MISSING: If critical fields are absent from webhook:
   - Validation uses Public API Key (READ-ONLY) to fetch complete event
   - OAuth is NOT used for reads
   
3. AUTHENTICATION:
   - Webhook signature verified via HMAC SHA256 (X-Signature header)
   - Webhook data trusted if signature valid
   - API reads use Public API Key for supplemental data only
   
BENEFIT: Minimal API calls, maximum webhook data utilization
"""

# In-memory idempotency cache (trigger_type + event_id + updated_at)
# Production systems should use Redis or similar for distributed idempotency
idempotency_cache = {}

# Allowlist of actionable webhook trigger types
ACTIONABLE_TRIGGERS = {
    'CREATE_EVENT',
    'UPDATE_EVENT',
    'STATUS_CHANGE_EVENT',
    'CREATE_BOOKING',
    'STATUS_CHANGE_BOOKING',
    'EVENT_CREATED',  # Alternative naming
    'EVENT_UPDATED',
    'BOOKING_CREATED',
    'BOOKING_UPDATED',
}

def verify_webhook_signature(body: bytes, x_signature_header: str) -> Tuple[bool, Optional[str]]:
    """Verify TripleSeat webhook signature using HMAC SHA256.
    
    Args:
        body: Raw request body bytes
        x_signature_header: Value of X-Signature header (format: t=<timestamp>,v1=<signature>)
    
    Returns:
        (is_valid, error_reason)
        - is_valid: True if signature matches
        - error_reason: None if valid, error message if invalid
    """
    # Try both possible env var names
    signing_key = os.getenv('TRIPLESEAT_WEBHOOK_SIGNING_KEY') or os.getenv('TRIPLESEAT_WEBHOOK_SECRET')
    
    if not signing_key:
        logger.error("TRIPLESEAT_WEBHOOK_SIGNING_KEY (or TRIPLESEAT_WEBHOOK_SECRET) not configured")
        return False, "SIGNING_KEY_NOT_CONFIGURED"
    
    if not x_signature_header:
        logger.warning("X-Signature header missing from webhook")
        return False, "MISSING_SIGNATURE_HEADER"
    
    # Parse X-Signature header: t=<timestamp>,v1=<signature>
    try:
        parts = {}
        for part in x_signature_header.split(','):
            if '=' in part:
                key, value = part.split('=', 1)
                parts[key.strip()] = value.strip()
        
        timestamp = parts.get('t')
        signature = parts.get('v1')
        
        if not timestamp or not signature:
            logger.warning("X-Signature header missing t or v1 component")
            return False, "MALFORMED_SIGNATURE_HEADER"
    except Exception as e:
        logger.warning(f"Failed to parse X-Signature header: {e}")
        return False, "SIGNATURE_PARSE_ERROR"
    
    # Reconstruct signed payload: timestamp.body
    signed_payload = f"{timestamp}.{body.decode('utf-8')}"
    
    # Compute expected signature using HMAC SHA256
    expected_signature = hmac.new(
        signing_key.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(signature, expected_signature)
    
    if not is_valid:
        logger.warning(f"Invalid webhook signature (possible tamper or key mismatch)")
    
    return is_valid, None


def extract_trigger_and_ids(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Extract webhook trigger type and event/booking IDs from payload.
    
    Returns:
        (trigger_type, event_id, booking_id, updated_at)
    """
    trigger_type = payload.get('webhook_trigger_type') or payload.get('type')
    
    # Try to extract event data
    event = payload.get('event', {})
    event_id = event.get('id')
    
    # Try to extract booking data (for booking webhooks)
    booking = payload.get('booking', {})
    booking_id = booking.get('id')
    
    # Get updated_at for idempotency (prefer event timestamp, fall back to booking)
    updated_at = event.get('updated_at') or booking.get('updated_at') or payload.get('updated_at')
    
    return trigger_type, event_id, booking_id, updated_at


async def handle_tripleseat_webhook(
    payload: dict, 
    correlation_id: str,
    x_signature_header: Optional[str] = None,
    raw_body: Optional[bytes] = None,
    verify_signature_flag: bool = True,
    dry_run: bool = True,
    enable_connector: bool = True,
    allowed_locations: list = None,
    test_location_override: bool = False,
    test_establishment_id: str = "4",
    skip_time_gate: bool = False,
    skip_validation: bool = False
):
    """Handle incoming TripleSeat webhook.
    
    Implements:
    - Signature verification (if X-Signature provided)
    - Payload-first processing (use webhook data directly when possible)
    - Trigger-type routing (filter by actionable triggers)
    - Idempotency detection
    - Permission-safe error handling
    - HTTP 200 response guarantee
    """
    logger.info(f"[req-{correlation_id}] Webhook received")
    logger.info(f"[req-{correlation_id}] Payload parsed")

    # ===== STEP 0: SIGNATURE VERIFICATION =====
    trigger_type, event_id, booking_id, updated_at = extract_trigger_and_ids(payload)
    logger.info(f"[req-{correlation_id}] Trigger type: {trigger_type}, Event: {event_id}, Booking: {booking_id}")
    
    if verify_signature_flag and x_signature_header and raw_body:
        is_valid, error_reason = verify_webhook_signature(raw_body, x_signature_header)
        if not is_valid:
            logger.warning(f"[req-{correlation_id}] Webhook signature verification failed: {error_reason}")
            return {
                "ok": False,
                "processed": False,
                "reason": f"SIGNATURE_VERIFICATION_FAILED_{error_reason}",
                "trigger": trigger_type
            }
        logger.info(f"[req-{correlation_id}] Webhook signature verified successfully")
    
    # ===== STEP 1: TRIGGER-TYPE ROUTING =====
    if trigger_type:
        if trigger_type not in ACTIONABLE_TRIGGERS:
            logger.info(f"[req-{correlation_id}] Non-actionable trigger type: {trigger_type}")
            return {
                "ok": True,
                "processed": False,
                "reason": f"TRIGGER_TYPE_NOT_ACTIONABLE",
                "trigger": trigger_type
            }
    else:
        logger.warning(f"[req-{correlation_id}] Missing webhook_trigger_type")
        return {
            "ok": True,
            "processed": False,
            "reason": "MISSING_TRIGGER_TYPE",
            "trigger": trigger_type
        }
    
    # ===== STEP 2: IDEMPOTENCY CHECK =====
    # Use trigger_type + event_id + updated_at as idempotency key
    primary_id = event_id or booking_id
    if primary_id and updated_at:
        idempotency_key = f"{trigger_type}:{primary_id}:{updated_at}"
        if idempotency_key in idempotency_cache:
            logger.info(f"[req-{correlation_id}] Duplicate webhook detected (idempotency): {idempotency_key}")
            return {
                "ok": True,
                "processed": False,
                "reason": "DUPLICATE_DELIVERY",
                "trigger": trigger_type
            }
    else:
        idempotency_key = None

    # ===== STEP 3: EXTRACT EVENT FROM PAYLOAD (PAYLOAD-FIRST) =====
    event = payload.get("event", {})
    site_id = event.get("site_id")
    
    # If we have no event in payload but have event_id, we might need to fetch
    if not event and event_id:
        logger.info(f"[req-{correlation_id}] Event data not in webhook payload, will fetch from API if needed")

    # Defensive validation: need either event data or event_id to proceed
    if not event and not event_id:
        logger.error(f"[req-{correlation_id}] No event data or event_id in webhook payload")
        return {
            "ok": True,
            "processed": False,
            "reason": "NO_EVENT_DATA",
            "trigger": trigger_type
        }

    # If event_id is missing but event exists, extract it
    if event and not event_id:
        event_id = event.get("id")
    
    # If site_id is missing from event but in payload root, extract it
    if not site_id:
        site_id = payload.get("site_id")
    
    if not site_id:
        logger.error(f"[req-{correlation_id}] Missing site_id in event or root payload")
        return {
            "ok": True,
            "processed": False,
            "reason": "MISSING_SITE_ID",
            "trigger": trigger_type
        }

    logger.info(f"[req-{correlation_id}] Location resolved: {site_id}")

    # ===== STEP 4: ALLOWED_LOCATIONS CHECK =====
    if allowed_locations and allowed_locations[0]:  # If configured
        allowed_locations_clean = [loc.strip() for loc in allowed_locations]
        if str(site_id) not in allowed_locations_clean:
            logger.warning(f"[req-{correlation_id}] Site {site_id} NOT in ALLOWED_LOCATIONS: {allowed_locations_clean}")
            return {
                "ok": True,
                "processed": False,
                "reason": "LOCATION_NOT_ALLOWED",
                "trigger": trigger_type
            }

    if not event_id:
        logger.error(f"[req-{correlation_id}] No event_id in webhook payload")
        return {
            "ok": True,
            "processed": False,
            "reason": "NO_EVENT_ID",
            "trigger": trigger_type
        }

    # ===== STEP 5: PROCESSING PIPELINE =====
    try:
        # STEP 5a: Validation
        if skip_validation:
            logger.info(f"[req-{correlation_id}] Validation SKIPPED (test/injection mode)")
            validation_passed = True
        else:
            validation_result = validate_event(event_id, correlation_id)
            validation_passed = validation_result.is_valid
            
            # Handle authorization denial gracefully
            if not validation_passed and validation_result.reason == "AUTHORIZATION_DENIED":
                logger.info(f"[req-{correlation_id}] Event {event_id} authorization denied by TripleSeat")
                
                # Register idempotency on safe acknowledgment
                if idempotency_key:
                    idempotency_cache[idempotency_key] = True
                    logger.info(f"[req-{correlation_id}] Idempotency registered: {idempotency_key}")
                
                return {
                    "ok": True,
                    "processed": False,
                    "authorization_status": "DENIED",
                    "reason": "TRIPLESEAT_AUTHORIZATION_DENIED",
                    "trigger": trigger_type
                }
        if not validation_passed:
            logger.info(f"[req-{correlation_id}] Event {event_id} failed validation: {validation_result.reason}")
            return {
                "ok": False,
                "processed": False,
                "reason": f"VALIDATION_FAILED_{validation_result.reason}",
                "trigger": trigger_type
            }

        # STEP 5b: Time Gate
        if skip_time_gate:
            logger.info(f"[req-{correlation_id}] Time gate: SKIPPED (test mode)")
            time_gate_status = "OPEN"
        else:
            time_gate_result = check_time_gate(event_id, correlation_id)
            if time_gate_result == "PROCEED":
                logger.info(f"[req-{correlation_id}] Time gate: OPEN")
                time_gate_status = "OPEN"
            else:
                logger.info(f"[req-{correlation_id}] Time gate: CLOSED ({time_gate_result})")
                time_gate_status = "CLOSED"
                
                # Register idempotency on safe acknowledgment
                if idempotency_key:
                    idempotency_cache[idempotency_key] = True
                    logger.info(f"[req-{correlation_id}] Idempotency registered: {idempotency_key}")
                
                return {
                    "ok": True,
                    "processed": False,
                    "reason": f"TIME_GATE_CLOSED_{time_gate_status}",
                    "trigger": trigger_type
                }

        # STEP 5c: Revel Injection
        injection_result = inject_order(
            event_id, 
            correlation_id, 
            dry_run=dry_run,
            enable_connector=enable_connector,
            test_location_override=test_location_override,
            test_establishment_id=test_establishment_id,
            webhook_payload=payload  # Pass webhook payload to avoid API fetch
        )
        if not injection_result.success:
            logger.error(f"[req-{correlation_id}] Event {event_id} injection failed: {injection_result.error}")
            send_failure_email(event_id, injection_result.error, correlation_id)
            return {
                "ok": False,
                "processed": False,
                "reason": f"INJECTION_FAILED_{injection_result.error}",
                "trigger": trigger_type
            }

        # STEP 5d: Success Email
        send_success_email(event_id, injection_result.order_details, correlation_id)

        # Register idempotency on success
        if idempotency_key:
            idempotency_cache[idempotency_key] = True
            logger.info(f"[req-{correlation_id}] Idempotency registered: {idempotency_key}")

        logger.info(f"[req-{correlation_id}] Webhook processed successfully")

        return {
            "ok": True,
            "processed": True,
            "reason": "PROCESSED_SUCCESSFULLY",
            "trigger": trigger_type
        }

    except Exception as e:
        logger.error(f"[req-{correlation_id}] Pipeline failed for event {event_id}: {e}")
        send_failure_email(event_id, str(e), correlation_id)
        return {
            "ok": False,
            "processed": False,
            "reason": f"PIPELINE_EXCEPTION_{type(e).__name__}",
            "trigger": trigger_type
        }


def verify_signature(body: bytes, signature: str) -> bool:
    """Verify Triple Seat webhook signature (legacy interface)."""
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
