import os
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TripleSeatAPIClient:
    def __init__(self):
        # TripleSeat uses API key authentication, not OAuth
        self.api_key = os.getenv('TRIPLESEAT_OAUTH_CLIENT_ID')  # This is actually the API key
        self.api_secret = os.getenv('TRIPLESEAT_OAUTH_CLIENT_SECRET')  # API secret
        # Base URL should NOT include /v1 - it's added per endpoint
        base = os.getenv('TRIPLESEAT_API_BASE', 'https://api.tripleseat.com')
        self.base_url = base.rstrip('/v1').rstrip('/')  # Remove trailing /v1 if present

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Fetch event details from Triple Seat API."""
        # TripleSeat API uses query params for auth
        url = f"{self.base_url}/v1/events/{event_id}.json"
        params = self._get_auth_params()

        try:
            logger.info(f"Fetching TripleSeat event {event_id} from {url}")
            response = requests.get(url, params=params)
            logger.info(f"TripleSeat response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            logger.info(f"TripleSeat event {event_id} fetched successfully")
            return data
        except requests.RequestException as e:
            logger.error(f"Failed to fetch event {event_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text[:500]}")
            return None

    def _get_auth_params(self) -> Dict[str, str]:
        """Get authentication query parameters for TripleSeat API."""
        return {
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }