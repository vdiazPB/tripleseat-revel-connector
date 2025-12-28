import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class TripleSeatFailureType(str, Enum):
    """Classification of TripleSeat API failures."""
    TOKEN_FETCH_FAILED = "TOKEN_FETCH_FAILED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    API_ERROR = "API_ERROR"
    UNKNOWN = "UNKNOWN"

class TripleSeatAPIClient:
    """TripleSeat API Client - OAuth 2.0 REMOVED.
    
    ⚠️ DEPRECATED - This class is now stub-only.
    
    All API calls are disabled to enforce webhook-payload-only mode.
    Event data should come from webhook handlers, not API calls.
    
    This class is kept for backward compatibility but all methods return None.
    """
    
    def __init__(self):
        logger.info("TripleSeatAPIClient initialized - OAuth 2.0 disabled (webhook-only mode)")

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Stub method - returns None.
        
        Use: Pass webhook payload directly to injection handler.
        Set: skip_validation=True when calling webhook handlers.
        """
        logger.warning(f"[get_event] API call blocked - OAuth 2.0 disabled. Use webhook payload.")
        return None
    
    def get_event_with_status(self, event_id: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Stub method - returns (None, AUTHORIZATION_DENIED).
        
        Use: Pass webhook payload directly to injection handler.
        Set: skip_validation=True when calling webhook handlers.
        """
        logger.warning(f"[get_event_with_status] API call blocked for event {event_id}. Use webhook payload.")
        return None, TripleSeatFailureType.AUTHORIZATION_DENIED

    def check_tripleseat_access(self) -> bool:
        """Stub - always returns False."""
        logger.warning("[check_tripleseat_access] Stub method - OAuth 2.0 disabled")
        return False
