#!/usr/bin/env python3
"""
Clear old trending cards and force fresh analysis with new thresholds.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.data.trend_database import TrendDatabase
from mtg_card_pricing.services.price_monitor import PriceMonitorService

def clear_and_reanalyze():
    """Clear old trend results and run fresh analysis."""
    
    print("MTG Card Pricing - Clear Old Trends and Reanalyze")
    print("=" * 60)
    
    trend_db = TrendDatabase()
    
    # Check current database status
    with trend_db._get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM price_snapshots")
        total_snapshots = cursor.fetchone()[0]
        
        # Check for trend_alerts table
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='trend_alerts'
        """)
        has_alerts_table = cursor.fetchone() is not None
        
        if has_alerts_table:
            cursor = conn.execute("SELECT COUNT(*) FROM trend_alerts")
            total_alerts = cursor.fetchone()[0]
        else:
            total_alerts = 0
    
    print(f"\nCurrent Database Status:")
    print(f"  Price snapshots: {total_snapshots:,}")
    print(f"  Stored trend alerts: {total_alerts:,}")
    
    if total_snapshots == 0:
        print("\n❌ No price data in database - cannot analyze trends")
        print("The trend tracker needs price snapshots to detect trends.")
        print("Since snapshot collection was removed, you'll need to:")
        print("  1. Import price data from another source")
        print("  2. Or re-enable snapshot collection temporarily")
        return
    
    # Clear old trend alerts if they exist
    if has_alerts_table and total_alerts > 0:
        print(f"\n🧹 Clearing {total_alerts} old trend alerts...")
        with trend_db._get_connection() as conn:
            conn.execute("DELETE FROM trend_alerts")
            conn.commit()
        print("✓ Old trend alerts cleared")
    
    # Show current configuration
    print(f"\nCurrent Analysis Configuration:")
    service = PriceMonitorService()
    trend_hours = int(trend_db.get_config_value('trend_analysis_hours') or 24)
    absolute_threshold = float(trend_db.get_config_value('absolute_alert_threshold') or 100.0)
    
    print(f"  Percentage threshold: {service.config['percentage_alert_threshold']}%")
    print(f"  Absolute threshold: ${absolute_threshold}")
    print(f"  Time window: {trend_hours} hours")
    print(f"  Min price: ${service.config['min_price_threshold']}")
    
    # Run fresh analysis
    print(f"\n🔍 Running fresh trend analysis with new thresholds...")
    
    trending_cards = trend_db.find_trending_cards(
        min_percentage_change=service.config['percentage_alert_threshold'],
        min_absolute_change=absolute_threshold,
        min_price_threshold=service.config['min_price_threshold'],
        hours_back=trend_hours,
        max_cards=service.config['max_cards_per_cycle']
    )
    
    print(f"\n📊 Fresh Analysis Results:")
    print(f"Found {len(trending_cards)} cards meeting new criteria")
    
    if trending_cards:
        print(f"\nCards with {service.config['percentage_alert_threshold']}%+ changes:")
        print(f"{'#':<3} {'Card Name':<35} {'Set':<6} {'Change %':>10} {'Current $':>10}")
        print("-" * 70)
        
        for i, card in enumerate(trending_cards[:10], 1):  # Show top 10
            print(f"{i:<3} {card['card_name'][:34]:<35} {card['set_code']:<6} "
                  f"{card['percentage_change']:>9.1f}% ${card['price_current']:>9.2f}")
        
        if len(trending_cards) > 10:
            print(f"... and {len(trending_cards) - 10} more cards")
        
        # Check if any cards are still under the threshold (shouldn't happen)
        low_cards = [card for card in trending_cards if card['percentage_change'] < service.config['percentage_alert_threshold']]
        if low_cards:
            print(f"\n⚠️  WARNING: {len(low_cards)} cards detected below {service.config['percentage_alert_threshold']}% threshold")
            print("This suggests the OR condition with absolute threshold is still catching them")
            for card in low_cards[:3]:
                print(f"  {card['card_name']}: {card['percentage_change']:.1f}% (${card['absolute_change']:.2f} change)")
    
    else:
        print("\n✅ No cards found with current thresholds")
        print("This means:")
        print(f"  • No cards have {service.config['percentage_alert_threshold']}%+ changes in {trend_hours} hours")
        print(f"  • Market has been stable recently")
        print(f"  • You may want to lower thresholds or extend time window")
    
    print(f"\n" + "="*60)
    print("Next steps:")
    print("  1. Restart your trend tracker application to see fresh results")
    print("  2. If still seeing old data, the GUI may be caching results")
    print("  3. Check that the service is using the cleared database")
    print("="*60)

if __name__ == "__main__":
    clear_and_reanalyze()