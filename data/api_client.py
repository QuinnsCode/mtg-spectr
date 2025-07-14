"""
API client for JustTCG API integration with rate limiting and error handling.
Handles card data retrieval and pricing information from JustTCG API.
"""

import requests
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import threading
from urllib.parse import urlencode, quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limiting configuration for API calls."""
    calls_per_minute: int = 10  # Very conservative limit
    calls_per_hour: int = 100   # Very conservative limit
    min_request_interval: float = 6.0  # Minimum 6 seconds between requests
    last_call_time: float = 0
    call_count_minute: int = 0
    call_count_hour: int = 0
    minute_reset_time: float = 0
    hour_reset_time: float = 0


class APIError(Exception):
    """Custom exception for API-related errors."""
    pass


class JustTCGClient:
    """
    Client for interacting with JustTCG API.
    Handles authentication via X-API-Key header, rate limiting, and data retrieval.
    
    API Key Authentication:
    - Requires API key from JustTCG dashboard
    - Uses X-API-Key header for authentication
    - Different plans have different rate limits
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.justtcg.com/v1"):
        """
        Initialize JustTCG API client.
        
        Args:
            api_key: API key from JustTCG dashboard (required for authentication)
                    Format: 'tcg_your_api_key_here'
            base_url: Base URL for the API (default: https://api.justtcg.com/v1)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.rate_limit = RateLimit()
        self.lock = threading.Lock()
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': 'MTG-Card-Pricing-Tool/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        if self.api_key:
            self.session.headers['X-API-Key'] = self.api_key
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting with minimum request intervals."""
        with self.lock:
            current_time = time.time()
            
            # Enforce minimum interval between requests
            if self.rate_limit.last_call_time > 0:
                time_since_last = current_time - self.rate_limit.last_call_time
                if time_since_last < self.rate_limit.min_request_interval:
                    sleep_time = self.rate_limit.min_request_interval - time_since_last
                    logger.info(f"Enforcing minimum interval, sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
                    current_time = time.time()
            
            # Reset counters if time windows have passed
            if current_time - self.rate_limit.minute_reset_time >= 60:
                self.rate_limit.call_count_minute = 0
                self.rate_limit.minute_reset_time = current_time
            
            if current_time - self.rate_limit.hour_reset_time >= 3600:
                self.rate_limit.call_count_hour = 0
                self.rate_limit.hour_reset_time = current_time
            
            # Check if we need to wait for rate limits
            if self.rate_limit.call_count_minute >= self.rate_limit.calls_per_minute:
                sleep_time = 60 - (current_time - self.rate_limit.minute_reset_time)
                if sleep_time > 0:
                    logger.info(f"Minute rate limit reached, sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
                    self.rate_limit.call_count_minute = 0
                    self.rate_limit.minute_reset_time = time.time()
            
            if self.rate_limit.call_count_hour >= self.rate_limit.calls_per_hour:
                sleep_time = 3600 - (current_time - self.rate_limit.hour_reset_time)
                if sleep_time > 0:
                    logger.info(f"Hourly rate limit reached, sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
                    self.rate_limit.call_count_hour = 0
                    self.rate_limit.hour_reset_time = time.time()
            
            # Update counters
            self.rate_limit.call_count_minute += 1
            self.rate_limit.call_count_hour += 1
            self.rate_limit.last_call_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, 
                     method: str = 'GET', data: Optional[Dict] = None, max_retries: int = 3) -> Dict:
        """
        Make API request with rate limiting, exponential backoff, and error handling.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            method: HTTP method
            data: Request body data
            max_retries: Maximum number of retry attempts
        
        Returns:
            Dict: API response data
        
        Raises:
            APIError: If request fails after all retries
        """
        self._check_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(max_retries + 1):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, timeout=30)
                elif method.upper() == 'POST':
                    response = self.session.post(url, params=params, json=data, timeout=30)
                else:
                    raise APIError(f"Unsupported HTTP method: {method}")
                
                # Handle specific HTTP status codes
                if response.status_code == 429:
                    if attempt < max_retries:
                        # Check for Retry-After header
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            wait_time = int(retry_after)
                        else:
                            # Longer exponential backoff: 10s, 20s, 40s, 80s...
                            wait_time = 10 * (2 ** attempt)
                        
                        logger.warning(f"Rate limited (429), retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limited after {max_retries} retries")
                        raise APIError(f"Rate limited: {response.status_code} {response.reason}")
                
                elif response.status_code == 401:
                    logger.error("Authentication failed - check your API key")
                    raise APIError("Authentication failed: Invalid or missing API key")
                
                elif response.status_code == 403:
                    logger.error("Access forbidden - check API key permissions")
                    raise APIError("Access forbidden: API key lacks required permissions")
                
                elif response.status_code == 404:
                    logger.warning(f"Resource not found: {url}")
                    raise APIError("Resource not found")
                
                elif response.status_code >= 500:
                    if attempt < max_retries:
                        wait_time = 5 * (2 ** attempt)
                        logger.warning(f"Server error ({response.status_code}), retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Server error after {max_retries} retries: {response.status_code}")
                        raise APIError(f"Server error: {response.status_code} {response.reason}")
                
                response.raise_for_status()
                
                # Try to parse JSON response
                try:
                    return response.json()
                except json.JSONDecodeError:
                    logger.warning(f"Non-JSON response from {url}")
                    return {'raw_response': response.text}
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries and not isinstance(e, requests.exceptions.Timeout):
                    wait_time = 5 * (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Request failed for {url}: {e}")
                    raise APIError(f"Request failed: {e}")
        
        raise APIError(f"Max retries exceeded for {url}")
    
    def search_cards(self, card_name: str, set_code: Optional[str] = None, 
                    exact_match: bool = False) -> List[Dict]:
        """
        Search for cards by name and optional set code.
        
        Args:
            card_name: Name of the card to search for
            set_code: Optional set code filter
            exact_match: Whether to search for exact name match
        
        Returns:
            List[Dict]: List of matching cards
        """
        params = {
            'name': card_name,
            'exact': str(exact_match).lower()
        }
        
        if set_code:
            params['set'] = set_code
        
        try:
            response = self._make_request('cards/search', params=params)
            
            # Handle different response formats
            if 'data' in response:
                return response['data']
            elif 'cards' in response:
                return response['cards']
            elif isinstance(response, list):
                return response
            else:
                logger.warning(f"Unexpected response format: {response}")
                return []
                
        except APIError as e:
            logger.error(f"Failed to search cards: {e}")
            return []
    
    def get_card_prices(self, card_id: str) -> List[Dict]:
        """
        Get pricing information for a specific card.
        
        Args:
            card_id: Unique identifier for the card
        
        Returns:
            List[Dict]: List of pricing information
        """
        try:
            response = self._make_request(f'cards/{card_id}/prices')
            
            if 'data' in response:
                return response['data']
            elif 'prices' in response:
                return response['prices']
            elif isinstance(response, list):
                return response
            else:
                logger.warning(f"Unexpected price response format: {response}")
                return []
                
        except APIError as e:
            logger.error(f"Failed to get card prices: {e}")
            return []
    
    def get_card_details(self, card_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific card.
        
        Args:
            card_id: Unique identifier for the card
        
        Returns:
            Optional[Dict]: Card details or None if not found
        """
        try:
            response = self._make_request(f'cards/{card_id}')
            
            if 'data' in response:
                return response['data']
            elif 'card' in response:
                return response['card']
            else:
                return response
                
        except APIError as e:
            logger.error(f"Failed to get card details: {e}")
            return None
    
    def get_set_information(self, set_code: str) -> Optional[Dict]:
        """
        Get information about a specific set.
        
        Args:
            set_code: Set code identifier
        
        Returns:
            Optional[Dict]: Set information or None if not found
        """
        try:
            # Get specific set information - may need game parameter for some endpoints
            response = self._make_request(f'sets/{set_code}', params={'game': 'magic-the-gathering'})
            
            if 'data' in response:
                return response['data']
            elif 'set' in response:
                return response['set']
            else:
                return response
                
        except APIError as e:
            logger.error(f"Failed to get set information: {e}")
            return None
    
    def get_all_sets(self) -> List[Dict]:
        """
        Get list of all available sets for Magic: The Gathering.
        
        Returns:
            List[Dict]: List of set information
        """
        try:
            # Get all sets for Magic: The Gathering - requires game parameter
            response = self._make_request('sets', params={'game': 'magic-the-gathering'})
            
            if 'data' in response:
                return response['data']
            elif 'sets' in response:
                return response['sets']
            elif isinstance(response, list):
                return response
            else:
                logger.warning(f"Unexpected sets response format: {response}")
                return []
                
        except APIError as e:
            logger.error(f"Failed to get all sets: {e}")
            return []
    
    def get_card_printings(self, card_name: str) -> List[Dict]:
        """
        Get all printings/versions of a card across different sets.
        
        Args:
            card_name: Name of the card
        
        Returns:
            List[Dict]: List of card printings with pricing
        """
        try:
            # First, search for the card
            cards = self.search_cards(card_name, exact_match=True)
            
            if not cards:
                logger.info(f"No cards found for '{card_name}'")
                return []
            
            printings = []
            
            # Get pricing for each printing
            for card in cards:
                card_id = card.get('id') or card.get('card_id')
                if not card_id:
                    continue
                
                prices = self.get_card_prices(card_id)
                
                # Combine card info with pricing
                for price_info in prices:
                    printing = {
                        'card_name': card_name,
                        'set_code': card.get('set_code') or card.get('set'),
                        'printing_info': card.get('collector_number') or card.get('number'),
                        'price_cents': self._extract_price_cents(price_info),
                        'condition': price_info.get('condition', 'NM'),
                        'foil': price_info.get('foil', False),
                        'source': 'JustTCG',
                        'card_id': card_id,
                        'rarity': card.get('rarity'),
                        'image_url': card.get('image_url') or card.get('image')
                    }
                    printings.append(printing)
            
            return printings
            
        except APIError as e:
            logger.error(f"Failed to get card printings: {e}")
            return []
    
    def _extract_price_cents(self, price_info: Dict) -> int:
        """
        Extract price in cents from price information.
        
        Args:
            price_info: Price information dictionary
        
        Returns:
            int: Price in cents
        """
        # Try different price field names
        price_fields = ['price', 'market_price', 'low_price', 'mid_price', 'high_price']
        
        for field in price_fields:
            if field in price_info:
                price_value = price_info[field]
                if isinstance(price_value, (int, float)):
                    return int(price_value * 100)
                elif isinstance(price_value, str):
                    try:
                        # Remove currency symbols and convert
                        clean_price = price_value.replace('$', '').replace(',', '')
                        return int(float(clean_price) * 100)
                    except ValueError:
                        continue
        
        # Default to 0 if no price found
        logger.warning(f"No valid price found in: {price_info}")
        return 0
    
    def batch_get_card_prices(self, card_names: List[str]) -> Dict[str, List[Dict]]:
        """
        Get pricing information for multiple cards in batch.
        
        Args:
            card_names: List of card names to get prices for
        
        Returns:
            Dict[str, List[Dict]]: Mapping of card names to their pricing data
        """
        results = {}
        
        for card_name in card_names:
            try:
                printings = self.get_card_printings(card_name)
                results[card_name] = printings
                
                # Add small delay between requests to be respectful
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to get prices for {card_name}: {e}")
                results[card_name] = []
        
        return results
    
    def test_connection(self) -> bool:
        """
        Test API connection and authentication.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            # Try to get a simple endpoint - sets endpoint requires game parameter
            response = self._make_request('sets', params={'game': 'magic-the-gathering', 'limit': 1})
            logger.info("API connection test successful")
            return True
            
        except APIError as e:
            logger.error(f"API connection test failed: {e}")
            return False
    
    def get_rate_limit_status(self) -> Dict:
        """
        Get current rate limit status.
        
        Returns:
            Dict: Rate limit status information
        """
        return {
            'calls_per_minute_limit': self.rate_limit.calls_per_minute,
            'calls_per_hour_limit': self.rate_limit.calls_per_hour,
            'calls_this_minute': self.rate_limit.call_count_minute,
            'calls_this_hour': self.rate_limit.call_count_hour,
            'last_call_time': self.rate_limit.last_call_time
        }


# Mock implementation for testing when API is not available
class MockJustTCGClient(JustTCGClient):
    """Mock implementation for testing purposes."""
    
    def __init__(self):
        # Don't call parent __init__ to avoid setting up real session
        self.rate_limit = RateLimit()
        self.lock = threading.Lock()
    
    def search_cards(self, card_name: str, set_code: Optional[str] = None, 
                    exact_match: bool = False) -> List[Dict]:
        """Mock card search."""
        return [
            {
                'id': f'mock_{card_name.lower().replace(" ", "_")}',
                'name': card_name,
                'set_code': set_code or 'DOM',
                'collector_number': '123',
                'rarity': 'rare',
                'image_url': 'https://example.com/image.jpg'
            }
        ]
    
    def get_card_prices(self, card_id: str) -> List[Dict]:
        """Mock card pricing."""
        return [
            {
                'price': 5.99,
                'condition': 'NM',
                'foil': False,
                'seller': 'Mock Store'
            },
            {
                'price': 4.50,
                'condition': 'LP',
                'foil': False,
                'seller': 'Mock Store'
            }
        ]
    
    def test_connection(self) -> bool:
        """Mock connection test."""
        return True


def create_api_client(api_key: Optional[str] = None, use_mock: bool = False) -> JustTCGClient:
    """
    Factory function to create API client with fallback to mock.
    
    Args:
        api_key: JustTCG API key
        use_mock: Force use of mock client
        
    Returns:
        JustTCGClient: Either real or mock client
    """
    if use_mock:
        logger.info("Using mock API client")
        return MockJustTCGClient()
    
    try:
        client = JustTCGClient(api_key)
        # Quick test to see if we can connect
        logger.info("Testing API connection...")
        if client.test_connection():
            logger.info("API connection successful, using real client")
            return client
        else:
            logger.warning("API connection failed, falling back to mock client")
            return MockJustTCGClient()
    except Exception as e:
        logger.error(f"Failed to create API client: {e}")
        logger.info("Falling back to mock client")
        return MockJustTCGClient()