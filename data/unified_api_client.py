"""
Unified API client that supports both Scryfall and JustTCG APIs.
Defaults to Scryfall for better reliability and free usage.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .scryfall_client import ScryfallClient, MockScryfallClient, create_scryfall_client
from .api_client import JustTCGClient, MockJustTCGClient, create_api_client

logger = logging.getLogger(__name__)


@dataclass
class CardPricing:
    """Standardized card pricing data structure."""
    card_name: str
    set_code: str
    set_name: str
    collector_number: str
    rarity: str
    prices: Dict[str, float]
    foil_available: bool
    nonfoil_available: bool
    source: str
    card_id: str
    image_url: str
    released_at: str
    scryfall_uri: Optional[str] = None
    legal_formats: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert CardPricing to dictionary format for database storage."""
        # Extract USD price for database
        usd_price = self.prices.get('usd', 0.0)
        price_cents = int(usd_price * 100) if usd_price > 0 else 0
        
        # Only include fields that the database can handle
        return {
            'card_name': self.card_name,
            'set_code': self.set_code,
            'printing_info': self.collector_number,
            'price_cents': price_cents,
            'condition': 'NM',  # Default condition
            'foil': self.foil_available,
            'source': self.source,
            'card_id': self.card_id,
            'image_url': self.image_url,
            'rarity': self.rarity
        }


