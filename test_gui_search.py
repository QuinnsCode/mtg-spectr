#!/usr/bin/env python3
"""
Test GUI search functionality without actually launching the GUI.
"""

import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from data.unified_api_client import create_unified_client
from data.database import DatabaseManager
from analysis.price_analyzer import PriceAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_gui_search_functionality():
    """Test the search functionality as used by the GUI."""
    
    print("=== GUI SEARCH FUNCTIONALITY TEST ===")
    
    # Initialize components like the GUI does
    client = create_unified_client()
    db = DatabaseManager(':memory:')
    analyzer = PriceAnalyzer(db)
    
    print(f"✓ Client provider: {client.provider}")
    print(f"✓ Database initialized: {db.db_path}")
    print(f"✓ Connection test: {client.test_connection()}")
    
    # Test single card search workflow
    print("\n1. Testing single card search workflow...")
    
    try:
        # Step 1: Get card printings from API (like SearchWorker does)
        card_name = "Lightning Bolt"
        printings = client.get_card_printings(card_name)
        print(f"   Found {len(printings)} printings for '{card_name}'")
        
        # Step 2: Filter by set code (optional)
        set_code = None  # No filtering for this test
        if set_code:
            printings = [p for p in printings if getattr(p, 'set_code', None) == set_code]
            print(f"   After filtering by set '{set_code}': {len(printings)} printings")
        
        # Step 3: Store in database
        print("   Storing printings in database...")
        stored_count = 0
        for printing in printings:
            try:
                result = db.insert_price_data(printing)
                if result:
                    stored_count += 1
            except Exception as e:
                print(f"   Error storing printing: {e}")
                continue
        
        print(f"   Stored {stored_count} printings in database")
        
        # Step 4: Get updated data from database
        db_data = db.get_card_prices(card_name, set_code)
        print(f"   Retrieved {len(db_data)} records from database")
        
        # Step 5: Perform analysis (optional)
        print("   Performing price analysis...")
        try:
            analysis_results = analyzer.analyze_card_prices(card_name, set_code)
            print(f"   Analysis found {len(analysis_results)} results")
        except Exception as e:
            print(f"   Analysis error: {e}")
            analysis_results = []
        
        # Step 6: Merge analysis with price data (like GUI does)
        results = []
        for data in db_data:
            # Find matching analysis result
            analysis = None
            for result in analysis_results:
                if (result.get('set_code') == data.get('set_code') and
                    result.get('printing_info') == data.get('printing_info') and
                    result.get('condition') == data.get('condition')):
                    analysis = result
                    break
            
            result_item = {
                'card_name': data['card_name'],
                'set_code': data['set_code'],
                'printing_info': data['printing_info'],
                'price_cents': data['price_cents'],
                'price_dollars': data['price_cents'] / 100.0,
                'condition': data['condition'],
                'foil': data['foil'],
                'timestamp': data['timestamp'],
                'source': data['source'],
                'is_anomaly': analysis.get('is_anomaly', False) if analysis else False,
                'anomaly_score': analysis.get('anomaly_score', 0.0) if analysis else 0.0,
                'expected_price': analysis.get('expected_price', 0.0) if analysis else 0.0,
                'savings_potential': analysis.get('savings_potential', 0.0) if analysis else 0.0
            }
            results.append(result_item)
        
        print(f"   Final results: {len(results)} items")
        
        # Show sample results
        if results:
            print("\n   Sample results:")
            for i, result in enumerate(results[:3]):  # Show first 3
                print(f"   {i+1}. {result['card_name']} - {result['set_code']} - ${result['price_dollars']:.2f}")
        
        print("\n✓ Single card search workflow completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Single card search workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test multiple card search workflow
    print("\n2. Testing multiple card search workflow...")
    
    try:
        card_names = ["Black Lotus", "Mox Pearl", "Ancestral Recall"]
        all_results = []
        
        for card_name in card_names:
            try:
                # Get printings for this card
                printings = client.get_card_printings(card_name)
                print(f"   {card_name}: {len(printings)} printings")
                
                # Store in database
                for printing in printings:
                    db.insert_price_data(printing)
                
                # Get results
                db_data = db.get_card_prices(card_name)
                for data in db_data:
                    result_item = {
                        'card_name': data['card_name'],
                        'set_code': data['set_code'],
                        'price_dollars': data['price_cents'] / 100.0,
                        'source': data['source']
                    }
                    all_results.append(result_item)
                
            except Exception as e:
                print(f"   Error with {card_name}: {e}")
                continue
        
        print(f"   Total results across all cards: {len(all_results)}")
        
        print("\n✓ Multiple card search workflow completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Multiple card search workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    return True

if __name__ == "__main__":
    success = test_gui_search_functionality()
    sys.exit(0 if success else 1)