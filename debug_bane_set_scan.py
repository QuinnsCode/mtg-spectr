#!/usr/bin/env python3
"""
Debug script to scan the set containing Bane of Progress.
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

def debug_bane_set_scan():
    """Debug scanning the set that contains Bane of Progress."""
    print("=== BANE OF PROGRESS SET SCAN DEBUG ===")
    
    # Initialize scanner
    client = create_unified_client()
    scanner = SetScanner(api_client=client)
    
    # Search for Bane of Progress to get set info
    print("1. Finding Bane of Progress set...")
    cards = client.search_cards("Bane of Progress")
    
    if not cards:
        print("❌ Card not found!")
        return
    
    card = cards[0]
    set_code = card.get('set', '')
    set_name = card.get('set_name', '')
    print(f"✓ Found in set: {set_name} ({set_code})")
    
    # Check if this set is available for scanning
    print("\n2. Checking if set is available for scanning...")
    available_sets = scanner.get_available_sets()
    available_codes = {s['code'] for s in available_sets}
    
    if set_code not in available_codes:
        print(f"❌ Set {set_code} is not available for scanning")
        print("Available sets with 'c' codes:")
        for s in available_sets:
            if s['code'].startswith('c'):
                print(f"   {s['name']} ({s['code']})")
        return
    
    print(f"✓ Set {set_code} is available for scanning")
    
    # Scan the set
    print("\n3. Scanning the set...")
    def progress_callback(current, total, card_name):
        if 'Bane of Progress' in card_name:
            print(f"🎯 Found Bane of Progress at {current}/{total}")
        elif current % 10 == 0:
            print(f"Progress: {current}/{total} - {card_name}")
    
    try:
        result = scanner.scan_set(
            set_code=set_code,
            progress_callback=progress_callback,
            max_cards=None  # Scan all cards
        )
        
        print(f"\n=== SCAN RESULTS ===")
        print(f"Set: {result.set_name} ({result.set_code})")
        print(f"Cards scanned: {result.scanned_cards}")
        print(f"Anomalies found: {result.anomalies_found}")
        
        # Check if Bane of Progress is in the anomalies
        print("\n4. Checking for Bane of Progress in anomalies...")
        bane_found = False
        for anomaly in result.anomaly_cards:
            if 'Bane of Progress' in anomaly.get('card_name', ''):
                bane_found = True
                print(f"✓ FOUND: Bane of Progress in anomalies!")
                print(f"   Current: ${anomaly['current_price']:.2f}")
                print(f"   Expected: ${anomaly['expected_price']:.2f}")
                print(f"   Type: {anomaly['anomaly_type']}")
                print(f"   Score: {anomaly['anomaly_score']:.2f}")
                print(f"   Confidence: {anomaly['confidence']:.1%}")
                break
        
        if not bane_found:
            print("❌ Bane of Progress NOT found in anomalies")
            
            # Check if it was scanned at all
            print("\n5. Checking if Bane of Progress was scanned...")
            all_cards = scanner._get_set_cards(set_code)
            bane_in_set = False
            for card in all_cards:
                if 'Bane of Progress' in card.get('name', ''):
                    bane_in_set = True
                    print(f"✓ Bane of Progress found in set data:")
                    print(f"   Name: {card.get('name', 'Unknown')}")
                    print(f"   Set: {card.get('set', 'Unknown')}")
                    print(f"   Rarity: {card.get('rarity', 'Unknown')}")
                    prices = card.get('prices', {})
                    usd_price = prices.get('usd')
                    print(f"   USD Price: ${usd_price}")
                    
                    if usd_price:
                        print(f"\n6. Testing anomaly detection on this card...")
                        anomaly_info = scanner._analyze_card_anomalies(card)
                        if anomaly_info:
                            print(f"✓ Card SHOULD be an anomaly:")
                            print(f"   Current: ${anomaly_info['current_price']:.2f}")
                            print(f"   Expected: ${anomaly_info['expected_price']:.2f}")
                            print(f"   Type: {anomaly_info['anomaly_type']}")
                            print(f"   Score: {anomaly_info['anomaly_score']:.2f}")
                        else:
                            print(f"❌ Card did NOT qualify as anomaly")
                    break
            
            if not bane_in_set:
                print("❌ Bane of Progress not found in set data")
        
        # Show all anomalies found
        print(f"\n=== ALL ANOMALIES FOUND ===")
        for i, anomaly in enumerate(result.anomaly_cards, 1):
            print(f"{i}. {anomaly['card_name']} - ${anomaly['current_price']:.2f} ({anomaly['anomaly_type']})")
            
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_bane_set_scan()