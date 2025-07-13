#!/usr/bin/env python3
"""
Debug script to analyze FIC set cards using set scanner to demonstrate
how the anomaly detection works and find examples of cards that are
flagged as anomalies.
"""

import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from analysis.set_scanner import SetScanner
from data.unified_api_client import create_unified_client
from data.database import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_fic_set_analysis():
    """Analyze FIC set cards to find examples of anomalies."""
    
    print("=" * 80)
    print("FIC SET ANOMALY ANALYSIS")
    print("=" * 80)
    
    # Initialize components
    client = create_unified_client()
    database_manager = DatabaseManager()
    set_scanner = SetScanner(api_client=client, database_manager=database_manager)
    
    # Check if FIC set is available
    print("1. Checking FIC set availability...")
    available_sets = set_scanner.get_available_sets()
    fic_set = None
    for set_info in available_sets:
        if set_info.get('code') == 'fic':
            fic_set = set_info
            break
    
    if fic_set:
        print(f"✓ FIC set found: {fic_set.get('name', 'Unknown')}")
        print(f"  - Card count: {fic_set.get('card_count', 'Unknown')}")
        print(f"  - Release date: {fic_set.get('released_at', 'Unknown')}")
    else:
        print("❌ FIC set not available for scanning")
        print("Available sets with 'fic' or 'commander' in name:")
        for set_info in available_sets:
            if ('fic' in set_info.get('code', '').lower() or 
                'commander' in set_info.get('name', '').lower()):
                print(f"  - {set_info.get('name', 'Unknown')} ({set_info.get('code', 'Unknown')})")
        return
    
    # Get FIC set cards
    print("\n2. Getting FIC set cards...")
    fic_cards = set_scanner._get_set_cards('fic')
    print(f"Found {len(fic_cards)} cards in FIC set")
    
    # Analyze each card
    print("\n3. Analyzing cards for anomalies...")
    anomaly_cards = []
    non_anomaly_cards = []
    
    for i, card in enumerate(fic_cards, 1):
        card_name = card.get('name', f'Card {i}')
        prices = card.get('prices', {})
        usd_price = prices.get('usd')
        
        if usd_price:
            try:
                current_price = float(usd_price)
                
                # Analyze using set scanner
                anomaly_info = set_scanner._analyze_card_anomalies(card)
                
                if anomaly_info:
                    anomaly_cards.append({
                        'name': card_name,
                        'price': current_price,
                        'info': anomaly_info
                    })
                else:
                    # Calculate components to understand why it's not an anomaly
                    expected_price = set_scanner._calculate_expected_price(card)
                    anomaly_score = set_scanner._calculate_anomaly_score(current_price, expected_price, card)
                    confidence = set_scanner._calculate_confidence(card, anomaly_score)
                    
                    non_anomaly_cards.append({
                        'name': card_name,
                        'price': current_price,
                        'expected_price': expected_price,
                        'anomaly_score': anomaly_score,
                        'confidence': confidence,
                        'rarity': card.get('rarity', 'Unknown'),
                        'type_line': card.get('type_line', 'Unknown')
                    })
            except (ValueError, TypeError):
                continue
    
    print(f"\n4. RESULTS SUMMARY")
    print("-" * 50)
    print(f"Total cards analyzed: {len(fic_cards)}")
    print(f"Cards with USD pricing: {len(anomaly_cards) + len(non_anomaly_cards)}")
    print(f"Anomalies found: {len(anomaly_cards)}")
    print(f"Non-anomalies: {len(non_anomaly_cards)}")
    
    # Show anomalies found
    if anomaly_cards:
        print(f"\n5. ANOMALIES FOUND")
        print("-" * 50)
        for anomaly in anomaly_cards:
            info = anomaly['info']
            print(f"Card: {anomaly['name']}")
            print(f"  - Current Price: ${anomaly['price']:.2f}")
            print(f"  - Expected Price: ${info['expected_price']:.2f}")
            print(f"  - Anomaly Type: {info['anomaly_type']}")
            print(f"  - Anomaly Score: {info['anomaly_score']:.3f}")
            print(f"  - Confidence: {info['confidence']:.3f}")
            print(f"  - Rarity: {info['rarity']}")
            print()
    else:
        print(f"\n5. NO ANOMALIES FOUND")
        print("-" * 50)
        print("No cards in FIC set met the anomaly criteria")
    
    # Show some non-anomalies for comparison
    print(f"\n6. SAMPLE NON-ANOMALIES (for comparison)")
    print("-" * 50)
    
    # Sort by price descending to show most expensive non-anomalies
    non_anomaly_cards.sort(key=lambda x: x['price'], reverse=True)
    
    for i, card in enumerate(non_anomaly_cards[:5]):  # Show top 5
        print(f"{i+1}. {card['name']}")
        print(f"   - Current Price: ${card['price']:.2f}")
        print(f"   - Expected Price: ${card['expected_price']:.2f}")
        print(f"   - Anomaly Score: {card['anomaly_score']:.3f}")
        print(f"   - Confidence: {card['confidence']:.3f}")
        print(f"   - Rarity: {card['rarity']}")
        print(f"   - Type: {card['type_line']}")
        
        # Explain why it's not an anomaly
        thresholds = set_scanner.anomaly_thresholds
        if card['price'] < 0.50:
            print(f"   - Reason: Below minimum price (${card['price']:.2f} < $0.50)")
        elif card['anomaly_score'] < thresholds['price_deviation']:
            print(f"   - Reason: Low deviation ({card['anomaly_score']:.3f} < {thresholds['price_deviation']})")
        elif card['confidence'] < thresholds['confidence_threshold']:
            print(f"   - Reason: Low confidence ({card['confidence']:.3f} < {thresholds['confidence_threshold']})")
        else:
            print(f"   - Reason: Unknown (should be anomaly?)")
        print()
    
    # Show threshold analysis
    print(f"\n7. THRESHOLD ANALYSIS")
    print("-" * 50)
    print("Current Set Scanner Thresholds:")
    thresholds = set_scanner.anomaly_thresholds
    for key, value in thresholds.items():
        print(f"  - {key}: {value}")
    
    # Calculate stats on non-anomalies
    if non_anomaly_cards:
        scores = [card['anomaly_score'] for card in non_anomaly_cards]
        confidences = [card['confidence'] for card in non_anomaly_cards]
        
        print(f"\nNon-anomaly Statistics:")
        print(f"  - Max anomaly score: {max(scores):.3f}")
        print(f"  - Min anomaly score: {min(scores):.3f}")
        print(f"  - Avg anomaly score: {sum(scores)/len(scores):.3f}")
        print(f"  - Max confidence: {max(confidences):.3f}")
        print(f"  - Min confidence: {min(confidences):.3f}")
        print(f"  - Avg confidence: {sum(confidences)/len(confidences):.3f}")
        
        # Count cards that would be anomalies with lower thresholds
        would_be_anomalies_lower_score = sum(1 for score in scores if score >= 1.0)
        would_be_anomalies_lower_conf = sum(1 for conf in confidences if conf >= 0.4)
        
        print(f"\nWith lower thresholds:")
        print(f"  - Cards that would be anomalies (score >= 1.0): {would_be_anomalies_lower_score}")
        print(f"  - Cards that would be anomalies (conf >= 0.4): {would_be_anomalies_lower_conf}")
    
    # Look specifically for Bane of Progress
    print(f"\n8. BANE OF PROGRESS ANALYSIS")
    print("-" * 50)
    
    bane_found = False
    for card in non_anomaly_cards:
        if 'Bane of Progress' in card['name']:
            bane_found = True
            print(f"Found Bane of Progress in FIC set:")
            print(f"  - Current Price: ${card['price']:.2f}")
            print(f"  - Expected Price: ${card['expected_price']:.2f}")
            print(f"  - Anomaly Score: {card['anomaly_score']:.3f}")
            print(f"  - Confidence: {card['confidence']:.3f}")
            print(f"  - Rarity: {card['rarity']}")
            
            # Detailed analysis
            price_ratio = card['price'] / card['expected_price']
            print(f"  - Price Ratio: {price_ratio:.2f}x expected")
            
            if price_ratio > 2.0:
                print(f"  - This card is overvalued ({price_ratio:.2f}x expected)")
            elif price_ratio < 0.5:
                print(f"  - This card is undervalued ({price_ratio:.2f}x expected)")
            else:
                print(f"  - This card is reasonably priced")
            
            # Why not anomaly?
            if card['anomaly_score'] < thresholds['price_deviation']:
                print(f"  - Not anomaly: Score {card['anomaly_score']:.3f} < {thresholds['price_deviation']}")
            elif card['confidence'] < thresholds['confidence_threshold']:
                print(f"  - Not anomaly: Confidence {card['confidence']:.3f} < {thresholds['confidence_threshold']}")
            break
    
    if not bane_found:
        print("Bane of Progress not found in FIC set cards")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    debug_fic_set_analysis()