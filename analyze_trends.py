#!/usr/bin/env python3
"""
Analyze current trend data to understand price movements.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.data.trend_database import TrendDatabase
from mtg_card_pricing.config.settings import get_settings
from datetime import datetime, timedelta

def analyze_trends():
    """Analyze current trends with different thresholds and time windows."""
    
    print("MTG Card Pricing - Trend Analysis")
    print("=" * 80)
    
    trend_db = TrendDatabase()
    settings = get_settings().settings.trend_tracker
    
    # Get database statistics
    with trend_db._get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM price_snapshots")
        total_snapshots = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(DISTINCT card_name) FROM price_snapshots")
        unique_cards = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM price_snapshots")
        min_time, max_time = cursor.fetchone()
    
    print(f"\nDatabase Statistics:")
    print(f"  Total price snapshots: {total_snapshots:,}")
    print(f"  Unique cards tracked: {unique_cards:,}")
    print(f"  Date range: {min_time} to {max_time}")
    
    # Test different time windows and thresholds
    time_windows = [24, 48, 72, 168]  # 1 day, 2 days, 3 days, 7 days
    thresholds = [10, 20, 30, 40, 50, 75, 100]
    
    print("\n" + "=" * 80)
    print("Trend Analysis by Time Window and Threshold")
    print("=" * 80)
    
    for hours in time_windows:
        print(f"\nTime Window: {hours} hours ({hours/24:.1f} days)")
        print("-" * 60)
        print(f"{'Threshold':<12} {'Cards Found':<15} {'Max Change %':<15} {'Top Card':<25}")
        print("-" * 60)
        
        for threshold in thresholds:
            trending = trend_db.find_trending_cards(
                min_percentage_change=threshold,
                min_absolute_change=0.01,  # Very low to focus on percentage
                min_price_threshold=settings.min_price_threshold,
                hours_back=hours,
                max_cards=1000
            )
            
            if trending:
                max_change = max(card['percentage_change'] for card in trending)
                top_card = next(card for card in trending if card['percentage_change'] == max_change)
                card_name = top_card['card_name'][:24]
                print(f"{threshold:>10}% {len(trending):>12} {max_change:>13.1f}% {card_name:<25}")
            else:
                print(f"{threshold:>10}% {0:>12} {'N/A':>15} {'No cards found':<25}")
    
    # Detailed analysis of current threshold
    print("\n" + "=" * 80)
    print(f"Detailed Analysis with Current Settings (20% threshold, 168 hours)")
    print("=" * 80)
    
    current_trending = trend_db.find_trending_cards(
        min_percentage_change=20.0,
        min_absolute_change=0.01,
        min_price_threshold=settings.min_price_threshold,
        hours_back=168,
        max_cards=1000
    )
    
    if current_trending:
        print(f"\nFound {len(current_trending)} trending cards")
        print("\nTop 20 by percentage change:")
        print(f"{'#':<3} {'Card Name':<35} {'Set':<6} {'Start $':<10} {'Current $':<10} {'Change %':<10} {'Change $':<10}")
        print("-" * 90)
        
        for i, card in enumerate(current_trending[:20], 1):
            print(f"{i:<3} {card['card_name'][:34]:<35} {card['set_code']:<6} "
                  f"${card['price_start']:<9.2f} ${card['price_current']:<9.2f} "
                  f"{card['percentage_change']:<9.1f}% ${card['absolute_change']:<9.2f}")
        
        # Distribution analysis
        print("\nPercentage Change Distribution:")
        ranges = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 75), (75, 100), (100, float('inf'))]
        
        for low, high in ranges:
            count = sum(1 for card in current_trending if low <= card['percentage_change'] < high)
            if count > 0:
                label = f"{low}-{high}%" if high != float('inf') else f"{low}%+"
                bar = "█" * min(count, 50)
                print(f"{label:<10} {count:>4} {bar}")
    else:
        print("\nNo trending cards found with current settings.")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("Recommendations:")
    print("=" * 80)
    
    if not current_trending or all(card['percentage_change'] < 50 for card in current_trending):
        print("✓ No cards with >50% change found. This could mean:")
        print("  1. The MTG market is relatively stable right now")
        print("  2. Major price spikes are rare and might need shorter time windows")
        print("  3. Consider monitoring high-volatility events (new set releases, tournaments)")
        print("\n✓ Suggested actions:")
        print("  - Keep the 20% threshold for general monitoring")
        print("  - Use shorter time windows (24-48 hours) to catch quick spikes")
        print("  - Set up alerts for specific high-value cards you're interested in")
        print("  - Monitor during spoiler season or major tournament weekends")

if __name__ == "__main__":
    analyze_trends()