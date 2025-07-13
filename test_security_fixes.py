#!/usr/bin/env python3
"""
Test script to verify security fixes are working properly.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.input_validator import InputValidator
from config.settings import SettingsManager
import tempfile
import json

def test_input_validation():
    """Test input validation functionality."""
    print("Testing Input Validation...")
    
    # Test valid inputs
    try:
        InputValidator.validate_card_name('Lightning Bolt')
        print("✓ Valid card name accepted")
    except ValueError as e:
        print(f"✗ Valid card name rejected: {e}")
        return False
    
    # Test SQL injection detection
    try:
        InputValidator.validate_card_name("DROP TABLE users; --")
        print("✗ SQL injection not detected")
        return False
    except ValueError:
        print("✓ SQL injection detected and blocked")
    
    # Test XSS detection
    try:
        InputValidator.validate_card_name("<script>alert(1)</script>")
        print("✗ XSS not detected")
        return False
    except ValueError:
        print("✓ XSS detected and blocked")
    
    # Test path traversal detection
    try:
        InputValidator.validate_path("../../../etc/passwd")
        print("✗ Path traversal not detected")
        return False
    except ValueError:
        print("✓ Path traversal detected and blocked")
    
    # Test API key validation
    try:
        InputValidator.validate_api_key("abc123validkey789")
        print("✓ Valid API key accepted")
    except ValueError as e:
        print(f"✗ Valid API key rejected: {e}")
        return False
    
    try:
        InputValidator.validate_api_key("<script>alert(1)</script>")
        print("✗ XSS in API key not detected")
        return False
    except ValueError:
        print("✓ XSS in API key detected and blocked")
    
    print("✓ All input validation tests passed\n")
    return True

def test_settings_encryption():
    """Test settings encryption functionality."""
    print("Testing Settings Encryption...")
    
    try:
        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a custom settings manager with temp directory
            settings = SettingsManager()
            
            # Test API key encryption
            test_key = "test_api_key_12345"
            success = settings.set_api_key(test_key)
            
            if not success:
                print("✗ API key encryption failed")
                return False
            
            # Test API key retrieval
            retrieved_key = settings.get_api_key()
            if retrieved_key == test_key:
                print("✓ API key encryption/decryption successful")
            else:
                print(f"✗ API key decryption failed: expected '{test_key}', got '{retrieved_key}'")
                return False
            
            # Test path validation
            try:
                path = settings.get_database_path()
                print(f"✓ Database path validation successful: {path}")
            except Exception as e:
                print(f"✗ Database path validation failed: {e}")
                return False
            
            print("✓ All settings encryption tests passed\n")
            return True
            
    except Exception as e:
        print(f"✗ Settings encryption test error: {e}")
        return False

def test_sql_injection_fixes():
    """Test SQL injection fixes in database queries."""
    print("Testing SQL Injection Fixes...")
    
    # Test that the query templates are properly parameterized
    # This is a structural test since we can't easily test the database without full setup
    
    # Read database.py to verify parameterized queries are used
    try:
        with open('data/database.py', 'r') as f:
            db_content = f.read()
        
        # Check that string formatting is not used in SQL queries
        if '.format(' in db_content and 'SELECT' in db_content:
            print("✗ String formatting found in database queries")
            return False
        
        # Check that parameterized queries are used
        if 'datetime(\'now\', \'-\' || ? || \' days\')' in db_content:
            print("✓ Parameterized queries detected in database")
        else:
            print("✗ Parameterized queries not found")
            return False
        
        print("✓ SQL injection fixes verified\n")
        return True
        
    except Exception as e:
        print(f"✗ SQL injection test error: {e}")
        return False

def test_path_validation():
    """Test path validation in settings."""
    print("Testing Path Validation...")
    
    try:
        settings = SettingsManager()
        
        # Test that dangerous path patterns are blocked
        try:
            settings._validate_path("../../../etc/passwd")
            print("✗ Path traversal not blocked")
            return False
        except ValueError:
            print("✓ Path traversal blocked")
        
        # Test that valid paths are accepted
        try:
            valid_path = settings._validate_path("valid_file.db")
            print(f"✓ Valid path accepted: {valid_path}")
        except ValueError as e:
            print(f"✗ Valid path rejected: {e}")
            return False
        
        print("✓ All path validation tests passed\n")
        return True
        
    except Exception as e:
        print(f"✗ Path validation test error: {e}")
        return False

def main():
    """Run all security tests."""
    print("Running Security Fix Tests...\n")
    
    tests = [
        test_input_validation,
        test_settings_encryption,
        test_sql_injection_fixes,
        test_path_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"Security Tests Summary: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All security fixes are working correctly!")
        return True
    else:
        print("❌ Some security fixes need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)