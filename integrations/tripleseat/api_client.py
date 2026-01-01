import logging
import os
from typing import Dict, Any, Optional
from enum import Enum
import requests
from .oauth1 import get_oauth1_session

logger = logging.getLogger(__name__)

class TripleSeatFailureType(str, Enum):
    """Classification of TripleSeat API failures."""
    TOKEN_FETCH_FAILED = "TOKEN_FETCH_FAILED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    API_ERROR = "API_ERROR"
    UNKNOWN = "UNKNOWN"

def safe_json_response(response: requests.Response, request_id: str = None) -> Optional[Dict[str, Any]]:
    """Safely parse JSON from response, explicitly rejecting HTML and non-JSON.
    
    Args:
        response: The HTTP response object
        request_id: Optional request ID for logging
        
    Returns:
        Parsed JSON dict or None if parsing fails
        
    Raises:
        ValueError: If response is HTML or not valid JSON
    """
    req_id = f"[req-{request_id}]" if request_id else ""
    
    # Log response details once
    content_type = response.headers.get('content-type', '').lower()
    body_preview = response.text[:300] if response.text else "empty"
    logger.info(f"{req_id} Response: HTTP {response.status_code}, Content-Type: {content_type}, Body preview: {body_preview}")
    
    # Explicitly reject HTML responses (indicates auth failure)
    if 'text/html' in content_type:
        logger.error(f"{req_id} Received HTML login page instead of JSON - OAuth authentication failed")
        raise ValueError("HTML_RESPONSE: OAuth authentication failed, received login page")
    
    if response.status_code != 200:
        logger.error(f"{req_id} Cannot parse JSON: HTTP {response.status_code}")
        return None
    
    if 'application/json' not in content_type:
        logger.error(f"{req_id} Response not JSON: content-type={content_type}")
        raise ValueError(f"INVALID_CONTENT_TYPE: Expected application/json, got {content_type}")
    
    try:
        text = response.text.strip()
        if not text:
            logger.error(f"{req_id} Response body is empty")
            raise ValueError("EMPTY_RESPONSE: No JSON content")
        
        data = response.json()
        logger.debug(f"{req_id} JSON parsed successfully")
        return data
    except ValueError as e:
        body_preview = response.text[:300] if response.text else "empty"
        logger.error(f"{req_id} JSON decode error: {e}. Body preview: {body_preview}")
        raise ValueError(f"JSON_DECODE_ERROR: {e}")

