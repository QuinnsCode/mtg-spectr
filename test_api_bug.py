#!/usr/bin/env python3
"""
Test script to reproduce the JustTCG API bug.
"""

import sys
import os
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_api_bug():
    """Reproduce the 400 Bad Request error."""
    
    try:
        from data.api_client import JustTCGClient
        import requests
        
        print("🐛 Reproducing JustTCG API Bug")
        print("=" * 50)
        
        # Test 1: Current broken implementation
        print("\n1. Testing current broken implementation:")
        print("   URL: https://api.justtcg.com/v1/sets?limit=1")
        print("   Missing: game parameter")
        
        try:
            # Simulate the current broken request
            response = requests.get(
                "https://api.justtcg.com/v1/sets",
                params={'limit': 1},
                headers={'X-API-Key': 'test_key'}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: Correct implementation
        print("\n2. Testing correct implementation:")
        print("   URL: https://api.justtcg.com/v1/sets?game=magic-the-gathering&limit=1")
        print("   Includes: game parameter")
        
        try:
            # Test the correct request format
            response = requests.get(
                "https://api.justtcg.com/v1/sets",
                params={'game': 'magic-the-gathering', 'limit': 1},
                headers={'X-API-Key': 'test_key'}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 401:
                print("   ✓ 401 Unauthorized (expected with test key)")
            else:
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 3: Test with actual API client
        print("\n3. Testing with API client:")
        client = JustTCGClient(api_key="test_key")
        
        try:
            result = client.test_connection()
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reproducing bug: {e}")
        return False

if __name__ == "__main__":
    test_api_bug()