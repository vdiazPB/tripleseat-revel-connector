import logging
import os
from typing import Dict, Any, Optional
from enum import Enum
import requests
from requests_oauthlib import OAuth1Session

logger = logging.getLogger(__name__)

class TripleSeatFailureType(str, Enum):
    """Classification of TripleSeat API failures."""
    TOKEN_FETCH_FAILED = "TOKEN_FETCH_FAILED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    API_ERROR = "API_ERROR"
    UNKNOWN = "UNKNOWN"

class TripleSeatAPIClient:
    """TripleSeat API Client - OAuth 1.0 Implementation.
    
    Uses OAuth 1.0 (3-legged authentication) for secure API access.
    No OAuth 2.0 - cleaner, more reliable authentication.
    """
    
    def __init__(self):
        self.base_url = os.getenv('TRIPLESEAT_API_BASE', 'https://api.tripleseat.com')
        self.consumer_key = os.getenv('CONSUMER_KEY', '').strip()
        self.consumer_secret = os.getenv('CONSUMER_SECRET', '').strip()
        self.access_token = os.getenv('TRIPLESEAT_OAUTH_TOKEN', '').strip()
        self.access_token_secret = os.getenv('TRIPLESEAT_OAUTH_TOKEN_SECRET', '').strip()
        
        # Validate OAuth 1.0 credentials
        if not all([self.consumer_key, self.consumer_secret]):
            logger.error("❌ OAuth 1.0 credentials missing: CONSUMER_KEY or CONSUMER_SECRET")
            self.oauth_session = None
        else:
            try:
                self.oauth_session = OAuth1Session(
                    client_key=self.consumer_key,
                    client_secret=self.consumer_secret,
                    resource_owner_key=self.access_token or '',
                    resource_owner_secret=self.access_token_secret or '',
                    signature_type='AUTH_HEADER'
                )
                logger.info("✅ TripleSeatAPIClient initialized with OAuth 1.0")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OAuth 1.0: {e}")
                self.oauth_session = None

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Fetch event details from TripleSeat API using OAuth 1.0.
        
        Args:
            event_id: TripleSeat event ID
            
        Returns:
            Event dictionary or None if API call fails
        """
        if not self.oauth_session:
            logger.error("[get_event] OAuth 1.0 session not initialized")
            return None
            
        try:
            url = f"{self.base_url}/v2/events/{event_id}"
            response = self.oauth_session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ [get_event] Retrieved event {event_id} via OAuth 1.0")
            return data.get('event')
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"[get_event] Event {event_id} not found (404)")
                return None
            elif e.response.status_code == 401:
                logger.error(f"[get_event] OAuth 1.0 authentication failed (401)")
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
        if not self.oauth_session:
            logger.error("[get_event_with_status] OAuth 1.0 session not initialized")
            return None, TripleSeatFailureType.AUTHORIZATION_DENIED
            
        try:
            url = f"{self.base_url}/v2/events/{event_id}"
            response = self.oauth_session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ [get_event_with_status] Retrieved event {event_id}")
            return data.get('event'), response.status_code
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"[get_event_with_status] Event {event_id} not found")
                return None, TripleSeatFailureType.RESOURCE_NOT_FOUND
            elif e.response.status_code == 401:
                logger.error(f"[get_event_with_status] OAuth 1.0 authentication failed")
                return None, TripleSeatFailureType.AUTHORIZATION_DENIED
            logger.error(f"[get_event_with_status] HTTP {e.response.status_code}")
            return None, TripleSeatFailureType.API_ERROR
        except Exception as e:
            logger.error(f"[get_event_with_status] Error: {e}")
            return None, TripleSeatFailureType.API_ERROR

    def check_tripleseat_access(self) -> bool:
        """Check if OAuth 1.0 credentials are valid."""
        if not self.oauth_session:
            logger.error("[check_tripleseat_access] OAuth 1.0 session not initialized")
            return False
            
        try:
            # Try a simple API call to verify auth
            url = f"{self.base_url}/v2/events"
            response = self.oauth_session.get(url, timeout=10, params={'limit': 1})
            is_valid = response.status_code == 200
            
            if is_valid:
                logger.info("✅ [check_tripleseat_access] OAuth 1.0 credentials valid")
            else:
                logger.warning(f"[check_tripleseat_access] OAuth 1.0 check failed: {response.status_code}")
            return is_valid
        except Exception as e:
            logger.error(f"[check_tripleseat_access] OAuth 1.0 validation error: {e}")
            return False
