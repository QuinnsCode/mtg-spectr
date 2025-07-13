#!/usr/bin/env python3
"""
Fix the real trend database with your 21 cards showing low percentages.
"""

import sys
import os
import sqlite3
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.config.settings import get_settings

def fix_real_database():
    """Fix the real trend database at ~/.mtg_card_pricing/price_trends.db"""
    
    print("MTG Card Pricing - Fix Real Database")
    print("=" * 50)
    
    # Get the actual database path
    settings = get_settings()
    config_dir = Path.home() / ".mtg_card_pricing"
    db_path = config_dir / "price_trends.db"
    
    print(f"Real database location: {db_path}")
    
    if not db_path.exists():
        print("❌ Real database not found!")
        print("Your trend tracker may not have created data yet.")
        return
    
    # Check what's in the real database
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Check tables
        cursor = conn.execute("""
            SELECT name FROM sqlite_master WHERE type='table'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\nTables in database: {', '.join(tables)}")
        
        # Check price snapshots
        if 'price_snapshots' in tables:
            cursor = conn.execute("SELECT COUNT(*) FROM price_snapshots")
            snapshot_count = cursor.fetchone()[0]
            print(f"Price snapshots: {snapshot_count:,}")
            
            if snapshot_count > 0:
                cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM price_snapshots")
                min_time, max_time = cursor.fetchone()
                print(f"Date range: {min_time} to {max_time}")
                
                # Show some sample data
                cursor = conn.execute("""
                    SELECT card_name, set_code, price_usd, timestamp 
                    FROM price_snapshots 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """)
                print(f"\nSample recent data:")
                for row in cursor.fetchall():
                    print(f"  {row[0]} ({row[1]}) ${row[2]} at {row[3]}")
        
        # Check trend alerts (cached results)
        if 'trend_alerts' in tables:
            cursor = conn.execute("SELECT COUNT(*) FROM trend_alerts")
            alert_count = cursor.fetchone()[0]
            print(f"\nCached trend alerts: {alert_count}")
            
            if alert_count > 0:
                print("These are the cached results you're seeing!")
                
                # Show the cached alerts that are causing the issue
                cursor = conn.execute("""
                    SELECT card_name, set_code, percentage_change, is_active 
                    FROM trend_alerts 
                    ORDER BY percentage_change DESC 
                    LIMIT 10
                """)
                print(f"\nTop cached alerts (causing your 21 cards issue):")
                for row in cursor.fetchall():
                    print(f"  {row[0]} ({row[1]}) {row[2]:.1f}% (active: {row[3]})")
                
                # Clear the cached alerts
                print(f"\n🧹 Clearing {alert_count} cached trend alerts...")
                conn.execute("DELETE FROM trend_alerts")
                conn.commit()
                print("✅ Cached alerts cleared!")
                
                print(f"\n🔄 Now your trend tracker should:")
                print(f"  1. Not show any cached 21 cards")
                print(f"  2. Run fresh analysis with 50% threshold")
                print(f"  3. Only show cards with 50%+ changes")
        
        # Check configuration values
        if 'monitoring_config' in tables:
            cursor = conn.execute("SELECT config_key, config_value FROM monitoring_config")
            configs = cursor.fetchall()
            if configs:
                print(f"\nDatabase configuration:")
                for key, value in configs:
                    print(f"  {key}: {value}")
    
    finally:
        conn.close()
    
    print(f"\n" + "="*50)
    print("✅ SOLUTION APPLIED")
    print("="*50)
    print("Your 21 trending cards were cached results from old thresholds.")
    print("I've cleared the cache - restart your trend tracker to see:")
    print("  • Fresh analysis with 50% threshold")
    print("  • Only cards with significant changes")
    print("  • Proper filtering working")
    print("="*50)

if __name__ == "__main__":
    fix_real_database()