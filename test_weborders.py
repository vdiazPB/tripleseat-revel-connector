#!/usr/bin/env python3
"""Test WebOrders API for creating orders."""

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

def test_weborders():
    """Test creating an order via WebOrders API."""
    client = RevelAPIClient()
    
    # Test establishment 4 (test location)
    establishment = "4"
    
    # Order with 2 items
    order_data = {
        "establishment": establishment,
        "local_id": "test_weborder_123",
        "notes": "Test WebOrders API Order",
        "items": [
            {
                "product_id": "579",      # TRIPLE OG
                "quantity": 2,
                "price": 5.95
            },
            {
                "product_id": "611",      # MAPLE BAR
                "quantity": 3,
                "price": 2.95
            }
        ],
        "discount_amount": 1.50,
        "payment_amount": 28.80,  # (5.95*2 + 2.95*3) - 1.50
    }
    
    logger.info("=" * 60)
    logger.info("Testing WebOrders API")
    logger.info("=" * 60)
    logger.info(f"Order data: {order_data}")
    
    result = client.create_order_via_weborders(order_data)
    
    if result:
        logger.info(f"✅ SUCCESS: Order created")
        logger.info(f"Order ID: {result.get('id') or result.get('order_id')}")
        logger.info(f"Response: {result}")
        return True
    else:
        logger.error(f"❌ FAILED: No order created")
        return False

if __name__ == '__main__':
    success = test_weborders()
    sys.exit(0 if success else 1)
