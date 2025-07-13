#!/usr/bin/env python3
"""
Debug script to identify the search issue.
"""

import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from data.scryfall_client import ScryfallClient

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def debug_search():
    """Debug the search functionality step by step."""
    
    print("=== DEBUGGING SCRYFALL SEARCH ===")
    
    # Create client
    client = ScryfallClient()
    
    # Test 1: Raw _make_request
    print("\n1. Testing raw _make_request...")
    try:
        params = {
            'q': 'Lightning Bolt',
            'unique': 'cards',
            'order': 'name',
            'page': 1,
            'include_extras': 'false'
        }
        response = client._make_request('cards/search', params=params)
        print(f"Raw response type: {type(response)}")
        print(f"Raw response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
        
        if response.get('object') == 'error':
            print(f"Error response: {response}")
        elif response.get('object') == 'list':
            print(f"Success! Found {len(response.get('data', []))} cards")
            if response.get('data'):
                print(f"First card: {response['data'][0]['name']}")
        else:
            print(f"Unexpected response object: {response.get('object')}")
            print(f"Full response: {response}")
            
    except Exception as e:
        print(f"Raw request failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: search_cards method
    print("\n2. Testing search_cards method...")
    try:
        cards = client.search_cards('Lightning Bolt')
        print(f"search_cards returned: {type(cards)}")
        print(f"Number of cards: {len(cards) if isinstance(cards, list) else 'Not a list'}")
        
        if cards:
            print(f"First card: {cards[0] if cards else 'None'}")
        else:
            print("No cards returned")
            
    except Exception as e:
        print(f"search_cards failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Connection test
    print("\n3. Testing connection...")
    try:
        connected = client.test_connection()
        print(f"Connection test: {connected}")
    except Exception as e:
        print(f"Connection test failed: {e}")

if __name__ == "__main__":
    debug_search()