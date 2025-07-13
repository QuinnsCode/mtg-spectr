"""
Set Scanner Module - Comprehensive MTG Set Analysis

This module provides functionality to scan entire Magic: The Gathering sets
for pricing anomalies and market opportunities. It analyzes every card in a
set to identify undervalued, overvalued, or volatile pricing patterns.

Key Features:
- Full set scanning with automatic pagination support
- Enhanced expected price calculation based on multiple factors
- Anomaly detection with configurable thresholds
- Progress tracking and batch processing
- Export functionality for analysis results

Classes:
    SetScanResult: Container for set scanning results
    CardAnomalyInfo: Information about detected anomalies
    SetScanner: Main class for performing set analysis

Example:
    scanner = SetScanner(api_client)
    result = scanner.scan_set('dsk')  # Scan Duskmourn set
    anomalies = scanner.get_top_anomalies(result, 'undervalued', 10)
    scanner.export_results(result, 'duskmourn_analysis.json')
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import statistics
import json

from data.unified_api_client import UnifiedAPIClient, create_unified_client
from data.database import DatabaseManager

# Optional import for advanced analysis
try:
    from analysis.price_analyzer import PriceAnalyzer
except ImportError:
    PriceAnalyzer = None

logger = logging.getLogger(__name__)


@dataclass
class SetScanResult:
    """Results from scanning a complete set."""
    set_code: str
    set_name: str
    total_cards: int
    scanned_cards: int
    anomalies_found: int
    scan_duration: float
    anomaly_cards: List[Dict[str, Any]]
    price_statistics: Dict[str, float]
    scan_timestamp: str


@dataclass
class CardAnomalyInfo:
    """Information about a card's anomaly status."""
    card_name: str
    set_code: str
    current_price: float
    expected_price: float
    anomaly_score: float
    anomaly_type: str  # 'undervalued', 'overvalued', 'volatile'
    confidence: float
    rarity: str
    foil_status: str
    market_data: Dict[str, Any]


