#!/usr/bin/env python3
"""
Test signal connection between search and results widgets.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

class MockSearchWidget(QObject):
    """Mock search widget to test signal emission."""
    search_completed = Signal(list)
    
    def emit_results(self, results):
        print(f"MockSearchWidget: Emitting {len(results)} results")
        self.search_completed.emit(results)

class MockResultsWidget(QObject):
    """Mock results widget to test signal reception."""
    
    def __init__(self):
        super().__init__()
        self.received_results = None
    
    def display_results(self, results):
        print(f"MockResultsWidget: Received {len(results)} results")
        self.received_results = results
        if results:
            print(f"  First result: {results[0].get('card_name', 'Unknown')}")

def test_signal_connection():
    """Test that signals are properly connected and working."""
    
    print("=== TESTING SIGNAL CONNECTION ===")
    
    # Create widgets
    search_widget = MockSearchWidget()
    results_widget = MockResultsWidget()
    
    # Connect signal
    print("1. Connecting search_completed signal to display_results slot...")
    search_widget.search_completed.connect(results_widget.display_results)
    
    # Test with empty results
    print("\n2. Testing with empty results...")
    search_widget.emit_results([])
    assert results_widget.received_results == []
    print("   ✓ Empty results received correctly")
    
    # Test with actual results
    print("\n3. Testing with actual results...")
    test_results = [
        {
            'card_name': 'Lightning Bolt',
            'set_code': 'LEA',
            'price_dollars': 100.0,
            'is_anomaly': False
        },
        {
            'card_name': 'Lightning Bolt',
            'set_code': 'LEB',
            'price_dollars': 90.0,
            'is_anomaly': True
        }
    ]
    
    search_widget.emit_results(test_results)
    assert results_widget.received_results == test_results
    print("   ✓ Results received correctly")
    
    print("\n=== SIGNAL CONNECTION TEST PASSED ===")

if __name__ == "__main__":
    # Create QApplication for Qt signals to work
    app = QApplication(sys.argv)
    
    try:
        test_signal_connection()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    sys.exit(0)