class TripleSeatAPIClient:
    """TripleSeat API Client - OAuth 1.0 Signature Authentication.
    
    Uses OAuth 1.0 to sign all API requests.
    Ensures ALL API calls include proper Authorization header with signature.
    """
    
    def __init__(self):
        self.base_url = os.getenv('TRIPLESEAT_API_BASE', 'https://api.tripleseat.com')
        self.session = get_oauth1_session()
        
        logger.info("✅ TripleSeatAPIClient initialized with OAuth 1.0 signature authentication")

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Fetch event details from TripleSeat API using OAuth 1.0.
        
        Args:
            event_id: TripleSeat event ID
            
        Returns:
            Event dictionary or None if API call fails
        """
        try:
            url = f"{self.base_url}/v1/events/{event_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = safe_json_response(response)
            if data:
                logger.info(f"✅ [get_event] Retrieved event {event_id} via OAuth 1.0")
                return data.get('event')
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"[get_event] Event {event_id} not found (404)")
                return None
            elif e.response.status_code == 401:
                logger.error(f"[get_event] OAuth 1.0 authentication failed (401)")
                return None
            logger.error(f"[get_event] HTTP error: {e.response.status_code} - {e}")
            return None
        except ValueError as e:
            logger.error(f"[get_event] Response validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"[get_event] Error fetching event {event_id}: {e}")
            return None
    
    def get_event_with_status(self, event_id: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch event and return tuple with status code.
        
        Uses OAuth 1.0 signature authentication.
        Explicitly rejects HTML responses and validates JSON content.
        
        Args:
            event_id: TripleSeat event ID
            
        Returns:
            Tuple of (event_dict, status_code) or (None, failure_type)
        """
        try:
            url = f"{self.base_url}/v1/events/{event_id}"
            logger.info(f"[get_event_with_status] Requesting: {url}")
            
            response = self.session.get(url, timeout=10)
            
            # Handle specific HTTP status codes
            if response.status_code == 404:
                logger.warning(f"[get_event_with_status] Event {event_id} not found")
                return None, TripleSeatFailureType.RESOURCE_NOT_FOUND
            elif response.status_code == 401:
                logger.error(f"[get_event_with_status] OAuth 1.0 authentication failed (401)")
                return None, TripleSeatFailureType.AUTHORIZATION_DENIED
            elif response.status_code == 403:
                logger.error(f"[get_event_with_status] OAuth 1.0 access forbidden (403)")
                return None, TripleSeatFailureType.AUTHORIZATION_DENIED
            elif response.status_code != 200:
                logger.error(f"[get_event_with_status] HTTP {response.status_code}: Unexpected status")
                return None, TripleSeatFailureType.API_ERROR
            
            # Safe JSON parsing with HTML detection
            try:
                data = safe_json_response(response)
                if data is None:
                    logger.error(f"[get_event_with_status] Failed to parse JSON response")
                    return None, TripleSeatFailureType.API_ERROR
                
                logger.info(f"✅ [get_event_with_status] Retrieved event {event_id}")
                return data.get('event'), response.status_code
                
            except ValueError as e:
                # HTML responses or JSON decode errors
                error_msg = str(e)
                if "HTML_RESPONSE" in error_msg:
                    logger.error(f"[get_event_with_status] Authentication failed - received HTML login page")
                    return None, TripleSeatFailureType.AUTHORIZATION_DENIED
                elif "INVALID_CONTENT_TYPE" in error_msg:
                    logger.error(f"[get_event_with_status] Invalid content type: {error_msg}")
                    return None, TripleSeatFailureType.API_ERROR
                else:
                    logger.error(f"[get_event_with_status] JSON parsing error: {error_msg}")
                    return None, TripleSeatFailureType.API_ERROR
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"[get_event_with_status] HTTP error: {e.response.status_code} - {e}")
            return None, TripleSeatFailureType.API_ERROR
        except Exception as e:
            logger.error(f"[get_event_with_status] Unexpected error: {e}")
            return None, TripleSeatFailureType.API_ERROR

    def check_tripleseat_access(self) -> bool:
        """Check if OAuth 1.0 authentication is valid."""
        try:
            # Try a simple API call to verify auth
            url = f"{self.base_url}/v1/events"
            response = self.session.get(url, timeout=10, params={'limit': 1})
            is_valid = response.status_code == 200
            
            if is_valid:
                logger.info("✅ [check_tripleseat_access] OAuth 1.0 authentication valid")
            else:
                logger.warning(f"[check_tripleseat_access] OAuth 1.0 check failed: {response.status_code}")
            return is_valid
        except Exception as e:
            logger.error(f"[check_tripleseat_access] OAuth 1.0 validation error: {e}")
            return False
    def update_event(self, event_id: int, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an event using PUT request with OAuth 1.0 signature.
        
        Args:
            event_id: TripleSeat event ID
            payload: Update payload (e.g., {'event': {'status': 'CLOSED'}})
            
        Returns:
            Updated event dictionary or None if API call fails
        """
        try:
            url = f"{self.base_url}/v1/events/{event_id}"
            response = self.session.put(url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = safe_json_response(response)
            if data:
                logger.info(f"✅ [update_event] Updated event {event_id} via OAuth 1.0")
                return data.get('event')
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"[update_event] Event {event_id} not found (404)")
                return None
            elif e.response.status_code == 401:
                logger.error(f"[update_event] OAuth 1.0 authentication failed (401)")
                return None
            logger.error(f"[update_event] HTTP error: {e.response.status_code} - {e}")
            return None
        except ValueError as e:
            logger.error(f"[update_event] Response validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"[update_event] Error updating event {event_id}: {e}")
            return None