#!/usr/bin/env python3
"""
Test script to verify set list shows recent sets and is alphabetized.
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

def test_set_list():
    """Test the set list to ensure it's comprehensive and alphabetized."""
    print("=== SET LIST TEST ===")
    
    # Initialize scanner
    client = create_unified_client()
    scanner = SetScanner(api_client=client)
    
    # Get available sets
    sets = scanner.get_available_sets()
    
    print(f"Total sets available: {len(sets)}")
    print("\nFirst 20 sets (alphabetically):")
    for i, set_info in enumerate(sets[:20]):
        print(f"  {i+1:2d}. {set_info['name']} ({set_info['code']}) - {set_info['card_count']} cards")
    
    print("\nLast 20 sets (alphabetically):")
    for i, set_info in enumerate(sets[-20:], len(sets) - 19):
        print(f"  {i:2d}. {set_info['name']} ({set_info['code']}) - {set_info['card_count']} cards")
    
    # Check for recent sets
    print("\n=== RECENT SETS CHECK ===")
    recent_sets = ['dsk', 'blb', 'otj', 'mkm', 'lci', 'woe', 'ltr', 'mom', 'one', 'bro', 'dmu']
    recent_names = {
        'dsk': 'Duskmourn: House of Horror',
        'blb': 'Bloomburrow',
        'otj': 'Outlaws of Thunder Junction',
        'mkm': 'Murders at Karlov Manor',
        'lci': 'The Lost Caverns of Ixalan',
        'woe': 'Wilds of Eldraine',
        'ltr': 'The Lord of the Rings: Tales of Middle-earth',
        'mom': 'March of the Machine',
        'one': 'Phyrexia: All Will Be One',
        'bro': 'The Brothers\' War',
        'dmu': 'Dominaria United'
    }
    
    available_codes = {s['code'] for s in sets}
    found_recent = 0
    
    for code in recent_sets:
        if code in available_codes:
            found_recent += 1
            print(f"✓ Found: {recent_names[code]} ({code})")
        else:
            print(f"✗ Missing: {recent_names[code]} ({code})")
    
    print(f"\nRecent sets found: {found_recent}/{len(recent_sets)}")
    
    # Check alphabetical order
    print("\n=== ALPHABETICAL ORDER CHECK ===")
    is_sorted = True
    for i in range(1, len(sets)):
        if sets[i-1]['name'].lower() > sets[i]['name'].lower():
            print(f"✗ Order error: '{sets[i-1]['name']}' should come after '{sets[i]['name']}'")
            is_sorted = False
    
    if is_sorted:
        print("✓ Sets are properly sorted alphabetically")
    
    # Check set types included
    print("\n=== SET TYPES INCLUDED ===")
    set_types = {}
    for set_info in sets:
        set_type = set_info.get('set_type', 'unknown')
        set_types[set_type] = set_types.get(set_type, 0) + 1
    
    for set_type, count in sorted(set_types.items()):
        print(f"  {set_type}: {count} sets")
    
    print(f"\n🎉 Set list test completed!")
    print(f"✓ {len(sets)} sets available")
    print(f"✓ Alphabetically sorted: {is_sorted}")
    print(f"✓ Recent sets coverage: {found_recent}/{len(recent_sets)}")
    
    return True

if __name__ == "__main__":
    test_set_list()