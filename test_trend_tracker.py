#!/usr/bin/env python3
"""
Test script for the MTG Card Price Trend Tracker system.

This script tests the core functionality of the trend tracking system
without requiring the full GUI to be running.
"""

import sys
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from data.trend_database import TrendDatabase
from analysis.trend_analyzer import TrendAnalyzer, TrendType
from services.price_monitor import PriceMonitorService
from services.alert_system import AlertSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_operations():
    """Test database operations."""
    logger.info("Testing database operations...")
    
    # Initialize database (use temp file since in-memory doesn't persist across connections)
    import tempfile
    import os
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    db = TrendDatabase(temp_db.name)
    
    # Debug: Check if tables exist
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Tables in database: {[table[0] for table in tables]}")
    
    # Test recording price snapshots
    test_cards = [
        ("Lightning Bolt", "lea", "162", 5.99, False),
        ("Lightning Bolt", "lea", "162", 6.25, False),
        ("Lightning Bolt", "lea", "162", 6.50, False),
        ("Black Lotus", "lea", "232", 15000.00, False),
        ("Black Lotus", "lea", "232", 16000.00, False),
        ("Bane of Progress", "fic", "123", 0.90, False),
    ]
    
    # Record snapshots with some time spacing
    for i, (name, set_code, num, price, foil) in enumerate(test_cards):
        success = db.record_price_snapshot(name, set_code, num, price, foil)
        assert success, f"Failed to record snapshot for {name}"
        
        # Add small delay to create different timestamps
        time.sleep(0.1)
    
    # Test price history retrieval
    history = db.get_price_history("Lightning Bolt", "lea", "162", False)
    assert len(history) == 3, f"Expected 3 history records, got {len(history)}"
    
    # Test trend calculation
    trend = db.calculate_trend("Lightning Bolt", "lea", "162", False)
    assert trend is not None, "Trend calculation failed"
    assert trend['percentage_change'] > 0, "Expected positive percentage change"
    
    # Test finding trending cards
    trending = db.find_trending_cards(min_percentage_change=5.0)
    assert len(trending) > 0, "Should find at least one trending card"
    
    # Cleanup
    os.unlink(temp_db.name)
    
    logger.info("✓ Database operations test passed")

def test_trend_analysis():
    """Test trend analysis algorithms."""
    logger.info("Testing trend analysis...")
    
    analyzer = TrendAnalyzer()
    
    # Create mock price history data
    base_time = datetime.now() - timedelta(hours=24)
    price_history = []
    
    # Simulate a steady upward trend (lower volatility)
    prices = [5.00, 5.30, 5.60, 5.90, 6.20, 6.50, 6.80]
    for i, price in enumerate(prices):
        timestamp = base_time + timedelta(hours=i * 3)
        price_history.append({
            'price_usd': price,
            'timestamp': timestamp.isoformat(),
            'card_name': 'Test Card',
            'set_code': 'tst',
            'collector_number': '001',
            'is_foil': False
        })
    
    # Analyze the trend
    analysis = analyzer.analyze_trend(price_history)
    assert analysis is not None, "Trend analysis failed"
    
    logger.info(f"Analysis result: trend_type={analysis.trend_type}, percentage_change={analysis.percentage_change}")
    assert analysis.trend_type == TrendType.UPWARD, f"Should detect upward trend, got {analysis.trend_type}"
    assert analysis.percentage_change > 30, "Should detect significant percentage change"
    
    # Test fast mover detection  
    fast_movers = analyzer.identify_fast_movers([analysis], min_percentage=20.0)
    assert len(fast_movers) == 1, "Should identify the card as a fast mover"
    
    # Test alert score calculation
    alert_score = analyzer.calculate_alert_score(analysis)
    logger.info(f"Alert score: {alert_score}")
    assert alert_score > 30, "Should generate a reasonable alert score"
    
    logger.info("✓ Trend analysis test passed")

def test_price_monitor_config():
    """Test price monitoring service configuration."""
    logger.info("Testing price monitor configuration...")
    
    monitor = PriceMonitorService()
    
    # Test configuration updates
    original_interval = monitor.config['monitoring_interval_hours']
    monitor.update_config(monitoring_interval_hours=12)
    assert monitor.config['monitoring_interval_hours'] == 12, "Config update failed"
    
    # Test statistics
    stats = monitor.get_monitoring_stats()
    assert 'service_stats' in stats, "Missing service stats"
    assert 'config' in stats, "Missing config in stats"
    
    logger.info("✓ Price monitor configuration test passed")

