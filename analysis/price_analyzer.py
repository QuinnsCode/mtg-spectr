"""
Price analysis module for MTG card pricing anomaly detection.
Implements statistical methods to identify underpriced card printings.
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings

# Suppress sklearn warnings
warnings.filterwarnings('ignore')

from data.database import DatabaseManager
from config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result of anomaly detection analysis."""
    card_name: str
    set_code: str
    printing_info: str
    condition: str
    foil: bool
    actual_price: float
    expected_price: float
    is_anomaly: bool
    anomaly_score: float
    savings_potential: float
    confidence: float
    method_used: str


class PriceAnalyzer:
    """Analyzes card prices to identify anomalies and underpriced items."""
    
    def __init__(self, database_manager: DatabaseManager):
        """
        Initialize price analyzer.
        
        Args:
            database_manager: Database manager instance
        """
        self.database_manager = database_manager
        self.settings = get_settings().settings.analysis
        
        # Analysis parameters
        self.anomaly_method = self.settings.anomaly_detection_method
        self.iqr_threshold = self.settings.iqr_threshold
        self.zscore_threshold = self.settings.zscore_threshold
        self.isolation_contamination = self.settings.isolation_forest_contamination
        self.minimum_data_points = self.settings.minimum_data_points
        self.historical_days = self.settings.historical_days
        self.confidence_level = self.settings.confidence_level
    
    def set_anomaly_method(self, method: str):
        """Set the anomaly detection method."""
        if method in ['iqr', 'zscore', 'isolation_forest']:
            self.anomaly_method = method
        else:
            logger.warning(f"Unknown anomaly method: {method}")
    
    def set_minimum_data_points(self, min_points: int):
        """Set minimum data points required for analysis."""
        self.minimum_data_points = max(1, min_points)
    
    def set_historical_days(self, days: int):
        """Set number of historical days to analyze."""
        self.historical_days = max(1, days)
    
    def analyze_card_prices(self, card_name: str, set_code: Optional[str] = None) -> List[Dict]:
        """
        Analyze card prices for anomalies.
        
        Args:
            card_name: Name of the card to analyze
            set_code: Optional set code filter
        
        Returns:
            List[Dict]: List of anomaly analysis results
        """
        try:
            # Get historical price data
            price_data = self.database_manager.get_historical_prices(
                card_name, set_code, self.historical_days
            )
            
            if len(price_data) < self.minimum_data_points:
                logger.info(f"Insufficient data for {card_name} ({len(price_data)} points)")
                return []
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(price_data)
            df['price_dollars'] = df['price_cents'] / 100.0
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Group by printing characteristics for comparison
            results = []
            
            # Group by set, condition, and foil status
            grouping_cols = ['set_code', 'condition', 'foil']
            for group_key, group_data in df.groupby(grouping_cols):
                if len(group_data) >= self.minimum_data_points:
                    group_results = self._analyze_group(group_data, card_name)
                    results.extend(group_results)
            
            # If no groups have enough data, analyze all together
            if not results and len(df) >= self.minimum_data_points:
                results = self._analyze_group(df, card_name)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing card prices: {e}")
            return []
    
    def _analyze_group(self, df: pd.DataFrame, card_name: str) -> List[Dict]:
        """
        Analyze a group of price data for anomalies.
        
        Args:
            df: DataFrame containing price data
            card_name: Name of the card
        
        Returns:
            List[Dict]: Analysis results for the group
        """
        results = []
        
        try:
            # Get price array
            prices = df['price_dollars'].values
            
            if len(prices) < self.minimum_data_points:
                return results
            
            # Detect anomalies based on method
            if self.anomaly_method == 'iqr':
                anomaly_mask, scores = self._detect_anomalies_iqr(prices)
            elif self.anomaly_method == 'zscore':
                anomaly_mask, scores = self._detect_anomalies_zscore(prices)
            elif self.anomaly_method == 'isolation_forest':
                anomaly_mask, scores = self._detect_anomalies_isolation_forest(prices)
            else:
                logger.warning(f"Unknown anomaly method: {self.anomaly_method}")
                return results
            
            # Calculate expected prices
            expected_prices = self._calculate_expected_prices(prices, anomaly_mask)
            
            # Create results for each record
            for i, (_, row) in enumerate(df.iterrows()):
                actual_price = row['price_dollars']
                expected_price = expected_prices[i]
                is_anomaly = anomaly_mask[i]
                anomaly_score = scores[i]
                
                # Calculate savings potential (for underpriced items)
                savings_potential = max(0, expected_price - actual_price)
                
                # Calculate confidence based on data quantity and variance
                confidence = self._calculate_confidence(prices, len(prices))
                
                result = {
                    'card_name': card_name,
                    'set_code': row.get('set_code', ''),
                    'printing_info': row.get('printing_info', ''),
                    'condition': row.get('condition', ''),
                    'foil': row.get('foil', False),
                    'actual_price': actual_price,
                    'expected_price': expected_price,
                    'is_anomaly': is_anomaly,
                    'anomaly_score': anomaly_score,
                    'savings_potential': savings_potential,
                    'confidence': confidence,
                    'method_used': self.anomaly_method
                }
                
                results.append(result)
            
        except Exception as e:
            logger.error(f"Error analyzing group: {e}")
        
        return results
    
    def _detect_anomalies_iqr(self, prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect anomalies using IQR method.
        
        Args:
            prices: Array of prices
        
        Returns:
            Tuple of (anomaly_mask, scores)
        """
        Q1 = np.percentile(prices, 25)
        Q3 = np.percentile(prices, 75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - self.iqr_threshold * IQR
        upper_bound = Q3 + self.iqr_threshold * IQR
        
        # Identify outliers (focus on underpriced items)
        anomaly_mask = prices < lower_bound
        
        # Calculate scores based on distance from bounds
        scores = np.zeros_like(prices)
        for i, price in enumerate(prices):
            if price < lower_bound:
                scores[i] = (lower_bound - price) / (IQR + 1e-6)
            elif price > upper_bound:
                scores[i] = (price - upper_bound) / (IQR + 1e-6)
            else:
                scores[i] = 0
        
        # Normalize scores to 0-1 range
        if scores.max() > 0:
            scores = scores / scores.max()
        
        return anomaly_mask, scores
    
    def _detect_anomalies_zscore(self, prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect anomalies using Z-score method.
        
        Args:
            prices: Array of prices
        
        Returns:
            Tuple of (anomaly_mask, scores)
        """
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        
        if std_price == 0:
            return np.zeros_like(prices, dtype=bool), np.zeros_like(prices)
        
        z_scores = np.abs((prices - mean_price) / std_price)
        
        # Focus on underpriced items (negative z-scores)
        underpriced_mask = prices < mean_price
        anomaly_mask = (z_scores > self.zscore_threshold) & underpriced_mask
        
        # Normalize scores to 0-1 range
        normalized_scores = z_scores / (self.zscore_threshold + 1e-6)
        normalized_scores = np.clip(normalized_scores, 0, 1)
        
        return anomaly_mask, normalized_scores
    
    def _detect_anomalies_isolation_forest(self, prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect anomalies using Isolation Forest.
        
        Args:
            prices: Array of prices
        
        Returns:
            Tuple of (anomaly_mask, scores)
        """
        if len(prices) < 10:  # Isolation Forest needs more data
            return self._detect_anomalies_iqr(prices)
        
        # Reshape for sklearn
        X = prices.reshape(-1, 1)
        
        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=self.isolation_contamination,
            random_state=42
        )
        
        anomaly_labels = iso_forest.fit_predict(X)
        anomaly_scores = iso_forest.decision_function(X)
        
        # Convert to boolean mask (anomalies are -1)
        anomaly_mask = anomaly_labels == -1
        
        # Focus on underpriced anomalies
        mean_price = np.mean(prices)
        underpriced_mask = prices < mean_price
        anomaly_mask = anomaly_mask & underpriced_mask
        
        # Normalize scores to 0-1 range
        scores = np.abs(anomaly_scores)
        if scores.max() > 0:
            scores = scores / scores.max()
        
        return anomaly_mask, scores
    
    def _calculate_expected_prices(self, prices: np.ndarray, anomaly_mask: np.ndarray) -> np.ndarray:
        """
        Calculate expected prices based on non-anomalous data.
        
        Args:
            prices: Array of prices
            anomaly_mask: Boolean mask indicating anomalies
        
        Returns:
            Array of expected prices
        """
        normal_prices = prices[~anomaly_mask]
        
        if len(normal_prices) == 0:
            # If all prices are anomalies, use median
            expected_price = np.median(prices)
        else:
            # Use mean of normal prices
            expected_price = np.mean(normal_prices)
        
        return np.full_like(prices, expected_price)
    
    def _calculate_confidence(self, prices: np.ndarray, data_points: int) -> float:
        """
        Calculate confidence level based on data quality.
        
        Args:
            prices: Array of prices
            data_points: Number of data points
        
        Returns:
            Confidence level (0-1)
        """
        # Base confidence on data quantity
        quantity_confidence = min(1.0, data_points / (self.minimum_data_points * 2))
        
        # Factor in price variance (lower variance = higher confidence)
        if len(prices) > 1:
            cv = np.std(prices) / (np.mean(prices) + 1e-6)  # Coefficient of variation
            variance_confidence = max(0.1, 1.0 - min(1.0, cv))
        else:
            variance_confidence = 0.5
        
        # Combine confidences
        confidence = (quantity_confidence + variance_confidence) / 2
        
        return min(1.0, confidence)
    
    def batch_analyze_cards(self, card_names: List[str], 
                           progress_callback: Optional[callable] = None) -> Dict[str, List[Dict]]:
        """
        Analyze multiple cards in batch.
        
        Args:
            card_names: List of card names to analyze
            progress_callback: Optional callback for progress updates
        
        Returns:
            Dictionary mapping card names to their analysis results
        """
        results = {}
        
        for i, card_name in enumerate(card_names):
            try:
                card_results = self.analyze_card_prices(card_name)
                results[card_name] = card_results
                
                if progress_callback:
                    progress_callback(i + 1, len(card_names))
                
            except Exception as e:
                logger.error(f"Error analyzing {card_name}: {e}")
                results[card_name] = []
        
        return results
    
    def get_top_anomalies(self, card_name: str, set_code: Optional[str] = None, 
                         limit: int = 10) -> List[Dict]:
        """
        Get top anomalies for a card sorted by score.
        
        Args:
            card_name: Name of the card
            set_code: Optional set code filter
            limit: Maximum number of results
        
        Returns:
            List of top anomaly results
        """
        results = self.analyze_card_prices(card_name, set_code)
        
        # Filter and sort anomalies
        anomalies = [r for r in results if r.get('is_anomaly', False)]
        anomalies.sort(key=lambda x: x.get('anomaly_score', 0), reverse=True)
        
        return anomalies[:limit]
    
    def get_savings_opportunities(self, card_name: str, set_code: Optional[str] = None,
                                min_savings: float = 1.0) -> List[Dict]:
        """
        Get cards with significant savings potential.
        
        Args:
            card_name: Name of the card
            set_code: Optional set code filter
            min_savings: Minimum savings amount to include
        
        Returns:
            List of savings opportunities
        """
        results = self.analyze_card_prices(card_name, set_code)
        
        # Filter by savings potential
        opportunities = [
            r for r in results 
            if r.get('is_anomaly', False) and r.get('savings_potential', 0) >= min_savings
        ]
        
        # Sort by savings potential
        opportunities.sort(key=lambda x: x.get('savings_potential', 0), reverse=True)
        
        return opportunities
    
    def analyze_market_trends(self, card_name: str, set_code: Optional[str] = None,
                            days: int = 30) -> Dict:
        """
        Analyze market trends for a card.
        
        Args:
            card_name: Name of the card
            set_code: Optional set code filter
            days: Number of days to analyze
        
        Returns:
            Dictionary with trend analysis
        """
        try:
            price_data = self.database_manager.get_historical_prices(card_name, set_code, days)
            
            if len(price_data) < 2:
                return {'error': 'Insufficient data for trend analysis'}
            
            df = pd.DataFrame(price_data)
            df['price_dollars'] = df['price_cents'] / 100.0
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate trend metrics
            prices = df['price_dollars'].values
            
            trend_analysis = {
                'card_name': card_name,
                'set_code': set_code,
                'analysis_period_days': days,
                'total_data_points': len(prices),
                'current_price': prices[-1],
                'historical_min': np.min(prices),
                'historical_max': np.max(prices),
                'historical_avg': np.mean(prices),
                'historical_std': np.std(prices),
                'price_volatility': np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0,
                'price_trend': 'increasing' if prices[-1] > prices[0] else 'decreasing',
                'price_change_pct': ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] > 0 else 0,
                'recent_anomalies': len([r for r in self.analyze_card_prices(card_name, set_code) 
                                       if r.get('is_anomaly', False)])
            }
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing market trends: {e}")
            return {'error': str(e)}
    
    def get_analysis_summary(self, results: List[Dict]) -> Dict:
        """
        Get summary statistics for analysis results.
        
        Args:
            results: List of analysis results
        
        Returns:
            Dictionary with summary statistics
        """
        if not results:
            return {'total_results': 0, 'anomalies_found': 0}
        
        total_results = len(results)
        anomalies = [r for r in results if r.get('is_anomaly', False)]
        anomaly_count = len(anomalies)
        
        if anomalies:
            avg_score = np.mean([r.get('anomaly_score', 0) for r in anomalies])
            avg_savings = np.mean([r.get('savings_potential', 0) for r in anomalies])
            total_savings = sum([r.get('savings_potential', 0) for r in anomalies])
            max_savings = max([r.get('savings_potential', 0) for r in anomalies])
        else:
            avg_score = 0
            avg_savings = 0
            total_savings = 0
            max_savings = 0
        
        return {
            'total_results': total_results,
            'anomalies_found': anomaly_count,
            'anomaly_rate': anomaly_count / total_results if total_results > 0 else 0,
            'average_anomaly_score': avg_score,
            'average_savings_potential': avg_savings,
            'total_savings_potential': total_savings,
            'max_savings_potential': max_savings,
            'method_used': self.anomaly_method,
            'analysis_parameters': {
                'minimum_data_points': self.minimum_data_points,
                'historical_days': self.historical_days,
                'confidence_level': self.confidence_level
            }
        }