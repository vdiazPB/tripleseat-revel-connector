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
    # ALWAYS check idempotency to prevent duplicate orders
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
        # STEP 5a: Extract event status and determine routing
        event_status = event.get('status', '').upper()
        logger.info(f"[req-{correlation_id}] Event status: {event_status}")
        
        # Route based on status:
        # - CLOSED: Process for Revel (POS injection)
        # - DEFINITE: Process for Supply It (Special Events/catering)
        # - Other: Reject
        
        is_revel_event = event_status == 'CLOSED'
        is_supplyit_event = event_status == 'DEFINITE'
        
        if not is_revel_event and not is_supplyit_event:
            logger.info(f"[req-{correlation_id}] Event {event_id} has status '{event_status}' - not CLOSED (Revel) or DEFINITE (Supply It)")
            return {
                "ok": True,
                "processed": False,
                "reason": f"INVALID_STATUS:{event_status}",
                "trigger": trigger_type
            }
        
        # STEP 5b: Validation (only for Revel events)
        if is_revel_event:
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

        # STEP 5c: Time Gate (only for Revel events)
        if is_revel_event:
            if skip_time_gate:
                logger.info(f"[req-{correlation_id}] Time gate: SKIPPED (test mode)")
                time_gate_status = "OPEN"
            else:
                # Pass event data from webhook to time_gate to avoid redundant API call
                time_gate_result = check_time_gate(event_id, correlation_id, event_data={'event': event})
                if time_gate_result == "PROCEED":
                    logger.info(f"[req-{correlation_id}] Time gate: OPEN")
                    time_gate_status = "OPEN"
                else:
                    logger.info(f"[req-{correlation_id}] Time gate: CLOSED (result={time_gate_result})")
                    
                    # Register idempotency on safe acknowledgment
                    if idempotency_key:
                        idempotency_cache[idempotency_key] = True
                        logger.info(f"[req-{correlation_id}] Idempotency registered: {idempotency_key}")
                    
                    return {
                        "ok": True,
                        "processed": False,
                        "reason": f"TIME_GATE_CLOSED_{time_gate_result}",
                        "trigger": trigger_type
                    }
        
        # STEP 5d: Process Supply It event (if DEFINITE status)
        if is_supplyit_event:
            logger.info(f"[req-{correlation_id}] Processing DEFINITE event for Supply It")
            
            from integrations.supplyit.injection import inject_order_to_supplyit
            
            # Get configuration
            connector_enabled = os.getenv('ENABLE_CONNECTOR', 'true').lower() == 'true'
            dry_run_mode = os.getenv('DRY_RUN_MODE', 'false').lower() == 'true'
            
            supplyit_result = inject_order_to_supplyit(
                event_id=event_id,
                correlation_id=correlation_id,
                dry_run=dry_run_mode,
                enable_connector=connector_enabled,
                webhook_payload=payload
            )
            
            # Register idempotency
            if idempotency_key:
                idempotency_cache[idempotency_key] = True
                logger.info(f"[req-{correlation_id}] Idempotency registered: {idempotency_key}")
            
            if not supplyit_result.is_valid:
                logger.error(f"[req-{correlation_id}] Supply It injection failed: {supplyit_result.error}")
                return {
                    "ok": True,
                    "processed": False,
                    "reason": f"SUPPLYIT_FAILED_{supplyit_result.error}",
                    "trigger": trigger_type
                }
            
            logger.info(f"[req-{correlation_id}] Supply It order created successfully")
            return {
                "ok": True,
                "processed": True,
                "event_id": event_id,
                "system": "Supply It",
                "reason": "SUPPLYIT_INJECTED",
                "trigger": trigger_type
            }
        
        # STEP 5e: Process Revel event (if CLOSED status)
        if is_revel_event:
            # STEP 5e1: Trigger Sync Endpoint (webhook -> reconciliation)
            # Instead of direct injection, call the sync endpoint which handles:
            # - Revel idempotency check (prevent duplicates)
            # - Full order validation
            # - Audit logging with correlation ID
            try:
                import requests
                sync_url = os.getenv('SYNC_ENDPOINT_URL', 'http://127.0.0.1:8000/api/sync/tripleseat')
                
                # Call sync endpoint with event_id
                response = requests.get(
                    sync_url,
                    params={'event_id': event_id},
                    timeout=30
                )
                
                if response.status_code != 200:
                    logger.error(f"[req-{correlation_id}] Sync endpoint returned {response.status_code}: {response.text[:500]}")
                    send_failure_email(event_id, f"Sync endpoint error: {response.status_code}", correlation_id)
                    return {
                        "ok": False,
                        "processed": False,
                        "reason": f"SYNC_ENDPOINT_ERROR_{response.status_code}",
                        "trigger": trigger_type
                    }
                
                sync_result = response.json()
                
                if not sync_result.get('success'):
                    logger.error(f"[req-{correlation_id}] Sync returned failure: {sync_result.get('error')}")
                    send_failure_email(event_id, f"Sync failed: {sync_result.get('error')}", correlation_id)
                    return {
                        "ok": False,
                        "processed": False,
                        "reason": f"SYNC_FAILED_{sync_result.get('error', 'UNKNOWN')}",
                        "trigger": trigger_type
                    }
                
                # Extract revel_order_id from sync response
                events = sync_result.get('events', [])
                revel_order_id = None
                if events and len(events) > 0:
                    revel_order_id = events[0].get('revel_order_id')
                    event_name = events[0].get('name')
                    event_date = events[0].get('date')
                
                logger.info(f"[req-{correlation_id}] Event {event_id} synced successfully - Revel Order: {revel_order_id}")
                
                # Register idempotency
                if idempotency_key:
                    idempotency_cache[idempotency_key] = True
                    logger.info(f"[req-{correlation_id}] Idempotency registered: {idempotency_key}")
                
                # STEP 5e2: Success Email
                # Create minimal order details for email
                order_details = {
                    'event_id': event_id,
                    'revel_order_id': revel_order_id,
                    'event_name': event_name if events else 'Unknown'
                }
                send_success_email(event_id, order_details, correlation_id)
                
                return {
                    "ok": True,
                    "processed": True,
                    "event_id": event_id,
                    "revel_order_id": revel_order_id,
                    "reason": "REVEL_INJECTED",
                    "trigger": trigger_type
                }
            
            except requests.exceptions.Timeout:
                logger.error(f"[req-{correlation_id}] Sync endpoint timed out")
                send_failure_email(event_id, "Sync endpoint timeout", correlation_id)
                return {
                    "ok": False,
                    "processed": False,
                    "reason": "SYNC_ENDPOINT_TIMEOUT",
                    "trigger": trigger_type
                }
            except Exception as e:
                logger.error(f"[req-{correlation_id}] Sync call failed: {e}")
                send_failure_email(event_id, f"Sync error: {str(e)}", correlation_id)
                return {
                "ok": False,
                "processed": False,
                "reason": f"SYNC_CALL_FAILED_{type(e).__name__}",
                "trigger": trigger_type
            }

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
