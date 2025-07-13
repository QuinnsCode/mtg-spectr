#!/usr/bin/env python3
"""
Test Revised Multipliers for FIC Cards

This script tests the proposed multiplier changes against FIC card prices
to see if they improve accuracy.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from typing import Dict, List, Optional, Any, Tuple
from data.unified_api_client import create_unified_client
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RevisedMultiplierTester:
    """Test revised multipliers against FIC cards"""
    
    def __init__(self):
        """Initialize the tester"""
        self.api_client = create_unified_client()
        
        # Current multipliers
        self.current_base_prices = {
            'common': 0.15,
            'uncommon': 0.40,
            'rare': 1.50,
            'mythic': 4.00
        }
        
        # Revised multipliers
        self.revised_base_prices = {
            'common': 0.20,
            'uncommon': 0.70,
            'rare': 2.75,
            'mythic': 7.00
        }
        
    def test_multipliers(self, sample_size: int = 20) -> Dict[str, Any]:
        """
        Test current vs revised multipliers
        
        Args:
            sample_size: Number of cards to test
            
        Returns:
            Dictionary with test results
        """
        print("=" * 60)
        print("TESTING REVISED MULTIPLIERS")
        print("=" * 60)
        
        # Get sample cards
        cards = self._get_sample_cards(sample_size)
        
        if not cards:
            print("No cards found for testing")
            return {}
        
        print(f"Testing {len(cards)} cards:")
        print()
        
        results = []
        
        for i, card in enumerate(cards, 1):
            card_name = card.get('name', 'Unknown')
            actual_price = self._get_actual_price(card)
            
            if actual_price is None:
                continue
                
            # Calculate current expected price
            current_expected = self._calculate_current_expected_price(card)
            
            # Calculate revised expected price
            revised_expected = self._calculate_revised_expected_price(card)
            
            # Calculate errors
            current_error = abs(actual_price - current_expected)
            revised_error = abs(actual_price - revised_expected)
            
            # Calculate improvement
            improvement = ((current_error - revised_error) / current_error) * 100 if current_error > 0 else 0
            
            print(f"{i:2d}. {card_name}")
            print(f"    Actual: ${actual_price:.2f}")
            print(f"    Current Expected: ${current_expected:.2f} (error: ${current_error:.2f})")
            print(f"    Revised Expected: ${revised_expected:.2f} (error: ${revised_error:.2f})")
            print(f"    Improvement: {improvement:+.1f}%")
            print()
            
            results.append({
                'card_name': card_name,
                'actual_price': actual_price,
                'current_expected': current_expected,
                'revised_expected': revised_expected,
                'current_error': current_error,
                'revised_error': revised_error,
                'improvement': improvement,
                'rarity': card.get('rarity', 'unknown'),
                'type_line': card.get('type_line', '')
            })
        
        # Summary statistics
        if results:
            print("=" * 60)
            print("SUMMARY STATISTICS")
            print("=" * 60)
            
            avg_current_error = sum(r['current_error'] for r in results) / len(results)
            avg_revised_error = sum(r['revised_error'] for r in results) / len(results)
            avg_improvement = sum(r['improvement'] for r in results) / len(results)
            
            print(f"Average Current Error: ${avg_current_error:.2f}")
            print(f"Average Revised Error: ${avg_revised_error:.2f}")
            print(f"Average Improvement: {avg_improvement:+.1f}%")
            print()
            
            # Count improvements vs degradations
            improvements = sum(1 for r in results if r['improvement'] > 0)
            degradations = sum(1 for r in results if r['improvement'] < 0)
            
            print(f"Cards with improved accuracy: {improvements}/{len(results)} ({improvements/len(results)*100:.1f}%)")
            print(f"Cards with degraded accuracy: {degradations}/{len(results)} ({degradations/len(results)*100:.1f}%)")
            
            # Overall error reduction
            total_current_error = sum(r['current_error'] for r in results)
            total_revised_error = sum(r['revised_error'] for r in results)
            overall_improvement = ((total_current_error - total_revised_error) / total_current_error) * 100
            
            print(f"Overall Error Reduction: {overall_improvement:.1f}%")
            
            # Best and worst performers
            best_improvement = max(results, key=lambda x: x['improvement'])
            worst_improvement = min(results, key=lambda x: x['improvement'])
            
            print(f"\nBest Improvement: {best_improvement['card_name']} ({best_improvement['improvement']:+.1f}%)")
            print(f"Worst Improvement: {worst_improvement['card_name']} ({worst_improvement['improvement']:+.1f}%)")
        
        return {
            'results': results,
            'summary': {
                'avg_current_error': avg_current_error,
                'avg_revised_error': avg_revised_error,
                'avg_improvement': avg_improvement,
                'overall_improvement': overall_improvement,
                'cards_improved': improvements,
                'cards_degraded': degradations,
                'total_cards': len(results)
            }
        }
    
    def _get_sample_cards(self, sample_size: int) -> List[Dict[str, Any]]:
        """Get sample of FIC cards for testing"""
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
            
            # Filter to cards with pricing
            cards_with_prices = [card for card in cards if card.get('prices', {}).get('usd')]
            
            # Sort by price descending and take a diverse sample
            cards_with_prices.sort(key=lambda x: float(x.get('prices', {}).get('usd', 0)), reverse=True)
            
            # Take top, middle, and bottom cards for diverse sample
            sample_cards = []
            total_cards = len(cards_with_prices)
            
            if total_cards >= sample_size:
                # Take cards from different price ranges
                for i in range(sample_size):
                    index = int((i / sample_size) * total_cards)
                    if index < total_cards:
                        sample_cards.append(cards_with_prices[index])
            else:
                sample_cards = cards_with_prices
            
            return sample_cards
            
        except Exception as e:
            logger.error(f"Error getting sample cards: {e}")
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
    
    def _calculate_current_expected_price(self, card: Dict[str, Any]) -> float:
        """Calculate expected price using current multipliers"""
        # Base price by rarity
        rarity = card.get('rarity', 'common')
        expected = self.current_base_prices.get(rarity, 1.00)
        
        # Type line adjustments
        type_line = card.get('type_line', '')
        
        if 'Legendary' in type_line:
            expected *= 2.5
        if 'Planeswalker' in type_line:
            expected *= 3.0
        elif 'Creature' in type_line:
            expected *= 1.3
        if 'Artifact' in type_line:
            expected *= 1.2
        if 'Land' in type_line:
            expected *= 1.2
        
        # Mana cost adjustments
        mana_cost = card.get('mana_cost', '')
        if mana_cost:
            mana_symbols = mana_cost.count('{')
            if mana_symbols == 0:
                expected *= 1.5
            elif mana_symbols == 1:
                expected *= 1.3
            elif mana_symbols == 2:
                expected *= 1.1
            elif mana_symbols >= 7:
                expected *= 0.6
            elif mana_symbols >= 5:
                expected *= 0.8
        
        # Commander set multiplier
        expected *= 1.4
        
        # Age adjustment
        released_at = card.get('released_at', '')
        if released_at:
            try:
                release_year = int(released_at[:4])
                current_year = datetime.now().year
                age_years = current_year - release_year
                
                if age_years >= 10:
                    expected *= 1.5
                elif age_years >= 5:
                    expected *= 1.2
                elif age_years >= 2:
                    expected *= 1.1
            except (ValueError, IndexError):
                pass
        
        return max(expected, 0.10)
    
    def _calculate_revised_expected_price(self, card: Dict[str, Any]) -> float:
        """Calculate expected price using revised multipliers"""
        # Base price by rarity (revised)
        rarity = card.get('rarity', 'common')
        expected = self.revised_base_prices.get(rarity, 1.00)
        
        # Type line adjustments (revised)
        type_line = card.get('type_line', '')
        
        if 'Legendary' in type_line and 'Creature' in type_line:
            expected *= 3.2  # Higher for legendary creatures
        elif 'Legendary' in type_line:
            expected *= 2.5  # Keep current for other legendary types
            
        if 'Planeswalker' in type_line:
            expected *= 3.0
        elif 'Creature' in type_line:
            expected *= 1.3
            
        # Equipment gets special handling
        if 'Equipment' in type_line:
            expected *= 1.8
        elif 'Artifact' in type_line:
            expected *= 1.4
            
        if 'Land' in type_line:
            expected *= 1.2
        
        # Instant/Sorcery multiplier
        if 'Instant' in type_line or 'Sorcery' in type_line:
            expected *= 1.3
        
        # Mana cost adjustments (same as current)
        mana_cost = card.get('mana_cost', '')
        if mana_cost:
            mana_symbols = mana_cost.count('{')
            if mana_symbols == 0:
                expected *= 1.5
            elif mana_symbols == 1:
                expected *= 1.3
            elif mana_symbols == 2:
                expected *= 1.1
            elif mana_symbols >= 7:
                expected *= 0.6
            elif mana_symbols >= 5:
                expected *= 0.8
        
        # Commander set multiplier (revised)
        expected *= 2.2
        
        # Age adjustment (same as current)
        released_at = card.get('released_at', '')
        if released_at:
            try:
                release_year = int(released_at[:4])
                current_year = datetime.now().year
                age_years = current_year - release_year
                
                if age_years >= 10:
                    expected *= 1.5
                elif age_years >= 5:
                    expected *= 1.2
                elif age_years >= 2:
                    expected *= 1.1
            except (ValueError, IndexError):
                pass
        
        return max(expected, 0.10)

def main():
    """Main function to run the multiplier test"""
    try:
        tester = RevisedMultiplierTester()
        results = tester.test_multipliers(sample_size=20)
        
        # Save results to file
        if results:
            import json
            output_file = 'revised_multipliers_test_results.json'
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Results saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())