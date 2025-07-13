#!/usr/bin/env python3
"""
FIC (Adventures in the Forgotten Realms Commander) Pricing Analysis Test

This script analyzes pricing calculations for FIC cards to understand
why expected prices are consistently lower than actual prices.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from typing import Dict, List, Optional, Any
from data.unified_api_client import create_unified_client
from analysis.set_scanner import SetScanner
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FICPricingAnalyzer:
    """Analyzer for FIC pricing calculations"""
    
    def __init__(self):
        """Initialize the analyzer"""
        self.api_client = create_unified_client()
        self.scanner = SetScanner(self.api_client)
        
    def analyze_fic_pricing(self, max_cards: int = 10) -> Dict[str, Any]:
        """
        Analyze FIC pricing calculations for a sample of cards
        
        Args:
            max_cards: Maximum number of cards to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        print("=" * 60)
        print("FIC (Adventures in the Forgotten Realms Commander) Pricing Analysis")
        print("=" * 60)
        
        # Get FIC cards
        fic_cards = self._get_fic_cards(max_cards)
        
        if not fic_cards:
            print("No FIC cards found")
            return {}
            
        print(f"Analyzing {len(fic_cards)} FIC cards:")
        print()
        
        results = []
        
        for i, card in enumerate(fic_cards, 1):
            card_name = card.get('name', 'Unknown')
            print(f"{i}. {card_name}")
            print("-" * 50)
            
            # Get actual price
            actual_price = self._get_actual_price(card)
            if actual_price is None:
                print("   No pricing data available")
                print()
                continue
                
            # Calculate expected price step by step
            expected_price, calculation_steps = self._calculate_expected_price_detailed(card)
            
            # Print detailed breakdown
            print(f"   Actual Price: ${actual_price:.2f}")
            print(f"   Expected Price: ${expected_price:.2f}")
            print(f"   Difference: ${actual_price - expected_price:.2f} ({((actual_price - expected_price) / expected_price * 100):+.1f}%)")
            print()
            print("   Calculation Steps:")
            for step in calculation_steps:
                print(f"     {step}")
            print()
            
            # Check for anomaly
            anomaly_info = self.scanner._analyze_card_anomalies(card)
            if anomaly_info:
                print(f"   Anomaly Detected: {anomaly_info['anomaly_type']}")
                print(f"   Anomaly Score: {anomaly_info['anomaly_score']:.2f}")
                print(f"   Confidence: {anomaly_info['confidence']:.2f}")
            else:
                print("   No anomaly detected")
            print()
            
            results.append({
                'card_name': card_name,
                'actual_price': actual_price,
                'expected_price': expected_price,
                'difference': actual_price - expected_price,
                'percentage_diff': ((actual_price - expected_price) / expected_price * 100) if expected_price > 0 else 0,
                'calculation_steps': calculation_steps,
                'anomaly_info': anomaly_info,
                'card_data': {
                    'rarity': card.get('rarity', 'unknown'),
                    'type_line': card.get('type_line', ''),
                    'mana_cost': card.get('mana_cost', ''),
                    'set_code': card.get('set', ''),
                    'collector_number': card.get('collector_number', '')
                }
            })
            
        # Print summary
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        if results:
            avg_actual = sum(r['actual_price'] for r in results) / len(results)
            avg_expected = sum(r['expected_price'] for r in results) / len(results)
            avg_diff = sum(r['difference'] for r in results) / len(results)
            
            print(f"Average Actual Price: ${avg_actual:.2f}")
            print(f"Average Expected Price: ${avg_expected:.2f}")
            print(f"Average Difference: ${avg_diff:.2f}")
            print(f"Average Percentage Difference: {(avg_diff / avg_expected * 100):+.1f}%")
            print()
            
            # Count cards by difference ranges
            undervalued = sum(1 for r in results if r['difference'] > 0)
            overvalued = sum(1 for r in results if r['difference'] < 0)
            
            print(f"Cards with actual > expected: {undervalued}/{len(results)} ({undervalued/len(results)*100:.1f}%)")
            print(f"Cards with actual < expected: {overvalued}/{len(results)} ({overvalued/len(results)*100:.1f}%)")
            print()
            
            # Show multipliers analysis
            print("MULTIPLIER ANALYSIS:")
            print("Current multipliers being applied:")
            print("  - Commander sets: 1.4x")
            print("  - Legendary creatures: 2.5x")
            print("  - Planeswalkers: 3.0x")
            print("  - Other creatures: 1.3x")
            print("  - Artifacts: 1.2x")
            print("  - Lands: 1.2x")
            print()
            
            # Check if commander multiplier is too low
            if avg_actual > avg_expected * 1.5:
                print("RECOMMENDATION: Commander set multiplier (1.4x) may be too low")
                suggested_multiplier = avg_actual / (avg_expected / 1.4)
                print(f"Suggested multiplier: {suggested_multiplier:.1f}x")
        
        return {
            'analysis_results': results,
            'timestamp': datetime.now().isoformat(),
            'set_code': 'afc',
            'cards_analyzed': len(results)
        }
    
    def _get_fic_cards(self, max_cards: int) -> List[Dict[str, Any]]:
        """Get FIC cards from the API"""
        try:
            # AFC is the correct set code for Adventures in the Forgotten Realms Commander
            query = "e:afc"
            
            # Use the underlying Scryfall client
            if hasattr(self.api_client, 'client') and hasattr(self.api_client.client, 'search_cards'):
                cards = self.api_client.client.search_cards(
                    query, 
                    unique='prints',
                    order='name'
                )
            else:
                cards = self.api_client.search_cards(query)
            
            # Filter to cards with pricing and limit
            cards_with_prices = []
            for card in cards:
                if card.get('prices', {}).get('usd'):
                    cards_with_prices.append(card)
                    if len(cards_with_prices) >= max_cards:
                        break
            
            return cards_with_prices
            
        except Exception as e:
            logger.error(f"Error getting FIC cards: {e}")
            return []
    
    def _get_actual_price(self, card: Dict[str, Any]) -> Optional[float]:
        """Get actual USD price for a card"""
        try:
            usd_price = card.get('prices', {}).get('usd')
            if usd_price:
                return float(usd_price)
        except (ValueError, TypeError):
            pass
        return None
    
    def _calculate_expected_price_detailed(self, card: Dict[str, Any]) -> tuple[float, List[str]]:
        """Calculate expected price with detailed step-by-step breakdown"""
        steps = []
        
        # Base price by rarity
        rarity = card.get('rarity', 'common')
        base_prices = {
            'common': 0.15,
            'uncommon': 0.40,
            'rare': 1.50,
            'mythic': 4.00
        }
        
        expected = base_prices.get(rarity, 1.00)
        steps.append(f"Base price ({rarity}): ${expected:.2f}")
        
        # Type line adjustments
        type_line = card.get('type_line', '')
        
        if 'Legendary' in type_line:
            old_expected = expected
            expected *= 2.5
            steps.append(f"Legendary multiplier (2.5x): ${old_expected:.2f} -> ${expected:.2f}")
            
        if 'Planeswalker' in type_line:
            old_expected = expected
            expected *= 3.0
            steps.append(f"Planeswalker multiplier (3.0x): ${old_expected:.2f} -> ${expected:.2f}")
            
        elif 'Creature' in type_line:
            old_expected = expected
            expected *= 1.3
            steps.append(f"Creature multiplier (1.3x): ${old_expected:.2f} -> ${expected:.2f}")
            
        if 'Artifact' in type_line:
            old_expected = expected
            expected *= 1.2
            steps.append(f"Artifact multiplier (1.2x): ${old_expected:.2f} -> ${expected:.2f}")
            
        if 'Land' in type_line:
            old_expected = expected
            expected *= 1.2
            steps.append(f"Land multiplier (1.2x): ${old_expected:.2f} -> ${expected:.2f}")
        
        # Mana cost adjustments
        mana_cost = card.get('mana_cost', '')
        if mana_cost:
            mana_symbols = mana_cost.count('{')
            old_expected = expected
            
            if mana_symbols == 0:
                expected *= 1.5
                steps.append(f"Free spell multiplier (1.5x): ${old_expected:.2f} -> ${expected:.2f}")
            elif mana_symbols == 1:
                expected *= 1.3
                steps.append(f"Very cheap spell multiplier (1.3x): ${old_expected:.2f} -> ${expected:.2f}")
            elif mana_symbols == 2:
                expected *= 1.1
                steps.append(f"Cheap spell multiplier (1.1x): ${old_expected:.2f} -> ${expected:.2f}")
            elif mana_symbols >= 7:
                expected *= 0.6
                steps.append(f"Very expensive spell multiplier (0.6x): ${old_expected:.2f} -> ${expected:.2f}")
            elif mana_symbols >= 5:
                expected *= 0.8
                steps.append(f"Expensive spell multiplier (0.8x): ${old_expected:.2f} -> ${expected:.2f}")
        
        # Set-based adjustments (Commander set)
        set_code = card.get('set', '')
        if set_code:
            old_expected = expected
            if set_code.startswith('c') or 'commander' in set_code.lower() or set_code == 'afc':
                expected *= 1.4
                steps.append(f"Commander set multiplier (1.4x): ${old_expected:.2f} -> ${expected:.2f}")
        
        # Age adjustment
        released_at = card.get('released_at', '')
        if released_at:
            try:
                release_year = int(released_at[:4])
                current_year = datetime.now().year
                age_years = current_year - release_year
                old_expected = expected
                
                if age_years >= 10:
                    expected *= 1.5
                    steps.append(f"Age multiplier (10+ years, 1.5x): ${old_expected:.2f} -> ${expected:.2f}")
                elif age_years >= 5:
                    expected *= 1.2
                    steps.append(f"Age multiplier (5-9 years, 1.2x): ${old_expected:.2f} -> ${expected:.2f}")
                elif age_years >= 2:
                    expected *= 1.1
                    steps.append(f"Age multiplier (2-4 years, 1.1x): ${old_expected:.2f} -> ${expected:.2f}")
            except (ValueError, IndexError):
                pass
        
        # Minimum price floor
        final_expected = max(expected, 0.10)
        if final_expected != expected:
            steps.append(f"Minimum price floor applied: ${expected:.2f} -> ${final_expected:.2f}")
        
        return final_expected, steps

def main():
    """Main function to run the FIC pricing analysis"""
    try:
        analyzer = FICPricingAnalyzer()
        results = analyzer.analyze_fic_pricing(max_cards=10)
        
        # Optionally save results to file
        if results:
            import json
            output_file = 'fic_pricing_analysis.json'
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Results saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())