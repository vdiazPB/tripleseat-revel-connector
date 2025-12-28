import logging
import os
from typing import Dict, Any, Optional
from enum import Enum
import requests

logger = logging.getLogger(__name__)

class TripleSeatFailureType(str, Enum):
    """Classification of TripleSeat API failures."""
    TOKEN_FETCH_FAILED = "TOKEN_FETCH_FAILED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    API_ERROR = "API_ERROR"
    UNKNOWN = "UNKNOWN"

def safe_json(response: requests.Response, request_id: str = None) -> Optional[Dict[str, Any]]:
    """Safely parse JSON from response, handling errors explicitly.
    
    Args:
        response: The HTTP response object
        request_id: Optional request ID for logging
        
    Returns:
        Parsed JSON dict or None if parsing fails
    """
    req_id = f"[req-{request_id}]" if request_id else ""
    
    if response.status_code != 200:
        logger.error(f"{req_id} Cannot parse JSON: HTTP {response.status_code}")
        return None
    
    content_type = response.headers.get('content-type', '').lower()
    if 'application/json' not in content_type:
        logger.error(f"{req_id} Response not JSON: content-type={content_type}")
        return None
    
    try:
        text = response.text.strip()
        if not text:
            logger.error(f"{req_id} Response body is empty")
            return None
        
        data = response.json()
        logger.debug(f"{req_id} JSON parsed successfully")
        return data
    except ValueError as e:
        body_preview = response.text[:300] if response.text else "empty"
        logger.error(f"{req_id} JSON decode error: {e}. Body preview: {body_preview}")
        return None

class TripleSeatAPIClient:
    """TripleSeat API Client - OAuth 2.0 Bearer Token Implementation.
    
    Uses OAuth 2.0 client credentials flow for Bearer token authentication.
    """
    
    def __init__(self):
        self.base_url = os.getenv('TRIPLESEAT_API_BASE', 'https://api.tripleseat.com')
        self.client_id = os.getenv('TRIPLESEAT_OAUTH_CLIENT_ID', '').strip()
        self.client_secret = os.getenv('TRIPLESEAT_OAUTH_CLIENT_SECRET', '').strip()
        self.token_url = os.getenv('TRIPLESEAT_OAUTH_TOKEN_URL', '').strip()
        
        self.access_token = None
        self.session = requests.Session()
        
        # Fetch OAuth 2.0 access token
        if not all([self.client_id, self.client_secret, self.token_url]):
            logger.error("❌ OAuth 2.0 credentials missing: CLIENT_ID, CLIENT_SECRET, or TOKEN_URL")
        else:
            try:
                self._fetch_access_token()
                logger.info("✅ TripleSeatAPIClient initialized with OAuth 2.0 Bearer token")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OAuth 2.0: {e}")
                self.access_token = None

    def _fetch_access_token(self):
        """Fetch OAuth 2.0 access token using client credentials."""
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'v1_access'  # Based on .env SCOPES
        }
        
        response = requests.post(self.token_url, data=data, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data.get('access_token')
        
        if not self.access_token:
            raise ValueError("No access_token in OAuth 2.0 response")
        
        # Set default headers for session
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Fetch event details from TripleSeat API using OAuth 2.0.
        
        Args:
            event_id: TripleSeat event ID
            
        Returns:
            Event dictionary or None if API call fails
        """
        if not self.access_token:
            logger.error("[get_event] OAuth 2.0 token not available")
            return None
            
        try:
            url = f"{self.base_url}/v2/events/{event_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = safe_json(response)
            if data:
                logger.info(f"✅ [get_event] Retrieved event {event_id} via OAuth 2.0")
                return data.get('event')
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"[get_event] Event {event_id} not found (404)")
                return None
            elif e.response.status_code == 401:
                logger.error(f"[get_event] OAuth 2.0 authentication failed (401)")
                return None
            logger.error(f"[get_event] HTTP error: {e.response.status_code} - {e}")
            return None
        except Exception as e:
            logger.error(f"[get_event] Error fetching event {event_id}: {e}")
            return None
    
    def get_event_with_status(self, event_id: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch event and return tuple with status code.
        
        Args:
            event_id: TripleSeat event ID
            
        Returns:
            Tuple of (event_dict, status_code) or (None, failure_type)
        """
        if not self.access_token:
            logger.error("[get_event_with_status] OAuth 2.0 token not available")
            return None, TripleSeatFailureType.AUTHORIZATION_DENIED
            
        try:
            url = f"{self.base_url}/v2/events/{event_id}"
            logger.info(f"[get_event_with_status] Requesting: {url}")
            
            response = self.session.get(url, timeout=10)
            
            # Log response details
            body_preview = response.text[:300] if response.text else "empty"
            logger.info(f"[get_event_with_status] Response: HTTP {response.status_code}, Body preview: {body_preview}")
            
            if response.status_code == 404:
                logger.warning(f"[get_event_with_status] Event {event_id} not found")
                return None, TripleSeatFailureType.RESOURCE_NOT_FOUND
            elif response.status_code == 401:
                logger.error(f"[get_event_with_status] OAuth 2.0 authentication failed (401)")
                return None, TripleSeatFailureType.AUTHORIZATION_DENIED
            elif response.status_code != 200:
                logger.error(f"[get_event_with_status] HTTP {response.status_code}: {body_preview}")
                return None, TripleSeatFailureType.API_ERROR
            
            # Safe JSON parsing
            data = safe_json(response)
            if data is None:
                logger.error(f"[get_event_with_status] Failed to parse JSON response")
                return None, TripleSeatFailureType.API_ERROR
            
            logger.info(f"✅ [get_event_with_status] Retrieved event {event_id}")
            return data.get('event'), response.status_code
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"[get_event_with_status] HTTP error: {e.response.status_code} - {e}")
            return None, TripleSeatFailureType.API_ERROR
        except Exception as e:
            logger.error(f"[get_event_with_status] Unexpected error: {e}")
            return None, TripleSeatFailureType.API_ERROR

    def check_tripleseat_access(self) -> bool:
        """Check if OAuth 2.0 credentials are valid."""
        if not self.access_token:
            logger.error("[check_tripleseat_access] OAuth 2.0 token not available")
            return False
            
        try:
            # Try a simple API call to verify auth
            url = f"{self.base_url}/v2/events"
            response = self.session.get(url, timeout=10, params={'limit': 1})
            is_valid = response.status_code == 200
            
            if is_valid:
                logger.info("✅ [check_tripleseat_access] OAuth 2.0 credentials valid")
            else:
                logger.warning(f"[check_tripleseat_access] OAuth 2.0 check failed: {response.status_code}")
            return is_valid
        except Exception as e:
            logger.error(f"[check_tripleseat_access] OAuth 2.0 validation error: {e}")
            return False
