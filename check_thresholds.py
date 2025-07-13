#!/usr/bin/env python3
"""
Check current trend detection thresholds and configuration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.data.trend_database import TrendDatabase
from mtg_card_pricing.config.settings import get_settings
from mtg_card_pricing.services.price_monitor import PriceMonitorService

def check_current_thresholds():
    """Check all current threshold configurations."""
    
    print("MTG Card Pricing - Current Threshold Configuration")
    print("=" * 60)
    
    # Check database configuration
    print("\n1. Database Configuration:")
    trend_db = TrendDatabase()
    
    db_configs = [
        'percentage_alert_threshold',
        'trend_analysis_hours',
        'absolute_alert_threshold'
    ]
    
    for config_key in db_configs:
        value = trend_db.get_config_value(config_key)
        print(f"   {config_key}: {value}")
    
    # Check settings file
    print("\n2. Settings File Configuration:")
    settings_manager = get_settings()
    trend_settings = settings_manager.settings.trend_tracker
    
    print(f"   percentage_alert_threshold: {trend_settings.percentage_alert_threshold}")
    print(f"   monitoring_interval_hours: {trend_settings.monitoring_interval_hours}")
    print(f"   min_price_threshold: {trend_settings.min_price_threshold}")
    print(f"   absolute_alert_threshold: {trend_settings.absolute_alert_threshold}")
    
    # Check service configuration
    print("\n3. Service Configuration (when loaded):")
    service = PriceMonitorService()
    
    print(f"   percentage_alert_threshold: {service.config['percentage_alert_threshold']}")
    print(f"   monitoring_interval_hours: {service.config['monitoring_interval_hours']}")
    print(f"   min_price_threshold: {service.config['min_price_threshold']}")
    
    # Test what find_trending_cards would use
    print("\n4. What find_trending_cards() would actually use:")
    
    # Get the actual parameters being passed
    trend_hours = int(trend_db.get_config_value('trend_analysis_hours') or 24)
    percentage_threshold = service.config['percentage_alert_threshold']
    
    print(f"   Time window: {trend_hours} hours")
    print(f"   Percentage threshold: {percentage_threshold}%")
    print(f"   Min price: ${service.config['min_price_threshold']}")
    
    # Test a sample query
    print("\n5. Testing trend detection with current settings:")
    
    trending = trend_db.find_trending_cards(
        min_percentage_change=percentage_threshold,
        min_absolute_change=0.01,
        min_price_threshold=service.config['min_price_threshold'],
        hours_back=trend_hours,
        max_cards=10
    )
    
    if trending:
        print(f"   Found {len(trending)} trending cards with current thresholds")
        print(f"   Top card: {trending[0]['card_name']} ({trending[0]['percentage_change']:.1f}%)")
    else:
        print("   No trending cards found with current thresholds")
    
    # Check if there's a mismatch
    print("\n6. Configuration Analysis:")
    
    if trend_settings.percentage_alert_threshold != percentage_threshold:
        print(f"   ⚠️  MISMATCH: Settings file has {trend_settings.percentage_alert_threshold}% but service uses {percentage_threshold}%")
    else:
        print(f"   ✅ Settings consistent: {percentage_threshold}%")
    
    # Show how to fix it
    if percentage_threshold < 30:
        print(f"\n7. To fix low threshold ({percentage_threshold}%):")
        print(f"   Run: python3 volatility_presets.py spike_hunter")
        print(f"   Or: python3 adjust_trend_threshold.py --percentage 50")

if __name__ == "__main__":
    check_current_thresholds()