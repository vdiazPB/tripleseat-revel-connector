import os
import requests
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class RevelAPIClient:
    def __init__(self):
        self.api_key = os.getenv('REVEL_API_KEY')
        self.api_secret = os.getenv('REVEL_API_SECRET')
        self.domain = os.getenv('REVEL_DOMAIN', '')
        # Handle domain that may or may not include .revelup.com
        if self.domain.endswith('.revelup.com'):
            self.base_url = f"https://{self.domain}"
        else:
            self.base_url = f"https://{self.domain}.revelup.com"
        # In-memory product cache (per request/instance)
        self._product_cache: Dict[str, Dict[str, Any]] = {}

    def get_products_by_establishment(self, establishment: str) -> List[Dict[str, Any]]:
        """Fetch all products for an establishment from Revel."""
        # Check cache first
        cache_key = f"products_{establishment}"
        if cache_key in self._product_cache:
            logger.info(f"Using cached products for establishment {establishment}")
            return self._product_cache[cache_key]

        url = f"{self.base_url}/resources/Product/"
        params = {
            'establishment': establishment,
            'limit': 1000  # Fetch all products
        }
        headers = self._get_headers()

        try:
            logger.info(f"Fetching products from Revel for establishment {establishment}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            products = data.get('objects', [])
            logger.info(f"Fetched {len(products)} products for establishment {establishment}")
            # Cache the results
            self._product_cache[cache_key] = products
            return products
        except requests.RequestException as e:
            logger.error(f"Failed to fetch products for establishment {establishment}: {e}")
            return []

    def resolve_product_by_name(self, establishment: str, product_name: str) -> Optional[Dict[str, Any]]:
        """Resolve a product by exact name match."""
        products = self.get_products_by_establishment(establishment)
        
        for product in products:
            if product.get('name') == product_name:
                logger.info(f"[PRODUCT MATCH] '{product_name}' → product_id={product.get('id')}")
                return product
        
        logger.warning(f"[PRODUCT NOT FOUND] '{product_name}' not found in establishment {establishment}")
        return None

    def get_order(self, external_order_id: str, establishment: str) -> Optional[Dict[str, Any]]:
        """Check if order exists by local_id (external reference)."""
        url = f"{self.base_url}/resources/Order/"
        params = {
            'establishment': establishment,
            'local_id': external_order_id  # Use local_id for external references
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
        url = f"{self.base_url}/resources/Order/"
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
            'API-AUTHENTICATION': f'{self.api_key}:{self.api_secret}',
            'Content-Type': 'application/json'
        }