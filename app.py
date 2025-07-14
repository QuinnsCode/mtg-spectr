# app.py - Updated Flask API for your MTG Card Pricing tool
from flask import Flask, request, jsonify
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services - with error handling for missing modules
api_client = None
trend_db = None
alert_system = None

try:
    # Import your existing modules
    from data.unified_api_client import create_unified_client
    from data.scryfall_client import create_scryfall_client  
    from data.trend_database import TrendDatabase
    
    # Try to import alert system (might not work in serverless environment)
    try:
        from data.alert_system import AlertSystem
        alert_system = AlertSystem()
        logger.info("Alert system initialized")
    except Exception as e:
        logger.warning(f"Alert system not available in serverless environment: {e}")
        alert_system = None
    
    # Configuration from environment variables
    USE_MOCK = os.environ.get('USE_MOCK_API', 'false').lower() == 'true'
    API_PROVIDER = os.environ.get('API_PROVIDER', 'scryfall')
    JUSTTCG_API_KEY = os.environ.get('JUSTTCG_API_KEY')
    
    # Initialize API client
    api_client = create_unified_client(
        provider=API_PROVIDER,
        api_key=JUSTTCG_API_KEY,
        use_mock=USE_MOCK
    )
    logger.info(f"API client initialized with {API_PROVIDER} provider")
    
    # Initialize trend database
    trend_db = TrendDatabase()
    logger.info("Trend database initialized")
    
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    logger.info("Running in basic mode without full functionality")

# ============================================================================
# BASIC ENDPOINTS (your existing ones)
# ============================================================================

@app.route('/')
def hello():
    return {'message': 'MTG Card Pricing API - Ready!'}

@app.route('/api/health')
def health():
    """Health check with service status."""
    services_status = {
        'api_client': api_client is not None and api_client.test_connection() if api_client else False,
        'trend_database': trend_db is not None,
        'alert_system': alert_system is not None
    }
    
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': services_status
    }

# ============================================================================
# CARD SEARCH API
# ============================================================================

@app.route('/api/search', methods=['POST'])
def search_cards():
    """Search for MTG cards."""
    if not api_client:
        return jsonify({'error': 'API client not available'}), 503
    
    try:
        data = request.get_json() or {}
        
        # Extract search parameters
        card_name = data.get('card_name', '').strip()
        set_code = data.get('set_code', '').strip() or None
        exact_match = data.get('exact_match', False)
        limit = min(data.get('limit', 100), 1000)
        
        if not card_name:
            return jsonify({'error': 'Card name is required'}), 400
        
        # Search using your existing API client
        search_results = api_client.search_cards(
            card_name=card_name,
            set_code=set_code,
            exact_match=exact_match
        )
        
        # Limit results
        if limit and len(search_results) > limit:
            search_results = search_results[:limit]
        
        # Format results
        formatted_results = []
        for card in search_results:
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
                'exact_match': exact_match
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/search/suggestions')
def get_search_suggestions():
    """Get autocomplete suggestions."""
    if not api_client:
        return jsonify([])
    
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([])
        
        suggestions = api_client.get_autocomplete_suggestions(query)
        return jsonify(suggestions)
        
    except Exception as e:
        logger.error(f"Suggestions failed: {e}")
        return jsonify([])

