#!/usr/bin/env python3
"""
FIC High-Value Cards Analysis

This script looks at the most expensive cards in the FIC set to understand
what types of cards are actually valuable vs. what the algorithm expects.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from typing import Dict, List, Optional, Any
from data.unified_api_client import create_unified_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FICHighValueAnalyzer:
    """Analyzer for high-value FIC cards"""
    
    def __init__(self):
        """Initialize the analyzer"""
        self.api_client = create_unified_client()
        
    def analyze_high_value_cards(self, min_price: float = 1.0) -> List[Dict[str, Any]]:
        """
        Analyze high-value FIC cards to understand patterns
        
        Args:
            min_price: Minimum USD price to consider
            
        Returns:
            List of card analysis results
        """
        print("=" * 60)
        print("FIC High-Value Cards Analysis")
        print("=" * 60)
        
        # Get all FIC cards
        all_cards = self._get_all_fic_cards()
        
        # Filter to high-value cards
        high_value_cards = []
        for card in all_cards:
            actual_price = self._get_actual_price(card)
            if actual_price and actual_price >= min_price:
                high_value_cards.append({
                    'card': card,
                    'actual_price': actual_price
                })
        
        # Sort by price descending
        high_value_cards.sort(key=lambda x: x['actual_price'], reverse=True)
        
        print(f"Found {len(high_value_cards)} cards with price >= ${min_price:.2f}")
        print()
        
        results = []
        for i, card_data in enumerate(high_value_cards[:20], 1):  # Top 20
            card = card_data['card']
            actual_price = card_data['actual_price']
            
            card_name = card.get('name', 'Unknown')
            rarity = card.get('rarity', 'unknown')
            type_line = card.get('type_line', '')
            mana_cost = card.get('mana_cost', '')
            
            print(f"{i:2d}. {card_name} - ${actual_price:.2f}")
            print(f"     Rarity: {rarity.capitalize()}")
            print(f"     Type: {type_line}")
            print(f"     Mana Cost: {mana_cost}")
            
            # Calculate expected price
            expected_price, _ = self._calculate_expected_price_detailed(card)
            difference = actual_price - expected_price
            percentage_diff = (difference / expected_price * 100) if expected_price > 0 else 0
            
            print(f"     Expected: ${expected_price:.2f}")
            print(f"     Difference: ${difference:+.2f} ({percentage_diff:+.1f}%)")
            print()
            
            results.append({
                'card_name': card_name,
                'actual_price': actual_price,
                'expected_price': expected_price,
                'difference': difference,
                'percentage_diff': percentage_diff,
                'rarity': rarity,
                'type_line': type_line,
                'mana_cost': mana_cost,
                'is_legendary': 'Legendary' in type_line,
                'is_planeswalker': 'Planeswalker' in type_line,
                'is_creature': 'Creature' in type_line,
                'is_artifact': 'Artifact' in type_line,
                'is_land': 'Land' in type_line
            })
        
        # Analysis summary
        print("=" * 60)
        print("HIGH-VALUE CARD ANALYSIS")
        print("=" * 60)
        
        if results:
            # Type analysis
            legendary_count = sum(1 for r in results if r['is_legendary'])
            planeswalker_count = sum(1 for r in results if r['is_planeswalker'])
            creature_count = sum(1 for r in results if r['is_creature'])
            artifact_count = sum(1 for r in results if r['is_artifact'])
            land_count = sum(1 for r in results if r['is_land'])
            
            print(f"Card type distribution in high-value cards:")
            print(f"  Legendary: {legendary_count}/{len(results)} ({legendary_count/len(results)*100:.1f}%)")
            print(f"  Planeswalkers: {planeswalker_count}/{len(results)} ({planeswalker_count/len(results)*100:.1f}%)")
            print(f"  Creatures: {creature_count}/{len(results)} ({creature_count/len(results)*100:.1f}%)")
            print(f"  Artifacts: {artifact_count}/{len(results)} ({artifact_count/len(results)*100:.1f}%)")
            print(f"  Lands: {land_count}/{len(results)} ({land_count/len(results)*100:.1f}%)")
            print()
            
            # Rarity analysis
            rarity_counts = {}
            for r in results:
                rarity = r['rarity']
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
            
            print("Rarity distribution in high-value cards:")
            for rarity, count in sorted(rarity_counts.items()):
                print(f"  {rarity.capitalize()}: {count}/{len(results)} ({count/len(results)*100:.1f}%)")
            print()
            
            # Price accuracy analysis
            underestimated = sum(1 for r in results if r['difference'] > 0)
            overestimated = sum(1 for r in results if r['difference'] < 0)
            
            print(f"Price estimation accuracy:")
            print(f"  Underestimated: {underestimated}/{len(results)} ({underestimated/len(results)*100:.1f}%)")
            print(f"  Overestimated: {overestimated}/{len(results)} ({overestimated/len(results)*100:.1f}%)")
            
            if underestimated > 0:
                avg_underestimation = sum(r['difference'] for r in results if r['difference'] > 0) / underestimated
                print(f"  Average underestimation: ${avg_underestimation:.2f}")
            
            if overestimated > 0:
                avg_overestimation = sum(abs(r['difference']) for r in results if r['difference'] < 0) / overestimated
                print(f"  Average overestimation: ${avg_overestimation:.2f}")
        
        return results
    
    def _get_all_fic_cards(self) -> List[Dict[str, Any]]:
        """Get all FIC cards from the API"""
        try:
            query = "e:afc"
            
            if hasattr(self.api_client, 'client') and hasattr(self.api_client.client, 'search_cards'):
                cards = self.api_client.client.search_cards(
                    query, 
                    unique='prints',
                    order='name'
                )
            else:
                cards = self.api_client.search_cards(query)
            
            return cards
            
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
        from datetime import datetime
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
    """Main function to run the high-value FIC analysis"""
    try:
        analyzer = FICHighValueAnalyzer()
        results = analyzer.analyze_high_value_cards(min_price=1.0)
        
        # Save results to file
        if results:
            import json
            output_file = 'fic_high_value_analysis.json'
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Results saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())