import os
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RevelAPIClient:
    def __init__(self):
        self.api_key = os.getenv('REVEL_API_KEY')
        self.api_secret = os.getenv('REVEL_API_SECRET')
        self.domain = os.getenv('REVEL_DOMAIN')
        self.base_url = f"https://{self.domain}.revelup.com"

    def get_order(self, external_order_id: str, establishment: str) -> Optional[Dict[str, Any]]:
        """Check if order exists by external_order_id."""
        url = f"{self.base_url}/api/orders/"
        params = {
            'establishment': establishment,
            'external_order_id': external_order_id
        }
        headers = self._get_headers()

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            orders = data.get('objects', [])
            return orders[0] if orders else None
        except requests.RequestException as e:
            logger.error(f"Failed to check order {external_order_id}: {e}")
            return None

    def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new order in Revel."""
        url = f"{self.base_url}/api/orders/"
        headers = self._get_headers()

        try:
            response = requests.post(url, headers=headers, json=order_data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to create order: {e}")
            return None

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        import base64
        auth_string = f"{self.api_key}:{self.api_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        return {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json'
        }