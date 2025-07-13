#!/usr/bin/env python3
"""
Test script to verify that all imports work correctly after the QAction fix.
Run this after installing dependencies to ensure everything is working.
"""

def test_imports():
    """Test all critical imports to ensure they work correctly."""
    try:
        print("Testing PySide6 imports...")
        from PySide6.QtWidgets import QApplication, QMainWindow
        from PySide6.QtGui import QAction
        from PySide6.QtCore import Qt
        print("✓ PySide6 imports successful")
        
        print("\nTesting application imports...")
        from gui.main_window import MainWindow
        print("✓ Main window import successful")
        
        from gui.search_widget import SearchWidget
        print("✓ Search widget import successful")
        
        from gui.results_widget import ResultsWidget
        print("✓ Results widget import successful")
        
        from data.database import DatabaseManager
        print("✓ Database manager import successful")
        
        from data.api_client import JustTCGClient
        print("✓ API client import successful")
        
        from analysis.price_analyzer import PriceAnalyzer
        print("✓ Price analyzer import successful")
        
        from config.settings import SettingsManager
        print("✓ Settings manager import successful")
        
        from config.input_validator import InputValidator
        print("✓ Input validator import successful")
        
        print("\n✅ All imports successful! The QAction fix is working correctly.")
        print("The application should now run without import errors.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        return False
    
    return True

if __name__ == "__main__":
    test_imports()