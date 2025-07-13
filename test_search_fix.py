#!/usr/bin/env python3
"""
Test the search fix for problematic queries.
"""

import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from data.unified_api_client import create_unified_client
from data.database import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_search_fix():
    """Test that the search fix handles problematic queries correctly."""
    
    print("=== TESTING SEARCH FIX ===")
    
    # Create client and database
    client = create_unified_client()
    db = DatabaseManager(':memory:')
    
    print(f"✓ Client provider: {client.provider}")
    print(f"✓ Connection test: {client.test_connection()}")
    
    # Test problematic queries that previously failed
    test_cases = [
        # Normal cases
        {'query': 'Lightning Bolt', 'expected': 1, 'description': 'Normal card name'},
        {'query': 'Black Lotus', 'expected': 1, 'description': 'Famous card'},
        {'query': 'Jace, the Mind Sculptor', 'expected': 1, 'description': 'Card with comma'},
        
        # Previously problematic cases
        {'query': 'Lightning Bolt (', 'expected': 1, 'description': 'Unclosed parentheses'},
        {'query': 'Lightning Bolt OR', 'expected': 1, 'description': 'Trailing OR'},
        {'query': 'Lightning Bolt AND', 'expected': 1, 'description': 'Trailing AND'},
        {'query': 'Lightning Bolt +', 'expected': 1, 'description': 'Trailing plus'},
        {'query': 'Lightning Bolt -', 'expected': 1, 'description': 'Trailing minus'},
        
        # Edge cases
        {'query': '', 'expected': 0, 'description': 'Empty string'},
        {'query': '   ', 'expected': 0, 'description': 'Whitespace only'},
        {'query': 'NonExistentCard12345', 'expected': 0, 'description': 'Non-existent card'},
    ]
    
    print(f"\nTesting {len(test_cases)} search queries...")
    print("-" * 80)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case['query']
        expected = test_case['expected']
        description = test_case['description']
        
        try:
            # Test unified client search
            cards = client.search_cards(query)
            result_count = len(cards)
            
            # For searches that should return results, just check if we got any
            if expected > 0:
                success = result_count > 0
                status = "✓" if success else "✗"
                result_text = f"{result_count} cards" if success else "No results"
            else:
                success = result_count == 0
                status = "✓" if success else "✗"
                result_text = f"{result_count} cards (expected 0)"
            
            print(f"{i:2d}. {status} {description:<25} '{query}' -> {result_text}")
            
            if success:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"{i:2d}. ✗ {description:<25} '{query}' -> ERROR: {e}")
            failed += 1
    
    print("-" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    
    # Test the full workflow for a successful search
    print("\n=== TESTING FULL WORKFLOW ===")
    
    try:
        card_name = "Lightning Bolt"
        print(f"Testing full workflow for: {card_name}")
        
        # Step 1: Search for card
        cards = client.search_cards(card_name)
        print(f"✓ Search found {len(cards)} cards")
        
        # Step 2: Get printings
        printings = client.get_card_printings(card_name)
        print(f"✓ Found {len(printings)} printings")
        
        # Step 3: Store in database
        stored = 0
        for printing in printings:
            try:
                result = db.insert_price_data(printing)
                if result:
                    stored += 1
            except Exception as e:
                print(f"  Warning: Failed to store printing: {e}")
                continue
        
        print(f"✓ Stored {stored} printings in database")
        
        # Step 4: Retrieve from database
        db_data = db.get_card_prices(card_name)
        print(f"✓ Retrieved {len(db_data)} records from database")
        
        # Step 5: Show sample results
        if db_data:
            print("\nSample results:")
            for i, record in enumerate(db_data[:3]):  # Show first 3
                price_dollars = record['price_cents'] / 100.0
                print(f"  {i+1}. {record['card_name']} - {record['set_code']} - ${price_dollars:.2f}")
        
        print("\n✓ Full workflow completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Full workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return failed == 0

if __name__ == "__main__":
    success = test_search_fix()
    print(f"\n{'='*50}")
    if success:
        print("🎉 ALL TESTS PASSED! Search functionality is working correctly.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    print(f"{'='*50}")
    
    sys.exit(0 if success else 1)