#!/usr/bin/env python3
"""
Create or update product mappings for TripleSeat to JERA/Supply It.
This handles the case where TripleSeat product names don't exactly match JERA product names.
"""

import json
import os

# Product mapping: TripleSeat product name -> JERA product ID or name
PRODUCT_MAPPINGS = {
    'OG': 'GLAZED DONUT',  # or product ID if we find one
    'TRIPLE OG': 'CHOCOLATE FROSTED DONUT',
    'SUGA DADDY': 'VANILLA SUGAR DONUT',
    'FEELIN TOASTY': 'COCONUT TOASTED DONUT',
    'CHOCOLATE RAINBOW RING': 'CHOCOLATE RAINBOW DONUT',
    'PINK RAINBOW RING': 'PINK RAINBOW DONUT',
    'OL FASHIONED': 'CAKE DONUT',
    'MAPLE BAR': 'MAPLE BAR DONUT',
    'FUDGY WUDGY': 'CHOCOLATE CAKE DONUT',
    'HEY BLONDIE': 'MAPLE VANILLA DONUT',
}

def save_mappings():
    """Save product mappings to file for use in injection."""
    mapping_file = os.path.join(
        os.path.dirname(__file__),
        'integrations',
        'supplyit',
        'product_mappings.json'
    )
    os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
    
    with open(mapping_file, 'w') as f:
        json.dump(PRODUCT_MAPPINGS, f, indent=2)
    
    print(f"Saved {len(PRODUCT_MAPPINGS)} product mappings to {mapping_file}")

if __name__ == '__main__':
    save_mappings()
