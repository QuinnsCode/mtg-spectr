#!/usr/bin/env python3
"""
Rate limit recovery script for JustTCG API.
This script helps you wait out rate limits and provides status updates.
"""

import time
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from data.api_client import create_api_client, JustTCGClient

def wait_for_rate_limit_reset(minutes: int = 5):
    """
    Wait for rate limits to reset.
    
    Args:
        minutes: Number of minutes to wait
    """
    print(f"Waiting {minutes} minutes for rate limits to reset...")
    
    for i in range(minutes * 60):
        remaining = (minutes * 60) - i
        mins, secs = divmod(remaining, 60)
        print(f"\rTime remaining: {mins:02d}:{secs:02d}", end="", flush=True)
        time.sleep(1)
    
    print("\nRate limit wait period complete!")

def test_api_status():
    """Test API status with different approaches."""
    print("\n" + "="*50)
    print("TESTING API STATUS")
    print("="*50)
    
    # Test 1: Direct client with no API key
    print("\n1. Testing with no API key (should get 401):")
    try:
        client = JustTCGClient(api_key=None)
        result = client.test_connection()
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Mock client
    print("\n2. Testing with mock client:")
    try:
        client = create_api_client(use_mock=True)
        result = client.test_connection()
        print(f"   Result: {result}")
        print(f"   Client type: {type(client).__name__}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Auto-fallback client
    print("\n3. Testing with auto-fallback client:")
    try:
        client = create_api_client(api_key=None)
        result = client.test_connection()
        print(f"   Result: {result}")
        print(f"   Client type: {type(client).__name__}")
    except Exception as e:
        print(f"   Error: {e}")

def main():
    print("JustTCG API Rate Limit Recovery Tool")
    print("="*40)
    
    while True:
        print("\nOptions:")
        print("1. Test API status")
        print("2. Wait 5 minutes for rate limit reset")
        print("3. Wait 10 minutes for rate limit reset")
        print("4. Wait 30 minutes for rate limit reset")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            test_api_status()
        elif choice == '2':
            wait_for_rate_limit_reset(5)
        elif choice == '3':
            wait_for_rate_limit_reset(10)
        elif choice == '4':
            wait_for_rate_limit_reset(30)
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()