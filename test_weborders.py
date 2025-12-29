#!/usr/bin/env python3
"""Test direct Order API for creating orders.

Note: WebOrders API endpoints are not available on this Revel installation.
Using the direct Order API which is fully supported and functional.
"""

import logging
import sys
import os
from dotenv import load_dotenv
from integrations.revel.api_client import RevelAPIClient

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load env
load_dotenv()

def test_direct_order_api():
    """Test creating an order via direct Order API."""
    client = RevelAPIClient()
    
    # Test establishment 4 (test location)
    establishment = "4"
    
    # Order with 2 items
    order_data = {
        "establishment": establishment,
        "local_id": "test_direct_order_123",
        "notes": "Test Direct Order API - Using Order Resource",
        "items": [
            {
                "product_id": 579,      # TRIPLE OG
                "quantity": 2,
                "price": 5.95
            },
            {
                "product_id": 611,      # MAPLE BAR
                "quantity": 3,
                "price": 2.95
            }
        ],
        "discount_amount": 1.50,
        "payment_amount": 28.80,  # (5.95*2 + 2.95*3) - 1.50
    }
    
    logger.info("=" * 60)
    logger.info("Testing Direct Order API (WebOrders not available)")
    logger.info("=" * 60)
    logger.info(f"Order data: {order_data}")
    
    result = client.create_order(order_data)
    
    if result:
        logger.info(f"✅ SUCCESS: Order created")
        order_id = result.get('id')
        logger.info(f"Order ID: {order_id}")
        logger.info(f"Order URI: {result.get('resource_uri')}")
        logger.info(f"Items created: {len(result.get('items', []))}")
        
        # Open/activate the order so it appears in Revel UI
        logger.info(f"\nOpening order {order_id} to activate it in Revel UI...")
        opened = client.open_order(str(order_id))
        if opened:
            logger.info(f"✅ Order {order_id} opened and activated")
        else:
            logger.warning(f"⚠️ Failed to open order {order_id}, but it may still be visible")
        
        return True
    else:
        logger.error(f"❌ FAILED: No order created")
        return False

if __name__ == '__main__':
    success = test_direct_order_api()
    sys.exit(0 if success else 1)
