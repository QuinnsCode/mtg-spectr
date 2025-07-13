#!/usr/bin/env python3
"""
Test script to verify GUI module imports and basic functionality.
This script tests the GUI components without actually running the application.
"""

import sys
import os
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_gui_imports():
    """Test if GUI modules can be imported."""
    print("Testing GUI module imports...")
    
    # Test if PySide6 is available
    try:
        import PySide6
        print("✓ PySide6 is available")
        pyside6_available = True
    except ImportError:
        print("✗ PySide6 not available - GUI tests will be skipped")
        pyside6_available = False
    
    if not pyside6_available:
        print("To install PySide6: pip install PySide6")
        return False
    
    # Test GUI module imports
    try:
        from gui.main_window import MainWindow
        print("✓ MainWindow module imported successfully")
    except ImportError as e:
        print(f"✗ MainWindow import failed: {e}")
        return False
    
    try:
        from gui.search_widget import SearchWidget
        print("✓ SearchWidget module imported successfully")
    except ImportError as e:
        print(f"✗ SearchWidget import failed: {e}")
        return False
    
    try:
        from gui.results_widget import ResultsWidget
        print("✓ ResultsWidget module imported successfully")
    except ImportError as e:
        print(f"✗ ResultsWidget import failed: {e}")
        return False
    
    return True

def test_main_module():
    """Test if main module can be imported."""
    print("\nTesting main module import...")
    
    try:
        # Import functions from main module
        from main import setup_logging, check_dependencies, setup_application
        print("✓ Main module functions imported successfully")
        
        # Test dependency checking
        deps_ok, missing_deps = check_dependencies()
        if deps_ok:
            print("✓ All dependencies are available")
        else:
            print(f"✗ Missing dependencies: {missing_deps}")
            print("Install missing dependencies with: pip install -r requirements.txt")
        
        return deps_ok
        
    except ImportError as e:
        print(f"✗ Main module import failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("MTG Card Pricing Analysis Tool - Import Test")
    print("=" * 60)
    
    # Test core functionality (should always work)
    print("\n1. Testing core functionality...")
    try:
        from config.settings import get_settings
        from data.database import DatabaseManager
        from data.api_client import MockJustTCGClient
        
        settings = get_settings()
        db = DatabaseManager(':memory:')
        api = MockJustTCGClient()
        
        print("✓ Core modules imported successfully")
        
    except Exception as e:
        print(f"✗ Core functionality test failed: {e}")
        return 1
    
    # Test scientific libraries
    print("\n2. Testing scientific libraries...")
    try:
        import pandas
        import numpy
        import sklearn
        print("✓ Scientific libraries available")
        
        # Test price analyzer
        from analysis.price_analyzer import PriceAnalyzer
        analyzer = PriceAnalyzer(db)
        print("✓ PriceAnalyzer imported successfully")
        
    except ImportError as e:
        print(f"✗ Scientific libraries not available: {e}")
        print("Install with: pip install pandas numpy scikit-learn")
    
    # Test GUI components
    print("\n3. Testing GUI components...")
    gui_ok = test_gui_imports()
    
    # Test main application
    print("\n4. Testing main application...")
    main_ok = test_main_module()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✓ Core functionality: PASSED")
    print(f"{'✓' if gui_ok else '✗'} GUI components: {'PASSED' if gui_ok else 'FAILED'}")
    print(f"{'✓' if main_ok else '✗'} Main application: {'PASSED' if main_ok else 'FAILED'}")
    
    if gui_ok and main_ok:
        print("\n🎉 All tests passed! The application is ready to run.")
        print("To start the application: python main.py")
    else:
        print("\n⚠️  Some tests failed. Install missing dependencies:")
        print("pip install -r requirements.txt")
    
    return 0 if (gui_ok and main_ok) else 1

if __name__ == "__main__":
    sys.exit(main())