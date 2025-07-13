#!/usr/bin/env python3
"""
Debug script to investigate why Bane of Progress from FIC set isn't flagged as an anomaly.

This script will:
1. Get all cards from the FIC set using the set scanner's card retrieval method
2. Search specifically for "Bane of Progress" in that card list
3. If found, show all the card data including prices, rarity, etc.
4. If found, run it through the anomaly detection process step by step to see why it's not flagged
5. If not found, search for cards with "Bane" or "Progress" in the name to see if there's a name mismatch
6. Check what other sets Bane of Progress appears in to understand its reprinting history
"""

import logging
import sys
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, '/mnt/c/Users/mikeb/PycharmProjects/PythonProject/mtg_card_pricing')

from data.unified_api_client import create_unified_client
from analysis.set_scanner import SetScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_bane_investigation.log')
    ]
)
logger = logging.getLogger(__name__)

def format_card_data(card: Dict[str, Any]) -> str:
    """Format card data for display."""
    name = card.get('name', 'Unknown')
    set_code = card.get('set', 'Unknown')
    rarity = card.get('rarity', 'Unknown')
    prices = card.get('prices', {})
    type_line = card.get('type_line', 'Unknown')
    collector_number = card.get('collector_number', 'Unknown')
    
    output = f"""
Card: {name}
Set: {set_code}
Rarity: {rarity}
Type: {type_line}
Collector Number: {collector_number}
Prices:
  USD: {prices.get('usd', 'N/A')}
  USD Foil: {prices.get('usd_foil', 'N/A')}
  EUR: {prices.get('eur', 'N/A')}
  TIX: {prices.get('tix', 'N/A')}
"""
    return output

