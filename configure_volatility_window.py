#!/usr/bin/env python3
"""
Configure trend analysis for volatile price movements with shorter time windows.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.data.trend_database import TrendDatabase
from mtg_card_pricing.services.price_monitor import PriceMonitorService
from mtg_card_pricing.config.settings import get_settings

def configure_volatility_tracking(hours_back=24, percentage_threshold=20.0):
    """
    Configure the trend tracker for volatile, short-term price movements.
    
    Args:
        hours_back: Time window in hours (default 24 for daily volatility)
        percentage_threshold: Minimum percentage change to track
    """
    
    print("MTG Card Pricing - Volatility Configuration")
    print("=" * 50)
    print(f"\nConfiguring for {hours_back}-hour volatility tracking")
    print(f"This will capture rapid price movements and spikes")
    
    # Update configuration in database
    trend_db = TrendDatabase()
    
    # Store the time window configuration
    trend_db.set_config_value('trend_analysis_hours', str(hours_back))
    trend_db.set_config_value('percentage_alert_threshold', str(percentage_threshold))
    
    print(f"\n✓ Updated trend analysis window to {hours_back} hours")
    print(f"✓ Percentage threshold set to {percentage_threshold}%")
    
    # Update monitoring interval to be more frequent for short windows
    if hours_back <= 24:
        recommended_interval = 1  # Check every hour for 24h window
    elif hours_back <= 48:
        recommended_interval = 2  # Check every 2 hours for 48h window
    else:
        recommended_interval = 6  # Default 6 hours for longer windows
    
    settings_manager = get_settings()
    settings_manager.settings.trend_tracker.monitoring_interval_hours = recommended_interval
    settings_manager.save_settings()
    
    print(f"✓ Monitoring interval set to {recommended_interval} hours")
    
    # Show what this configuration will capture
    print(f"\nThis configuration will:")
    print(f"  • Track price changes over the last {hours_back} hours only")
    print(f"  • Alert on changes ≥ {percentage_threshold}%")
    print(f"  • Check for new trends every {recommended_interval} hours")
    print(f"  • Capture short-term spikes and volatile movements")
    
    # Analyze what we would find with this configuration
    print(f"\n" + "="*50)
    print(f"Analyzing current data with {hours_back}-hour window...")
    
    try:
        trending = trend_db.find_trending_cards(
            min_percentage_change=percentage_threshold,
            min_absolute_change=0.01,
            min_price_threshold=0.50,
            hours_back=hours_back,
            max_cards=100
        )
        
        if trending:
            print(f"\nFound {len(trending)} cards with ≥{percentage_threshold}% change in {hours_back} hours:")
            print(f"\nTop 10 volatile cards:")
            print(f"{'Card':<35} {'Set':<6} {'Change %':>10} {'$/day':>10}")
            print("-" * 65)
            
            for card in trending[:10]:
                # Calculate daily rate of change
                daily_rate = (card['percentage_change'] / hours_back) * 24
                print(f"{card['card_name'][:34]:<35} {card['set_code']:<6} "
                      f"{card['percentage_change']:>9.1f}% {daily_rate:>9.1f}%")
        else:
            print(f"\nNo cards found with ≥{percentage_threshold}% change in {hours_back} hours")
            print("This might mean:")
            print("  • The market has been stable recently")
            print("  • You need more price snapshots to detect trends")
            print("  • Try a lower percentage threshold")
    
    except Exception as e:
        print(f"\nError analyzing trends: {e}")
    
    print(f"\n" + "="*50)
    print("Volatility Tracking Recommendations:")
    print(f"  • For day-trading style monitoring: Use 24-hour window")
    print(f"  • For weekly volatility: Use 48-72 hour window")
    print(f"  • For spike detection: Use 12-24 hour window with 15-20% threshold")
    print(f"  • For buyout detection: Use 6-12 hour window with 30%+ threshold")

def main():
    """Main function with command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Configure trend tracking for volatile price movements'
    )
    parser.add_argument(
        '--hours', 
        type=int, 
        default=24,
        help='Time window in hours (default: 24 for daily volatility)'
    )
    parser.add_argument(
        '--percentage', 
        type=float, 
        default=20.0,
        help='Minimum percentage change threshold (default: 20.0)'
    )
    
    args = parser.parse_args()
    
    if args.hours < 1 or args.hours > 168:
        print("Error: Hours must be between 1 and 168")
        return
    
    if args.percentage < 1 or args.percentage > 500:
        print("Error: Percentage must be between 1 and 500")
        return
    
    configure_volatility_tracking(args.hours, args.percentage)

if __name__ == "__main__":
    main()