class UnifiedAPIClient:
    """
    Unified API client that supports multiple MTG card APIs.
    
    Provides a consistent interface regardless of the underlying API provider.
    Default provider is Scryfall (free, reliable, comprehensive).
    """
    
    def __init__(self, provider: str = "scryfall", api_key: Optional[str] = None, 
                 use_mock: bool = False):
        """
        Initialize unified API client.
        
        Args:
            provider: API provider ("scryfall" or "justtcg")
            api_key: API key for JustTCG (ignored for Scryfall)
            use_mock: Use mock client for testing
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.use_mock = use_mock
        
        # Initialize the appropriate client
        if self.provider == "scryfall":
            self.client = create_scryfall_client(use_mock=use_mock)
        elif self.provider == "justtcg":
            self.client = create_api_client(api_key=api_key, use_mock=use_mock)
        else:
            logger.warning(f"Unknown provider '{provider}', defaulting to Scryfall")
            self.provider = "scryfall"
            self.client = create_scryfall_client(use_mock=use_mock)
        
        logger.info(f"Unified API client initialized with {self.provider} provider")
    
    def test_connection(self) -> bool:
        """
        Test API connection.
        
        Returns:
            bool: True if connection successful
        """
        try:
            return self.client.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def search_cards(self, card_name: str, set_code: Optional[str] = None,
                    exact_match: bool = False) -> List[Dict]:
        """
        Search for cards by name.
        
        Args:
            card_name: Card name to search for
            set_code: Optional set code filter
            exact_match: Whether to search for exact match
            
        Returns:
            List[Dict]: List of matching cards
        """
        try:
            if self.provider == "scryfall":
                # Build Scryfall search query
                query = f'!"{card_name}"' if exact_match else card_name
                if set_code:
                    query += f' e:{set_code}'
                
                return self.client.search_cards(query)
            
            elif self.provider == "justtcg":
                return self.client.search_cards(card_name, set_code, exact_match)
            
        except Exception as e:
            logger.error(f"Card search failed: {e}")
            return []
    
    def get_card_by_name(self, card_name: str, set_code: Optional[str] = None) -> Optional[Dict]:
        """
        Get a specific card by name.
        
        Args:
            card_name: Exact card name
            set_code: Optional set code
            
        Returns:
            Optional[Dict]: Card data or None
        """
        try:
            if self.provider == "scryfall":
                return self.client.get_card_by_name(card_name, set_code)
            
            elif self.provider == "justtcg":
                # For JustTCG, search and get first exact match
                cards = self.client.search_cards(card_name, set_code, exact_match=True)
                return cards[0] if cards else None
            
        except Exception as e:
            logger.error(f"Card lookup failed: {e}")
            return None
    
    def get_card_printings(self, card_name: str) -> List[CardPricing]:
        """
        Get all printings of a card with standardized pricing data.
        
        Args:
            card_name: Card name
            
        Returns:
            List[CardPricing]: List of standardized card pricing data
        """
        try:
            if self.provider == "scryfall":
                printings = self.client.get_card_printings(card_name)
                return [self._convert_scryfall_printing(p) for p in printings]
            
            elif self.provider == "justtcg":
                printings = self.client.get_card_printings(card_name)
                return [self._convert_justtcg_printing(p) for p in printings]
            
        except Exception as e:
            logger.error(f"Failed to get card printings: {e}")
            return []
    
    def _convert_scryfall_printing(self, printing: Dict) -> CardPricing:
        """Convert Scryfall printing data to standardized format."""
        return CardPricing(
            card_name=printing.get('card_name', ''),
            set_code=printing.get('set_code', ''),
            set_name=printing.get('set_name', ''),
            collector_number=printing.get('collector_number', ''),
            rarity=printing.get('rarity', ''),
            prices=printing.get('prices', {}),
            foil_available=printing.get('foil', False),
            nonfoil_available=printing.get('nonfoil', False),
            source=printing.get('source', 'Scryfall'),
            card_id=printing.get('card_id', ''),
            image_url=printing.get('image_uris', {}).get('normal', ''),
            released_at=printing.get('released_at', ''),
            scryfall_uri=printing.get('scryfall_uri', ''),
            legal_formats=printing.get('legal_formats', {})
        )
    
    def _convert_justtcg_printing(self, printing: Dict) -> CardPricing:
        """Convert JustTCG printing data to standardized format."""
        # Convert price_cents to USD price
        price_usd = printing.get('price_cents', 0) / 100.0
        
        return CardPricing(
            card_name=printing.get('card_name', ''),
            set_code=printing.get('set_code', ''),
            set_name=printing.get('set_code', ''),  # JustTCG doesn't provide set name
            collector_number=printing.get('printing_info', ''),
            rarity=printing.get('rarity', ''),
            prices={'usd': price_usd} if price_usd > 0 else {},
            foil_available=printing.get('foil', False),
            nonfoil_available=not printing.get('foil', True),
            source=printing.get('source', 'JustTCG'),
            card_id=printing.get('card_id', ''),
            image_url=printing.get('image_url', ''),
            released_at='',  # JustTCG doesn't provide release date
            scryfall_uri=None,
            legal_formats=None
        )
    
    def get_autocomplete_suggestions(self, query: str) -> List[str]:
        """
        Get card name autocomplete suggestions.
        
        Args:
            query: Partial card name
            
        Returns:
            List[str]: List of suggestions
        """
        try:
            if self.provider == "scryfall":
                return self.client.autocomplete_card_name(query)
            
            elif self.provider == "justtcg":
                # JustTCG doesn't have autocomplete, so do a basic search
                cards = self.client.search_cards(query)
                return [card.get('name', '') for card in cards[:10]]
            
        except Exception as e:
            logger.error(f"Autocomplete failed: {e}")
            return []
    
    def get_sets(self) -> List[Dict]:
        """
        Get list of MTG sets.
        
        Returns:
            List[Dict]: List of set information
        """
        try:
            if self.provider == "scryfall":
                return self.client.get_sets()
            
            elif self.provider == "justtcg":
                return self.client.get_all_sets()
            
        except Exception as e:
            logger.error(f"Failed to get sets: {e}")
            return []
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the current API provider.
        
        Returns:
            Dict[str, Any]: Provider information
        """
        return {
            'provider': self.provider,
            'client_type': type(self.client).__name__,
            'requires_api_key': self.provider == "justtcg",
            'has_api_key': bool(self.api_key) if self.provider == "justtcg" else None,
            'is_mock': self.use_mock,
            'features': {
                'search': True,
                'pricing': True,
                'autocomplete': self.provider == "scryfall",
                'sets': True,
                'printings': True,
                'images': True,
                'legal_formats': self.provider == "scryfall"
            }
        }
    
    def switch_provider(self, provider: str, api_key: Optional[str] = None) -> bool:
        """
        Switch to a different API provider.
        
        Args:
            provider: New provider ("scryfall" or "justtcg")
            api_key: API key for JustTCG
            
        Returns:
            bool: True if switch was successful
        """
        try:
            old_provider = self.provider
            
            if provider.lower() == "scryfall":
                self.client = create_scryfall_client(use_mock=self.use_mock)
                self.provider = "scryfall"
                self.api_key = None
                
            elif provider.lower() == "justtcg":
                self.client = create_api_client(api_key=api_key, use_mock=self.use_mock)
                self.provider = "justtcg"
                self.api_key = api_key
                
            else:
                logger.error(f"Unknown provider: {provider}")
                return False
            
            # Test the new connection
            if self.test_connection():
                logger.info(f"Successfully switched from {old_provider} to {self.provider}")
                return True
            else:
                logger.error(f"Failed to connect with {provider}, reverting to {old_provider}")
                # Revert to old provider
                self.switch_provider(old_provider, self.api_key)
                return False
                
        except Exception as e:
            logger.error(f"Failed to switch provider: {e}")
            return False


def create_unified_client(provider: str = "scryfall", api_key: Optional[str] = None, 
                         use_mock: bool = False) -> UnifiedAPIClient:
    """
    Factory function to create unified API client.
    
    Args:
        provider: API provider ("scryfall" or "justtcg")
        api_key: API key for JustTCG
        use_mock: Use mock client for testing
        
    Returns:
        UnifiedAPIClient: Configured client
    """
    return UnifiedAPIClient(provider=provider, api_key=api_key, use_mock=use_mock)