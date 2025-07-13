#!/usr/bin/env python3
"""
Debug why cards with low percentage changes are being detected.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.data.trend_database import TrendDatabase

def debug_low_threshold():
    """Debug why low percentage cards are being detected."""
    
    print("MTG Card Pricing - Debug Low Threshold Detection")
    print("=" * 60)
    
    trend_db = TrendDatabase()
    
    # Check what's actually in the database
    with trend_db._get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM price_snapshots")
        total_snapshots = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(DISTINCT card_name) FROM price_snapshots")
        unique_cards = cursor.fetchone()[0]
        
        print(f"\nDatabase Contents:")
        print(f"  Total snapshots: {total_snapshots:,}")
        print(f"  Unique cards: {unique_cards:,}")
    
    if total_snapshots == 0:
        print("\n❌ No price data in database - can't analyze trends")
        return
    
    # Test different thresholds to see what cards are being found
    print(f"\nTesting different thresholds:")
    
    thresholds_to_test = [5, 10, 15, 20, 25, 30, 40, 50]
    
    for threshold in thresholds_to_test:
        cards = trend_db.find_trending_cards(
            min_percentage_change=threshold,
            min_absolute_change=0.01,
            min_price_threshold=0.50,
            hours_back=12,  # Use current window
            max_cards=1000
        )
        
        if cards:
            max_change = max(card['percentage_change'] for card in cards)
            print(f"  {threshold:>2}% threshold: {len(cards):>3} cards (max change: {max_change:.1f}%)")
        else:
            print(f"  {threshold:>2}% threshold: {0:>3} cards")
    
    # Show the actual cards being detected with current 30% threshold
    print(f"\nCards detected with 30% threshold:")
    
    trending_30 = trend_db.find_trending_cards(
        min_percentage_change=30.0,
        min_absolute_change=0.01,
        min_price_threshold=0.50,
        hours_back=12,
        max_cards=20
    )
    
    if trending_30:
        print(f"Found {len(trending_30)} cards:")
        print(f"{'Card Name':<35} {'Set':<6} {'Change %':>10} {'Start $':>10} {'Current $':>10}")
        print("-" * 75)
        
        for card in trending_30:
            print(f"{card['card_name'][:34]:<35} {card['set_code']:<6} "
                  f"{card['percentage_change']:>9.1f}% "
                  f"${card['price_start']:>9.2f} ${card['price_current']:>9.2f}")
    else:
        print("No cards found with 30% threshold")
    
    # Check if maybe it's an OR condition issue
    print(f"\nDebugging trend detection logic:")
    
    # Test with very high absolute threshold to see if that's the issue
    trending_debug = trend_db.find_trending_cards(
        min_percentage_change=30.0,
        min_absolute_change=100.0,  # Very high to effectively disable
        min_price_threshold=0.50,
        hours_back=12,
        max_cards=20
    )
    
    print(f"With 30% percentage AND $100 absolute: {len(trending_debug)} cards")
    
    # Check the actual logic in find_trending_cards
    print(f"\nChecking trend detection logic:")
    print(f"The condition is: (percentage_change >= {30.0} OR absolute_change >= {0.01})")
    print(f"This means ANY card with $0.01+ change will be included!")
    print(f"That's why you're seeing low percentage cards.")

if __name__ == "__main__":
    debug_low_threshold()