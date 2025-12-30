import json
import os
from typing import Optional, Dict, Any

def get_revel_establishment(site_id: str) -> Optional[str]:
    """Get Revel establishment name for Triple Seat site."""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'locations.json')
    try:
        with open(config_path, 'r') as f:
            locations = json.load(f)
            site_config = locations.get(str(site_id))
            if site_config:
                # Return the location name, not the revel_establishment ID
                return site_config.get('name')
            return None
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        return None

def get_dining_option_id(establishment: str) -> Optional[int]:
    """Get Triple Seat dining option ID for establishment."""
    # This would need to be configured or fetched from Revel
    # For now, return a placeholder
    return 1  # Placeholder

def get_payment_type_id(establishment: str) -> Optional[int]:
    """Get Triple Seat payment type ID for establishment."""
    # Placeholder
    return 1  # Placeholder

def get_discount_id(establishment: str) -> Optional[int]:
    """Get Triple Seat discount ID for establishment."""
    # Placeholder
    return 1  # Placeholder