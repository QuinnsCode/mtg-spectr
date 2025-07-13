#!/usr/bin/env python3
"""
Debug script to check why cc1 set is filtered out.
"""

import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from analysis.set_scanner import SetScanner
from data.unified_api_client import create_unified_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_cc1_filtering():
    """Debug why cc1 set is filtered out."""
    print("=== CC1 SET FILTERING DEBUG ===")
    
    # Initialize scanner
    client = create_unified_client()
    scanner = SetScanner(api_client=client)
    
    # Get all sets (unfiltered)
    print("1. Getting all sets from API...")
    all_sets = client.get_sets()
    
    # Find cc1 set
    cc1_set = None
    for set_info in all_sets:
        if set_info.get('code') == 'cc1':
            cc1_set = set_info
            break
    
    if not cc1_set:
        print("❌ CC1 set not found in API response")
        return
    
    print(f"✓ Found CC1 set: {cc1_set.get('name', 'Unknown')}")
    print(f"   Code: {cc1_set.get('code', 'Unknown')}")
    print(f"   Set Type: {cc1_set.get('set_type', 'Unknown')}")
    print(f"   Card Count: {cc1_set.get('card_count', 0)}")
    print(f"   Digital: {cc1_set.get('digital', 'Unknown')}")
    print(f"   Released: {cc1_set.get('released_at', 'Unknown')}")
    
    # Check filtering criteria
    print("\n2. Checking filtering criteria...")
    
    set_type = cc1_set.get('set_type', '')
    card_count = cc1_set.get('card_count', 0)
    is_digital = cc1_set.get('digital', False)
    
    # Current filtering logic
    allowed_types = ['expansion', 'core', 'masters', 'draft_innovation', 'commander']
    min_cards = 50
    
    print(f"   Set type '{set_type}' in allowed types {allowed_types}: {set_type in allowed_types}")
    print(f"   Digital: {is_digital} (should be False)")
    print(f"   Card count {card_count} >= {min_cards}: {card_count >= min_cards}")
    
    # Check what's filtering it out
    if set_type not in allowed_types:
        print(f"❌ FILTERED OUT: Set type '{set_type}' not in allowed types")
    elif is_digital:
        print(f"❌ FILTERED OUT: Digital set")
    elif card_count < min_cards:
        print(f"❌ FILTERED OUT: Card count {card_count} < {min_cards}")
    else:
        print(f"✓ SHOULD PASS: All criteria met")
    
    # Check if we should include this set type
    print(f"\n3. Analyzing set type '{set_type}'...")
    
    # Count how many sets of this type exist
    same_type_sets = [s for s in all_sets if s.get('set_type') == set_type]
    print(f"   Total sets of type '{set_type}': {len(same_type_sets)}")
    
    # Show examples
    print(f"   Examples of '{set_type}' sets:")
    for i, s in enumerate(same_type_sets[:5]):
        print(f"      {i+1}. {s.get('name', 'Unknown')} ({s.get('code', 'Unknown')}) - {s.get('card_count', 0)} cards")
    
    # Check if this type should be included
    if set_type in ['promo', 'token', 'memorabilia', 'box', 'from_the_vault']:
        print(f"   ℹ️  '{set_type}' is typically excluded from analysis")
    else:
        print(f"   ⚠️  '{set_type}' might be worth including")
    
    # Test modified filtering
    print(f"\n4. Testing modified filtering...")
    
    # More inclusive filtering
    inclusive_types = ['expansion', 'core', 'masters', 'draft_innovation', 'commander', 'premium', 'duel_deck']
    min_cards_inclusive = 8  # Commander Collections are small
    
    would_pass = (set_type in inclusive_types and 
                  not is_digital and 
                  card_count >= min_cards_inclusive)
    
    print(f"   With inclusive filtering: {would_pass}")
    
    if would_pass:
        print(f"   ✓ CC1 would be included with modified filtering")
    else:
        print(f"   ❌ CC1 would still be filtered out")

if __name__ == "__main__":
    debug_cc1_filtering()