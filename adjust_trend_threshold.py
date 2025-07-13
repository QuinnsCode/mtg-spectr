#!/usr/bin/env python3
"""
Adjust trend detection thresholds for more significant price movements.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.config.settings import get_settings
from mtg_card_pricing.data.trend_database import TrendDatabase

def adjust_thresholds(percentage_threshold=50.0, absolute_threshold=1.00):
    """Adjust trend detection thresholds."""
    
    print("MTG Card Pricing - Adjusting Trend Detection Thresholds")
    print("=" * 50)
    
    # Get current settings
    settings_manager = get_settings()
    
    # Show current thresholds
    print("\nCurrent Thresholds:")
    print(f"  Percentage threshold: {settings_manager.settings.trend_tracker.percentage_alert_threshold}%")
    print(f"  Absolute threshold: ${settings_manager.settings.trend_tracker.absolute_alert_threshold}")
    print(f"  Minimum price: ${settings_manager.settings.trend_tracker.min_price_threshold}")
    
    # Update thresholds
    print(f"\nUpdating to new thresholds:")
    print(f"  Percentage threshold: {percentage_threshold}%")
    print(f"  Absolute threshold: ${absolute_threshold}")
    
    # Update settings
    settings_manager.settings.trend_tracker.percentage_alert_threshold = percentage_threshold
    settings_manager.settings.trend_tracker.absolute_alert_threshold = absolute_threshold
    
    # Save settings
    if settings_manager.save_settings():
        print("\n✓ Settings updated successfully!")
    else:
        print("\n✗ Failed to save settings")
        return
    
    # Also update the database configuration
    trend_db = TrendDatabase()
    trend_db.set_config_value('percentage_alert_threshold', str(percentage_threshold))
    trend_db.set_config_value('absolute_alert_threshold', str(absolute_threshold))
    
    print("\n✓ Database configuration updated!")
    
    # Preview what would be found with new thresholds
    print("\nAnalyzing current data with new thresholds...")
    
    # Find cards with the new thresholds
    trending_cards = trend_db.find_trending_cards(
        min_percentage_change=percentage_threshold,
        min_absolute_change=absolute_threshold,
        min_price_threshold=settings_manager.settings.trend_tracker.min_price_threshold,
        max_cards=100  # Limit for preview
    )
    
    print(f"\nWith new thresholds, found {len(trending_cards)} trending cards:")
    
    if trending_cards:
        print("\nTop 10 cards by percentage change:")
        print(f"{'Card Name':<40} {'Set':<8} {'Change %':>10} {'Change $':>10} {'Current $':>10}")
        print("-" * 80)
        
        for card in trending_cards[:10]:
            print(f"{card['card_name'][:39]:<40} {card['set_code']:<8} "
                  f"{card['percentage_change']:>9.1f}% "
                  f"${card['absolute_change']:>9.2f} "
                  f"${card['price_current']:>9.2f}")
    else:
        print("  No cards found with these thresholds.")
        print("\nSuggestions:")
        print("  - The market might be stable with few >50% movements")
        print("  - Try a lower threshold like 30% or 40%")
        print("  - Check if monitoring has been running long enough to detect trends")
        print("  - Ensure the database has recent price snapshots")
    
    print("\nNote: These new thresholds will be used in the next monitoring cycle.")

def main():
    """Main function with argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Adjust trend detection thresholds')
    parser.add_argument('--percentage', type=float, default=50.0,
                        help='Percentage change threshold (default: 50.0)')
    parser.add_argument('--absolute', type=float, default=1.00,
                        help='Absolute dollar change threshold (default: 1.00)')
    
    args = parser.parse_args()
    
    if args.percentage <= 0 or args.percentage > 500:
        print("Error: Percentage threshold must be between 0 and 500")
        return
    
    if args.absolute < 0 or args.absolute > 1000:
        print("Error: Absolute threshold must be between 0 and 1000")
        return
    
    adjust_thresholds(args.percentage, args.absolute)

if __name__ == "__main__":
    main()