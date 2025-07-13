#!/usr/bin/env python3
"""
Debug what price threshold is actually being used.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.data.trend_database import TrendDatabase
from mtg_card_pricing.services.price_monitor import PriceMonitorService

def debug_thresholds():
    """Debug actual vs expected thresholds."""
    
    print("Price Threshold Debug")
    print("=" * 40)
    
    # Check what the service uses
    service = PriceMonitorService()
    print(f"Service min_price_threshold: ${service.config['min_price_threshold']}")
    
    # Check what the test actually passed
    trend_db = TrendDatabase()
    
    print("\nTesting different min_price_threshold values:")
    
    for threshold in [0.5, 1.0, 2.0]:
        trending = trend_db.find_trending_cards(
            min_percentage_change=50.0,
            min_absolute_change=1000.0,
            min_price_threshold=threshold,
            hours_back=24,
            max_cards=10
        )
        
        print(f"\nWith ${threshold} threshold:")
        for card in trending:
            print(f"  {card['card_name']}: {card['price_start']:.2f} -> {card['price_current']:.2f}")

if __name__ == "__main__":
    debug_thresholds()