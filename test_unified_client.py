#!/usr/bin/env python3
"""
Test script for unified API client.
"""

import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from data.unified_api_client import create_unified_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_unified_client():
    """Test the unified API client."""
    
    print("Testing Unified API Client")
    print("=" * 50)
    
    # Test Scryfall provider
    print("\n1. Testing Scryfall provider...")
    client = create_unified_client(provider="scryfall")
    
    info = client.get_provider_info()
    print(f"Provider: {info['provider']}")
    print(f"Client type: {info['client_type']}")
    print(f"Features: {info['features']}")
    
    # Test connection
    print(f"Connection: {'✓' if client.test_connection() else '✗'}")
    
    # Test search
    print("\n2. Testing card search...")
    cards = client.search_cards("Lightning Bolt")
    print(f"Found {len(cards)} cards")
    
    # Test card lookup
    print("\n3. Testing card lookup...")
    card = client.get_card_by_name("Lightning Bolt")
    if card:
        print(f"Card: {card.get('name')} - {card.get('set_name')}")
    
    # Test printings with standardized format
    print("\n4. Testing card printings...")
    printings = client.get_card_printings("Lightning Bolt")
    print(f"Found {len(printings)} printings")
    
    if printings:
        for printing in printings[:3]:  # Show first 3
            usd_price = printing.prices.get('usd', 0)
            print(f"  {printing.set_name} ({printing.set_code}): ${usd_price:.2f}")
    
    # Test autocomplete
    print("\n5. Testing autocomplete...")
    suggestions = client.get_autocomplete_suggestions("Light")
    print(f"Suggestions: {suggestions[:5]}")
    
    # Test sets
    print("\n6. Testing sets...")
    sets = client.get_sets()
    print(f"Found {len(sets)} sets")
    
    # Test provider switching
    print("\n7. Testing provider switch...")
    success = client.switch_provider("justtcg")
    print(f"Switch to JustTCG: {'✓' if success else '✗'}")
    
    # Switch back
    success = client.switch_provider("scryfall")
    print(f"Switch back to Scryfall: {'✓' if success else '✗'}")
    
    print("\nUnified client test completed!")

if __name__ == "__main__":
    test_unified_client()