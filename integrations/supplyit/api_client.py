import logging
import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SupplyItAPIClient:
    """Supply It API Client for creating orders in Special Events location.
    
    Uses JERA API (Supply It) authentication with API key and username.
    Base URL: https://api.supplyit.com/api/v2
    """
    
    def __init__(self):
        self.base_url = os.getenv('SUPPLYIT_API_BASE', 'https://app.supplyit.com/api/v2')
        self.api_key = os.getenv('JERA_API_KEY')
        self.username = os.getenv('JERA_API_USERNAME')
        
        if not self.api_key or not self.username:
            logger.error("JERA_API_KEY or JERA_API_USERNAME not configured")
            return
        
        logger.info("✅ SupplyItAPIClient initialized with credentials")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with Supply It API authentication."""
        headers = {
            'Authorization': self.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if self.username:
            headers['X-Api-User'] = self.username
        return headers
    
    def get_location_by_name(self, location_name: str) -> Optional[Dict[str, Any]]:
        """Get location ID by name.
        
        Args:
            location_name: Name of the location (e.g., "Special Events")
        
        Returns:
            Location dict with ID and details, or None if not found
        """
        try:
            url = f"{self.base_url}/locations"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"[get_location_by_name] HTTP {response.status_code}")
                return None
            
            locations = response.json()
            if not isinstance(locations, list):
                locations = locations.get('locations', [])
            
            # Find location by name (case-insensitive)
            for loc in locations:
                if loc.get('Name', '').lower() == location_name.lower():
                    logger.info(f"[get_location_by_name] Found location '{location_name}' with ID {loc.get('ID')}")
                    return loc
            
            logger.warning(f"[get_location_by_name] Location '{location_name}' not found")
            return None
            
        except Exception as e:
            logger.error(f"[get_location_by_name] Error: {e}")
            return None
    
    def get_location_by_code(self, location_code: str) -> Optional[Dict[str, Any]]:
        """Get location by code.
        
        Args:
            location_code: Code of the location (e.g., "8", "c11")
        
        Returns:
            Location dict with ID and details, or None if not found
        """
        try:
            url = f"{self.base_url}/locations"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"[get_location_by_code] HTTP {response.status_code}")
                return None
            
            locations = response.json()
            if not isinstance(locations, list):
                locations = locations.get('locations', [])
            
            # Find location by code (exact match, case-insensitive)
            for loc in locations:
                if str(loc.get('Code', '')).lower() == str(location_code).lower():
                    logger.info(f"[get_location_by_code] Found location code '{location_code}' with ID {loc.get('ID')}")
                    return loc
            
            logger.warning(f"[get_location_by_code] Location code '{location_code}' not found")
            return None
            
        except Exception as e:
            logger.error(f"[get_location_by_code] Error: {e}")
            return None
    
    def get_contact_by_name(self, location_id: int, contact_name: str) -> Optional[Dict[str, Any]]:
        """Get contact by name within a location.
        
        Args:
            location_id: Supply It location ID
            contact_name: Name of the contact
        
        Returns:
            Contact dict with ID, or None if not found
        """
        try:
            # Supply It API doesn't have a direct contact search, would need to get all contacts
            # For now, we'll return None and contacts will be optional in orders
            logger.warning(f"[get_contact_by_name] Contact lookup not yet implemented")
            return None
            
        except Exception as e:
            logger.error(f"[get_contact_by_name] Error: {e}")
            return None
    
    def get_product_by_name(self, location_id: int, product_name: str) -> Optional[Dict[str, Any]]:
        """Get product by name within a location.
        
        Note: Supply It API requires X-Supplyit-LocationCode header to fetch products.
        This method finds the location code first, then fetches products.
        
        Args:
            location_id: Supply It location ID
            product_name: Name of the product
        
        Returns:
            Product dict with ID, or None if not found
        """
        try:
            # Find location code by ID (needed for products endpoint)
            location_code = None
            locations = self._get_all_locations()
            for loc in locations:
                if loc.get('ID') == location_id:
                    location_code = loc.get('Code')
                    break
            
            if not location_code:
                logger.warning(f"[get_product_by_name] Location ID {location_id} not found")
                return None
            
            # Fetch products with location code header (REQUIRED by API)
            url = f"{self.base_url}/products"
            headers = self._get_headers()
            headers['X-Supplyit-LocationCode'] = location_code
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"[get_product_by_name] HTTP {response.status_code}")
                return None
            
            products = response.json()
            if not isinstance(products, list):
                products = products.get('products', [])
            
            # Find product by name (case-insensitive)
            for prod in products:
                if prod.get('Name', '').lower() == product_name.lower():
                    logger.info(f"[get_product_by_name] Found product '{product_name}' with ID {prod.get('ID')}")
                    return prod
            
            logger.warning(f"[get_product_by_name] Product '{product_name}' not found in location code '{location_code}'")
            return None
            
        except Exception as e:
            logger.error(f"[get_product_by_name] Error: {e}")
            return None
    
    def _get_all_locations(self) -> List[Dict[str, Any]]:
        """Get all locations for caching/lookup.
        
        Returns:
            List of location dicts with ID, Code, Name, etc.
        """
        try:
            url = f"{self.base_url}/locations"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, list) else data.get('locations', [])
            return []
        except Exception as e:
            logger.error(f"[_get_all_locations] Error: {e}")
            return []
    
    def create_order(self, order_data: Dict[str, Any], correlation_id: str = None) -> Optional[Dict[str, Any]]:
        """Create an order in Supply It.
        
        Note: Supply It API requires X-Supplyit-LocationCode header to create orders.
        
        Args:
            order_data: Order dict with Location, OrderItems, OrderDate, etc.
            correlation_id: Request correlation ID for logging
        
        Returns:
            Created order dict with ID, or None if creation fails
        """
        req_id = f"[req-{correlation_id}]" if correlation_id else "[supplyit]"
        
        try:
            url = f"{self.base_url}/orders"
            
            logger.info(f"{req_id} Creating Supply It order")
            logger.debug(f"{req_id} Order payload: {order_data}")
            
            # Get location code from order data
            location_code = order_data.get('Location', {}).get('Code', '8')
            
            # Add location code header (REQUIRED by API)
            headers = self._get_headers()
            headers['X-Supplyit-LocationCode'] = location_code
            
            response = requests.put(url, json=order_data, headers=headers, timeout=30)
            
            if response.status_code not in [200, 201]:
                logger.error(f"{req_id} [create_order] HTTP {response.status_code}: {response.text}")
                return None
            
            created_order = response.json()
            order_id = created_order.get('ID')
            
            logger.info(f"{req_id} [create_order SUCCESS] Order created with ID {order_id}")
            return created_order
            
        except Exception as e:
            logger.error(f"{req_id} [create_order] Error: {e}")
            return None
