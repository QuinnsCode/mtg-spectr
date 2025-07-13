#!/usr/bin/env python3
"""
Simple test to debug search results display issue.
"""

import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_search_flow():
    """Test the basic search flow without GUI dependencies."""
    
    print("=== TESTING SEARCH FLOW ===")
    
    from data.unified_api_client import create_unified_client
    from data.database import DatabaseManager
    
    # Create components
    client = create_unified_client()
    db = DatabaseManager(':memory:')  # In-memory database for testing
    
    print(f"1. API Client: {client.provider}")
    print(f"2. Database: {db.db_path}")
    
    # Test card search
    card_name = "Lightning Bolt"
    print(f"\n3. Searching for '{card_name}'...")
    
    try:
        # Get card printings
        printings = client.get_card_printings(card_name)
        print(f"   Found {len(printings)} printings")
        
        if printings:
            print("\n   First printing details:")
            first = printings[0]
            print(f"   - Card: {first.card_name}")
            print(f"   - Set: {first.set_code} ({first.set_name})")
            print(f"   - Price: ${first.prices.get('usd', 0)}")
            print(f"   - Source: {first.source}")
            
            # Store in database
            print("\n4. Storing in database...")
            stored = db.insert_price_data(first)
            print(f"   Stored: {stored}")
            
            # Retrieve from database
            print("\n5. Retrieving from database...")
            db_results = db.get_card_prices(card_name)
            print(f"   Retrieved {len(db_results)} records")
            
            if db_results:
                print("\n   First record from DB:")
                first_db = db_results[0]
                print(f"   - Card: {first_db.get('card_name')}")
                print(f"   - Set: {first_db.get('set_code')}")
                print(f"   - Price: ${first_db.get('price_cents', 0) / 100.0:.2f}")
                print(f"   - Source: {first_db.get('source')}")
                
                # This is what the GUI would receive
                print("\n6. Final result format (as GUI would see it):")
                result_item = {
                    'card_name': first_db['card_name'],
                    'set_code': first_db['set_code'],
                    'printing_info': first_db['printing_info'],
                    'price_cents': first_db['price_cents'],
                    'price_dollars': first_db['price_cents'] / 100.0,
                    'condition': first_db['condition'],
                    'foil': first_db['foil'],
                    'timestamp': first_db['timestamp'],
                    'source': first_db['source'],
                    'is_anomaly': False,
                    'anomaly_score': 0.0,
                    'expected_price': 0.0,
                    'savings_potential': 0.0
                }
                print(f"   Result: {result_item}")
                
                return [result_item]  # This is what search_completed signal would emit
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    results = test_search_flow()
    print(f"\n=== FINAL RESULTS: {len(results)} items ===")
    if results:
        print("Results would be passed to ResultsWidget.display_results()")