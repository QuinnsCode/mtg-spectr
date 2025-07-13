"""
Scryfall API Client - Free MTG Card Data with Pagination Support

This module provides a comprehensive client for the Scryfall API, offering
free access to Magic: The Gathering card data without requiring an API key.

Key Features:
- Automatic pagination handling for large result sets
- Rate limiting compliance (10 requests/second)
- Comprehensive search with query sanitization
- Full card pricing and variation data
- Mock client for testing

Recent Improvements:
- Fixed pagination to retrieve all cards in large sets (400+ cards)
- Enhanced search to include all printings and variations
- Better error handling and retry logic

API Documentation: https://scryfall.com/docs/api

Example:
    client = create_scryfall_client()
    cards = client.search_cards("e:dsk")  # Get all cards from Duskmourn
    card = client.get_card_by_name("Lightning Bolt", "2ed")
"""

import requests
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import threading
from urllib.parse import urlencode, quote

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ScryfallRateLimit:
    """Rate limiting for Scryfall API - 10 requests per second."""
    requests_per_second: int = 10
    min_request_interval: float = 0.1  # 100ms between requests
    last_request_time: float = 0


class ScryfallAPIError(Exception):
    """Custom exception for Scryfall API errors."""
    pass


class ScryfallClient:
    """
    Client for interacting with Scryfall API.
    
    Scryfall provides free access to comprehensive MTG card data including:
    - Card information and images
    - Pricing data (USD, EUR, foil, etc.)
    - Set information
    - Card rulings
    - Search functionality
    
    Rate limit: 10 requests per second (100ms between requests)
    No authentication required.
    """
    
    def __init__(self, base_url: str = "https://api.scryfall.com"):
        """
        Initialize Scryfall API client.
        
        Args:
            base_url: Base URL for Scryfall API
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.rate_limit = ScryfallRateLimit()
        self.lock = threading.Lock()
        
        # Set required headers
        self.session.headers.update({
            'User-Agent': 'MTG-Card-Pricing-Tool/1.0',
            'Accept': 'application/json'
        })
    
    def _check_rate_limit(self):
        """Enforce rate limiting - max 10 requests per second."""
        with self.lock:
            current_time = time.time()
            
            if self.rate_limit.last_request_time > 0:
                time_since_last = current_time - self.rate_limit.last_request_time
                if time_since_last < self.rate_limit.min_request_interval:
                    sleep_time = self.rate_limit.min_request_interval - time_since_last
                    logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
                    time.sleep(sleep_time)
            
            self.rate_limit.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, 
                     method: str = 'GET', max_retries: int = 3) -> Dict:
        """
        Make API request with rate limiting and error handling.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            method: HTTP method
            max_retries: Maximum retry attempts
            
        Returns:
            Dict: API response data
            
        Raises:
            ScryfallAPIError: If request fails
        """
        self._check_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(max_retries + 1):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, timeout=30)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=params, timeout=30)
                else:
                    raise ScryfallAPIError(f"Unsupported HTTP method: {method}")
                
                # Handle specific status codes
                if response.status_code == 400:
                    logger.warning(f"Bad request: {url}")
                    try:
                        error_data = response.json()
                        return error_data
                    except:
                        return {'object': 'error', 'status': 400, 'code': 'bad_request'}
                
                elif response.status_code == 404:
                    logger.warning(f"Resource not found: {url}")
                    return {'object': 'error', 'status': 404, 'code': 'not_found'}
                
                elif response.status_code == 422:
                    logger.warning(f"Invalid request: {url}")
                    try:
                        error_data = response.json()
                        return error_data
                    except:
                        return {'object': 'error', 'status': 422, 'code': 'unprocessable_entity'}
                
                elif response.status_code == 429:
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise ScryfallAPIError("Rate limited after all retries")
                
                elif response.status_code >= 500:
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise ScryfallAPIError(f"Server error: {response.status_code}")
                
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    return response.json()
                except json.JSONDecodeError:
                    logger.warning(f"Non-JSON response from {url}")
                    return {'raw_response': response.text}
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Request failed for {url}: {e}")
                    raise ScryfallAPIError(f"Request failed: {e}")
        
        raise ScryfallAPIError(f"Max retries exceeded for {url}")
    
    def search_cards(self, query: str, unique: str = 'cards', order: str = 'name', 
                    page: int = 1, include_extras: bool = False) -> List[Dict]:
        """
        Search for cards using Scryfall's search syntax.
        
        Args:
            query: Search query (e.g., "Lightning Bolt", "c:red", "e:dom")
            unique: How to handle duplicates ('cards', 'art', 'prints')
            order: Sort order ('name', 'set', 'released', 'rarity', 'color', 'usd', etc.)
            page: Page number for pagination
            include_extras: Include tokens and special cards
            
        Returns:
            List[Dict]: List of matching cards
        """
        # Validate query
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []
        
        # Clean and sanitize query string
        query = query.strip()
        
        # Remove problematic characters that can break Scryfall search
        # Keep only alphanumeric, spaces, common punctuation for card names
        import re
        
        # First, handle common search operators that might be in card names
        # Replace standalone operators that might break search
        query = re.sub(r'\b(AND|OR|NOT)\b(?!\s+(the|of|a|an|in|on|at|to|for|with|by)\b)', '', query, flags=re.IGNORECASE)
        
        # Remove unclosed parentheses at the end
        query = re.sub(r'\([^)]*$', '', query)
        query = re.sub(r'^[^(]*\)', '', query)
        
        # Remove trailing operators and punctuation that might cause issues
        query = re.sub(r'[+\-*/=<>!&|]+$', '', query)
        
        # Clean up multiple spaces
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Final validation
        if not query:
            logger.warning("Query became empty after sanitization")
            return []
        
        params = {
            'q': query,
            'unique': unique,
            'order': order,
            'page': page,
            'include_extras': str(include_extras).lower()
        }
        
        try:
            all_cards = []
            current_page = page
            
            while True:
                # Update params for current page
                params['page'] = current_page
                response = self._make_request('cards/search', params=params)
                
                if response.get('object') == 'error':
                    error_code = response.get('code', 'unknown')
                    error_details = response.get('details', 'Unknown error')
                    logger.warning(f"Search error ({error_code}): {error_details} (query: '{query}')")
                    
                    # Try fallback with named search for exact matches (only on first page)
                    if error_code in ['not_found', 'bad_request'] and query and current_page == 1:
                        logger.info(f"Trying fallback named search for: {query}")
                        try:
                            fallback_result = self.get_card_by_name(query)
                            if fallback_result:
                                return [fallback_result]
                        except Exception:
                            pass  # Fallback failed, continue with empty result
                    
                    # If error on later pages, return what we have so far
                    if current_page > 1:
                        logger.warning(f"Error on page {current_page}, returning {len(all_cards)} cards collected so far")
                        break
                    
                    return []
                
                # Add cards from this page
                page_cards = response.get('data', [])
                all_cards.extend(page_cards)
                
                # Check if there are more pages
                if not response.get('has_more', False):
                    break
                
                # Move to next page
                current_page += 1
                
                # Safety check to prevent infinite loops
                if current_page > 50:  # Maximum 50 pages (very large sets)
                    logger.warning(f"Hit maximum page limit (50) for query: {query}")
                    break
                
                # Log progress for large searches
                if current_page % 5 == 0:
                    logger.info(f"Retrieved {len(all_cards)} cards so far (page {current_page})")
            
            logger.info(f"Retrieved {len(all_cards)} total cards for query: {query}")
            return all_cards
            
        except ScryfallAPIError as e:
            logger.error(f"Failed to search cards: {e}")
            return []
    
    def get_card_by_name(self, name: str, set_code: Optional[str] = None) -> Optional[Dict]:
        """
        Get a card by exact name.
        
        Args:
            name: Exact card name
            set_code: Optional set code for specific printing
            
        Returns:
            Optional[Dict]: Card data or None if not found
        """
        params = {'exact': name}
        if set_code:
            params['set'] = set_code
        
        try:
            response = self._make_request('cards/named', params=params)
            
            if response.get('object') == 'error':
                logger.warning(f"Card not found: {name}")
                return None
            
            return response
            
        except ScryfallAPIError as e:
            logger.error(f"Failed to get card by name: {e}")
            return None
    
    def get_card_by_id(self, card_id: str) -> Optional[Dict]:
        """
        Get a card by Scryfall ID.
        
        Args:
            card_id: Scryfall card ID
            
        Returns:
            Optional[Dict]: Card data or None if not found
        """
        try:
            response = self._make_request(f'cards/{card_id}')
            
            if response.get('object') == 'error':
                logger.warning(f"Card not found: {card_id}")
                return None
            
            return response
            
        except ScryfallAPIError as e:
            logger.error(f"Failed to get card by ID: {e}")
            return None
    
    def get_random_card(self) -> Optional[Dict]:
        """
        Get a random card.
        
        Returns:
            Optional[Dict]: Random card data
        """
        try:
            response = self._make_request('cards/random')
            
            if response.get('object') == 'error':
                return None
            
            return response
            
        except ScryfallAPIError as e:
            logger.error(f"Failed to get random card: {e}")
            return None
    
    def autocomplete_card_name(self, query: str) -> List[str]:
        """
        Get card name autocomplete suggestions.
        
        Args:
            query: Partial card name
            
        Returns:
            List[str]: List of card name suggestions
        """
        params = {'q': query}
        
        try:
            response = self._make_request('cards/autocomplete', params=params)
            
            if response.get('object') == 'error':
                return []
            
            return response.get('data', [])
            
        except ScryfallAPIError as e:
            logger.error(f"Failed to get autocomplete: {e}")
            return []
    
    def get_card_prices(self, card_data: Dict) -> Dict[str, float]:
        """
        Extract pricing information from card data.
        
        Args:
            card_data: Card data from Scryfall API
            
        Returns:
            Dict[str, float]: Pricing information
        """
        prices = card_data.get('prices', {})
        
        # Convert string prices to float, handle None values
        parsed_prices = {}
        for price_type, price_str in prices.items():
            if price_str is not None:
                try:
                    parsed_prices[price_type] = float(price_str)
                except (ValueError, TypeError):
                    parsed_prices[price_type] = 0.0
            else:
                parsed_prices[price_type] = 0.0
        
        return parsed_prices
    
    def get_card_printings(self, card_name: str) -> List[Dict]:
        """
        Get all printings of a card with pricing information.
        
        Args:
            card_name: Name of the card
            
        Returns:
            List[Dict]: List of card printings with pricing
        """
        try:
            # Search for all printings of the card
            cards = self.search_cards(f'!"{card_name}"', unique='prints', order='released')
            
            printings = []
            for card in cards:
                prices = self.get_card_prices(card)
                
                printing = {
                    'card_name': card.get('name', card_name),
                    'set_code': card.get('set', ''),
                    'set_name': card.get('set_name', ''),
                    'collector_number': card.get('collector_number', ''),
                    'rarity': card.get('rarity', ''),
                    'prices': prices,
                    'foil': card.get('foil', False),
                    'nonfoil': card.get('nonfoil', False),
                    'source': 'Scryfall',
                    'card_id': card.get('id', ''),
                    'scryfall_uri': card.get('scryfall_uri', ''),
                    'image_uris': card.get('image_uris', {}),
                    'released_at': card.get('released_at', ''),
                    'legal_formats': card.get('legalities', {})
                }
                printings.append(printing)
            
            return printings
            
        except ScryfallAPIError as e:
            logger.error(f"Failed to get card printings: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test API connection.
        
        Returns:
            bool: True if connection successful
        """
        try:
            response = self.get_random_card()
            if response and response.get('object') == 'card':
                logger.info("Scryfall API connection successful")
                return True
            else:
                logger.error("Scryfall API connection failed")
                return False
                
        except Exception as e:
            logger.error(f"Scryfall API connection test failed: {e}")
            return False
    
    def get_sets(self) -> List[Dict]:
        """
        Get list of all MTG sets.
        
        Returns:
            List[Dict]: List of set information
        """
        try:
            response = self._make_request('sets')
            
            if response.get('object') == 'error':
                logger.error("Failed to get sets")
                return []
            
            return response.get('data', [])
            
        except ScryfallAPIError as e:
            logger.error(f"Failed to get sets: {e}")
            return []


