#!/usr/bin/env python3
"""
Diagnostic script to identify why search results might not be displaying.
"""

import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def diagnose_search_issue():
    """Run diagnostics on the search functionality."""
    
    print("=== DIAGNOSING SEARCH ISSUE ===\n")
    
    from data.unified_api_client import create_unified_client
    from data.database import DatabaseManager
    
    # 1. Test API connection
    print("1. Testing API connection...")
    client = create_unified_client()
    if client.test_connection():
        print("   ✓ API connection successful")
    else:
        print("   ✗ API connection failed!")
        return
    
    # 2. Test search functionality
    print("\n2. Testing card search...")
    card_name = "Lightning Bolt"
    try:
        cards = client.search_cards(card_name)
        print(f"   ✓ Found {len(cards)} cards matching '{card_name}'")
        if cards:
            print(f"   First card: {cards[0].get('name', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ Search failed: {e}")
        return
    
    # 3. Test card printings
    print("\n3. Testing get_card_printings...")
    try:
        printings = client.get_card_printings(card_name)
        print(f"   ✓ Found {len(printings)} printings")
        if printings:
            first = printings[0]
            print(f"   First printing: {first.card_name} - {first.set_code}")
            print(f"   Price data available: {bool(first.prices)}")
            if first.prices:
                print(f"   USD price: ${first.prices.get('usd', 'N/A')}")
    except Exception as e:
        print(f"   ✗ Get printings failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Test database storage
    print("\n4. Testing database storage...")
    db = DatabaseManager(':memory:')
    try:
        if printings:
            stored = db.insert_price_data(printings[0])
            print(f"   ✓ Database insert: {stored}")
            
            # Retrieve from database
            db_results = db.get_card_prices(card_name)
            print(f"   ✓ Retrieved {len(db_results)} records from database")
        else:
            print("   ✗ No printings to store")
    except Exception as e:
        print(f"   ✗ Database operation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. Test the complete workflow (simulating SearchWorker)
    print("\n5. Testing complete search workflow...")
    try:
        # This simulates what happens in SearchWorker._search_single_card
        results = []
        
        # Get printings
        printings = client.get_card_printings(card_name)
        print(f"   Step 1: Got {len(printings)} printings")
        
        # Store in database
        for printing in printings[:5]:  # Just first 5 for testing
            db.insert_price_data(printing)
        print(f"   Step 2: Stored printings in database")
        
        # Get from database
        db_data = db.get_card_prices(card_name)
        print(f"   Step 3: Retrieved {len(db_data)} records from database")
        
        # Convert to result format (without analysis)
        for data in db_data:
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
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'expected_price': 0.0,
                'savings_potential': 0.0
            }
            results.append(result_item)
        
        print(f"   Step 4: Created {len(results)} result items")
        
        # This is what would be emitted via search_completed signal
        if results:
            print("\n   Sample result that would be sent to ResultsWidget:")
            sample = results[0]
            for key, value in sample.items():
                print(f"     {key}: {value}")
        
        return results
        
    except Exception as e:
        print(f"   ✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_potential_issues():
    """Check for common issues that might prevent results from displaying."""
    
    print("\n\n=== CHECKING POTENTIAL ISSUES ===\n")
    
    issues = []
    
    # 1. Check if results might be getting filtered out
    print("1. Common filtering issues:")
    print("   - Empty price data could be filtered")
    print("   - Condition mismatches (expecting specific conditions)")
    print("   - Set code case sensitivity")
    
    # 2. Check signal/slot connection issues
    print("\n2. Signal/slot connection issues:")
    print("   - search_completed signal should emit List[Dict]")
    print("   - results_widget.display_results expects List[Dict]")
    print("   - Connection made in main_window.py line 375")
    
    # 3. Check data format issues
    print("\n3. Data format issues:")
    print("   - Results must be a list of dictionaries")
    print("   - Required keys: card_name, set_code, price_dollars, etc.")
    print("   - Missing keys could cause display issues")
    
    # 4. Check threading issues
    print("\n4. Threading issues:")
    print("   - SearchWorker runs in separate thread")
    print("   - Results emitted via Qt signal (thread-safe)")
    print("   - UI updates must happen in main thread")
    
    return issues

if __name__ == "__main__":
    # Run diagnostics
    results = diagnose_search_issue()
    
    # Check for issues
    check_potential_issues()
    
    # Summary
    print("\n\n=== SUMMARY ===")
    if results:
        print(f"✓ Search workflow completed successfully")
        print(f"✓ Generated {len(results)} results")
        print("\nIf results are not showing in the GUI, check:")
        print("1. ResultsWidget.display_results is being called")
        print("2. ResultsWidget.update_results_table is working")
        print("3. No exceptions in the GUI thread")
        print("4. Table widget is visible and properly sized")
    else:
        print("✗ Search workflow failed")
        print("Check the error messages above for details")