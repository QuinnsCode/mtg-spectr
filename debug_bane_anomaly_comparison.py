#!/usr/bin/env python3
"""
Debug script to compare anomaly detection between individual card search and set scanner
for "Bane of Progress" to identify inconsistencies.

This script:
1. Searches for "Bane of Progress" using individual card search functionality
2. Gets the same card data that set scanner would use for FIC set 
3. Compares anomaly detection logic between both methods
4. Shows exact expected price calculations, anomaly scores, and confidence levels
5. Identifies why one method detects it as anomaly and the other doesn't
"""

import sys
import logging
from pathlib import Path
import json
from datetime import datetime

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from analysis.set_scanner import SetScanner
from data.unified_api_client import create_unified_client
from data.database import DatabaseManager

# Import PriceAnalyzer with fallback
try:
    from analysis.price_analyzer import PriceAnalyzer
    PRICE_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PriceAnalyzer not available: {e}")
    PRICE_ANALYZER_AVAILABLE = False
    PriceAnalyzer = None

# Import SearchWorker with fallback
try:
    from gui.search_widget import SearchWorker
    SEARCH_WIDGET_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SearchWorker not available: {e}")
    SEARCH_WIDGET_AVAILABLE = False
    SearchWorker = None

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_bane_anomaly_comparison():
    """Compare anomaly detection between individual search and set scanner for Bane of Progress."""
    
    print("=" * 80)
    print("BANE OF PROGRESS ANOMALY DETECTION COMPARISON")
    print("=" * 80)
    
    # Initialize components
    client = create_unified_client()
    database_manager = DatabaseManager()
    set_scanner = SetScanner(api_client=client, database_manager=database_manager)
    
    # Step 1: Search for Bane of Progress using individual card search
    print("\n1. INDIVIDUAL CARD SEARCH (SearchWidget path)")
    print("-" * 50)
    
    individual_results = []
    fic_individual_result = None
    
    if PRICE_ANALYZER_AVAILABLE and SEARCH_WIDGET_AVAILABLE:
        try:
            price_analyzer = PriceAnalyzer(database_manager)
            search_worker = SearchWorker(client, database_manager, price_analyzer)
            search_params = {
                'card_name': 'Bane of Progress',
                'set_code': None,
                'search_mode': 'single',
                'include_analysis': True,
                'analysis_method': 'iqr',
                'min_data_points': 5,
                'historical_days': 30
            }
            
            search_worker.set_search_params(search_params)
            
            # Get individual search results
            print("Searching for 'Bane of Progress' via individual card search...")
            individual_results = search_worker._search_single_card('Bane of Progress', None, True)
            
            print(f"Individual search found {len(individual_results)} results")
            
            # Find FIC printing in individual results
            for result in individual_results:
                if result.get('set_code') == 'fic':
                    fic_individual_result = result
                    break
            
            if fic_individual_result:
                print(f"✓ Found FIC printing in individual search:")
                print(f"  - Card: {fic_individual_result['card_name']}")
                print(f"  - Set: {fic_individual_result['set_code']}")
                print(f"  - Current Price: ${fic_individual_result['price_dollars']:.2f}")
                print(f"  - Expected Price: ${fic_individual_result['expected_price']:.2f}")
                print(f"  - Is Anomaly: {fic_individual_result['is_anomaly']}")
                print(f"  - Anomaly Score: {fic_individual_result['anomaly_score']:.3f}")
                print(f"  - Savings Potential: ${fic_individual_result['savings_potential']:.2f}")
                print(f"  - Method: PriceAnalyzer")
            else:
                print("❌ FIC printing not found in individual search results")
                
        except Exception as e:
            print(f"❌ Error running individual search: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Individual search not available (missing dependencies)")
        print("   This is likely due to missing numpy/pandas/sklearn dependencies")
        print("   Will focus on Set Scanner analysis only")
    
    # Step 2: Get card data using set scanner approach
    print("\n2. SET SCANNER APPROACH (SetScanner path)")
    print("-" * 50)
    
    # Search for Bane of Progress using unified client (same as set scanner)
    print("Searching for 'Bane of Progress' via API...")
    api_cards = client.search_cards("Bane of Progress")
    
    print(f"Found {len(api_cards)} printings of 'Bane of Progress':")
    for i, card in enumerate(api_cards):
        set_code = card.get('set', 'Unknown')
        set_name = card.get('set_name', 'Unknown')
        prices = card.get('prices', {})
        usd_price = prices.get('usd', 'N/A')
        print(f"  {i+1}. {set_code} - {set_name} - ${usd_price}")
    
    # Find FIC printing in API results
    fic_api_card = None
    for card in api_cards:
        if card.get('set') == 'fic':
            fic_api_card = card
            break
    
    # If no FIC, use the first available card for demonstration
    demo_card = fic_api_card if fic_api_card else (api_cards[0] if api_cards else None)
    
    if demo_card:
        is_fic = demo_card.get('set') == 'fic'
        print(f"\n{'✓ Found FIC printing' if is_fic else '✓ Using first available printing for demonstration'}:")
        print(f"  - Card: {demo_card.get('name', 'Unknown')}")
        print(f"  - Set: {demo_card.get('set', 'Unknown')} ({demo_card.get('set_name', 'Unknown')})")
        print(f"  - Rarity: {demo_card.get('rarity', 'Unknown')}")
        print(f"  - Type: {demo_card.get('type_line', 'Unknown')}")
        print(f"  - Mana Cost: {demo_card.get('mana_cost', 'Unknown')}")
        
        # Get pricing info
        prices = demo_card.get('prices', {})
        usd_price = prices.get('usd')
        print(f"  - USD Price: ${usd_price}")
        
        if usd_price:
            current_price = float(usd_price)
            print(f"  - Current Price (float): ${current_price:.2f}")
            
            # Use set scanner anomaly detection
            print(f"\n  Set Scanner Anomaly Analysis:")
            expected_price = set_scanner._calculate_expected_price(demo_card)
            print(f"  - Expected Price: ${expected_price:.2f}")
            
            anomaly_score = set_scanner._calculate_anomaly_score(current_price, expected_price, demo_card)
            print(f"  - Anomaly Score: {anomaly_score:.3f}")
            
            anomaly_type = set_scanner._determine_anomaly_type(current_price, expected_price, anomaly_score)
            print(f"  - Anomaly Type: {anomaly_type}")
            
            confidence = set_scanner._calculate_confidence(demo_card, anomaly_score)
            print(f"  - Confidence: {confidence:.3f}")
            
            # Check if it meets thresholds
            thresholds = set_scanner.anomaly_thresholds
            print(f"  - Thresholds: price_deviation={thresholds['price_deviation']}, confidence_threshold={thresholds['confidence_threshold']}")
            
            # Test set scanner's analyze_card_anomalies method
            scanner_anomaly_info = set_scanner._analyze_card_anomalies(demo_card)
            if scanner_anomaly_info:
                print(f"  - Set Scanner Result: IS ANOMALY")
                print(f"    - Anomaly Type: {scanner_anomaly_info['anomaly_type']}")
                print(f"    - Anomaly Score: {scanner_anomaly_info['anomaly_score']:.3f}")
                print(f"    - Confidence: {scanner_anomaly_info['confidence']:.3f}")
            else:
                print(f"  - Set Scanner Result: NOT ANOMALY")
        else:
            print("  - No USD price available")
            
        # Update variables for later use
        fic_api_card = demo_card
        scanner_price = float(usd_price) if usd_price else 0
        scanner_expected = set_scanner._calculate_expected_price(demo_card)
        scanner_score = set_scanner._calculate_anomaly_score(scanner_price, scanner_expected, demo_card)
        scanner_confidence = set_scanner._calculate_confidence(demo_card, scanner_score)
        
    else:
        print("❌ No printings found in API search")
    
    # Step 3: Compare methods side by side
    print("\n3. DETAILED COMPARISON")
    print("-" * 50)
    
    if demo_card and 'scanner_price' in locals():
        print("INDIVIDUAL SEARCH vs SET SCANNER:")
        print(f"{'Metric':<25} {'Individual Search':<20} {'Set Scanner':<20}")
        print("-" * 65)
        
        # Price comparison
        if fic_individual_result:
            ind_price = fic_individual_result['price_dollars']
            ind_expected = fic_individual_result['expected_price']
            ind_anomaly = fic_individual_result['is_anomaly']
            ind_score = fic_individual_result['anomaly_score']
        else:
            ind_price = "N/A"
            ind_expected = "N/A"
            ind_anomaly = "N/A"
            ind_score = "N/A"
            
        print(f"{'Current Price':<25} ${ind_price if ind_price == 'N/A' else f'{ind_price:.2f}':<19} ${scanner_price:<19.2f}")
        print(f"{'Expected Price':<25} ${ind_expected if ind_expected == 'N/A' else f'{ind_expected:.2f}':<19} ${scanner_expected:<19.2f}")
        
        # Anomaly detection
        scanner_anomaly_info = set_scanner._analyze_card_anomalies(demo_card)
        scanner_anomaly = scanner_anomaly_info is not None
        print(f"{'Is Anomaly':<25} {str(ind_anomaly):<20} {str(scanner_anomaly):<20}")
        
        # Anomaly scores
        print(f"{'Anomaly Score':<25} {ind_score if ind_score == 'N/A' else f'{ind_score:.3f}':<20} {scanner_score:<20.3f}")
        
        # Method used
        print(f"{'Method':<25} {'PriceAnalyzer':<20} {'SetScanner':<20}")
        
        # Analysis method details
        print(f"{'Analysis Type':<25} {'Statistical (IQR)':<20} {'Expected Price':<20}")
        
        # Confidence/thresholds
        print(f"{'Confidence':<25} {'N/A':<20} {scanner_confidence:<20.3f}")
        
        # Why different results?
        print(f"\n4. WHY DIFFERENT RESULTS?")
        print("-" * 50)
        
        print("INDIVIDUAL SEARCH (PriceAnalyzer):")
        print("- Uses statistical analysis on historical price data from database")
        print("- Requires historical data points to calculate anomalies")
        print("- Uses IQR, Z-score, or Isolation Forest methods")
        print("- Compares current price to historical price distribution")
        print("- Looks for outliers in actual market data")
        
        print("\nSET SCANNER (SetScanner):")
        print("- Uses rule-based expected price calculation")
        print("- Based on card characteristics (rarity, type, mana cost, set)")
        print("- Uses fixed multipliers and heuristics")
        print("- Compares current price to calculated expected price")
        print("- No dependency on historical data")
        
    # Check historical data availability
    print(f"\n5. HISTORICAL DATA ANALYSIS")
    print("-" * 50)
    
    try:
        card_set = demo_card.get('set', 'fic') if demo_card else 'fic'
        historical_data = database_manager.get_historical_prices('Bane of Progress', card_set, 30)
        print(f"Historical data points for Bane of Progress ({card_set.upper()}): {len(historical_data)}")
        
        if len(historical_data) < 5:
            print("❌ INSUFFICIENT DATA: PriceAnalyzer requires at least 5 data points")
            print("   This explains why individual search may not detect anomaly")
        else:
            print("✓ SUFFICIENT DATA: PriceAnalyzer can perform statistical analysis")
            
            # Show historical price distribution
            prices = [data['price_cents'] / 100.0 for data in historical_data]
            print(f"   Price range: ${min(prices):.2f} - ${max(prices):.2f}")
            print(f"   Average price: ${sum(prices)/len(prices):.2f}")
            
    except Exception as e:
        print(f"❌ Error getting historical data: {e}")
    
    # Step 6: Threshold Analysis
    print(f"\n6. THRESHOLD ANALYSIS")
    print("-" * 50)
    
    print("SET SCANNER THRESHOLDS:")
    thresholds = set_scanner.anomaly_thresholds
    for key, value in thresholds.items():
        print(f"  - {key}: {value}")
    
    if PRICE_ANALYZER_AVAILABLE:
        try:
            price_analyzer = PriceAnalyzer(database_manager)
            print("\nPRICE ANALYZER SETTINGS:")
            print(f"  - anomaly_method: {price_analyzer.anomaly_method}")
            print(f"  - minimum_data_points: {price_analyzer.minimum_data_points}")
            print(f"  - historical_days: {price_analyzer.historical_days}")
            print(f"  - iqr_threshold: {price_analyzer.iqr_threshold}")
            print(f"  - zscore_threshold: {price_analyzer.zscore_threshold}")
        except Exception as e:
            print(f"\nPRICE ANALYZER SETTINGS: Not available ({e})")
    else:
        print("\nPRICE ANALYZER SETTINGS: Not available (missing dependencies)")
    
    # Step 7: Decision factors
    print(f"\n7. DECISION FACTORS")
    print("-" * 50)
    
    if demo_card and 'scanner_price' in locals():
        scanner_anomaly_info = set_scanner._analyze_card_anomalies(demo_card)
        if scanner_anomaly_info:
            print("SET SCANNER DETECTED ANOMALY:")
            print(f"  - Price deviation: {scanner_score:.3f} >= {thresholds['price_deviation']}")
            print(f"  - Confidence: {scanner_confidence:.3f} >= {thresholds['confidence_threshold']}")
            print(f"  - Above minimum price: ${scanner_price:.2f} >= $0.50")
        else:
            print("SET SCANNER DID NOT DETECT ANOMALY:")
            if scanner_price < 0.50:
                print(f"  - Below minimum price: ${scanner_price:.2f} < $0.50")
            elif scanner_score < thresholds['price_deviation']:
                print(f"  - Low deviation: {scanner_score:.3f} < {thresholds['price_deviation']}")
            elif scanner_confidence < thresholds['confidence_threshold']:
                print(f"  - Low confidence: {scanner_confidence:.3f} < {thresholds['confidence_threshold']}")
        
        if fic_individual_result and fic_individual_result['is_anomaly']:
            print("\nINDIVIDUAL SEARCH DETECTED ANOMALY:")
            print(f"  - Statistical analysis found price outlier")
            print(f"  - Anomaly score: {fic_individual_result['anomaly_score']:.3f}")
            print(f"  - Expected from historical data: ${fic_individual_result['expected_price']:.2f}")
        elif fic_individual_result:
            print("\nINDIVIDUAL SEARCH DID NOT DETECT ANOMALY:")
            print(f"  - No statistical anomaly found in historical data")
            print(f"  - Price within normal distribution")
        else:
            print("\nINDIVIDUAL SEARCH: Not available or no results")
    else:
        print("❌ Cannot analyze - missing card data from API")
    
    # Step 8: Recommendations
    print(f"\n8. RECOMMENDATIONS")
    print("-" * 50)
    
    print("To resolve inconsistencies:")
    print("1. Ensure both methods use the same price data source")
    print("2. Consider adjusting set scanner thresholds if too strict")
    print("3. Improve historical data collection for PriceAnalyzer")
    print("4. Consider hybrid approach combining both methods")
    print("5. Add logging to track why cards are/aren't flagged as anomalies")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    debug_bane_anomaly_comparison()