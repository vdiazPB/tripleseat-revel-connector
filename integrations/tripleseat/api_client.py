import os
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TripleSeatAPIClient:
    def __init__(self):
        self.client_id = os.getenv('TRIPLESEAT_CLIENT_ID')
        self.client_secret = os.getenv('TRIPLESEAT_CLIENT_SECRET')
        self.base_url = "https://api.tripleseat.com/v1"

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Fetch event details from Triple Seat API."""
        url = f"{self.base_url}/events/{event_id}"
        headers = self._get_headers()

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch event {event_id}: {e}")
            return None

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Content-Type': 'application/json'
        }

    def _get_access_token(self) -> str:
        """Get access token (simplified - in production, handle token caching/refresh)."""
        # This is a placeholder - implement proper OAuth flow
        return f"{self.client_id}:{self.client_secret}"  # Simplified for demo