class SetScanner:
    """Scanner for analyzing entire MTG sets for price anomalies."""
    
    def __init__(self, api_client: Optional[UnifiedAPIClient] = None, 
                 database_manager: Optional[DatabaseManager] = None):
        """
        Initialize set scanner.
        
        Args:
            api_client: API client for card data
            database_manager: Database for storing results
        """
        self.api_client = api_client or create_unified_client()
        self.database_manager = database_manager
        self.price_analyzer = PriceAnalyzer(database_manager) if (database_manager and PriceAnalyzer) else None
        
        # Rate limiting for API calls
        self.min_request_interval = 0.1  # 100ms between requests
        self.last_request_time = 0
        
        # Anomaly detection parameters
        self.anomaly_thresholds = {
            'price_deviation': 0.7,  # Lowered to catch borderline cases like Bane of Progress
            'volatility_threshold': 0.3,  # 30% price volatility
            'minimum_sample_size': 3,  # Minimum data points for analysis
            'confidence_threshold': 0.4  # Lower confidence threshold to catch more anomalies
        }
    
    def get_available_sets(self) -> List[Dict[str, Any]]:
        """
        Get list of available sets for scanning.
        
        Returns:
            List[Dict]: Available sets with metadata
        """
        sets = self.api_client.get_sets()
        
        # Filter to scannable sets with reasonable card counts
        scannable_sets = []
        for set_info in sets:
            set_type = set_info.get('set_type', '')
            card_count = set_info.get('card_count', 0)
            is_digital = set_info.get('digital', False)
            
            # Include expansion sets, core sets, and supplemental sets
            # Exclude very small sets and digital-only sets
            if (set_type in ['expansion', 'core', 'masters', 'draft_innovation', 'commander', 'arsenal', 'premium', 'duel_deck'] and 
                not is_digital and
                card_count >= 8):  # At least 8 cards for meaningful analysis (Commander Collections are small)
                scannable_sets.append(set_info)
        
        # Sort alphabetically by set name
        scannable_sets.sort(key=lambda x: x.get('name', '').lower())
        
        return scannable_sets
    
    def scan_set(self, set_code: str, 
                 progress_callback: Optional[callable] = None,
                 max_cards: Optional[int] = None) -> SetScanResult:
        """
        Scan all cards in a set for anomalies.
        
        Args:
            set_code: Set code to scan (e.g., 'dsk', 'blb')
            progress_callback: Optional callback for progress updates
            max_cards: Optional limit on cards to scan (for testing)
            
        Returns:
            SetScanResult: Comprehensive scan results
        """
        logger.info(f"Starting set scan for: {set_code}")
        start_time = time.time()
        
        try:
            # Get set information
            set_info = self._get_set_info(set_code)
            if not set_info:
                raise ValueError(f"Set not found: {set_code}")
            
            set_name = set_info.get('name', set_code)
            total_cards = set_info.get('card_count', 0)
            
            logger.info(f"Scanning {set_name} ({total_cards} cards)")
            
            # Get all cards in the set
            all_cards = self._get_set_cards(set_code)
            
            if max_cards:
                all_cards = all_cards[:max_cards]
            
            # Scan each card for pricing data and anomalies
            anomaly_cards = []
            scanned_count = 0
            
            for i, card in enumerate(all_cards):
                try:
                    # Rate limiting
                    self._rate_limit()
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(i + 1, len(all_cards), card.get('name', 'Unknown'))
                    
                    # Analyze card for anomalies
                    anomaly_info = self._analyze_card_anomalies(card)
                    
                    if anomaly_info:
                        anomaly_cards.append(anomaly_info)
                    
                    scanned_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error scanning card {card.get('name', 'Unknown')}: {e}")
                    continue
            
            # Calculate set-wide statistics
            price_stats = self._calculate_set_statistics(all_cards, anomaly_cards)
            
            # Create result
            scan_duration = time.time() - start_time
            result = SetScanResult(
                set_code=set_code,
                set_name=set_name,
                total_cards=total_cards,
                scanned_cards=scanned_count,
                anomalies_found=len(anomaly_cards),
                scan_duration=scan_duration,
                anomaly_cards=anomaly_cards,
                price_statistics=price_stats,
                scan_timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"Set scan completed: {scanned_count} cards scanned, {len(anomaly_cards)} anomalies found")
            return result
            
        except Exception as e:
            logger.error(f"Set scan failed: {e}")
            raise
    
    def _get_set_info(self, set_code: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific set."""
        try:
            # Try to get set info from the sets endpoint
            sets = self.api_client.get_sets()
            for set_info in sets:
                if set_info.get('code') == set_code:
                    return set_info
            return None
        except Exception as e:
            logger.error(f"Error getting set info: {e}")
            return None
    
    def _get_set_cards(self, set_code: str) -> List[Dict[str, Any]]:
        """Get all cards from a specific set."""
        try:
            # Use Scryfall search to get all cards in the set
            query = f"e:{set_code}"
            
            # Use the underlying Scryfall client for more advanced search options
            if hasattr(self.api_client, 'client') and hasattr(self.api_client.client, 'search_cards'):
                # Use 'prints' to get all printings and include extras for comprehensive coverage
                cards = self.api_client.client.search_cards(
                    query, 
                    unique='prints', 
                    order='collector_number',
                    include_extras=True
                )
            else:
                cards = self.api_client.search_cards(query)
            
            logger.info(f"Found {len(cards)} cards in set {set_code}")
            return cards
            
        except Exception as e:
            logger.error(f"Error getting set cards: {e}")
            return []
    
    def _analyze_card_anomalies(self, card: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a single card for pricing anomalies by comparing across different printings.
        
        Args:
            card: Card data from Scryfall API
            
        Returns:
            Optional[Dict]: Anomaly information if anomaly detected
        """
        try:
            card_name = card.get('name', '')
            if not card_name:
                return None
            
            # Get pricing data for this printing (prefer non-foil)
            prices = card.get('prices', {})
            usd_price = prices.get('usd')
            usd_foil_price = prices.get('usd_foil')
            
            # Determine which price to use and its value
            if usd_price:
                try:
                    current_price = float(usd_price)
                    if current_price >= 0.50:  # Skip very low-value cards
                        pass  # Use non-foil price
                    else:
                        current_price = None
                except (ValueError, TypeError):
                    current_price = None
            else:
                current_price = None
            
            # If non-foil price is not available or too low, try foil price
            if current_price is None and usd_foil_price:
                try:
                    foil_price = float(usd_foil_price)
                    if foil_price >= 0.50:  # Skip very low-value cards
                        current_price = foil_price
                except (ValueError, TypeError):
                    pass
            
            # If no valid price found, skip this card
            if current_price is None:
                return None
            
            # Get all printings of this card to compare prices
            all_printings = self._get_all_card_printings(card_name)
            
            # First try cross-printing comparison if multiple printings exist
            if all_printings and len(all_printings) >= 2:
                # Analyze price differences across printings
                anomaly_result = self._analyze_cross_printing_anomaly(card, all_printings)
                if anomaly_result:
                    return anomaly_result
            
            # Fallback to market-based anomaly detection for cards with few printings
            # or when cross-printing analysis doesn't find anomalies
            
            # Calculate expected price from other printings if available
            if all_printings and len(all_printings) >= 1:
                # Determine foil status for comparison
                card_prices = card.get('prices', {})
                target_usd = card_prices.get('usd')
                target_usd_foil = card_prices.get('usd_foil')
                
                # Prioritize non-foil, but use foil if that's what's available
                if target_usd and float(target_usd) > 0:
                    is_foil = False
                    price_key = 'usd'
                elif target_usd_foil and float(target_usd_foil) > 0:
                    is_foil = True
                    price_key = 'usd_foil'
                else:
                    return None
                
                # Use average price from other sets as expected price (same foil status only)
                other_prices = []
                target_set = card.get('set', '')
                
                for printing in all_printings:
                    if printing.get('set', '') != target_set:  # Skip same set
                        price_str = printing.get('prices', {}).get(price_key)
                        if price_str:
                            try:
                                price = float(price_str)
                                if price >= 0.25:  # Only include meaningful prices
                                    other_prices.append(price)
                            except (ValueError, TypeError):
                                continue
                
                if other_prices:
                    # Use minimum of other printings as expected price (most conservative)
                    expected_price = min(other_prices)
                else:
                    # No other printings with valid prices, skip this card
                    return None
            else:
                # No other printings exist, skip this card
                return None
            
            anomaly_score = self._calculate_anomaly_score(current_price, expected_price, card)
            anomaly_type = self._determine_anomaly_type(current_price, expected_price, anomaly_score)
            
            if anomaly_type:
                # Calculate confidence level
                confidence = self._calculate_confidence(card, anomaly_score)
                set_code = card.get('set', '')
                rarity = card.get('rarity', 'common')
                
                if confidence >= self.anomaly_thresholds['confidence_threshold']:
                    return {
                        'card_name': card_name,
                        'set_code': set_code,
                        'current_price': current_price,
                        'expected_price': expected_price,
                        'anomaly_score': anomaly_score,
                        'anomaly_type': anomaly_type,
                        'confidence': confidence,
                        'rarity': rarity,
                        'foil_status': 'foil' if is_foil else 'nonfoil',
                        'market_data': {
                            'usd_foil': prices.get('usd_foil'),
                            'eur': prices.get('eur'),
                            'tix': prices.get('tix'),
                            'type_line': card.get('type_line', ''),
                            'mana_cost': card.get('mana_cost', ''),
                            'collector_number': card.get('collector_number', ''),
                            'other_printings_count': len(other_prices),
                            'min_other_price': expected_price,
                            'avg_other_price': sum(other_prices) / len(other_prices),
                            'other_prices': other_prices,
                            'price_key_used': price_key,
                            'foil_comparison': is_foil,
                            'expected_price_source': 'minimum_other_printing',
                            'detection_method': 'market_based_fallback'
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"Error analyzing card {card.get('name', 'Unknown')}: {e}")
            return None
    
    def _calculate_expected_price_rule_based(self, card: Dict[str, Any]) -> float:
        """Calculate expected price based on card characteristics (DEPRECATED - kept for reference only)."""
        rarity = card.get('rarity', 'common')
        type_line = card.get('type_line', '')
        
        # Enhanced base price by rarity
        # Check if this is a Commander set
        set_code = card.get('set', '')
        is_commander_set = (set_code.startswith('c') or 'commander' in set_code.lower() or 
                           set_code in ['afc', 'nec', 'ncc', 'clb', 'dmc', 'brc', 'fic'])
        
        if is_commander_set:
            # Higher base prices for Commander sets due to format demand
            base_prices = {
                'common': 0.18,
                'uncommon': 0.50,
                'rare': 2.00,
                'mythic': 5.50
            }
        else:
            # Standard base prices
            base_prices = {
                'common': 0.15,
                'uncommon': 0.40,
                'rare': 1.50,
                'mythic': 4.00
            }
        
        expected = base_prices.get(rarity, 1.00)
        
        # Significant adjustments for card types
        if 'Legendary' in type_line and 'Creature' in type_line:
            expected *= 2.8  # Legendary creatures drive Commander deck construction
        elif 'Legendary' in type_line:
            expected *= 2.5  # Other legendary cards
        if 'Planeswalker' in type_line:
            expected *= 3.0  # Planeswalkers are generally valuable
        if 'Land' in type_line:
            expected *= 1.2  # Lands are often undervalued but useful
        elif 'Creature' in type_line:
            expected *= 1.3  # Creatures are generally more valuable
        if 'Artifact' in type_line:
            expected *= 1.2  # Artifacts are versatile
        if 'Equipment' in type_line:
            expected *= 1.3  # Equipment is popular in Commander
        if ('Instant' in type_line or 'Sorcery' in type_line) and is_commander_set:
            expected *= 1.1  # Spells get a small boost in Commander products
        
        # Adjust for mana cost (more nuanced)
        mana_cost = card.get('mana_cost', '')
        if mana_cost:
            mana_symbols = mana_cost.count('{')
            if mana_symbols == 0:  # Free spells
                expected *= 1.5
            elif mana_symbols == 1:  # Very cheap
                expected *= 1.3
            elif mana_symbols == 2:  # Cheap
                expected *= 1.1
            elif mana_symbols >= 7:  # Very expensive
                expected *= 0.6
            elif mana_symbols >= 5:  # Expensive
                expected *= 0.8
        
        # Set-based adjustments
        if set_code:
            # Commander-focused sets tend to have higher prices due to format demand
            if is_commander_set:
                expected *= 1.8  # Increased from 1.4 to better reflect Commander market
            # Masters sets often have reprints of valuable cards
            elif 'masters' in set_code.lower() or set_code.endswith('m'):
                expected *= 1.3
            # Core sets tend to be lower value
            elif set_code.startswith('m') and set_code[1:].isdigit():
                expected *= 0.8
        
        # Age adjustment (older cards tend to be more valuable)
        released_at = card.get('released_at', '')
        if released_at:
            try:
                from datetime import datetime
                release_year = int(released_at[:4])
                current_year = datetime.now().year
                age_years = current_year - release_year
                
                if age_years >= 10:  # 10+ years old
                    expected *= 1.5
                elif age_years >= 5:  # 5-9 years old
                    expected *= 1.2
                elif age_years >= 2:  # 2-4 years old
                    expected *= 1.1
            except (ValueError, IndexError):
                pass  # Invalid date format
        
        return max(expected, 0.10)  # Minimum expected price
    
    def _get_all_card_printings(self, card_name: str) -> List[Dict[str, Any]]:
        """Get all printings of a card across different sets."""
        try:
            # Use Scryfall's advanced search to get ALL printings of this card
            # The "prints" unique mode returns all printings across different sets
            if hasattr(self.api_client, 'client') and hasattr(self.api_client.client, 'search_cards'):
                # Use underlying Scryfall client for more control
                search_results = self.api_client.client.search_cards(
                    f'!"{card_name}"',  # Exact name match
                    unique='prints',    # Get all printings, not just unique cards
                    include_extras=False  # Don't include promo/special versions
                )
            else:
                # Fallback to unified client
                search_results = self.api_client.search_cards(f'!"{card_name}"')
            
            if not search_results:
                return []
            
            # Filter to cards with exact name match and valid USD prices (either normal or foil)
            valid_printings = []
            for printing in search_results:
                if printing.get('name', '').lower() == card_name.lower():
                    prices = printing.get('prices', {})
                    usd_price = prices.get('usd')
                    usd_foil_price = prices.get('usd_foil')
                    
                    # Include if either regular or foil price is available and meaningful
                    has_valid_price = False
                    if usd_price:
                        try:
                            if float(usd_price) >= 0.25:
                                has_valid_price = True
                        except (ValueError, TypeError):
                            pass
                    
                    if not has_valid_price and usd_foil_price:
                        try:
                            if float(usd_foil_price) >= 0.25:
                                has_valid_price = True
                        except (ValueError, TypeError):
                            pass
                    
                    if has_valid_price:
                        valid_printings.append(printing)
            
            return valid_printings
            
        except Exception as e:
            logger.warning(f"Error getting printings for {card_name}: {e}")
            return []
    
    def _analyze_cross_printing_anomaly(self, target_card: Dict[str, Any], 
                                       all_printings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze if a card's price is anomalous compared to its other printings."""
        try:
            target_name = target_card.get('name', '')
            target_set = target_card.get('set', '')
            target_prices = target_card.get('prices', {})
            
            # Determine if we're analyzing foil or non-foil
            target_usd = target_prices.get('usd')
            target_usd_foil = target_prices.get('usd_foil')
            
            # Prioritize non-foil, but analyze foil if that's what's available
            if target_usd and float(target_usd) > 0:
                target_price = float(target_usd)
                is_foil = False
                price_key = 'usd'
            elif target_usd_foil and float(target_usd_foil) > 0:
                target_price = float(target_usd_foil)
                is_foil = True
                price_key = 'usd_foil'
            else:
                return None
            
            # Collect prices from other printings (same foil status only)
            other_prices = []
            for printing in all_printings:
                if printing.get('set', '') != target_set:  # Skip same set
                    price_str = printing.get('prices', {}).get(price_key)
                    if price_str:
                        try:
                            price = float(price_str)
                            if price >= 0.25:
                                other_prices.append({
                                    'price': price,
                                    'set': printing.get('set', ''),
                                    'rarity': printing.get('rarity', ''),
                                    'set_name': printing.get('set_name', ''),
                                    'foil': is_foil
                                })
                        except (ValueError, TypeError):
                            continue
            
            if len(other_prices) < 1:
                return None  # Need at least one other printing to compare
            
            # Calculate statistics for other printings
            price_values = [p['price'] for p in other_prices]
            avg_other_price = sum(price_values) / len(price_values)
            min_other_price = min(price_values)
            max_other_price = max(price_values)
            
            # Use minimum price as expected price (most conservative comparison)
            expected_price = min_other_price
            
            # Determine if this is an anomaly
            price_ratio = target_price / expected_price
            
            # More liberal thresholds for real market comparison
            if price_ratio <= 0.6:  # Target price is 60% or less of minimum
                anomaly_type = 'undervalued'
                anomaly_score = (expected_price - target_price) / expected_price
            elif price_ratio >= 1.8:  # Target price is 180% or more of minimum
                anomaly_type = 'overvalued'
                anomaly_score = (target_price - expected_price) / expected_price
            else:
                return None  # No anomaly
            
            # Calculate confidence based on number of comparison points and price consistency
            std_dev = (sum((p - avg_other_price) ** 2 for p in price_values) / len(price_values)) ** 0.5
            coefficient_of_variation = std_dev / avg_other_price if avg_other_price > 0 else 1.0
            
            # Higher confidence when:
            # - More comparison printings available
            # - Other printings have consistent pricing (low coefficient of variation)
            # - Larger price difference
            base_confidence = min(anomaly_score * 0.8, 0.9)
            comparison_bonus = min(len(other_prices) * 0.05, 0.2)
            consistency_bonus = max(0, (0.3 - coefficient_of_variation) * 0.5)
            
            confidence = min(base_confidence + comparison_bonus + consistency_bonus, 1.0)
            
            # Require minimum confidence of 0.5 for market-based anomalies
            if confidence < 0.5:
                return None
            
            return {
                'card_name': target_name,
                'set_code': target_set,
                'current_price': target_price,
                'expected_price': expected_price,  # Use minimum of other printings as "expected"
                'anomaly_score': anomaly_score,
                'anomaly_type': anomaly_type,
                'confidence': confidence,
                'rarity': target_card.get('rarity', 'unknown'),
                'foil_status': 'foil' if is_foil else 'nonfoil',
                'market_data': {
                    'comparison_printings': len(other_prices),
                    'avg_other_price': avg_other_price,
                    'min_other_price': min_other_price,
                    'max_other_price': max_other_price,
                    'expected_price_source': 'minimum_other_printing',
                    'other_printings': other_prices[:5],  # Include up to 5 other printings for reference
                    'price_ratio': price_ratio,
                    'coefficient_of_variation': coefficient_of_variation,
                    'type_line': target_card.get('type_line', ''),
                    'mana_cost': target_card.get('mana_cost', ''),
                    'collector_number': target_card.get('collector_number', ''),
                    'detection_method': 'cross_printing'
                }
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing cross-printing anomaly for {target_card.get('name', 'Unknown')}: {e}")
            return None
    
    def _calculate_anomaly_score(self, current_price: float, expected_price: float, 
                                card: Dict[str, Any]) -> float:
        """Calculate anomaly score for a card."""
        if expected_price == 0:
            return 0.0
        
        # Basic deviation score
        deviation = abs(current_price - expected_price) / expected_price
        
        # Adjust for card characteristics
        rarity = card.get('rarity', 'common')
        rarity_weights = {
            'common': 0.5,
            'uncommon': 0.7,
            'rare': 1.0,
            'mythic': 1.5
        }
        
        weight = rarity_weights.get(rarity, 1.0)
        
        return deviation * weight
    
    def _determine_anomaly_type(self, current_price: float, expected_price: float, 
                               anomaly_score: float) -> Optional[str]:
        """Determine the type of anomaly."""
        threshold = self.anomaly_thresholds['price_deviation']
        
        if anomaly_score < threshold:
            return None
        
        # More nuanced thresholds for better detection
        price_ratio = current_price / expected_price
        
        if price_ratio < 0.7:  # Current price < 70% of expected
            return 'undervalued'
        elif price_ratio > 1.5:  # Current price > 150% of expected
            return 'overvalued'
        else:
            return 'volatile'
    
    def _calculate_confidence(self, card: Dict[str, Any], anomaly_score: float) -> float:
        """Calculate confidence level for anomaly detection."""
        # Base confidence from anomaly score (more generous)
        base_confidence = min(anomaly_score / 2.0, 1.0)
        
        # Adjust for card characteristics
        rarity = card.get('rarity', 'common')
        if rarity in ['rare', 'mythic']:
            base_confidence *= 1.2
        
        # Adjust for price data availability
        prices = card.get('prices', {})
        price_sources = sum(1 for p in prices.values() if p is not None)
        if price_sources >= 3:
            base_confidence *= 1.1
        
        return min(base_confidence, 1.0)
    
    def _calculate_set_statistics(self, all_cards: List[Dict[str, Any]], 
                                 anomaly_cards: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate statistics for the entire set."""
        prices = []
        
        for card in all_cards:
            usd_price = card.get('prices', {}).get('usd')
            if usd_price:
                try:
                    prices.append(float(usd_price))
                except (ValueError, TypeError):
                    continue
        
        if not prices:
            return {}
        
        stats = {
            'total_cards_with_prices': len(prices),
            'average_price': statistics.mean(prices),
            'median_price': statistics.median(prices),
            'min_price': min(prices),
            'max_price': max(prices),
            'price_std_dev': statistics.stdev(prices) if len(prices) > 1 else 0,
            'anomaly_rate': len(anomaly_cards) / len(all_cards) if all_cards else 0,
            'undervalued_count': sum(1 for a in anomaly_cards if a['anomaly_type'] == 'undervalued'),
            'overvalued_count': sum(1 for a in anomaly_cards if a['anomaly_type'] == 'overvalued'),
            'volatile_count': sum(1 for a in anomaly_cards if a['anomaly_type'] == 'volatile')
        }
        
        return stats
    
    def _rate_limit(self):
        """Implement rate limiting for API calls."""
        current_time = time.time()
        if self.last_request_time > 0:
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def export_results(self, scan_result: SetScanResult, filename: str):
        """Export scan results to JSON file."""
        try:
            # Convert dataclass to dict
            result_dict = {
                'set_code': scan_result.set_code,
                'set_name': scan_result.set_name,
                'total_cards': scan_result.total_cards,
                'scanned_cards': scan_result.scanned_cards,
                'anomalies_found': scan_result.anomalies_found,
                'scan_duration': scan_result.scan_duration,
                'anomaly_cards': scan_result.anomaly_cards,
                'price_statistics': scan_result.price_statistics,
                'scan_timestamp': scan_result.scan_timestamp
            }
            
            with open(filename, 'w') as f:
                json.dump(result_dict, f, indent=2)
            
            logger.info(f"Results exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            raise
    
    def get_top_anomalies(self, scan_result: SetScanResult, 
                         anomaly_type: Optional[str] = None,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top anomalies from scan results.
        
        Args:
            scan_result: Scan results
            anomaly_type: Filter by anomaly type ('undervalued', 'overvalued', 'volatile')
            limit: Maximum number of results
            
        Returns:
            List[Dict]: Top anomalies sorted by score
        """
        anomalies = scan_result.anomaly_cards
        
        # Filter by type if specified
        if anomaly_type:
            anomalies = [a for a in anomalies if a['anomaly_type'] == anomaly_type]
        
        # Sort by anomaly score (highest first)
        anomalies.sort(key=lambda x: x['anomaly_score'], reverse=True)
        
        return anomalies[:limit]