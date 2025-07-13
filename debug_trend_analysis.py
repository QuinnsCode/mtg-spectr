#!/usr/bin/env python3
"""
Debug script to identify why trend analysis gets stuck.
This script will help identify performance bottlenecks and hanging issues.
"""

import sys
import os
import time
import sqlite3
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.data.trend_database import TrendDatabase

def debug_database_performance():
    """Debug database performance issues."""
    
    print("=== DATABASE PERFORMANCE DEBUG ===")
    
    # Initialize database
    trend_db = TrendDatabase()
    
    # Check database size and card count
    print("\n1. Database Statistics:")
    try:
        with trend_db._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM price_snapshots")
            total_records = cursor.fetchone()[0]
            print(f"   Total price records: {total_records:,}")
            
            cursor = conn.execute("SELECT COUNT(DISTINCT card_name) FROM price_snapshots")
            unique_cards = cursor.fetchone()[0]
            print(f"   Unique cards: {unique_cards:,}")
            
            cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM price_snapshots")
            min_time, max_time = cursor.fetchone()
            print(f"   Date range: {min_time} to {max_time}")
            
            # Check recent data
            cutoff_time = datetime.now() - timedelta(hours=24)
            cursor = conn.execute("SELECT COUNT(*) FROM price_snapshots WHERE timestamp > ?", (cutoff_time,))
            recent_records = cursor.fetchone()[0]
            print(f"   Recent records (24h): {recent_records:,}")
            
            # Check distinct cards in recent data
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT card_name) 
                FROM price_snapshots 
                WHERE timestamp > ? AND price_usd >= 0.50
            """, (cutoff_time,))
            recent_cards = cursor.fetchone()[0]
            print(f"   Recent cards (24h, $0.50+): {recent_cards:,}")
            
    except Exception as e:
        print(f"   Error checking database: {e}")
    
    # Test the problematic query
    print("\n2. Testing Problematic Query:")
    try:
        start_time = time.time()
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        with trend_db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT DISTINCT card_name, set_code, collector_number, is_foil
                FROM price_snapshots
                WHERE timestamp > ? AND price_usd >= ?
            """, (cutoff_time, 0.50))
            
            cards = cursor.fetchall()
            query_time = time.time() - start_time
            
            print(f"   Query returned {len(cards):,} cards in {query_time:.2f} seconds")
            
            if len(cards) > 100:
                print(f"   WARNING: Large result set ({len(cards)} cards) will cause N+1 query problem!")
                print(f"   Each card requires individual trend calculation - this could take hours!")
            
    except Exception as e:
        print(f"   Error running query: {e}")
    
    # Test trend calculation performance
    print("\n3. Testing Trend Calculation Performance:")
    try:
        # Get a sample of cards to test
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        with trend_db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT DISTINCT card_name, set_code, collector_number, is_foil
                FROM price_snapshots
                WHERE timestamp > ? AND price_usd >= ?
                LIMIT 10
            """, (cutoff_time, 0.50))
            
            sample_cards = cursor.fetchall()
        
        print(f"   Testing trend calculation on {len(sample_cards)} sample cards...")
        
        total_time = 0
        for i, card in enumerate(sample_cards):
            start_time = time.time()
            trend = trend_db.calculate_trend(
                card['card_name'], card['set_code'], 
                card['collector_number'], card['is_foil']
            )
            calc_time = time.time() - start_time
            total_time += calc_time
            
            print(f"   Card {i+1}: {card['card_name']} - {calc_time:.3f}s")
            
            if calc_time > 1.0:
                print(f"     WARNING: Slow trend calculation!")
        
        avg_time = total_time / len(sample_cards) if sample_cards else 0
        print(f"   Average time per card: {avg_time:.3f}s")
        
        # Estimate total time for all cards
        if avg_time > 0:
            with trend_db._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT card_name) 
                    FROM price_snapshots 
                    WHERE timestamp > ? AND price_usd >= ?
                """, (cutoff_time, 0.50))
                total_cards = cursor.fetchone()[0]
                
                estimated_time = total_cards * avg_time
                print(f"   Estimated total time for {total_cards} cards: {estimated_time:.1f}s ({estimated_time/60:.1f} minutes)")
                
                if estimated_time > 300:  # 5 minutes
                    print(f"   ERROR: This will take too long and likely cause the hang!")
            
    except Exception as e:
        print(f"   Error testing trend calculation: {e}")

def debug_find_trending_cards():
    """Debug the find_trending_cards method specifically."""
    
    print("\n=== FIND TRENDING CARDS DEBUG ===")
    
    trend_db = TrendDatabase()
    
    print("\n1. Testing find_trending_cards with timeout...")
    start_time = time.time()
    
    try:
        # Set a timeout for the operation
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Operation timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second timeout
        
        trending_cards = trend_db.find_trending_cards(
            min_percentage_change=20.0,
            min_absolute_change=0.01,
            min_price_threshold=0.50
        )
        
        signal.alarm(0)  # Cancel timeout
        
        elapsed = time.time() - start_time
        print(f"   Found {len(trending_cards)} trending cards in {elapsed:.2f}s")
        
    except TimeoutError:
        print("   ERROR: find_trending_cards timed out after 30 seconds!")
        print("   This confirms the hanging issue is in this method.")
        
    except Exception as e:
        print(f"   Error in find_trending_cards: {e}")

def main():
    """Main debug function."""
    
    print("MTG Card Pricing - Trend Analysis Debug")
    print("=" * 50)
    
    debug_database_performance()
    debug_find_trending_cards()
    
    print("\n=== RECOMMENDATIONS ===")
    print("1. Add database indexes on (timestamp, price_usd) and (card_name, set_code)")
    print("2. Implement batching to process cards in groups of 100-500")
    print("3. Add timeout mechanisms to prevent infinite hangs")
    print("4. Consider optimizing the trend calculation query")
    print("5. Add progress indicators for long-running operations")

if __name__ == "__main__":
    main()