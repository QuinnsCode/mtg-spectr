#!/usr/bin/env python3
"""
Test script to demonstrate full set scanning with pagination fix.
"""

import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from analysis.set_scanner import SetScanner
from data.unified_api_client import create_unified_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_full_set_scan():
    """Test full set scanning to demonstrate pagination fix."""
    print("=== FULL SET SCAN TEST ===")
    
    # Initialize scanner
    client = create_unified_client()
    scanner = SetScanner(api_client=client)
    
    # Find a medium-sized set to test with
    sets = scanner.get_available_sets()
    test_set = None
    
    # Look for a set with 150-250 cards (good size for testing)
    for set_info in sets:
        card_count = set_info.get('card_count', 0)
        if 150 <= card_count <= 250:
            test_set = set_info
            break
    
    if not test_set:
        print("No suitable test set found")
        return
    
    print(f"Testing full scan with: {test_set['name']} ({test_set['code']})")
    print(f"Expected cards: {test_set['card_count']}")
    
    # Progress callback
    def progress_callback(current, total, card_name):
        if current % 25 == 0 or current == total:
            percentage = (current / total) * 100
            print(f"Progress: {current}/{total} ({percentage:.1f}%) - {card_name}")
    
    print("\nStarting full set scan...")
    try:
        result = scanner.scan_set(
            set_code=test_set['code'],
            progress_callback=progress_callback,
            max_cards=None  # No limit - scan all cards
        )
        
        print(f"\n=== SCAN RESULTS ===")
        print(f"Set: {result.set_name} ({result.set_code})")
        print(f"Total cards in set: {result.total_cards}")
        print(f"Cards actually scanned: {result.scanned_cards}")
        print(f"Anomalies found: {result.anomalies_found}")
        print(f"Scan duration: {result.scan_duration:.2f} seconds")
        
        # Check if we got all the cards
        if result.scanned_cards == result.total_cards:
            print("✅ SUCCESS: All cards in the set were scanned!")
        else:
            print(f"⚠️  PARTIAL: {result.scanned_cards}/{result.total_cards} cards scanned")
            print("   (This might be due to cards without pricing data)")
        
        # Show price statistics
        stats = result.price_statistics
        if stats:
            print(f"\n=== PRICE STATISTICS ===")
            print(f"Cards with prices: {stats.get('total_cards_with_prices', 0)}")
            print(f"Average price: ${stats.get('average_price', 0):.2f}")
            print(f"Median price: ${stats.get('median_price', 0):.2f}")
            print(f"Price range: ${stats.get('min_price', 0):.2f} - ${stats.get('max_price', 0):.2f}")
            print(f"Anomaly rate: {stats.get('anomaly_rate', 0):.1%}")
        
        # Show top anomalies
        if result.anomaly_cards:
            print(f"\n=== TOP ANOMALIES ===")
            top_anomalies = scanner.get_top_anomalies(result, limit=3)
            
            for i, anomaly in enumerate(top_anomalies, 1):
                print(f"{i}. {anomaly['card_name']} ({anomaly['rarity']})")
                print(f"   Current: ${anomaly['current_price']:.2f} | Expected: ${anomaly['expected_price']:.2f}")
                print(f"   Type: {anomaly['anomaly_type']} | Score: {anomaly['anomaly_score']:.2f}")
                print(f"   Confidence: {anomaly['confidence']:.1%}")
                print()
        
        # Export results
        export_filename = f"full_scan_results_{test_set['code']}.json"
        scanner.export_results(result, export_filename)
        print(f"Results exported to: {export_filename}")
        
        return True
        
    except Exception as e:
        print(f"✗ Scan failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_set_scan()
    if success:
        print("\n🎉 Full set scan test completed successfully!")
        print("The pagination fix is working - all cards in the set are being scanned!")
    else:
        print("\n❌ Full set scan test failed.")
    
    sys.exit(0 if success else 1)