#!/usr/bin/env python3
"""
Configure trend tracker to focus only on percentage changes, ignoring small absolute changes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.data.trend_database import TrendDatabase
from mtg_card_pricing.config.settings import get_settings

def apply_percentage_only(percentage=50, hours=24):
    """
    Configure trend tracker to only track percentage changes.
    Sets absolute threshold very high to effectively disable it.
    """
    
    print(f"MTG Card Pricing - Percentage-Only Configuration")
    print("=" * 60)
    print(f"Focus: {percentage}%+ percentage changes only")
    print(f"Time window: {hours} hours")
    
    # Configuration
    trend_db = TrendDatabase()
    settings_manager = get_settings()
    
    # Set database configuration
    trend_db.set_config_value('trend_analysis_hours', str(hours))
    trend_db.set_config_value('percentage_alert_threshold', str(percentage))
    trend_db.set_config_value('absolute_alert_threshold', '1000.0')  # Effectively disabled
    
    # Update settings
    settings_manager.settings.trend_tracker.percentage_alert_threshold = percentage
    settings_manager.settings.trend_tracker.absolute_alert_threshold = 1000.0  # Effectively disabled
    settings_manager.settings.trend_tracker.monitoring_interval_hours = 2
    settings_manager.settings.trend_tracker.min_price_threshold = 1.0
    settings_manager.save_settings()
    
    print(f"\n✅ Configuration Applied:")
    print(f"   Percentage threshold: {percentage}%")
    print(f"   Absolute threshold: $1000 (effectively disabled)")
    print(f"   Time window: {hours} hours")
    print(f"   Minimum price: $1.00")
    print(f"   Monitoring interval: 2 hours")
    
    print(f"\n🎯 This will ONLY detect cards with:")
    print(f"   • {percentage}%+ percentage increase in {hours} hours")
    print(f"   • Cards worth $1.00 or more")
    print(f"   • Ignores small dollar amount changes")
    
    print(f"\n📈 Perfect for detecting:")
    print(f"   • Buyout spikes (sudden {percentage}%+ jumps)")
    print(f"   • Speculation bubbles")
    print(f"   • Tournament breakouts")
    print(f"   • Major price corrections")

def main():
    """Main function with arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Configure percentage-only trend detection')
    parser.add_argument('--percentage', type=float, default=50.0,
                        help='Minimum percentage change (default: 50.0)')
    parser.add_argument('--hours', type=int, default=24,
                        help='Time window in hours (default: 24)')
    
    args = parser.parse_args()
    
    if args.percentage < 5 or args.percentage > 500:
        print("Error: Percentage must be between 5 and 500")
        return
    
    if args.hours < 1 or args.hours > 168:
        print("Error: Hours must be between 1 and 168")
        return
    
    apply_percentage_only(args.percentage, args.hours)

if __name__ == "__main__":
    main()