#!/usr/bin/env python3
"""
Test script to verify that all import fixes work correctly.
"""

import sys
import os
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_imports():
    """Test all critical imports to ensure they work correctly."""
    try:
        print("Testing PySide6 imports...")
        from PySide6.QtWidgets import QApplication, QMainWindow
        from PySide6.QtGui import QAction
        from PySide6.QtCore import Qt
        print("✓ PySide6 imports successful")
        
        print("\nTesting configuration imports...")
        from config.settings import get_settings, SettingsManager
        print("✓ Settings imports successful")
        
        from config.input_validator import InputValidator
        print("✓ Input validator imports successful")
        
        print("\nTesting data layer imports...")
        from data.database import DatabaseManager
        print("✓ Database manager imports successful")
        
        from data.api_client import JustTCGClient
        print("✓ API client imports successful")
        
        print("\nTesting analysis imports...")
        from analysis.price_analyzer import PriceAnalyzer
        print("✓ Price analyzer imports successful")
        
        print("\nTesting GUI imports...")
        from gui.main_window import MainWindow
        print("✓ Main window imports successful")
        
        from gui.search_widget import SearchWidget
        print("✓ Search widget imports successful")
        
        from gui.results_widget import ResultsWidget
        print("✓ Results widget imports successful")
        
        print("\n✅ All imports successful! The application should now run without import errors.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🎉 Import fixes are working correctly!")
        print("You can now run the application with: python main.py")
    else:
        print("\n❌ Import fixes need more work.")
        sys.exit(1)