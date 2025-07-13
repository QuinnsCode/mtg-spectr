#!/usr/bin/env python3
"""
Show exactly what the trend tracker would output with your current data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.services.price_monitor import PriceMonitorService
from mtg_card_pricing.data.trend_database import TrendDatabase

def show_what_you_see():
    """Show exactly what the user would see in their trend tracker."""
    
    print("MTG Card Pricing - What You Actually See")
    print("=" * 60)
    
    # Initialize the actual service (as it would run)
    service = PriceMonitorService()
    trend_db = TrendDatabase()
    
    print("Current Service Configuration:")
    print(f"  Percentage threshold: {service.config['percentage_alert_threshold']}%")
    print(f"  Min price threshold: ${service.config['min_price_threshold']}")
    print(f"  Max cards per cycle: {service.config['max_cards_per_cycle']}")
    
    # Get the actual parameters the service will use
    trend_hours = int(trend_db.get_config_value('trend_analysis_hours') or 24)
    absolute_threshold = float(trend_db.get_config_value('absolute_alert_threshold') or 100.0)
    
    print(f"  Time window: {trend_hours} hours")
    print(f"  Absolute threshold: ${absolute_threshold}")
    
    print(f"\nDatabase Status:")
    with trend_db._get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM price_snapshots")
        total_snapshots = cursor.fetchone()[0]
        print(f"  Total price snapshots: {total_snapshots:,}")
        
        if total_snapshots > 0:
            cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM price_snapshots")
            min_time, max_time = cursor.fetchone()
            print(f"  Date range: {min_time} to {max_time}")
    
    # Run the exact same analysis the service would run
    print(f"\n" + "="*60)
    print("RUNNING ACTUAL TREND ANALYSIS")
    print("="*60)
    
    trending_cards = trend_db.find_trending_cards(
        min_percentage_change=service.config['percentage_alert_threshold'],
        min_absolute_change=absolute_threshold,
        min_price_threshold=service.config['min_price_threshold'],
        hours_back=trend_hours,
        max_cards=service.config['max_cards_per_cycle']
    )
    
    print(f"\nResults: {len(trending_cards)} trending cards found")
    
    if trending_cards:
        print(f"\nYour Trending Cards (exactly what you see):")
        print(f"{'#':<3} {'Card Name':<35} {'Set':<6} {'Change %':>10} {'Start $':>10} {'Current $':>10}")
        print("-" * 80)
        
        for i, card in enumerate(trending_cards, 1):
            print(f"{i:<3} {card['card_name'][:34]:<35} {card['set_code']:<6} "
                  f"{card['percentage_change']:>9.1f}% "
                  f"${card['price_start']:>9.2f} ${card['price_current']:>9.2f}")
        
        # Analyze why each card was detected
        print(f"\nWhy These Cards Were Detected:")
        for card in trending_cards:
            reasons = []
            if card['percentage_change'] >= service.config['percentage_alert_threshold']:
                reasons.append(f"{card['percentage_change']:.1f}% >= {service.config['percentage_alert_threshold']}%")
            if card['absolute_change'] >= absolute_threshold:
                reasons.append(f"${card['absolute_change']:.2f} >= ${absolute_threshold}")
            
            print(f"  {card['card_name']}: {' OR '.join(reasons)}")
    
    else:
        print("\nNo trending cards detected.")
        print("\nPossible reasons:")
        print("  1. No price data in database")
        print("  2. Thresholds too high for existing data")
        print("  3. Time window too narrow")
        print("  4. All cards below minimum price threshold")
    
    # Show what the exact filter conditions are
    print(f"\n" + "="*60)
    print("FILTER CONDITIONS SUMMARY")
    print("="*60)
    print(f"A card is detected if ALL of these are true:")
    print(f"  ✓ Has price data in last {trend_hours} hours")
    print(f"  ✓ Current or historical price >= ${service.config['min_price_threshold']}")
    print(f"  ✓ ({service.config['percentage_alert_threshold']}%+ change OR ${absolute_threshold}+ absolute change)")
    
    # If we have test data, explain it
    if trending_cards and any('Test' in card['card_name'] or card['set_code'] == 'TST' for card in trending_cards):
        print(f"\nNOTE: Test data detected. Run this on your real database for actual results.")

if __name__ == "__main__":
    show_what_you_see()