#!/usr/bin/env python3
"""
Test script for rate limiting implementation.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from data.api_client import JustTCGClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rate_limiting():
    """Test the rate limiting and retry logic."""
    
    print("Testing JustTCG API rate limiting and retry logic...")
    
    # Initialize client (without API key for testing)
    client = JustTCGClient(api_key=None)
    
    print(f"Rate limits: {client.rate_limit.calls_per_minute}/min, {client.rate_limit.calls_per_hour}/hour")
    
    # Test connection (this will likely fail with 401 but should handle 429 properly)
    print("\n1. Testing connection...")
    try:
        result = client.test_connection()
        print(f"Connection test result: {result}")
    except Exception as e:
        print(f"Connection test failed (expected): {e}")
    
    # Test rate limit status
    print("\n2. Rate limit status:")
    status = client.get_rate_limit_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test multiple rapid calls to trigger rate limiting
    print("\n3. Testing rapid calls (should trigger rate limiting)...")
    for i in range(5):
        try:
            print(f"Making call {i+1}...")
            client.test_connection()
            time.sleep(0.1)  # Short delay
        except Exception as e:
            print(f"Call {i+1} failed: {e}")
    
    print("\n4. Final rate limit status:")
    status = client.get_rate_limit_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\nRate limiting test completed!")

if __name__ == "__main__":
    test_rate_limiting()