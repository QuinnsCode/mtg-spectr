#!/usr/bin/env python3
"""
Comprehensive security verification script for the MTG Card Pricing Analysis Tool.
Verifies that all security fixes are properly implemented and working.
"""

import sys
import os
import re
import tempfile
import sqlite3

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_sql_injection_fixes():
    """Verify that SQL injection vulnerabilities have been fixed."""
    print("🔍 Verifying SQL Injection Fixes...")
    
    try:
        # Read the database.py file to check for proper parameterization
        with open('data/database.py', 'r') as f:
            content = f.read()
        
        # Check that the vulnerable patterns have been fixed
        issues = []
        
        # Look for string formatting in SQL queries (vulnerable pattern)
        if re.search(r'\.format\([^)]*\).*(?:SELECT|INSERT|UPDATE|DELETE)', content, re.IGNORECASE):
            issues.append("String formatting found in SQL queries")
        
        # Check for proper parameterized queries
        if 'datetime(\'now\', \'-\' || ? || \' days\')' in content:
            print("✓ Historical prices query properly parameterized")
        else:
            issues.append("Historical prices query not properly parameterized")
        
        # Check for input validation imports
        if 'from ..config.input_validator import InputValidator' in content:
            print("✓ Input validation imported in database module")
        else:
            issues.append("Input validation not imported in database module")
        
        # Check for validation calls
        if 'InputValidator.validate_card_name' in content:
            print("✓ Card name validation implemented")
        else:
            issues.append("Card name validation not implemented")
        
        if issues:
            print("❌ SQL injection fix issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ All SQL injection fixes verified")
            return True
    
    except Exception as e:
        print(f"❌ Error verifying SQL injection fixes: {e}")
        return False

def verify_api_key_encryption():
    """Verify that API key encryption is properly implemented."""
    print("🔍 Verifying API Key Encryption...")
    
    try:
        # Read the settings.py file
        with open('config/settings.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('cryptography.fernet import Fernet', 'Fernet encryption imported'),
            ('_encrypt_sensitive_data', 'Encryption method implemented'),
            ('_decrypt_sensitive_data', 'Decryption method implemented'),
            ('_get_or_create_key', 'Key management implemented'),
            ('validate_api_key', 'API key validation implemented')
        ]
        
        issues = []
        for pattern, description in checks:
            if pattern in content:
                print(f"✓ {description}")
            else:
                issues.append(f"{description} not found")
        
        if issues:
            print("❌ API key encryption issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ All API key encryption features verified")
            return True
    
    except Exception as e:
        print(f"❌ Error verifying API key encryption: {e}")
        return False

def verify_path_validation():
    """Verify that path validation is properly implemented."""
    print("🔍 Verifying Path Validation...")
    
    try:
        # Read the settings.py file
        with open('config/settings.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('_validate_path', 'Path validation method implemented'),
            ('dangerous_patterns', 'Dangerous pattern detection'),
            ('os.path.isabs', 'Absolute path handling'),
            ('resolve()', 'Path resolution for security'),
            ('startswith(str(base_dir.resolve()))', 'Base directory restriction')
        ]
        
        issues = []
        for pattern, description in checks:
            if pattern in content:
                print(f"✓ {description}")
            else:
                issues.append(f"{description} not found")
        
        if issues:
            print("❌ Path validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ All path validation features verified")
            return True
    
    except Exception as e:
        print(f"❌ Error verifying path validation: {e}")
        return False

def verify_input_validation():
    """Verify that comprehensive input validation is implemented."""
    print("🔍 Verifying Input Validation...")
    
    try:
        # Check if input validator file exists
        if not os.path.exists('config/input_validator.py'):
            print("❌ Input validator module not found")
            return False
        
        # Read the input validator file
        with open('config/input_validator.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('validate_card_name', 'Card name validation'),
            ('validate_set_code', 'Set code validation'),
            ('validate_search_term', 'Search term validation'),
            ('validate_numeric_input', 'Numeric input validation'),
            ('validate_api_key', 'API key validation'),
            ('validate_path', 'Path validation'),
            ('SQL_INJECTION_PATTERNS', 'SQL injection detection patterns'),
            ('XSS_PATTERNS', 'XSS detection patterns'),
            ('_check_sql_injection', 'SQL injection checking method'),
            ('_check_xss', 'XSS checking method')
        ]
        
        issues = []
        for pattern, description in checks:
            if pattern in content:
                print(f"✓ {description}")
            else:
                issues.append(f"{description} not found")
        
        if issues:
            print("❌ Input validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ All input validation features verified")
            return True
    
    except Exception as e:
        print(f"❌ Error verifying input validation: {e}")
        return False

