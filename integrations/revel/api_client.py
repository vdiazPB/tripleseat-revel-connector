import os
import requests
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class RevelAPIClient:
    def __init__(self):
        self.api_key = os.getenv('REVEL_API_KEY')
        self.api_secret = os.getenv('REVEL_API_SECRET')
        self.domain = os.getenv('REVEL_DOMAIN', '').strip()
        # Validate domain is set
        if not self.domain:
            logger.error("❌ REVEL_DOMAIN environment variable is not set!")
        # Handle domain that may or may not include .revelup.com
        if self.domain.endswith('.revelup.com'):
            self.base_url = f"https://{self.domain}"
        else:
            self.base_url = f"https://{self.domain}.revelup.com"
        logger.info(f"🔧 RevelAPIClient init - domain='{self.domain}', base_url='{self.base_url}'")
        # In-memory product cache (per request/instance)
        self._product_cache: Dict[str, Dict[str, Any]] = {}
        
        # Default user and POS station for API orders (configurable via env)
        # Use 1 (atlasadmin - standard service account) for integration/API orders
        self.default_user_id = os.getenv('REVEL_DEFAULT_USER_ID', '1')
        self.default_pos_station_id = os.getenv('REVEL_DEFAULT_POS_STATION_ID', '4')
        logger.info(f"🔧 Using default_user_id={self.default_user_id}")
        
        # Triple Seat specific configuration
        # Pinkbox CustomMenu: ID 2340, ProductGroup: ID 4425
        self.tripleseat_custom_menu_id = os.getenv('REVEL_TRIPLESEAT_CUSTOM_MENU_ID', '2340')
        self.tripleseat_product_group_id = os.getenv('REVEL_TRIPLESEAT_PRODUCT_GROUP_ID', '4425')
        # Triple Seat Dining Option: ID 113
        self.tripleseat_dining_option_id = int(os.getenv('REVEL_TRIPLESEAT_DINING_OPTION_ID', '113'))
        # Triple Seat Custom Payment Type: ID 236
        self.tripleseat_payment_type_id = os.getenv('REVEL_TRIPLESEAT_PAYMENT_TYPE_ID', '236')
        # Triple Seat Discount (open discount): ID 3358
        self.tripleseat_discount_id = os.getenv('REVEL_TRIPLESEAT_DISCOUNT_ID', '3358')

    def get_products_by_establishment(self, establishment: str) -> List[Dict[str, Any]]:
        """Fetch all products for an establishment from Revel."""
        # Check cache first
        cache_key = f"products_{establishment}"
        if cache_key in self._product_cache:
            logger.info(f"Using cached products for establishment {establishment}")
            return self._product_cache[cache_key]

        url = f"{self.base_url}/resources/Product/"
        params = {
            'establishment': establishment,  # Use plain ID in query params
            'limit': 1000  # Fetch all products
        }
        headers = self._get_headers()

        try:
            logger.info(f"Fetching products from Revel for establishment {establishment}")
            logger.debug(f"  Full URL: {url}")
            logger.debug(f"  Params: {params}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            products = data.get('objects', [])
            logger.info(f"Fetched {len(products)} products for establishment {establishment}")
            # Cache the results
            self._product_cache[cache_key] = products
            return products
        except requests.exceptions.InvalidURL as e:
            logger.error(f"INVALID URL - Failed to fetch products for establishment {establishment}: {e}")
            logger.error(f"  base_url: '{self.base_url}'")
            logger.error(f"  Full URL would be: {url}")
            return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch products for establishment {establishment}: {e}")
            logger.error(f"  URL attempted: {url}")
            logger.error(f"  Params: {params}")
            return []
            return []

    def resolve_product_by_name(self, establishment: str, product_name: str) -> Optional[Dict[str, Any]]:
        """Resolve a product by exact match first, then fuzzy match if needed.
        
        Tries:
        1. Exact match (case-insensitive)
        2. Fuzzy match (substring + similarity threshold)
        
        Returns matched product or None.
        """
        products = self.get_products_by_establishment(establishment)
        product_name_lower = product_name.lower()
        
        # First pass: exact match (case-insensitive)
        for product in products:
            if product.get('name', '').lower() == product_name_lower:
                logger.info(f"[PRODUCT MATCH - EXACT] '{product_name}' → product_id={product.get('id')}")
                return product
        
        # Second pass: fuzzy match (substring + similarity)
        best_match = None
        best_score = 0.0
        threshold = 0.6  # 60% similarity threshold
        
        for product in products:
            revel_name = product.get('name', '').lower()
            
            # Check if search term is a substring of product name
            if product_name_lower in revel_name or revel_name in product_name_lower:
                logger.info(f"[PRODUCT MATCH - SUBSTRING] '{product_name}' → '{revel_name}' (product_id={product.get('id')})")
                return product
            
            # Calculate similarity score
            similarity = SequenceMatcher(None, product_name_lower, revel_name).ratio()
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = product
        
        if best_match:
            logger.info(f"[PRODUCT MATCH - FUZZY] '{product_name}' → '{best_match.get('name')}' (score={best_score:.2f}, product_id={best_match.get('id')})")
            return best_match
        
        logger.warning(f"[PRODUCT NOT FOUND] '{product_name}' not found in establishment {establishment}")
        return None

    def get_order(self, external_order_id: str, establishment: str) -> Optional[Dict[str, Any]]:
        """Check if order exists by local_id (external reference)."""
        url = f"{self.base_url}/resources/Order/"
        params = {
            'establishment': establishment,  # Use plain ID in query params
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
            logger.error(f"  URL attempted: {url}")
            logger.error(f"  Params: {params}")
            return None

    def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new order in Revel with line items.
        
        Order creation requires two steps:
        1. Create the order record with required fields
        2. Add order items to the order
        
        Args:
            order_data: Dict containing:
                - establishment: Revel establishment ID
                - notes: Order notes/description
                - local_id: External reference ID (for deduplication)
                - items: List of line items with product_id, quantity, price
                - discount_amount: Optional discount amount to apply
        
        Returns:
            Created order dict with all items, or None on failure
        """
        establishment = order_data.get('establishment')
        notes = order_data.get('notes', '')
        local_id = order_data.get('local_id', '')
        items = order_data.get('items', [])
        discount_amount = order_data.get('discount_amount', 0)
        customer_name = order_data.get('customer_name', '')  # Optional customer name
        customer_phone = order_data.get('customer_phone', '')  # Optional customer phone (will be converted to int)
        
        headers = self._get_headers()
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')  # Local time for OrderHistory opened field
        now_iso = datetime.now().isoformat()  # Local time ISO format
        order_uuid = str(uuid.uuid4())
        
        # Build required fields for order creation
        # Using Triple Seat dining option (ID 113)
        # NOTE: created_at and last_updated_at are actually PosStation URIs, not datetimes!
        
        # Build notes with customer phone if available
        notes_with_customer = notes
        if customer_phone:
            notes_with_customer = f"{notes} | Phone: {customer_phone}".strip() if notes else f"Phone: {customer_phone}"
        
        revel_order_data = {
            'uuid': order_uuid,
            'establishment': f'/enterprise/Establishment/{establishment}/',
            'pos_mode': 'Q',  # Q = quick service
            'notes': notes_with_customer,  # Include customer phone in notes
            'local_id': local_id,  # For tracking/deduplication
            'web_order': True,  # Mark as API/web order
            'created_date': now_iso,
            'updated_date': now_iso,
            # Users
            'created_by': f'/enterprise/User/{self.default_user_id}/',
            'updated_by': f'/enterprise/User/{self.default_user_id}/',
            # Station/Dining
            'station': f'/resources/PosStation/{self.default_pos_station_id}/',
            'created_at': f'/resources/PosStation/{self.default_pos_station_id}/',  # POS Station URI
            'last_updated_at': f'/resources/PosStation/{self.default_pos_station_id}/',  # POS Station URI
            'dining_option': self.tripleseat_dining_option_id,
            # Financial fields (all zero for now)
            'final_total': 0,
            'tax': 0,
            'subtotal': 0,
            'remaining_due': 0,
            'surcharge': 0,
            'reporting_id': 0,  # Will be auto-generated by Revel when order is finalized
        }
        
        # Add customer name if provided
        if customer_name:
            revel_order_data['call_name'] = customer_name

        try:
            # Step 1: Create the order
            url = f"{self.base_url}/resources/Order/"
            logger.info(f"Creating order in Revel (establishment={establishment}, local_id={local_id})")
            logger.debug(f"Order data being sent: {revel_order_data}")
            response = requests.post(url, headers=headers, json=revel_order_data)
            
            if response.status_code not in [200, 201]:
                logger.error(f"Failed to create order: {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                return None
            
            created_order = response.json()
            logger.debug(f"Order response: {created_order}")
            order_id = created_order.get('id')
            order_uri = created_order.get('resource_uri')
            logger.info(f"✅ Order created: ID={order_id}, URI={order_uri}")
            
            # Step 2: Add line items
            items_url = f"{self.base_url}/resources/OrderItem/"
            created_items = []
            
            for item in items:
                item_uuid = str(uuid.uuid4())
                ts_price = float(item.get('price', 0))  # Triple Seat price per unit
                
                item_data = {
                    'uuid': item_uuid,
                    'order': order_uri,
                    'product': f"/resources/Product/{item.get('product_id')}/",
                    'quantity': item.get('quantity', 1),
                    # Triple Seat price override - these fields ensure the TS price is used, not the product's default price
                    'price': ts_price,  # Unit price from Triple Seat
                    'initial_price': ts_price,  # Initial/base price for this item
                    'price_to_display': ts_price,  # Display price (override Revel product price)
                    'created_by': f'/enterprise/User/{self.default_user_id}/',
                    'updated_by': f'/enterprise/User/{self.default_user_id}/',
                    'station': f'/resources/PosStation/{self.default_pos_station_id}/',
                    'created_date': now_iso,
                    'updated_date': now_iso,
                    # Required numeric fields
                    'tax_amount': 0,
                    'modifier_amount': 0,
                    'temp_sort': 0,
                    'tax_rate': 0,
                    'dining_option': self.tripleseat_dining_option_id,  # Triple Seat dining option
                }
                
                logger.info(f"Adding item: product_id={item.get('product_id')}, qty={item.get('quantity')}")
                item_response = requests.post(items_url, headers=headers, json=item_data)
                
                if item_response.status_code in [200, 201]:
                    created_items.append(item_response.json())
                    logger.info(f"  ✅ Item added: {item_response.json().get('id')}")
                else:
                    logger.error(f"  ❌ Failed to add item: {item_response.text[:200]}")
            
            # Step 3: Apply Triple Seat discount AFTER items are added (so amount is calculated correctly)
            if discount_amount and discount_amount > 0:
                discount_success = self._apply_discount(order_uri, discount_amount, now, headers)
                if discount_success:
                    logger.info(f"  ✅ Triple Seat Discount applied: ${discount_amount}")
                else:
                    logger.warning(f"  ⚠️ Failed to apply discount (order still created)")
            
            # Step 4: Apply Triple Seat payment
            payment_amount = order_data.get('payment_amount', 0)
            if payment_amount and payment_amount > 0:
                payment_success = self._apply_payment(order_uri, payment_amount, now, headers, establishment)
                if payment_success:
                    logger.info(f"  ✅ Triple Seat Payment applied: ${payment_amount}")
                else:
                    logger.warning(f"  ⚠️ Failed to apply payment (order still created)")
            
            # Step 5: Finalize order - set totals and close it so it appears in UI
            # Calculate subtotal from items, not from payment/discount amounts
            # The payment_amount passed in is already the final_total after discount
            # So: final_total = payment_amount, subtotal = final_total + discount_amount
            final_total = float(payment_amount) if payment_amount else 0
            subtotal = float(payment_amount) + float(discount_amount) if payment_amount else 0
            logger.info(f"Finalizing: discount_amount={discount_amount}, final_total={final_total}, subtotal={subtotal}")
            finalize_success = self._finalize_order(order_uri, subtotal, discount_amount, final_total, headers, now)
            if finalize_success:
                logger.info(f"  ✅ Order finalized (will appear in Revel UI)")
            
            # Return order with items
            created_order['items'] = created_items
            logger.info(f"Order {order_id} created with {len(created_items)}/{len(items)} items")
            return created_order
            
        except requests.RequestException as e:
            logger.error(f"Failed to create order: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text[:500]}")
            return None

    def _finalize_order(self, order_uri: str, subtotal: float, discount_amount: float, final_total: float, headers: Dict[str, str], opened_at: str) -> bool:
        """Finalize an order by setting totals and closing it.
        
        This makes the order visible in the Revel UI Order History.
        Automatically closes the order if remaining_due <= 0 (fully paid or overpaid).
        """
        try:
            url = f"{self.base_url}{order_uri}"
            
            logger.info(f"_finalize_order called with: subtotal={subtotal}, discount_amount={discount_amount}, final_total={final_total}")
            
            # Calculate remaining_due: if final_total is paid, remaining_due = 0
            # In this case, the order should be closed
            remaining_due = 0  # We're providing full payment, so nothing remaining
            should_close = remaining_due <= 0
            
            finalize_data = {
                'subtotal': subtotal,  # Amount before discount
                'final_total': final_total,  # Amount after discount
                'discount': f'/resources/Discount/{self.tripleseat_discount_id}/',  # Ensure discount reference is set
                'closed': should_close,  # Close if fully paid (remaining_due <= 0)
                'printed': True,  # Mark as printed
                'opened': opened_at,  # Set opened timestamp (required for Order History UI display)
                # Note: NOT including discount_amount here - Revel may calculate it from AppliedDiscountOrder
            }
            
            logger.info(f"Finalizing order - sending: {finalize_data}")
            logger.info(f"{'Closing order (fully paid)' if should_close else 'Keeping order open (invoice)'}")
            response = requests.patch(url, headers=headers, json=finalize_data)
            
            if response.status_code in [200, 202]:
                resp_data = response.json()
                logger.info(f"✅ Order finalized successfully")
                logger.info(f"Response discount_amount: {resp_data.get('discount_amount')}")
                logger.info(f"Response printed: {resp_data.get('printed')}")
                
                # Ensure printed flag is actually set (sometimes Revel doesn't apply it in first PATCH)
                if not resp_data.get('printed'):
                    logger.info("⚠️ Printed flag not set in response, applying second PATCH...")
                    printed_data = {'printed': True}
                    printed_response = requests.patch(url, headers=headers, json=printed_data)
                    if printed_response.status_code in [200, 202]:
                        logger.info("✅ Printed flag successfully set")
                    else:
                        logger.warning(f"⚠️ Failed to set printed flag: {printed_response.status_code}")
                
                # Create OrderHistory record so order appears in Order History UI
                logger.info("Creating OrderHistory record...")
                self._create_order_history(order_uri, headers, opened_at)
                
                return True
            else:
                logger.error(f"Failed to finalize order: HTTP {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                return False
        except Exception as e:
            logger.error(f"Failed to finalize order: {e}")
            return False

    def _create_order_history(self, order_uri: str, headers: Dict[str, str], opened_at: str) -> bool:
        """Create an OrderHistory record for the order to make it appear in Order History UI.
        
        OrderHistory records are required for orders to display in Revel's Order History UI.
        """
        try:
            history_url = f"{self.base_url}/resources/OrderHistory/"
            history_data = {
                'uuid': str(uuid.uuid4()),
                'order': order_uri,
                'order_opened_by': f'/enterprise/User/{self.default_user_id}/',
                'order_opened_at': f'/resources/PosStation/{self.default_pos_station_id}/',
                'opened': opened_at,  # Timestamp from screenshot format: YYYY-MM-DDTHH:MM:SS
            }
            
            logger.debug(f"Creating OrderHistory: {history_data}")
            resp = requests.post(history_url, headers=headers, json=history_data)
            
            if resp.status_code in [200, 201]:
                history = resp.json()
                logger.info(f"✅ OrderHistory record created: ID={history.get('id')}")
                return True
            else:
                logger.warning(f"⚠️ Failed to create OrderHistory: HTTP {resp.status_code}")
                logger.warning(f"Response: {resp.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"Failed to create OrderHistory: {e}")
            return False

    def open_order(self, order_id: str) -> bool:
        """Open/activate an order so it appears in Revel UI.
        
        Sets the 'opened' flag to true, which makes the order visible in POS.
        """
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/resources/Order/{order_id}/"
            
            # PATCH the order to mark it as opened
            order_data = {
                'opened': True,
            }
            
            logger.info(f"Opening order {order_id} (marking as active)")
            response = requests.patch(url, headers=headers, json=order_data)
            
            if response.status_code in [200, 202]:
                logger.info(f"✅ Order {order_id} opened successfully")
                return True
            else:
                logger.error(f"Failed to open order {order_id}: HTTP {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                return False
        except Exception as e:
            logger.error(f"Failed to open order {order_id}: {e}")
            return False

    def _apply_discount(self, order_uri: str, amount: float, now: str, headers: Dict[str, str]) -> bool:
        """Apply Triple Seat Discount to an order.
        
        For variable discounts, we need to set the amount properly on the order
        so that the AppliedDiscountOrder gets created with the correct value.
        """
        try:
            # For variable discounts, set both discount and the amount
            # The discount_amount field controls what gets applied
            discount_data = {
                'discount': f'/resources/Discount/{self.tripleseat_discount_id}/',
                'discount_amount': amount,  # This is the actual discount amount to apply
                'discount_rule_amount': amount,  # Also try setting rule_amount
                'discount_reason': 'Triple Seat Discount',  # Set discount reason for display
                'discounted_by': f'/enterprise/User/{self.default_user_id}/',  # Track who applied discount
            }
            url = f"{self.base_url}{order_uri}"
            logger.debug(f"Applying discount: {discount_data}")
            response = requests.patch(url, headers=headers, json=discount_data)
            logger.debug(f"Discount PATCH response: {response.status_code}")
            return response.status_code in [200, 202]
        except Exception as e:
            logger.error(f"Failed to apply discount: {e}")
            return False

    def _apply_payment(self, order_uri: str, amount: float, now: str, headers: Dict[str, str], establishment: str) -> bool:
        """Apply Triple Seat payment to an order."""
        try:
            payment_url = f"{self.base_url}/resources/Payment/"
            payment_data = {
                'uuid': str(uuid.uuid4()),
                'order': order_uri,
                'payment_type': int(self.tripleseat_payment_type_id),  # Triple Seat payment type
                'amount': str(amount),
                'tip': '0.00',
                'payment_date': now,
                'created_date': now,
                'updated_date': now,
                'created_by': f'/enterprise/User/{self.default_user_id}/',
                'updated_by': f'/enterprise/User/{self.default_user_id}/',
                'station': f'/resources/PosStation/{self.default_pos_station_id}/',
                'establishment': f'/enterprise/Establishment/{establishment}/',
            }
            response = requests.post(payment_url, headers=headers, json=payment_data)
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to apply payment: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        import base64
        auth_string = f"{self.api_key}:{self.api_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        return {
            'API-AUTHENTICATION': f'{self.api_key}:{self.api_secret}',
            'Content-Type': 'application/json'
        }