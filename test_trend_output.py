#!/usr/bin/env python3
"""
Test the trend tracker output to ensure it's working correctly.
Creates test data and verifies the output matches expectations.
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.data.trend_database import TrendDatabase
from mtg_card_pricing.services.price_monitor import PriceMonitorService

def create_test_data():
    """Create test price data to verify trend detection."""
    
    print("Creating test price data...")
    
    trend_db = TrendDatabase()
    
    # Clear existing data
    with trend_db._get_connection() as conn:
        conn.execute("DELETE FROM price_snapshots")
        conn.commit()
    
    # Create test scenarios
    now = datetime.now()
    
    test_cards = [
        # Card that should NOT be detected (only 10% change)
        {
            'name': 'Low Change Card',
            'set': 'TST',
            'collector': '001',
            'old_price': 10.00,
            'new_price': 11.00,  # 10% change
            'hours_ago': 12
        },
        # Card that SHOULD be detected (60% change)
        {
            'name': 'High Change Card',
            'set': 'TST', 
            'collector': '002',
            'old_price': 5.00,
            'new_price': 8.00,  # 60% change
            'hours_ago': 12
        },
        # Card with exactly 50% change (should be detected)
        {
            'name': 'Exactly 50 Percent Card',
            'set': 'TST',
            'collector': '003', 
            'old_price': 2.00,
            'new_price': 3.00,  # 50% change
            'hours_ago': 12
        },
        # Card with small absolute change but high percentage (should be detected)
        {
            'name': 'Small Dollar Big Percent',
            'set': 'TST',
            'collector': '004',
            'old_price': 1.00,
            'new_price': 2.00,  # 100% change but only $1
            'hours_ago': 12
        },
        # Card under minimum price threshold (should be ignored)
        {
            'name': 'Too Cheap Card',
            'set': 'TST',
            'collector': '005',
            'old_price': 0.50,
            'new_price': 1.00,  # 100% change but under $1 minimum
            'hours_ago': 12
        }
    ]
    
    # Insert test data
    with trend_db._get_connection() as conn:
        for card in test_cards:
            # Insert old price
            old_time = now - timedelta(hours=card['hours_ago'])
            conn.execute("""
                INSERT INTO price_snapshots 
                (card_name, set_code, collector_number, is_foil, price_usd, timestamp, market_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (card['name'], card['set'], card['collector'], False, 
                  card['old_price'], old_time.isoformat(), 'test'))
            
            # Insert new price  
            conn.execute("""
                INSERT INTO price_snapshots 
                (card_name, set_code, collector_number, is_foil, price_usd, timestamp, market_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (card['name'], card['set'], card['collector'], False, 
                  card['new_price'], now.isoformat(), 'test'))
        
        conn.commit()
    
    print(f"✓ Created test data for {len(test_cards)} cards")
    return test_cards

def test_current_configuration():
    """Test the current trend detection configuration."""
    
    print("\n" + "="*80)
    print("TESTING CURRENT CONFIGURATION")
    print("="*80)
    
    trend_db = TrendDatabase()
    
    # Show current configuration
    print("\nCurrent Configuration:")
    percentage_threshold = trend_db.get_config_value('percentage_alert_threshold')
    absolute_threshold = trend_db.get_config_value('absolute_alert_threshold') 
    hours_back = trend_db.get_config_value('trend_analysis_hours')
    
    print(f"  Percentage threshold: {percentage_threshold}%")
    print(f"  Absolute threshold: ${absolute_threshold}")
    print(f"  Time window: {hours_back} hours")
    
    # Test trend detection
    print(f"\nRunning find_trending_cards()...")
    
    trending = trend_db.find_trending_cards(
        min_percentage_change=float(percentage_threshold),
        min_absolute_change=float(absolute_threshold),
        min_price_threshold=1.0,
        hours_back=int(hours_back),
        max_cards=1000
    )
    
    print(f"\nResults: Found {len(trending)} trending cards")
    
    if trending:
        print(f"\nDetailed Results:")
        print(f"{'Card Name':<25} {'Change %':>10} {'Start $':>10} {'Current $':>10} {'Absolute':>10}")
        print("-" * 75)
        
        for card in trending:
            print(f"{card['card_name']:<25} {card['percentage_change']:>9.1f}% "
                  f"${card['price_start']:>9.2f} ${card['price_current']:>9.2f} "
                  f"${card['absolute_change']:>9.2f}")
    
    return trending

def test_service_integration():
    """Test the price monitor service integration."""
    
    print(f"\n" + "="*80)
    print("TESTING SERVICE INTEGRATION")
    print("="*80)
    
    service = PriceMonitorService()
    
    # Show service configuration
    print(f"\nService Configuration:")
    print(f"  Percentage threshold: {service.config['percentage_alert_threshold']}%")
    print(f"  Min price threshold: ${service.config['min_price_threshold']}")
    
    # Run the analysis cycle
    print(f"\nRunning service analysis cycle...")
    service._analyze_trends_and_alerts()
    
    print(f"\nService Results:")
    print(f"  Trends detected: {service.stats.trends_detected}")
    print(f"  Alerts generated: {service.stats.alerts_generated}")

def verify_expected_results(test_cards, trending_results):
    """Verify the results match what we expect."""
    
    print(f"\n" + "="*80)
    print("VERIFYING EXPECTED RESULTS")
    print("="*80)
    
    print(f"\nTest Card Analysis:")
    
    for card in test_cards:
        percentage_change = ((card['new_price'] - card['old_price']) / card['old_price']) * 100
        should_detect = (
            percentage_change >= 50.0 and  # Above percentage threshold
            card['new_price'] >= 1.0      # Above minimum price
        )
        
        actually_detected = any(
            result['card_name'] == card['name'] 
            for result in trending_results
        )
        
        status = "✓" if should_detect == actually_detected else "✗"
        expect_text = "SHOULD detect" if should_detect else "should NOT detect"
        actual_text = "WAS detected" if actually_detected else "was NOT detected"
        
        print(f"  {status} {card['name']:<25} {percentage_change:>6.1f}% - {expect_text}, {actual_text}")
    
    # Summary
    correct_predictions = sum(1 for card in test_cards
                            if ((((card['new_price'] - card['old_price']) / card['old_price']) * 100 >= 50.0 
                                and card['new_price'] >= 1.0) == 
                               any(result['card_name'] == card['name'] for result in trending_results)))
    
    print(f"\nAccuracy: {correct_predictions}/{len(test_cards)} predictions correct")
    
    if correct_predictions == len(test_cards):
        print("🎉 ALL TESTS PASSED - Trend detection is working correctly!")
        return True
    else:
        print("❌ SOME TESTS FAILED - There may be configuration issues")
        return False

def main():
    """Main test function."""
    
    print("MTG Card Pricing - Trend Output Verification Test")
    print("="*80)
    print("This test will create sample data and verify trend detection works correctly.")
    
    try:
        # Create test data
        test_cards = create_test_data()
        
        # Test current configuration
        trending_results = test_current_configuration()
        
        # Test service integration  
        test_service_integration()
        
        # Verify results
        success = verify_expected_results(test_cards, trending_results)
        
        print(f"\n" + "="*80)
        if success:
            print("✅ TREND TRACKER IS WORKING CORRECTLY")
            print("The output you see should only include cards with 50%+ changes")
        else:
            print("❌ TREND TRACKER HAS ISSUES")
            print("The configuration may not be applied correctly")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()