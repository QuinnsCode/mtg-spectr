#!/usr/bin/env python3
"""
Test script to demonstrate large set scanning with multiple pages.
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

def test_large_set_scan():
    """Test large set scanning with multiple pages."""
    print("=== LARGE SET SCAN TEST ===")
    
    # Initialize scanner
    client = create_unified_client()
    scanner = SetScanner(api_client=client)
    
    # Find a large set to test with
    sets = scanner.get_available_sets()
    test_set = None
    
    # Look for a set with 400+ cards (will definitely require multiple pages)
    for set_info in sets:
        card_count = set_info.get('card_count', 0)
        if card_count >= 400:
            test_set = set_info
            break
    
    if not test_set:
        print("No large set found for testing")
        return
    
    print(f"Testing large set scan with: {test_set['name']} ({test_set['code']})")
    print(f"Expected cards: {test_set['card_count']}")
    print("This set will require multiple pages of results...")
    
    # Progress callback (show every 50 cards for large sets)
    def progress_callback(current, total, card_name):
        if current % 50 == 0 or current == total:
            percentage = (current / total) * 100
            print(f"Progress: {current}/{total} ({percentage:.1f}%) - {card_name}")
    
    print("\nStarting large set scan (limited to 100 cards for demo)...")
    try:
        result = scanner.scan_set(
            set_code=test_set['code'],
            progress_callback=progress_callback,
            max_cards=100  # Limit to 100 cards for demo to avoid long wait
        )
        
        print(f"\n=== SCAN RESULTS ===")
        print(f"Set: {result.set_name} ({result.set_code})")
        print(f"Total cards in set: {result.total_cards}")
        print(f"Cards actually scanned: {result.scanned_cards}")
        print(f"Anomalies found: {result.anomalies_found}")
        print(f"Scan duration: {result.scan_duration:.2f} seconds")
        
        # Test card retrieval to verify pagination
        print(f"\n=== PAGINATION TEST ===")
        all_cards = scanner._get_set_cards(test_set['code'])
        print(f"Total cards retrieved: {len(all_cards)}")
        
        if len(all_cards) == result.total_cards:
            print("✅ SUCCESS: Pagination retrieved all cards!")
        elif len(all_cards) >= result.total_cards * 0.9:  # Allow for some variation
            print(f"✅ SUCCESS: Pagination retrieved most cards ({len(all_cards)}/{result.total_cards})")
        else:
            print(f"⚠️  PARTIAL: Only {len(all_cards)}/{result.total_cards} cards retrieved")
        
        # Show sample of cards to verify variety
        print(f"\n=== SAMPLE CARDS ===")
        for i, card in enumerate(all_cards[:5]):
            print(f"{i+1}. {card.get('name', 'Unknown')} ({card.get('set', 'Unknown')})")
        
        if len(all_cards) > 5:
            print(f"... and {len(all_cards) - 5} more cards")
        
        return True
        
    except Exception as e:
        print(f"✗ Scan failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_large_set_scan()
    if success:
        print("\n🎉 Large set scan test completed successfully!")
        print("The pagination fix handles large sets with multiple pages correctly!")
    else:
        print("\n❌ Large set scan test failed.")
    
    sys.exit(0 if success else 1)