@app.route('/api/cards/printings/<card_name>')
def get_card_printings(card_name):
    """Get all printings of a card."""
    if not api_client:
        return jsonify({'error': 'API client not available'}), 503
    
    try:
        printings = api_client.get_card_printings(card_name)
        
        # Convert to dict format
        printings_data = []
        for printing in printings:
            if hasattr(printing, 'card_name'):  # CardPricing object
                printing_dict = {
                    'card_name': printing.card_name,
                    'set_code': printing.set_code,
                    'set_name': printing.set_name,
                    'collector_number': printing.collector_number,
                    'rarity': printing.rarity,
                    'prices': printing.prices,
                    'foil_available': printing.foil_available,
                    'nonfoil_available': printing.nonfoil_available,
                    'source': printing.source,
                    'card_id': printing.card_id,
                    'image_url': printing.image_url,
                    'released_at': printing.released_at
                }
            else:  # Already a dict
                printing_dict = printing
            
            printings_data.append(printing_dict)
        
        return jsonify({
            'status': 'success',
            'card_name': card_name,
            'printings': printings_data,
            'count': len(printings_data),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get printings for {card_name}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ============================================================================
# SETS API
# ============================================================================

@app.route('/api/sets')
def get_sets():
    """Get list of MTG sets."""
    if not api_client:
        return jsonify({'error': 'API client not available'}), 503
    
    try:
        sets_data = api_client.get_sets()
        
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
        logger.error(f"Failed to get sets: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/sets/<set_code>/scan', methods=['POST'])
def scan_set(set_code):
    """Scan all cards in a set."""
    if not api_client:
        return jsonify({'error': 'API client not available'}), 503
    
    try:
        # Search for all cards in the set
        if hasattr(api_client, 'provider') and api_client.provider == "scryfall":
            cards = api_client.search_cards(f"e:{set_code}")
        else:
            cards = api_client.search_cards("", set_code=set_code)
        
        if not cards:
            return jsonify({
                'status': 'error',
                'error': f'No cards found for set {set_code}'
            }), 404
        
        # Process cards
        processed_cards = []
        total_value = 0
        
        for card in cards:
            prices = card.get('prices', {})
            usd_price = prices.get('usd')
            
            # Handle None, empty string, or string prices
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
        logger.error(f"Failed to scan set {set_code}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ============================================================================
# TREND ANALYSIS API
# ============================================================================

@app.route('/api/trends/analyze', methods=['POST'])
def analyze_trends():
    """Analyze price trends."""
    if not trend_db:
        return jsonify({'error': 'Trend database not available'}), 503
    
    try:
        data = request.get_json() or {}
        
        # Extract parameters
        min_percentage_change = data.get('min_percentage_change', 20.0)
        min_absolute_change = data.get('min_absolute_change', 0.50)
        min_price_threshold = data.get('min_price_threshold', 0.50)
        hours_back = data.get('hours_back', 168)
        max_cards = data.get('max_cards', 1000)
        
        # Use your existing trend analysis
        trending_cards = trend_db.find_trending_cards(
            min_percentage_change=min_percentage_change,
            min_absolute_change=min_absolute_change,
            min_price_threshold=min_price_threshold,
            hours_back=hours_back,
            max_cards=max_cards
        )
        
        return jsonify({
            'status': 'success',
            'trending_cards': trending_cards,
            'count': len(trending_cards),
            'analysis_params': {
                'min_percentage_change': min_percentage_change,
                'min_absolute_change': min_absolute_change,
                'min_price_threshold': min_price_threshold,
                'hours_back': hours_back
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/database/stats')
def get_database_stats():
    """Get database statistics."""
    if not trend_db:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        stats = trend_db.get_database_stats()
        return jsonify({
            'status': 'success',
            'database_stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ============================================================================
# API PROVIDER INFO
# ============================================================================

@app.route('/api/provider/info')
def get_provider_info():
    """Get API provider information."""
    if not api_client:
        return jsonify({'error': 'API client not available'}), 503
    
    try:
        if hasattr(api_client, 'get_provider_info'):
            provider_info = api_client.get_provider_info()
        else:
            provider_info = {
                'provider': getattr(api_client, 'provider', 'unknown'),
                'client_type': type(api_client).__name__
            }
        
        return jsonify({
            'status': 'success',
            'provider_info': provider_info,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get provider info: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

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
            'POST /api/sets/<code>/scan',
            'POST /api/trends/analyze',
            'GET /api/database/stats',
            'GET /api/provider/info'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'error': 'Internal server error'
    }), 500

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)