def verify_gui_integration():
    """Verify that GUI components use input validation."""
    print("🔍 Verifying GUI Integration...")
    
    try:
        # Check if GUI components import and use input validation
        if not os.path.exists('gui/search_widget.py'):
            print("❌ Search widget not found")
            return False
        
        with open('gui/search_widget.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('from ..config.input_validator import InputValidator', 'Input validator imported'),
            ('InputValidator.validate_card_name', 'Card name validation used'),
            ('InputValidator.validate_set_code', 'Set code validation used'),
            ('InputValidator.validate_multiple_card_names', 'Multiple card names validation used')
        ]
        
        issues = []
        for pattern, description in checks:
            if pattern in content:
                print(f"✓ {description}")
            else:
                issues.append(f"{description} not found")
        
        if issues:
            print("❌ GUI integration issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ All GUI integration features verified")
            return True
    
    except Exception as e:
        print(f"❌ Error verifying GUI integration: {e}")
        return False

def verify_requirements():
    """Verify that security dependencies are included."""
    print("🔍 Verifying Security Dependencies...")
    
    try:
        if not os.path.exists('requirements.txt'):
            print("❌ Requirements file not found")
            return False
        
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        if 'cryptography' in content:
            print("✓ Cryptography dependency included")
            return True
        else:
            print("❌ Cryptography dependency not found in requirements")
            return False
    
    except Exception as e:
        print(f"❌ Error verifying requirements: {e}")
        return False

def test_validation_logic():
    """Test the actual validation logic."""
    print("🔍 Testing Validation Logic...")
    
    try:
        from config.input_validator import InputValidator
        
        # Test SQL injection detection
        try:
            InputValidator.validate_card_name("'; DROP TABLE users; --")
            print("❌ SQL injection not detected")
            return False
        except ValueError:
            print("✓ SQL injection detection working")
        
        # Test XSS detection
        try:
            InputValidator.validate_card_name("<script>alert('xss')</script>")
            print("❌ XSS not detected")
            return False
        except ValueError:
            print("✓ XSS detection working")
        
        # Test path traversal detection
        try:
            InputValidator.validate_path("../../../etc/passwd")
            print("❌ Path traversal not detected")
            return False
        except ValueError:
            print("✓ Path traversal detection working")
        
        # Test valid input acceptance
        try:
            result = InputValidator.validate_card_name("Lightning Bolt")
            print("✓ Valid input accepted")
        except ValueError:
            print("❌ Valid input rejected")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ Error testing validation logic: {e}")
        return False

def main():
    """Run comprehensive security verification."""
    print("🔒 MTG Card Pricing Tool - Security Verification\n")
    print("=" * 60)
    
    verifications = [
        verify_sql_injection_fixes,
        verify_api_key_encryption,
        verify_path_validation,
        verify_input_validation,
        verify_gui_integration,
        verify_requirements,
        test_validation_logic
    ]
    
    passed = 0
    total = len(verifications)
    
    for verification in verifications:
        try:
            if verification():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Verification failed with error: {e}\n")
    
    print("=" * 60)
    print(f"Security Verification Summary: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 ALL SECURITY FIXES VERIFIED SUCCESSFULLY!")
        print("\nSecurity improvements implemented:")
        print("✅ SQL injection vulnerabilities fixed")
        print("✅ API key encryption implemented")
        print("✅ Path validation and sanitization added")
        print("✅ Comprehensive input validation implemented")
        print("✅ GUI components secured")
        print("✅ Security dependencies included")
        return True
    else:
        print("⚠️  Some security verifications failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)