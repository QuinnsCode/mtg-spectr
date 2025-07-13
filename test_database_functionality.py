#!/usr/bin/env python3
"""
Test script to verify database functionality works with security fixes.
"""

import sys
import os
import tempfile
import sqlite3

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_operations():
    """Test basic database operations with security fixes."""
    print("Testing Database Operations with Security Fixes...")
    
    # Import after setting up the path
    try:
        from data.database import DatabaseManager
        print("✓ Database manager imported successfully")
    except Exception as e:
        print(f"✗ Database manager import failed: {e}")
        return False
    
    # Create a temporary database for testing
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        db = DatabaseManager(db_path)
        print("✓ Database initialized successfully")
        
        # Test valid card data insertion
        valid_card = {
            'card_name': 'Lightning Bolt',
            'set_code': 'LEA',
            'price_cents': 1000,
            'condition': 'NM',
            'foil': False,
            'source': 'JustTCG'
        }
        
        success = db.insert_price_data(valid_card)
        if success:
            print("✓ Valid card data insertion successful")
        else:
            print("✗ Valid card data insertion failed")
            return False
        
        # Test card retrieval
        results = db.get_card_prices('Lightning Bolt')
        if results:
            print(f"✓ Card retrieval successful: found {len(results)} results")
        else:
            print("✗ Card retrieval failed")
            return False
        
        # Test historical data retrieval
        historical = db.get_historical_prices('Lightning Bolt', days=7)
        if isinstance(historical, list):
            print(f"✓ Historical data retrieval successful: found {len(historical)} results")
        else:
            print("✗ Historical data retrieval failed")
            return False
        
        # Test database stats
        stats = db.get_database_stats()
        if stats and 'total_records' in stats:
            print(f"✓ Database stats successful: {stats['total_records']} total records")
        else:
            print("✗ Database stats failed")
            return False
        
        # Test with potentially malicious inputs (should be blocked)
        try:
            malicious_card = {
                'card_name': 'DROP TABLE card_prices; --',
                'set_code': 'LEA',
                'price_cents': 1000
            }
            db.insert_price_data(malicious_card)
            print("✗ SQL injection attempt was not blocked")
            return False
        except ValueError:
            print("✓ SQL injection attempt was blocked")
        except Exception as e:
            print(f"✗ Unexpected error during SQL injection test: {e}")
            return False
        
        # Test malicious search
        try:
            results = db.get_card_prices("'; DROP TABLE card_prices; --")
            print("✗ SQL injection in search was not blocked")
            return False
        except ValueError:
            print("✓ SQL injection in search was blocked")
        except Exception as e:
            print(f"✗ Unexpected error during search injection test: {e}")
            return False
        
        # Cleanup
        os.unlink(db_path)
        print("✓ Database cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Database test error: {e}")
        return False

def test_parameterized_queries():
    """Test that parameterized queries are working correctly."""
    print("Testing Parameterized Queries...")
    
    try:
        # Create a test database directly
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                days INTEGER
            )
        ''')
        
        # Test parameterized query with dynamic days value
        days = 30
        cursor.execute('''
            INSERT INTO test_table (name, days) 
            VALUES (?, ?)
        ''', ('test_name', days))
        
        # Test the same pattern used in our fixed code
        cursor.execute('''
            SELECT * FROM test_table 
            WHERE name = ? 
            AND days >= ?
        ''', ('test_name', days))
        
        results = cursor.fetchall()
        if results:
            print("✓ Parameterized queries working correctly")
        else:
            print("✗ Parameterized queries failed")
            return False
        
        conn.commit()
        conn.close()
        os.unlink(db_path)
        
        return True
        
    except Exception as e:
        print(f"✗ Parameterized query test error: {e}")
        return False

def main():
    """Run all database functionality tests."""
    print("Running Database Functionality Tests with Security Fixes...\n")
    
    tests = [
        test_database_operations,
        test_parameterized_queries
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"Database Functionality Tests Summary: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All database functionality tests passed!")
        return True
    else:
        print("❌ Some database functionality tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)