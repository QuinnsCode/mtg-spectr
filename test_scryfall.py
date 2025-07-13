#!/usr/bin/env python3
"""
Test script for Scryfall API integration.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from data.scryfall_client import create_scryfall_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scryfall_api():
    """Test the Scryfall API functionality."""
    
    print("Testing Scryfall API...")
    print("=" * 50)
    
    # Create client
    client = create_scryfall_client()
    print(f"Client type: {type(client).__name__}")
    
    # Test connection
    print("\n1. Testing connection...")
    connected = client.test_connection()
    print(f"Connection successful: {connected}")
    
    # Test card search
    print("\n2. Testing card search...")
    cards = client.search_cards("Lightning Bolt")
    print(f"Found {len(cards)} cards for 'Lightning Bolt'")
    
    if cards:
        card = cards[0]
        print(f"First result: {card.get('name')} ({card.get('set_name')})")
        
        # Test pricing
        prices = client.get_card_prices(card)
        print(f"Prices: {prices}")
    
    # Test exact card lookup
    print("\n3. Testing exact card lookup...")
    card = client.get_card_by_name("Lightning Bolt")
    if card:
        print(f"Found: {card.get('name')} - ${card.get('prices', {}).get('usd', 'N/A')}")
    else:
        print("Card not found")
    
    # Test autocomplete
    print("\n4. Testing autocomplete...")
    suggestions = client.autocomplete_card_name("Light")
    print(f"Autocomplete suggestions: {suggestions[:5]}...")  # Show first 5
    
    # Test card printings
    print("\n5. Testing card printings...")
    printings = client.get_card_printings("Lightning Bolt")
    print(f"Found {len(printings)} printings")
    
    if printings:
        for printing in printings[:3]:  # Show first 3
            usd_price = printing.get('prices', {}).get('usd', 0)
            print(f"  {printing.get('set_name')} ({printing.get('set_code')}): ${usd_price}")
    
    # Test sets
    print("\n6. Testing sets...")
    sets = client.get_sets()
    print(f"Found {len(sets)} sets")
    
    if sets:
        recent_sets = [s for s in sets if s.get('set_type') == 'expansion'][:5]
        print("Recent expansion sets:")
        for set_info in recent_sets:
            print(f"  {set_info.get('name')} ({set_info.get('code')}) - {set_info.get('released_at')}")
    
    print("\nScryfall API test completed!")

if __name__ == "__main__":
    test_scryfall_api()