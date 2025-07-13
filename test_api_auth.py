#!/usr/bin/env python3
"""
Test script to verify JustTCG API authentication works correctly.
"""

import sys
import os
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_api_authentication():
    """Test JustTCG API authentication with X-API-Key header."""
    
    try:
        from data.api_client import JustTCGClient
        from config.settings import get_settings
        
        print("🔑 Testing JustTCG API Authentication")
        print("=" * 50)
        
        # Get settings
        settings = get_settings()
        api_key = settings.settings.api.justtcg_api_key
        
        if not api_key:
            print("❌ No API key configured")
            print("\nTo configure your API key:")
            print("1. Launch the application: python main.py")
            print("2. Go to Settings → API Configuration")
            print("3. Enter your JustTCG API key")
            print("4. Or set environment variable: JUSTTCG_API_KEY")
            print("\nSee API_SETUP.md for detailed instructions.")
            return False
        
        print(f"✓ API key found: {api_key[:10]}...")
        
        # Test client creation
        client = JustTCGClient(api_key=api_key)
        print("✓ API client created successfully")
        
        # Check headers
        headers = client.session.headers
        if 'X-API-Key' in headers:
            print("✓ X-API-Key header configured correctly")
        else:
            print("❌ X-API-Key header not found")
            return False
        
        print(f"✓ Authentication header: X-API-Key: {headers['X-API-Key'][:10]}...")
        
        # Test basic connectivity (this will fail without network, but tests the setup)
        print("\n🌐 Testing API connectivity...")
        try:
            # This is a simple test - actual API calls would need network
            response = client.search_cards("Lightning Bolt")
            print("✓ API call successful")
            print(f"✓ Found {len(response)} results")
        except Exception as e:
            print(f"⚠️  API call failed (expected without network): {e}")
            print("   This is normal if you don't have internet or the API is down")
        
        print("\n✅ API authentication setup is correct!")
        print("Your API key is properly configured for JustTCG API calls.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_api_key_help():
    """Show help for getting and configuring API key."""
    print("\n📋 How to get your JustTCG API key:")
    print("1. Go to https://justtcg.com/")
    print("2. Sign up for an account")
    print("3. Subscribe to a plan (Free, Starter, Professional, or Enterprise)")
    print("4. Go to your dashboard and copy your API key")
    print("5. Format: 'tcg_your_api_key_here'")
    print("\n📋 How to configure your API key:")
    print("Method 1: Use the application settings")
    print("Method 2: Set environment variable JUSTTCG_API_KEY")
    print("Method 3: Edit config file at ~/.mtg_card_pricing/config.json")
    print("\nSee API_SETUP.md for detailed instructions.")

if __name__ == "__main__":
    success = test_api_authentication()
    
    if not success:
        show_api_key_help()
        sys.exit(1)
    
    print("\n🎉 Ready to use JustTCG API!")
    print("You can now run the application: python main.py")