#!/usr/bin/env python3
"""
Debug script to investigate why "Bane of Progress" is not showing as an anomaly.
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

def debug_bane_of_progress():
    """Debug why Bane of Progress is not showing as an anomaly."""
    print("=== BANE OF PROGRESS DEBUG ===")
    
    # Initialize scanner
    client = create_unified_client()
    scanner = SetScanner(api_client=client)
    
    # Search for Bane of Progress
    print("1. Searching for 'Bane of Progress'...")
    cards = client.search_cards("Bane of Progress")
    
    if not cards:
        print("❌ Card not found!")
        return
    
    card = cards[0]  # Get the first result
    print(f"✓ Found: {card.get('name', 'Unknown')}")
    print(f"   Set: {card.get('set_name', 'Unknown')} ({card.get('set', 'Unknown')})")
    print(f"   Rarity: {card.get('rarity', 'Unknown')}")
    print(f"   Type: {card.get('type_line', 'Unknown')}")
    print(f"   Mana Cost: {card.get('mana_cost', 'Unknown')}")
    
    # Check pricing
    prices = card.get('prices', {})
    usd_price = prices.get('usd')
    print(f"   USD Price: ${usd_price}")
    
    if not usd_price:
        print("❌ No USD pricing data!")
        return
    
    current_price = float(usd_price)
    print(f"   Current Price: ${current_price:.2f}")
    
    # Test the set scanner's expected price calculation
    print("\n2. Testing Set Scanner Expected Price Calculation...")
    expected_price = scanner._calculate_expected_price(card)
    print(f"   Expected Price: ${expected_price:.2f}")
    
    # Test anomaly score calculation
    anomaly_score = scanner._calculate_anomaly_score(current_price, expected_price, card)
    print(f"   Anomaly Score: {anomaly_score:.2f}")
    
    # Test anomaly type determination
    anomaly_type = scanner._determine_anomaly_type(current_price, expected_price, anomaly_score)
    print(f"   Anomaly Type: {anomaly_type}")
    
    # Test confidence calculation
    confidence = scanner._calculate_confidence(card, anomaly_score)
    print(f"   Confidence: {confidence:.1%}")
    
    # Check thresholds
    print("\n3. Checking Thresholds...")
    thresholds = scanner.anomaly_thresholds
    print(f"   Price Deviation Threshold: {thresholds['price_deviation']}")
    print(f"   Confidence Threshold: {thresholds['confidence_threshold']}")
    print(f"   Minimum Price Filter: $0.50")
    
    # Analyze why it might not be an anomaly
    print("\n4. Analysis...")
    
    if current_price < 0.50:
        print(f"❌ FILTERED OUT: Price ${current_price:.2f} is below $0.50 minimum")
    elif anomaly_score < thresholds['price_deviation']:
        print(f"❌ NOT ANOMALY: Anomaly score {anomaly_score:.2f} is below threshold {thresholds['price_deviation']}")
    elif confidence < thresholds['confidence_threshold']:
        print(f"❌ LOW CONFIDENCE: Confidence {confidence:.1%} is below threshold {thresholds['confidence_threshold']:.1%}")
    else:
        print(f"✓ SHOULD BE ANOMALY: Meets all criteria")
    
    # Compare with different expected price methods
    print("\n5. Alternative Expected Price Calculations...")
    
    # Simple rarity-based
    rarity_prices = {'common': 0.25, 'uncommon': 0.50, 'rare': 2.00, 'mythic': 5.00}
    simple_expected = rarity_prices.get(card.get('rarity', 'common'), 1.00)
    print(f"   Simple Rarity-Based: ${simple_expected:.2f}")
    
    # More aggressive for creatures
    if 'Creature' in card.get('type_line', ''):
        creature_expected = simple_expected * 1.5  # Creatures often worth more
        print(f"   Creature Adjustment: ${creature_expected:.2f}")
    
    # Check if it would be an anomaly with different thresholds
    if current_price > expected_price * 2:
        print(f"✓ OVERVALUED: Current price is {current_price/expected_price:.1f}x expected")
    elif current_price < expected_price * 0.5:
        print(f"✓ UNDERVALUED: Current price is {current_price/expected_price:.1f}x expected")
    else:
        print(f"ℹ️  NORMAL: Price ratio is {current_price/expected_price:.1f}x expected")

if __name__ == "__main__":
    debug_bane_of_progress()