# Mock implementation for testing
class MockScryfallClient(ScryfallClient):
    """Mock Scryfall client for testing."""
    
    def __init__(self):
        # Don't call parent __init__ to avoid real session setup
        self.rate_limit = ScryfallRateLimit()
        self.lock = threading.Lock()
    
    def search_cards(self, query: str, **kwargs) -> List[Dict]:
        """Mock card search."""
        return [
            {
                'id': f'mock-{query.lower().replace(" ", "-")}',
                'name': query,
                'set': 'dom',
                'set_name': 'Dominaria',
                'collector_number': '123',
                'rarity': 'rare',
                'prices': {
                    'usd': '5.99',
                    'usd_foil': '12.99',
                    'eur': '5.50',
                    'eur_foil': '12.00',
                    'tix': '2.50'
                },
                'foil': True,
                'nonfoil': True,
                'image_uris': {
                    'normal': 'https://example.com/image.jpg'
                },
                'scryfall_uri': 'https://scryfall.com/card/dom/123',
                'released_at': '2023-01-01'
            }
        ]
    
    def get_card_by_name(self, name: str, set_code: Optional[str] = None) -> Optional[Dict]:
        """Mock card lookup."""
        return self.search_cards(name)[0] if name else None
    
    def test_connection(self) -> bool:
        """Mock connection test."""
        return True
    
    def get_card_printings(self, card_name: str) -> List[Dict]:
        """Mock card printings."""
        return [
            {
                'card_name': card_name,
                'set_code': 'dom',
                'set_name': 'Dominaria',
                'collector_number': '123',
                'rarity': 'rare',
                'prices': {
                    'usd': 5.99,
                    'usd_foil': 12.99,
                    'eur': 5.50,
                    'eur_foil': 12.00,
                    'tix': 2.50
                },
                'foil': True,
                'nonfoil': True,
                'source': 'Scryfall (Mock)',
                'card_id': f'mock-{card_name.lower().replace(" ", "-")}',
                'scryfall_uri': 'https://scryfall.com/card/dom/123',
                'image_uris': {'normal': 'https://example.com/image.jpg'},
                'released_at': '2023-01-01',
                'legal_formats': {'standard': 'legal', 'modern': 'legal'}
            }
        ]
    
    def get_sets(self) -> List[Dict]:
        """Mock sets data."""
        return [
            {
                'id': 'dom',
                'code': 'dom',
                'name': 'Dominaria',
                'set_type': 'expansion',
                'card_count': 269,
                'digital': False,
                'released_at': '2018-04-27',
                'block': 'Dominaria',
                'icon_svg_uri': 'https://example.com/dom.svg'
            },
            {
                'id': 'big',
                'code': 'big',
                'name': 'The Big Score',
                'set_type': 'expansion',
                'card_count': 95,
                'digital': False,
                'released_at': '2024-04-19',
                'block': 'Outlaws of Thunder Junction',
                'icon_svg_uri': 'https://example.com/big.svg'
            },
            {
                'id': 'dsk',
                'code': 'dsk',
                'name': 'Duskmourn: House of Horror',
                'set_type': 'expansion',
                'card_count': 276,
                'digital': False,
                'released_at': '2024-09-27',
                'block': 'Duskmourn',
                'icon_svg_uri': 'https://example.com/dsk.svg'
            },
            {
                'id': 'blb',
                'code': 'blb',
                'name': 'Bloomburrow',
                'set_type': 'expansion',
                'card_count': 261,
                'digital': False,
                'released_at': '2024-08-02',
                'block': 'Bloomburrow',
                'icon_svg_uri': 'https://example.com/blb.svg'
            },
            {
                'id': 'otj',
                'code': 'otj',
                'name': 'Outlaws of Thunder Junction',
                'set_type': 'expansion',
                'card_count': 276,
                'digital': False,
                'released_at': '2024-04-19',
                'block': 'Outlaws of Thunder Junction',
                'icon_svg_uri': 'https://example.com/otj.svg'
            },
            {
                'id': 'mkm',
                'code': 'mkm',
                'name': 'Murders at Karlov Manor',
                'set_type': 'expansion',
                'card_count': 286,
                'digital': False,
                'released_at': '2024-02-09',
                'block': 'Murders at Karlov Manor',
                'icon_svg_uri': 'https://example.com/mkm.svg'
            },
            {
                'id': 'lci',
                'code': 'lci',
                'name': 'The Lost Caverns of Ixalan',
                'set_type': 'expansion',
                'card_count': 291,
                'digital': False,
                'released_at': '2023-11-17',
                'block': 'The Lost Caverns of Ixalan',
                'icon_svg_uri': 'https://example.com/lci.svg'
            },
            {
                'id': 'woe',
                'code': 'woe',
                'name': 'Wilds of Eldraine',
                'set_type': 'expansion',
                'card_count': 276,
                'digital': False,
                'released_at': '2023-09-08',
                'block': 'Wilds of Eldraine',
                'icon_svg_uri': 'https://example.com/woe.svg'
            },
            {
                'id': 'ltr',
                'code': 'ltr',
                'name': 'The Lord of the Rings: Tales of Middle-earth',
                'set_type': 'expansion',
                'card_count': 281,
                'digital': False,
                'released_at': '2023-06-23',
                'block': 'The Lord of the Rings',
                'icon_svg_uri': 'https://example.com/ltr.svg'
            },
            {
                'id': 'mom',
                'code': 'mom',
                'name': 'March of the Machine',
                'set_type': 'expansion',
                'card_count': 271,
                'digital': False,
                'released_at': '2023-04-21',
                'block': 'March of the Machine',
                'icon_svg_uri': 'https://example.com/mom.svg'
            },
            {
                'id': 'one',
                'code': 'one',
                'name': 'Phyrexia: All Will Be One',
                'set_type': 'expansion',
                'card_count': 271,
                'digital': False,
                'released_at': '2023-02-10',
                'block': 'Phyrexia',
                'icon_svg_uri': 'https://example.com/one.svg'
            },
            {
                'id': 'bro',
                'code': 'bro',
                'name': 'The Brothers\' War',
                'set_type': 'expansion',
                'card_count': 287,
                'digital': False,
                'released_at': '2022-11-18',
                'block': 'The Brothers\' War',
                'icon_svg_uri': 'https://example.com/bro.svg'
            },
            {
                'id': 'dmu',
                'code': 'dmu',
                'name': 'Dominaria United',
                'set_type': 'expansion',
                'card_count': 281,
                'digital': False,
                'released_at': '2022-09-09',
                'block': 'Dominaria United',
                'icon_svg_uri': 'https://example.com/dmu.svg'
            },
            {
                'id': 'snc',
                'code': 'snc',
                'name': 'Streets of New Capenna',
                'set_type': 'expansion',
                'card_count': 281,
                'digital': False,
                'released_at': '2022-04-29',
                'block': 'Streets of New Capenna',
                'icon_svg_uri': 'https://example.com/snc.svg'
            },
            {
                'id': 'neo',
                'code': 'neo',
                'name': 'Kamigawa: Neon Dynasty',
                'set_type': 'expansion',
                'card_count': 302,
                'digital': False,
                'released_at': '2022-02-18',
                'block': 'Kamigawa: Neon Dynasty',
                'icon_svg_uri': 'https://example.com/neo.svg'
            },
            {
                'id': 'vow',
                'code': 'vow',
                'name': 'Innistrad: Crimson Vow',
                'set_type': 'expansion',
                'card_count': 277,
                'digital': False,
                'released_at': '2021-11-19',
                'block': 'Innistrad: Double Feature',
                'icon_svg_uri': 'https://example.com/vow.svg'
            },
            {
                'id': 'mid',
                'code': 'mid',
                'name': 'Innistrad: Midnight Hunt',
                'set_type': 'expansion',
                'card_count': 277,
                'digital': False,
                'released_at': '2021-09-24',
                'block': 'Innistrad: Double Feature',
                'icon_svg_uri': 'https://example.com/mid.svg'
            },
            {
                'id': 'afr',
                'code': 'afr',
                'name': 'Adventures in the Forgotten Realms',
                'set_type': 'expansion',
                'card_count': 281,
                'digital': False,
                'released_at': '2021-07-23',
                'block': 'Adventures in the Forgotten Realms',
                'icon_svg_uri': 'https://example.com/afr.svg'
            },
            {
                'id': 'stx',
                'code': 'stx',
                'name': 'Strixhaven: School of Mages',
                'set_type': 'expansion',
                'card_count': 275,
                'digital': False,
                'released_at': '2021-04-23',
                'block': 'Strixhaven: School of Mages',
                'icon_svg_uri': 'https://example.com/stx.svg'
            },
            {
                'id': 'khm',
                'code': 'khm',
                'name': 'Kaldheim',
                'set_type': 'expansion',
                'card_count': 285,
                'digital': False,
                'released_at': '2021-02-05',
                'block': 'Kaldheim',
                'icon_svg_uri': 'https://example.com/khm.svg'
            },
            {
                'id': 'znr',
                'code': 'znr',
                'name': 'Zendikar Rising',
                'set_type': 'expansion',
                'card_count': 280,
                'digital': False,
                'released_at': '2020-09-25',
                'block': 'Zendikar Rising',
                'icon_svg_uri': 'https://example.com/znr.svg'
            },
            {
                'id': 'm21',
                'code': 'm21',
                'name': 'Core Set 2021',
                'set_type': 'core',
                'card_count': 274,
                'digital': False,
                'released_at': '2020-07-03',
                'block': 'Core Set 2021',
                'icon_svg_uri': 'https://example.com/m21.svg'
            },
            {
                'id': 'iko',
                'code': 'iko',
                'name': 'Ikoria: Lair of Behemoths',
                'set_type': 'expansion',
                'card_count': 274,
                'digital': False,
                'released_at': '2020-04-24',
                'block': 'Ikoria: Lair of Behemoths',
                'icon_svg_uri': 'https://example.com/iko.svg'
            },
            {
                'id': 'thb',
                'code': 'thb',
                'name': 'Theros Beyond Death',
                'set_type': 'expansion',
                'card_count': 254,
                'digital': False,
                'released_at': '2020-01-24',
                'block': 'Theros Beyond Death',
                'icon_svg_uri': 'https://example.com/thb.svg'
            },
            {
                'id': 'eld',
                'code': 'eld',
                'name': 'Throne of Eldraine',
                'set_type': 'expansion',
                'card_count': 269,
                'digital': False,
                'released_at': '2019-10-04',
                'block': 'Throne of Eldraine',
                'icon_svg_uri': 'https://example.com/eld.svg'
            },
            {
                'id': 'm20',
                'code': 'm20',
                'name': 'Core Set 2020',
                'set_type': 'core',
                'card_count': 321,
                'digital': False,
                'released_at': '2019-07-12',
                'block': 'Core Set 2020',
                'icon_svg_uri': 'https://example.com/m20.svg'
            },
            {
                'id': 'war',
                'code': 'war',
                'name': 'War of the Spark',
                'set_type': 'expansion',
                'card_count': 264,
                'digital': False,
                'released_at': '2019-05-03',
                'block': 'War of the Spark',
                'icon_svg_uri': 'https://example.com/war.svg'
            },
            {
                'id': 'rna',
                'code': 'rna',
                'name': 'Ravnica Allegiance',
                'set_type': 'expansion',
                'card_count': 259,
                'digital': False,
                'released_at': '2019-01-25',
                'block': 'Guilds of Ravnica',
                'icon_svg_uri': 'https://example.com/rna.svg'
            },
            {
                'id': 'grn',
                'code': 'grn',
                'name': 'Guilds of Ravnica',
                'set_type': 'expansion',
                'card_count': 259,
                'digital': False,
                'released_at': '2018-10-05',
                'block': 'Guilds of Ravnica',
                'icon_svg_uri': 'https://example.com/grn.svg'
            },
            {
                'id': 'm19',
                'code': 'm19',
                'name': 'Core Set 2019',
                'set_type': 'core',
                'card_count': 314,
                'digital': False,
                'released_at': '2018-07-13',
                'block': 'Core Set 2019',
                'icon_svg_uri': 'https://example.com/m19.svg'
            }
        ]


def create_scryfall_client(use_mock: bool = False) -> ScryfallClient:
    """
    Factory function to create Scryfall client.
    
    Args:
        use_mock: Force use of mock client
        
    Returns:
        ScryfallClient: Real or mock client
    """
    if use_mock:
        logger.info("Using mock Scryfall client")
        return MockScryfallClient()
    
    try:
        client = ScryfallClient()
        if client.test_connection():
            logger.info("Scryfall API connection successful")
            return client
        else:
            logger.warning("Scryfall API connection failed, using mock client")
            return MockScryfallClient()
    except Exception as e:
        logger.error(f"Failed to create Scryfall client: {e}")
        logger.info("Using mock client")
        return MockScryfallClient()