def test_alert_system():
    """Test alert system functionality."""
    logger.info("Testing alert system...")
    
    alert_system = AlertSystem()
    
    # Test configuration
    alert_system.update_config(
        enabled=True,
        system_tray_enabled=False,  # Disable for testing
        max_alerts_per_hour=20,
        quiet_hours_start=23,  # 11 PM  
        quiet_hours_end=7      # 7 AM (avoid current time)
    )
    
    # Test alert processing with mock data
    test_alert_data = {
        'card_name': 'Test Alert Card',
        'set_code': 'tst',
        'percentage_change': 45.5,
        'absolute_change': 2.50,
        'price_current': 7.99,
        'is_foil': False,
        'alert_score': 75
    }
    
    # Process the alert (should succeed)
    result = alert_system.process_trend_alert(test_alert_data)
    logger.info(f"Alert processing result: {result}")
    
    if not result:
        logger.info(f"Alert config: enabled={alert_system.config.enabled}")
        logger.info(f"Is quiet hours: {alert_system._is_quiet_hours()}")
        logger.info(f"Hourly count: {alert_system.alert_counts}")
    
    assert result == True, "Alert processing should succeed"
    
    # Check recent alerts
    recent_alerts = alert_system.get_recent_alerts(hours=1)
    assert len(recent_alerts) == 1, "Should have one recent alert"
    
    # Test statistics
    stats = alert_system.get_alert_statistics()
    assert stats['total_alerts_24h'] == 1, "Should show one alert in 24h stats"
    
    logger.info("✓ Alert system test passed")

def test_integration():
    """Test integration between components."""
    logger.info("Testing system integration...")
    
    # Initialize components
    import tempfile
    import os
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    db = TrendDatabase(temp_db.name)
    analyzer = TrendAnalyzer()
    
    # Create realistic test scenario
    cards_data = [
        # Card showing steady upward trend (lower volatility)
        {
            'name': 'Trending Card',
            'set': 'tst',
            'number': '001',
            'prices': [5.00, 5.30, 5.60, 5.90, 6.20, 6.50]  # 30% increase over time
        },
        # Card showing stable pricing
        {
            'name': 'Stable Card', 
            'set': 'tst',
            'number': '002',
            'prices': [10.00, 10.05, 9.95, 10.10, 9.90, 10.00]
        }
    ]
    
    # Record price snapshots (spread over longer period to meet duration requirements)
    base_time = datetime.now() - timedelta(hours=24)
    for card in cards_data:
        for i, price in enumerate(card['prices']):
            timestamp = base_time + timedelta(hours=i * 4)  # 4 hour intervals
            db.record_price_snapshot(
                card['name'], card['set'], card['number'], 
                price, False, 'test', timestamp
            )
            time.sleep(0.01)  # Small delay for different timestamps
    
    # Find trending cards
    trending_cards = db.find_trending_cards(
        min_percentage_change=20.0,
        min_absolute_change=1.0
    )
    
    assert len(trending_cards) >= 1, "Should find at least one trending card"
    
    # Analyze the trending card
    trending_card = trending_cards[0]
    history = db.get_price_history(
        trending_card['card_name'],
        trending_card['set_code'],
        trending_card['collector_number'],
        trending_card['is_foil']
    )
    
    # Add required fields for analysis
    for record in history:
        record['card_name'] = trending_card['card_name']
        record['set_code'] = trending_card['set_code']
        record['collector_number'] = trending_card['collector_number']
        record['is_foil'] = trending_card['is_foil']
    
    # Debug: check history details
    if history:
        first_time = datetime.fromisoformat(history[0]['timestamp'])
        last_time = datetime.fromisoformat(history[-1]['timestamp'])
        duration_hours = (last_time - first_time).total_seconds() / 3600
        logger.info(f"History duration: {duration_hours} hours")
        logger.info(f"History timestamps: {[h['timestamp'] for h in history]}")
    
    analysis = analyzer.analyze_trend(history)
    logger.info(f"Integration test: history length={len(history)}, analysis={analysis}")
    assert analysis is not None, "Should successfully analyze trend"
    assert analysis.trend_type == TrendType.UPWARD, "Should detect upward trend"
    
    # Cleanup
    os.unlink(temp_db.name)
    
    logger.info("✓ Integration test passed")

def run_all_tests():
    """Run all test functions."""
    logger.info("Starting MTG Card Price Trend Tracker tests...")
    
    try:
        test_database_operations()
        test_trend_analysis()
        test_price_monitor_config()
        test_alert_system()
        test_integration()
        
        logger.info("🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)