def analyze_card_anomaly_detection(scanner: SetScanner, card: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a card through the anomaly detection process step by step."""
    logger.info(f"Analyzing anomaly detection for: {card.get('name', 'Unknown')}")
    
    # Step 1: Basic card info
    card_name = card.get('name', '')
    prices = card.get('prices', {})
    usd_price = prices.get('usd')
    rarity = card.get('rarity', 'common')
    set_code = card.get('set', '')
    
    analysis = {
        'card_name': card_name,
        'set_code': set_code,
        'rarity': rarity,
        'raw_usd_price': usd_price,
        'steps': []
    }
    
    # Step 2: Check if USD price exists
    if not usd_price:
        analysis['steps'].append({
            'step': 'price_check',
            'result': 'FAIL',
            'reason': 'No USD price available'
        })
        return analysis
    
    # Step 3: Convert to float
    try:
        current_price = float(usd_price)
        analysis['current_price'] = current_price
        analysis['steps'].append({
            'step': 'price_conversion',
            'result': 'PASS',
            'current_price': current_price
        })
    except (ValueError, TypeError):
        analysis['steps'].append({
            'step': 'price_conversion',
            'result': 'FAIL',
            'reason': 'Could not convert price to float'
        })
        return analysis
    
    # Step 4: Check minimum price threshold
    if current_price < 0.50:
        analysis['steps'].append({
            'step': 'minimum_price_threshold',
            'result': 'FAIL',
            'reason': f'Price ${current_price} below minimum threshold of $0.50'
        })
        return analysis
    
    analysis['steps'].append({
        'step': 'minimum_price_threshold',
        'result': 'PASS',
        'current_price': current_price
    })
    
    # Step 5: Calculate expected price
    expected_price = scanner._calculate_expected_price(card)
    analysis['expected_price'] = expected_price
    analysis['steps'].append({
        'step': 'expected_price_calculation',
        'result': 'PASS',
        'expected_price': expected_price
    })
    
    # Step 6: Calculate anomaly score
    anomaly_score = scanner._calculate_anomaly_score(current_price, expected_price, card)
    analysis['anomaly_score'] = anomaly_score
    analysis['steps'].append({
        'step': 'anomaly_score_calculation',
        'result': 'PASS',
        'anomaly_score': anomaly_score
    })
    
    # Step 7: Check anomaly threshold
    threshold = scanner.anomaly_thresholds['price_deviation']
    analysis['anomaly_threshold'] = threshold
    
    if anomaly_score < threshold:
        analysis['steps'].append({
            'step': 'anomaly_threshold_check',
            'result': 'FAIL',
            'reason': f'Anomaly score {anomaly_score:.3f} below threshold {threshold}'
        })
        return analysis
    
    analysis['steps'].append({
        'step': 'anomaly_threshold_check',
        'result': 'PASS',
        'anomaly_score': anomaly_score,
        'threshold': threshold
    })
    
    # Step 8: Determine anomaly type
    anomaly_type = scanner._determine_anomaly_type(current_price, expected_price, anomaly_score)
    analysis['anomaly_type'] = anomaly_type
    
    if not anomaly_type:
        analysis['steps'].append({
            'step': 'anomaly_type_determination',
            'result': 'FAIL',
            'reason': 'No anomaly type determined'
        })
        return analysis
    
    analysis['steps'].append({
        'step': 'anomaly_type_determination',
        'result': 'PASS',
        'anomaly_type': anomaly_type
    })
    
    # Step 9: Calculate confidence
    confidence = scanner._calculate_confidence(card, anomaly_score)
    analysis['confidence'] = confidence
    analysis['steps'].append({
        'step': 'confidence_calculation',
        'result': 'PASS',
        'confidence': confidence
    })
    
    # Step 10: Check confidence threshold
    confidence_threshold = scanner.anomaly_thresholds['confidence_threshold']
    analysis['confidence_threshold'] = confidence_threshold
    
    if confidence < confidence_threshold:
        analysis['steps'].append({
            'step': 'confidence_threshold_check',
            'result': 'FAIL',
            'reason': f'Confidence {confidence:.3f} below threshold {confidence_threshold}'
        })
        return analysis
    
    analysis['steps'].append({
        'step': 'confidence_threshold_check',
        'result': 'PASS',
        'confidence': confidence,
        'threshold': confidence_threshold
    })
    
    # Step 11: Final result
    analysis['final_result'] = 'ANOMALY_DETECTED'
    analysis['steps'].append({
        'step': 'final_result',
        'result': 'PASS',
        'message': 'Card would be flagged as anomaly'
    })
    
    return analysis

def search_for_bane_variants(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Search for cards with 'Bane' or 'Progress' in the name."""
    variants = []
    
    for card in cards:
        card_name = card.get('name', '').lower()
        if 'bane' in card_name or 'progress' in card_name:
            variants.append(card)
    
    return variants

def get_bane_of_progress_printings(api_client) -> List[Dict[str, Any]]:
    """Get all printings of Bane of Progress across all sets."""
    logger.info("Searching for all Bane of Progress printings...")
    
    try:
        # Search for all printings of Bane of Progress
        if hasattr(api_client, 'client') and hasattr(api_client.client, 'search_cards'):
            # Use direct Scryfall search for all printings
            printings = api_client.client.search_cards(
                '!"Bane of Progress"',
                unique='prints'
            )
        else:
            printings = api_client.search_cards('"Bane of Progress"')
        
        logger.info(f"Found {len(printings)} printings of Bane of Progress")
        return printings
        
    except Exception as e:
        logger.error(f"Error searching for Bane of Progress printings: {e}")
        return []

def main():
    """Main investigation function."""
    logger.info("Starting Bane of Progress investigation...")
    
    # Initialize API client and scanner
    logger.info("Initializing API client...")
    api_client = create_unified_client(provider="scryfall")
    
    if not api_client.test_connection():
        logger.error("Failed to connect to API")
        return
    
    logger.info("Initializing set scanner...")
    scanner = SetScanner(api_client)
    
    # Step 1: Get all cards from FIC set
    logger.info("Getting all cards from FIC set...")
    fic_cards = scanner._get_set_cards('fic')
    
    if not fic_cards:
        logger.error("No cards found in FIC set")
        return
    
    logger.info(f"Found {len(fic_cards)} cards in FIC set")
    
    # Step 2: Search for Bane of Progress in FIC set
    logger.info("Searching for 'Bane of Progress' in FIC set...")
    bane_in_fic = None
    
    for card in fic_cards:
        if card.get('name', '').lower() == 'bane of progress':
            bane_in_fic = card
            break
    
    if bane_in_fic:
        logger.info("✓ Found Bane of Progress in FIC set!")
        print("=" * 60)
        print("BANE OF PROGRESS FOUND IN FIC SET")
        print("=" * 60)
        print(format_card_data(bane_in_fic))
        
        # Step 3: Run through anomaly detection
        logger.info("Running anomaly detection analysis...")
        analysis = analyze_card_anomaly_detection(scanner, bane_in_fic)
        
        print("\n" + "=" * 60)
        print("ANOMALY DETECTION ANALYSIS")
        print("=" * 60)
        print(f"Card: {analysis['card_name']}")
        print(f"Set: {analysis['set_code']}")
        print(f"Rarity: {analysis['rarity']}")
        print(f"Current Price: ${analysis.get('current_price', 'N/A')}")
        print(f"Expected Price: ${analysis.get('expected_price', 'N/A')}")
        print(f"Anomaly Score: {analysis.get('anomaly_score', 'N/A')}")
        print(f"Anomaly Threshold: {analysis.get('anomaly_threshold', 'N/A')}")
        print(f"Confidence: {analysis.get('confidence', 'N/A')}")
        print(f"Confidence Threshold: {analysis.get('confidence_threshold', 'N/A')}")
        print(f"Anomaly Type: {analysis.get('anomaly_type', 'N/A')}")
        print(f"Final Result: {analysis.get('final_result', 'NOT_ANOMALY')}")
        
        print("\nStep-by-step analysis:")
        for i, step in enumerate(analysis['steps'], 1):
            status = "✓" if step['result'] == 'PASS' else "✗"
            print(f"{i}. {step['step']}: {status} {step['result']}")
            if step['result'] == 'FAIL':
                print(f"   Reason: {step.get('reason', 'Unknown')}")
            elif 'current_price' in step:
                print(f"   Current Price: ${step['current_price']}")
            elif 'expected_price' in step:
                print(f"   Expected Price: ${step['expected_price']}")
            elif 'anomaly_score' in step:
                print(f"   Anomaly Score: {step['anomaly_score']}")
            elif 'confidence' in step:
                print(f"   Confidence: {step['confidence']}")
            elif 'anomaly_type' in step:
                print(f"   Anomaly Type: {step['anomaly_type']}")
        
        # Save detailed analysis
        with open('bane_of_progress_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        
    else:
        logger.warning("✗ Bane of Progress NOT found in FIC set")
        print("=" * 60)
        print("BANE OF PROGRESS NOT FOUND IN FIC SET")
        print("=" * 60)
        
        # Step 4: Search for similar cards
        logger.info("Searching for cards with 'Bane' or 'Progress' in name...")
        variants = search_for_bane_variants(fic_cards)
        
        if variants:
            print(f"\nFound {len(variants)} cards with 'Bane' or 'Progress' in name:")
            for card in variants:
                print(f"- {card.get('name', 'Unknown')}")
        else:
            print("\nNo cards found with 'Bane' or 'Progress' in name")
    
    # Step 5: Get all printings of Bane of Progress
    logger.info("Getting all printings of Bane of Progress...")
    all_printings = get_bane_of_progress_printings(api_client)
    
    print("\n" + "=" * 60)
    print("ALL BANE OF PROGRESS PRINTINGS")
    print("=" * 60)
    
    if all_printings:
        print(f"Found {len(all_printings)} printings of Bane of Progress:")
        
        for printing in all_printings:
            set_code = printing.get('set', 'Unknown')
            set_name = printing.get('set_name', 'Unknown')
            prices = printing.get('prices', {})
            usd_price = prices.get('usd', 'N/A')
            rarity = printing.get('rarity', 'Unknown')
            released_at = printing.get('released_at', 'Unknown')
            
            print(f"\n- Set: {set_code.upper()} ({set_name})")
            print(f"  Released: {released_at}")
            print(f"  Rarity: {rarity}")
            print(f"  USD Price: ${usd_price}")
            
            # Check if this is the FIC printing
            if set_code.lower() == 'fic':
                print("  *** THIS IS THE FIC PRINTING ***")
    else:
        print("No printings of Bane of Progress found")
    
    # Step 6: Summary and recommendations
    print("\n" + "=" * 60)
    print("INVESTIGATION SUMMARY")
    print("=" * 60)
    
    if bane_in_fic:
        print("✓ Bane of Progress exists in FIC set data")
        
        final_result = analysis.get('final_result', 'NOT_ANOMALY')
        if final_result == 'ANOMALY_DETECTED':
            print("✓ Card passes all anomaly detection checks")
            print("→ The card should be flagged as an anomaly")
        else:
            print("✗ Card fails anomaly detection")
            failed_steps = [step for step in analysis['steps'] if step['result'] == 'FAIL']
            if failed_steps:
                print("→ Failed at step:", failed_steps[0]['step'])
                print("→ Reason:", failed_steps[0].get('reason', 'Unknown'))
    else:
        print("✗ Bane of Progress NOT found in FIC set data")
        print("→ This indicates a data retrieval issue")
    
    if all_printings:
        fic_printing = next((p for p in all_printings if p.get('set', '').lower() == 'fic'), None)
        if fic_printing:
            print("✓ FIC printing exists in Scryfall database")
        else:
            print("✗ FIC printing NOT found in Scryfall database")
    
    print("\nRecommendations:")
    if not bane_in_fic:
        print("1. Check set code mapping - 'fic' might not be the correct code")
        print("2. Verify FIC set is properly indexed in Scryfall")
        print("3. Check if card is in a different variant/collector number")
    elif analysis.get('final_result') != 'ANOMALY_DETECTED':
        failed_steps = [step for step in analysis['steps'] if step['result'] == 'FAIL']
        if failed_steps:
            step_name = failed_steps[0]['step']
            if step_name == 'minimum_price_threshold':
                print("1. Card price is below minimum threshold - consider lowering threshold")
            elif step_name == 'anomaly_threshold_check':
                print("1. Anomaly score is below threshold - consider lowering threshold")
            elif step_name == 'confidence_threshold_check':
                print("1. Confidence is below threshold - consider lowering threshold")
    
    logger.info("Investigation completed")

if __name__ == "__main__":
    main()