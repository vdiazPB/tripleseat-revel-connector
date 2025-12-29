import logging
import json
import os
from datetime import datetime, time
from typing import Optional
from integrations.tripleseat.api_client import TripleSeatAPIClient, TripleSeatFailureType

logger = logging.getLogger(__name__)

def check_time_gate(event_id: str, correlation_id: str = None, event_data: dict = None) -> str:
    """Check if event is within injection time window.
    
    AUTHENTICATION STRATEGY:
    - Uses provided event_data if available (from webhook, no API call needed)
    - Falls back to Public API Key fetch if event_data not provided
    
    Args:
        event_id: TripleSeat event ID
        correlation_id: Optional correlation ID for logging
        event_data: Optional event data dict (from webhook). If provided, skips API call.
    
    Returns:
        "PROCEED" if event is within injection window
        "TOO_EARLY" if event date is in the future
        "EVENT_DAY_PASSED" if event date is in the past (and outside window)
        "OUTSIDE_WINDOW" if today is event day but outside time window
        "UNKNOWN_TIMEZONE" if site timezone cannot be determined
        "INVALID_DATE_FORMAT" if event date cannot be parsed
        "MISSING_DATA" if event data is missing required fields
        "EVENT_DATA_UNAVAILABLE" if event cannot be fetched
        "AUTHORIZATION_DENIED" if authorization to event denied
    """
    # Use provided event_data if available, otherwise fetch from API
    if event_data:
        event = event_data.get("event", {})
        logger.info(f"[req-{correlation_id}] Using provided event_data (no API call)")
    else:
        client = TripleSeatAPIClient()
        response, failure_type = client.get_event_with_status(event_id)

        if not response:
            if failure_type == TripleSeatFailureType.AUTHORIZATION_DENIED:
                return "AUTHORIZATION_DENIED"
            return "EVENT_DATA_UNAVAILABLE"

        event = response.get("event", {})
    
    event_date_str = event.get("event_date")
    event_start_str = event.get("event_start")  # e.g. "12/28/2025 9:00 AM"
    event_start_utc = event.get("event_start_utc")  # ISO format backup
    site_id = event.get("site_id")

    if not event_date_str or not site_id:
        return "MISSING_DATA"

    # Get timezone from config
    timezone = get_site_timezone(site_id)
    if not timezone:
        return "UNKNOWN_TIMEZONE"

    # Parse event date - TripleSeat returns MM/DD/YYYY format
    try:
        # Try ISO format first
        try:
            event_date = datetime.fromisoformat(event_date_str).date()
        except ValueError:
            # Fall back to MM/DD/YYYY format
            event_date = datetime.strptime(event_date_str, "%m/%d/%Y").date()
    except ValueError:
        logger.error(f"Cannot parse event date: {event_date_str}")
        return "INVALID_DATE_FORMAT"

    # Get current time in site timezone
    # For simplicity, assume UTC for now - in production, use proper timezone handling
    now = datetime.now()
    now_date = now.date()

    if now_date < event_date:
        return "TOO_EARLY"
    elif now_date > event_date:
        return "EVENT_DAY_PASSED"
    else:
        # Same day - check if event has already started
        # Try to parse event start time to see if event has passed
        if event_start_str or event_start_utc:
            try:
                # Try event_start_utc first (ISO format)
                if event_start_utc:
                    event_start_dt = datetime.fromisoformat(event_start_utc.replace('Z', '+00:00'))
                    event_start_time = event_start_dt.time()
                elif event_start_str:
                    # Parse "12/28/2025 9:00 AM" format
                    event_start_dt = datetime.strptime(event_start_str, "%m/%d/%Y %I:%M %p")
                    event_start_time = event_start_dt.time()
                else:
                    event_start_time = None
                
                current_time = now.time()
                
                if event_start_time and current_time >= event_start_time:
                    logger.warning(f"Event has already started at {event_start_time}, current time is {current_time}")
                    return "EVENT_ALREADY_STARTED"
                else:
                    logger.info(f"Event starts at {event_start_time}, current time is {current_time} - gate OPEN")
                    return "PROCEED"
            except (ValueError, AttributeError) as e:
                logger.warning(f"Could not parse event start time, allowing injection: {e}")
                return "PROCEED"
        else:
            # No event start time available, use daily time window
            # Check time window: 12:01 AM to 11:59:59 PM
            current_time = now.time()
            start_time = time(0, 1, 0)   # 12:01:00 AM
            end_time = time(23, 59, 59)  # 11:59:59 PM

            if start_time <= current_time <= end_time:
                logger.info(f"Time gate OPEN: {current_time} is within {start_time} to {end_time}")
                return "PROCEED"
            else:
                logger.warning(f"Time gate CLOSED: {current_time} is outside {start_time} to {end_time}")
                return "OUTSIDE_TIME_WINDOW"

def get_site_timezone(site_id: str) -> Optional[str]:
    """Get timezone for site from config."""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'locations.json')
    try:
        with open(config_path, 'r') as f:
            locations = json.load(f)
            site_config = locations.get(str(site_id))
            return site_config.get('timezone') if site_config else None
    except (FileNotFoundError, json.JSONDecodeError):
        return None