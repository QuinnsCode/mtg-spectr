# api/index.py - Vercel-compatible Flask API
from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# Simple Scryfall client (embedded for Vercel)
class ScryfallClient:
    def __init__(self):
        self.base_url = "https://api.scryfall.com"
    
    def search_cards(self, query, limit=100):
        """Search cards using Scryfall API directly."""
        try:
            url = f"{self.base_url}/cards/search"
            params = {'q': query}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                cards = data.get('data', [])
                return cards[:limit] if limit else cards
            else:
                return []
        except Exception:
            return []
    
    def get_sets(self):
        """Get all MTG sets."""
        try:
            response = requests.get(f"{self.base_url}/sets", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []
        except Exception:
            return []
    
    def get_autocomplete(self, query):
        """Get autocomplete suggestions."""
        try:
            url = f"{self.base_url}/cards/autocomplete"
            params = {'q': query}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []
        except Exception:
            return []

# Initialize client
scryfall = ScryfallClient()

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def hello():
    return {'message': 'MTG Card Pricing API - Ready!'}

@app.route('/api/health')
def health():
    """Health check."""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'scryfall_api': True,
            'serverless': True
        }
    }

@app.route('/api/search', methods=['POST'])
def search_cards():
    """Search for MTG cards."""
    try:
        data = request.get_json() or {}
        card_name = data.get('card_name', '').strip()
        set_code = data.get('set_code', '').strip()
        limit = min(data.get('limit', 10), 100)
        
        if not card_name:
            return jsonify({'error': 'Card name is required'}), 400
        
        # Build search query
        query = card_name
        if set_code:
            query += f' e:{set_code}'
        
        # Search using Scryfall
        cards = scryfall.search_cards(query, limit)
        
        # Format results
        formatted_results = []
        for card in cards:
            formatted_card = {
                'id': card.get('id', ''),
                'name': card.get('name', ''),
                'set': card.get('set', ''),
                'set_name': card.get('set_name', ''),
                'collector_number': card.get('collector_number', ''),
                'rarity': card.get('rarity', ''),
                'prices': card.get('prices', {}),
                'foil': card.get('foil', False),
                'nonfoil': card.get('nonfoil', True),
                'image_uris': card.get('image_uris', {}),
                'scryfall_uri': card.get('scryfall_uri', ''),
                'released_at': card.get('released_at', '')
            }
            formatted_results.append(formatted_card)
        
        return jsonify({
            'status': 'success',
            'results': formatted_results,
            'count': len(formatted_results),
            'search_params': {
                'card_name': card_name,
                'set_code': set_code,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/search/suggestions')
def get_search_suggestions():
    """Get autocomplete suggestions."""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([])
        
        suggestions = scryfall.get_autocomplete(query)
        return jsonify(suggestions)
        
    except Exception as e:
        return jsonify([])

@app.route('/api/sets')
def get_sets():
    """Get list of MTG sets."""
    try:
        sets_data = scryfall.get_sets()
        
        # Sort by release date (newest first)
        if sets_data:
            sorted_sets = sorted(
                sets_data, 
                key=lambda x: x.get('released_at', '1900-01-01'), 
                reverse=True
            )
        else:
            sorted_sets = []
        
        return jsonify({
            'status': 'success',
            'sets': sorted_sets,
            'count': len(sorted_sets),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/sets/<set_code>/scan', methods=['POST'])
def scan_set(set_code):
    """Scan all cards in a set."""
    try:
        # Search for all cards in the set
        cards = scryfall.search_cards(f"e:{set_code}")
        
        if not cards:
            return jsonify({
                'status': 'error',
                'error': f'No cards found for set {set_code}'
            }), 404
        
        # Process cards and calculate values
        processed_cards = []
        total_value = 0
        
        for card in cards:
            prices = card.get('prices', {})
            usd_price = prices.get('usd')
            
            # Handle price conversion
            if usd_price is None or usd_price == '':
                usd_price = 0.0
            elif isinstance(usd_price, str):
                try:
                    usd_price = float(usd_price)
                except (ValueError, TypeError):
                    usd_price = 0.0
            elif not isinstance(usd_price, (int, float)):
                usd_price = 0.0
            
            card_data = {
                'name': card.get('name', ''),
                'set_code': card.get('set', set_code),
                'collector_number': card.get('collector_number', ''),
                'rarity': card.get('rarity', ''),
                'usd_price': usd_price,
                'prices': prices,
                'image_uris': card.get('image_uris', {}),
                'scryfall_uri': card.get('scryfall_uri', '')
            }
            processed_cards.append(card_data)
            total_value += usd_price
        
        # Sort by price (highest first)
        processed_cards.sort(key=lambda x: x['usd_price'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'set_code': set_code,
            'cards': processed_cards,
            'summary': {
                'total_cards': len(processed_cards),
                'total_value': round(total_value, 2),
                'average_value': round(total_value / len(processed_cards), 2) if processed_cards else 0,
                'cards_with_price': len([c for c in processed_cards if c['usd_price'] > 0])
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/cards/printings/<card_name>')
def get_card_printings(card_name):
    """Get all printings of a card."""
    try:
        # Search for all printings using exact name
        cards = scryfall.search_cards(f'!"{card_name}"')
        
        printings_data = []
        for card in cards:
            printing_dict = {
                'card_name': card.get('name', card_name),
                'set_code': card.get('set', ''),
                'set_name': card.get('set_name', ''),
                'collector_number': card.get('collector_number', ''),
                'rarity': card.get('rarity', ''),
                'prices': card.get('prices', {}),
                'foil_available': card.get('foil', False),
                'nonfoil_available': card.get('nonfoil', True),
                'source': 'Scryfall',
                'card_id': card.get('id', ''),
                'image_url': card.get('image_uris', {}).get('normal', ''),
                'released_at': card.get('released_at', ''),
                'scryfall_uri': card.get('scryfall_uri', '')
            }
            printings_data.append(printing_dict)
        
        return jsonify({
            'status': 'success',
            'card_name': card_name,
            'printings': printings_data,
            'count': len(printings_data),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /api/health',
            'POST /api/search',
            'GET /api/search/suggestions',
            'GET /api/cards/printings/<name>',
            'GET /api/sets',
            'POST /api/sets/<code>/scan'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'error': 'Internal server error'
    }), 500