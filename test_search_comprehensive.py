#!/usr/bin/env python3
"""
Comprehensive test for search functionality.
"""

import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from data.unified_api_client import create_unified_client

def test_comprehensive_search():
    """Test comprehensive search functionality."""
    
    print("=== COMPREHENSIVE SEARCH TEST ===")
    
    # Create client
    client = create_unified_client()
    print(f"Using provider: {client.provider}")
    print(f"Connection: {'✓' if client.test_connection() else '✗'}")
    
    # Test cases
    test_cases = [
        # Basic card searches
        {'name': 'Lightning Bolt', 'expected': 1, 'description': 'Popular common card'},
        {'name': 'Black Lotus', 'expected': 2, 'description': 'Famous Power 9 card'},
        {'name': 'Ancestral Recall', 'expected': 2, 'description': 'Another Power 9 card'},
        
        # Case sensitivity
        {'name': 'lightning bolt', 'expected': 1, 'description': 'Lowercase'},
        {'name': 'LIGHTNING BOLT', 'expected': 1, 'description': 'Uppercase'},
        
        # Partial matches
        {'name': 'Lightning', 'expected': 175, 'description': 'Partial name (will find many)'},
        
        # Edge cases
        {'name': 'A', 'expected': 175, 'description': 'Single letter (many results)'},
        {'name': 'NonExistentCard12345', 'expected': 0, 'description': 'Non-existent card'},
        
        # Special characters (should be handled gracefully)
        {'name': 'Jace, the Mind Sculptor', 'expected': 1, 'description': 'Card with comma'},
        {'name': "Elspeth, Knight-Errant", 'expected': 1, 'description': 'Card with apostrophe and hyphen'},
        
        # Empty/invalid searches
        {'name': '', 'expected': 0, 'description': 'Empty string'},
        {'name': '   ', 'expected': 0, 'description': 'Whitespace only'},
    ]
    
    print(f"\nTesting {len(test_cases)} search cases...")
    print("-" * 80)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        name = test_case['name']
        expected = test_case['expected']
        description = test_case['description']
        
        try:
            cards = client.search_cards(name)
            result_count = len(cards)
            
            # For searches that return many results, just check if we got results
            if expected == 175:  # Many results expected
                success = result_count > 0
                status = "✓" if success else "✗"
                result_text = f"{result_count} cards" if success else "No results"
            else:
                success = result_count == expected
                status = "✓" if success else "✗"
                result_text = f"{result_count} cards (expected {expected})"
            
            print(f"{i:2d}. {status} {description:<30} '{name}' -> {result_text}")
            
            if success:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"{i:2d}. ✗ {description:<30} '{name}' -> ERROR: {e}")
            failed += 1
    
    print("-" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    
    # Test additional functionality
    print("\n=== ADDITIONAL FUNCTIONALITY ===")
    
    # Test card printings
    print("\nTesting card printings for 'Lightning Bolt':")
    printings = client.get_card_printings('Lightning Bolt')
    print(f"Found {len(printings)} printings")
    
    if printings:
        print("Sample printings:")
        for printing in printings[:5]:  # Show first 5
            usd_price = printing.prices.get('usd', 0)
            print(f"  • {printing.set_name} ({printing.set_code}): ${usd_price:.2f}")
    
    # Test autocomplete
    print("\nTesting autocomplete for 'Light':")
    suggestions = client.get_autocomplete_suggestions('Light')
    print(f"Found {len(suggestions)} suggestions: {suggestions[:5]}")
    
    # Test exact search
    print("\nTesting exact search:")
    cards = client.search_cards('Lightning Bolt', exact_match=True)
    print(f"Exact search found {len(cards)} cards")
    
    # Test set filtering
    print("\nTesting set filtering:")
    cards = client.search_cards('Lightning Bolt', set_code='clu')
    print(f"Set-filtered search found {len(cards)} cards")
    
    print("\n=== TEST COMPLETED ===")
    return passed, failed

if __name__ == "__main__":
    passed, failed = test_comprehensive_search()
    exit_code = 0 if failed == 0 else 1
    sys.exit(exit_code)