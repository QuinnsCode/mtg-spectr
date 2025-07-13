#!/usr/bin/env python3
"""
Debug script to investigate why set scanner is only finding 175 cards instead of full set.
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
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_set_cards():
    """Debug set card retrieval."""
    print("=== SET CARD DEBUG TEST ===")
    
    # Initialize scanner
    client = create_unified_client()
    scanner = SetScanner(api_client=client)
    
    # Get available sets and pick a large one
    sets = scanner.get_available_sets()
    
    # Find a set with a lot of cards
    test_set = None
    for set_info in sets:
        if set_info.get('card_count', 0) > 300:  # Find a large set
            test_set = set_info
            break
    
    if not test_set:
        print("No large set found for testing")
        return
    
    print(f"Testing with set: {test_set['name']} ({test_set['code']})")
    print(f"Expected cards: {test_set['card_count']}")
    
    # Test the _get_set_cards method directly
    print("\n=== TESTING _get_set_cards ===")
    cards = scanner._get_set_cards(test_set['code'])
    print(f"Cards retrieved: {len(cards)}")
    
    if len(cards) < test_set['card_count']:
        print(f"⚠️  WARNING: Expected {test_set['card_count']} cards, got {len(cards)}")
        print("This suggests a pagination issue or search limitation")
    
    # Test the underlying search
    print("\n=== TESTING UNDERLYING SEARCH ===")
    query = f"e:{test_set['code']}"
    print(f"Search query: {query}")
    
    if hasattr(client, 'client') and hasattr(client.client, 'search_cards'):
        direct_cards = client.client.search_cards(query, unique='cards', order='collector_number')
        print(f"Direct search results: {len(direct_cards)}")
    else:
        direct_cards = client.search_cards(query)
        print(f"Unified client search results: {len(direct_cards)}")
    
    # Check if we need to handle pagination
    if len(direct_cards) < test_set['card_count']:
        print("\n=== PAGINATION INVESTIGATION ===")
        print("The search might be paginated. Let's check if this is a Scryfall pagination issue.")
        
        # Try to get more details about the search response
        try:
            # Test with the real Scryfall API if available
            from data.scryfall_client import create_scryfall_client
            real_client = create_scryfall_client(use_mock=False)
            
            if hasattr(real_client, '_make_request'):
                # Check if we can get pagination info
                response = real_client._make_request('cards/search', {'q': query})
                if 'has_more' in response:
                    print(f"Has more pages: {response['has_more']}")
                    print(f"Next page URL: {response.get('next_page', 'None')}")
                
        except Exception as e:
            print(f"Real API test failed: {e}")
    
    # Test a full scan to see the actual behavior
    print("\n=== TESTING FULL SET SCAN ===")
    print("Running a limited scan to see how many cards are actually processed...")
    
    def progress_callback(current, total, card_name):
        if current % 50 == 0 or current == total:
            print(f"Progress: {current}/{total} - {card_name}")
    
    try:
        result = scanner.scan_set(
            set_code=test_set['code'],
            progress_callback=progress_callback,
            max_cards=200  # Limit to avoid long wait
        )
        
        print(f"\nScan Results:")
        print(f"Total cards in set metadata: {result.total_cards}")
        print(f"Cards actually scanned: {result.scanned_cards}")
        print(f"Cards retrieved by search: {len(cards)}")
        
        if result.scanned_cards < result.total_cards:
            print(f"⚠️  ISSUE: Only {result.scanned_cards} cards scanned out of {result.total_cards} expected")
        
    except Exception as e:
        print(f"Scan test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_set_cards()