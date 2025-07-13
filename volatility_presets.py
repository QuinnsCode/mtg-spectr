#!/usr/bin/env python3
"""
Volatility tracking presets for different trading strategies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.data.trend_database import TrendDatabase
from mtg_card_pricing.config.settings import get_settings

def apply_preset(preset_name):
    """Apply predefined volatility tracking presets."""
    
    presets = {
        'spike_hunter': {
            'name': 'Spike Hunter',
            'description': 'Detect buyouts and sudden price spikes',
            'hours': 12,
            'percentage': 30,
            'absolute': 5.00,  # $5+ absolute change for spikes
            'monitoring_interval': 1,
            'min_price': 1.00
        },
        'day_trader': {
            'name': 'Day Trader',
            'description': 'Daily volatility for active trading',
            'hours': 24,
            'percentage': 15,
            'absolute': 2.00,  # $2+ changes for daily trading
            'monitoring_interval': 2,
            'min_price': 0.50
        },
        'swing_trader': {
            'name': 'Swing Trader',
            'description': 'Multi-day trends for swing positions',
            'hours': 72,
            'percentage': 25,
            'absolute': 3.00,  # $3+ changes for swing trading
            'monitoring_interval': 6,
            'min_price': 1.00
        },
        'tournament_tracker': {
            'name': 'Tournament Tracker',
            'description': 'Catch tournament-driven price movements',
            'hours': 48,
            'percentage': 20,
            'absolute': 2.50,  # $2.50+ for tournament effects
            'monitoring_interval': 3,
            'min_price': 2.00
        },
        'scalper': {
            'name': 'Scalper',
            'description': 'Ultra-short term movements',
            'hours': 6,
            'percentage': 15,
            'absolute': 1.00,  # $1+ for quick scalping
            'monitoring_interval': 1,
            'min_price': 5.00
        }
    }
    
    if preset_name not in presets:
        print(f"Error: Unknown preset '{preset_name}'")
        print(f"Available presets: {', '.join(presets.keys())}")
        return
    
    preset = presets[preset_name]
    
    print(f"MTG Card Pricing - Applying '{preset['name']}' Preset")
    print("=" * 60)
    print(f"Description: {preset['description']}")
    print()
    
    # Apply configuration
    trend_db = TrendDatabase()
    settings_manager = get_settings()
    
    # Update database configuration
    trend_db.set_config_value('trend_analysis_hours', str(preset['hours']))
    trend_db.set_config_value('percentage_alert_threshold', str(preset['percentage']))
    trend_db.set_config_value('absolute_alert_threshold', str(preset['absolute']))
    
    # Update settings
    settings_manager.settings.trend_tracker.monitoring_interval_hours = preset['monitoring_interval']
    settings_manager.settings.trend_tracker.percentage_alert_threshold = preset['percentage']
    settings_manager.settings.trend_tracker.absolute_alert_threshold = preset['absolute']
    settings_manager.settings.trend_tracker.min_price_threshold = preset['min_price']
    settings_manager.save_settings()
    
    print(f"✓ Time window: {preset['hours']} hours")
    print(f"✓ Percentage threshold: {preset['percentage']}%")
    print(f"✓ Absolute threshold: ${preset['absolute']}")
    print(f"✓ Monitoring interval: {preset['monitoring_interval']} hours")
    print(f"✓ Minimum price: ${preset['min_price']}")
    
    print(f"\nThis preset will:")
    print(f"  • Track {preset['hours']}-hour price movements")
    print(f"  • Alert on {preset['percentage']}%+ changes OR ${preset['absolute']}+ absolute changes")
    print(f"  • Check every {preset['monitoring_interval']} hours")
    print(f"  • Only monitor cards ≥ ${preset['min_price']}")
    
    # Show trading strategy info
    strategy_info = {
        'spike_hunter': [
            "Perfect for detecting buyouts and artificial spikes",
            "Catches cards that suddenly jump 30%+ in 12 hours",
            "Best during spoiler season or major announcements"
        ],
        'day_trader': [
            "Ideal for daily price movement monitoring",
            "Catches moderate volatility for quick trades", 
            "Good balance of frequency and signal quality"
        ],
        'swing_trader': [
            "Tracks multi-day trends for position trading",
            "Less frequent alerts but stronger signals",
            "Good for building medium-term positions"
        ],
        'tournament_tracker': [
            "Optimized for tournament meta shifts",
            "48-hour window catches weekend tournament effects",
            "Focus on competitive-level cards"
        ],
        'scalper': [
            "Ultra-fast movements for arbitrage",
            "High-frequency monitoring of expensive cards",
            "Requires constant attention but highest profit potential"
        ]
    }
    
    print(f"\nStrategy Notes:")
    for note in strategy_info[preset_name]:
        print(f"  • {note}")

def list_presets():
    """List all available volatility presets."""
    
    presets = [
        ('spike_hunter', 'Spike Hunter', '12h/30%', 'Detect buyouts and sudden spikes'),
        ('day_trader', 'Day Trader', '24h/15%', 'Daily volatility monitoring'),
        ('swing_trader', 'Swing Trader', '72h/25%', 'Multi-day trend tracking'),
        ('tournament_tracker', 'Tournament Tracker', '48h/20%', 'Tournament-driven movements'),
        ('scalper', 'Scalper', '6h/15%', 'Ultra-short term arbitrage')
    ]
    
    print("Available Volatility Presets:")
    print("=" * 60)
    print(f"{'Preset':<18} {'Name':<18} {'Window':<10} {'Description'}")
    print("-" * 60)
    
    for preset_id, name, window, desc in presets:
        print(f"{preset_id:<18} {name:<18} {window:<10} {desc}")
    
    print(f"\nUsage: python3 volatility_presets.py <preset_name>")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Apply volatility tracking presets')
    parser.add_argument('preset', nargs='?', help='Preset name to apply')
    parser.add_argument('--list', action='store_true', help='List available presets')
    
    args = parser.parse_args()
    
    if args.list or not args.preset:
        list_presets()
        return
    
    apply_preset(args.preset)

if __name__ == "__main__":
    main()