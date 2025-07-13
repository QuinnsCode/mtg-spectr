#!/usr/bin/env python3
"""
Test script for set scanning functionality.
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

def progress_callback(current, total, card_name):
    """Progress callback for set scanning."""
    percentage = (current / total) * 100
    print(f"\rScanning: {current}/{total} ({percentage:.1f}%) - {card_name[:30]:<30}", end="", flush=True)

def test_set_scanner():
    """Test the set scanning functionality."""
    
    print("=== MTG SET SCANNER TEST ===")
    
    # Initialize scanner
    client = create_unified_client()
    scanner = SetScanner(api_client=client)
    
    # Show available sets
    print("\nAvailable sets for scanning:")
    available_sets = scanner.get_available_sets()
    
    for i, set_info in enumerate(available_sets[:10]):  # Show first 10
        print(f"  {i+1}. {set_info['name']} ({set_info['code']}) - {set_info['card_count']} cards")
    
    # Test with a smaller set first
    test_set = None
    for set_info in available_sets:
        if set_info['card_count'] < 100:  # Find a smaller set for testing
            test_set = set_info
            break
    
    if not test_set:
        # Use first available set but limit cards
        test_set = available_sets[0]
        print(f"\nUsing {test_set['name']} ({test_set['code']}) with card limit for testing")
    else:
        print(f"\nUsing {test_set['name']} ({test_set['code']}) for testing")
    
    # Scan the set (limit to 20 cards for testing)
    print("\nStarting set scan...")
    try:
        scan_result = scanner.scan_set(
            set_code=test_set['code'],
            progress_callback=progress_callback,
            max_cards=20  # Limit for testing
        )
        
        print(f"\n\n=== SCAN RESULTS ===")
        print(f"Set: {scan_result.set_name} ({scan_result.set_code})")
        print(f"Cards scanned: {scan_result.scanned_cards}")
        print(f"Anomalies found: {scan_result.anomalies_found}")
        print(f"Scan duration: {scan_result.scan_duration:.2f} seconds")
        
        # Show price statistics
        stats = scan_result.price_statistics
        if stats:
            print(f"\n=== PRICE STATISTICS ===")
            print(f"Cards with prices: {stats.get('total_cards_with_prices', 0)}")
            print(f"Average price: ${stats.get('average_price', 0):.2f}")
            print(f"Median price: ${stats.get('median_price', 0):.2f}")
            print(f"Price range: ${stats.get('min_price', 0):.2f} - ${stats.get('max_price', 0):.2f}")
            print(f"Anomaly rate: {stats.get('anomaly_rate', 0):.1%}")
            print(f"Undervalued: {stats.get('undervalued_count', 0)}")
            print(f"Overvalued: {stats.get('overvalued_count', 0)}")
            print(f"Volatile: {stats.get('volatile_count', 0)}")
        
        # Show top anomalies
        if scan_result.anomaly_cards:
            print(f"\n=== TOP ANOMALIES ===")
            top_anomalies = scanner.get_top_anomalies(scan_result, limit=5)
            
            for i, anomaly in enumerate(top_anomalies, 1):
                print(f"{i}. {anomaly['card_name']} ({anomaly['rarity']})")
                print(f"   Current: ${anomaly['current_price']:.2f} | Expected: ${anomaly['expected_price']:.2f}")
                print(f"   Type: {anomaly['anomaly_type']} | Score: {anomaly['anomaly_score']:.2f}")
                print(f"   Confidence: {anomaly['confidence']:.1%}")
                print()
        
        # Export results
        export_filename = f"scan_results_{test_set['code']}.json"
        scanner.export_results(scan_result, export_filename)
        print(f"Results exported to: {export_filename}")
        
        print("\n✓ Set scanning test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Set scanning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_full_set_scan():
    """Demonstrate scanning a full set (commented out for safety)."""
    print("\n=== FULL SET SCAN EXAMPLE ===")
    print("To scan a full set, use:")
    print("```python")
    print("scanner = SetScanner()")
    print("result = scanner.scan_set('dsk')  # Duskmourn set")
    print("top_undervalued = scanner.get_top_anomalies(result, 'undervalued', 10)")
    print("scanner.export_results(result, 'duskmourn_scan.json')")
    print("```")
    print("\nThis will:")
    print("- Scan all ~400 cards in the set")
    print("- Take 40-60 seconds (with rate limiting)")
    print("- Find undervalued cards with high confidence")
    print("- Export detailed results to JSON")

if __name__ == "__main__":
    print("MTG Set Scanner - Anomaly Detection System")
    print("=" * 50)
    
    success = test_set_scanner()
    
    if success:
        demonstrate_full_set_scan()
        print("\n🎉 Set scanner is ready for use!")
    else:
        print("\n❌ Set scanner test failed.")
    
    sys.exit(0 if success else 1)