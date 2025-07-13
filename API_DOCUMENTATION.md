# API Documentation

## Overview

The MTG Card Pricing Analysis Tool supports multiple APIs for retrieving card data and pricing information. The application uses a unified API client architecture that allows seamless switching between providers.

## Supported APIs

### Scryfall API (Recommended)

**Base URL**: `https://api.scryfall.com`  
**Authentication**: None required  
**Rate Limit**: 10 requests per second  
**Documentation**: https://scryfall.com/docs/api

#### Key Features
- Free to use without registration
- Comprehensive card data including all printings
- Automatic pagination for large result sets
- Real-time pricing data
- High reliability and uptime

#### Implementation Details
```python
from data.scryfall_client import create_scryfall_client

client = create_scryfall_client()
cards = client.search_cards("e:dsk")  # Get all cards from a set
```

### JustTCG API

**Base URL**: `https://api.justtcg.com/v1`  
**Authentication**: API key required  
**Rate Limit**: 10 calls/minute, 100 calls/hour  
**Documentation**: Internal API

#### Key Features
- Specialized TCG pricing data
- Historical price tracking
- Condition-specific pricing
- Limited to 175 results per search

#### Implementation Details
```python
from data.api_client import APIClient

client = APIClient(api_key="your_key")
cards = client.search_cards("Lightning Bolt")
```

## Unified API Client

The application uses a unified API client that abstracts the differences between providers:

```python
from data.unified_api_client import create_unified_client

# Automatically selects the best available API
client = create_unified_client()

# Or specify a provider
client = create_unified_client(provider="scryfall")
```

## API Methods

### Search Cards
```python
cards = client.search_cards(query, **kwargs)
```
- **query**: Search string (card name, set code, etc.)
- **Returns**: List of card dictionaries

### Get Card by Name
```python
card = client.get_card_by_name(name, set_code=None)
```
- **name**: Exact card name
- **set_code**: Optional set code for specific printing
- **Returns**: Card dictionary or None

### Get Sets
```python
sets = client.get_sets()
```
- **Returns**: List of all available sets

### Get Card Printings
```python
printings = client.get_card_printings(card_name)
```
- **card_name**: Name of the card
- **Returns**: List of all printings across sets

## Pagination

The Scryfall client automatically handles pagination for large result sets:

```python
# Automatically retrieves all pages
cards = client.search_cards("e:dsk")  # 400+ cards handled seamlessly
```

## Rate Limiting

Both APIs implement rate limiting to prevent overuse:

### Scryfall
- 10 requests per second
- Automatic 100ms delay between requests
- No hourly or daily limits

### JustTCG
- 10 requests per minute
- 100 requests per hour
- Exponential backoff on 429 errors

## Error Handling

The clients implement comprehensive error handling:

```python
try:
    cards = client.search_cards("Lightning Bolt")
except ScryfallAPIError as e:
    logger.error(f"API error: {e}")
```

Common errors:
- **404**: Card/set not found
- **429**: Rate limit exceeded
- **500**: Server error

## Query Sanitization

The Scryfall client includes advanced query sanitization:

```python
# Problematic characters are automatically cleaned
query = "Fire // Ice"  # Handled correctly
query = "Urza's Mine"  # Apostrophes handled
query = "AND/OR/NOT"   # Operators sanitized
```

## Mock Clients

For testing without API access:

```python
client = create_unified_client(use_mock=True)
# Returns realistic test data
```

## Best Practices

1. **Use Scryfall for general searches** - It's free and has better limits
2. **Use JustTCG for specific TCG pricing** - When you need condition-specific data
3. **Cache results when possible** - Reduce API calls for repeated searches
4. **Handle errors gracefully** - Always wrap API calls in try/except
5. **Respect rate limits** - The clients handle this automatically

## Response Format

### Card Object
```json
{
  "name": "Lightning Bolt",
  "set": "2ed",
  "set_name": "Unlimited Edition",
  "collector_number": "162",
  "rarity": "common",
  "type_line": "Instant",
  "mana_cost": "{R}",
  "prices": {
    "usd": "5.99",
    "usd_foil": "12.99",
    "eur": "5.50"
  },
  "image_uris": {
    "normal": "https://...",
    "large": "https://..."
  },
  "released_at": "1993-12-01"
}
```

### Set Object
```json
{
  "code": "dsk",
  "name": "Duskmourn: House of Horror",
  "set_type": "expansion",
  "card_count": 276,
  "digital": false,
  "released_at": "2024-09-27"
}
```

## Extending the API

To add a new API provider:

1. Create a new client class inheriting from base functionality
2. Implement required methods (search, get_card, etc.)
3. Add to unified client factory
4. Update configuration options

Example:
```python
class NewAPIClient:
    def search_cards(self, query: str) -> List[Dict]:
        # Implementation
        pass
    
    def get_card_by_name(self, name: str) -> Optional[Dict]:
        # Implementation
        pass
```