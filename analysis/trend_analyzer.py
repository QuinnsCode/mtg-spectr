"""
Advanced trend analysis algorithms for MTG card price monitoring.

This module provides sophisticated algorithms for detecting and analyzing
price trends, including fast upward movements and market anomalies.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TrendType(Enum):
    """Types of price trends."""
    UPWARD = "upward"
    DOWNWARD = "downward"
    STABLE = "stable"
    VOLATILE = "volatile"

class TrendStrength(Enum):
    """Strength classification for trends."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    EXTREME = "extreme"

@dataclass
class TrendAnalysis:
    """Comprehensive trend analysis result."""
    card_name: str
    set_code: str
    collector_number: str
    is_foil: bool
    trend_type: TrendType
    trend_strength: TrendStrength
    percentage_change: float
    absolute_change: float
    duration_hours: float
    confidence_score: float
    price_start: float
    price_current: float
    price_peak: float
    price_low: float
    volatility: float
    acceleration: float  # Rate of change acceleration
    momentum_score: float
    data_points: int
    last_updated: datetime

class TrendAnalyzer:
    """Advanced trend analysis engine."""
    
    def __init__(self):
        """Initialize trend analyzer with default thresholds."""
        self.config = {
            'min_data_points': 3,
            'min_duration_hours': 6,
            'weak_threshold': 10.0,      # % change
            'moderate_threshold': 25.0,   # % change
            'strong_threshold': 50.0,     # % change
            'extreme_threshold': 100.0,   # % change
            'volatility_threshold': 0.15, # Coefficient of variation
            'momentum_window': 24,        # Hours for momentum calculation
            'acceleration_threshold': 5.0 # % per day acceleration
        }
    
    def analyze_trend(self, price_history: List[Dict]) -> Optional[TrendAnalysis]:
        """Perform comprehensive trend analysis on price history."""
        if len(price_history) < self.config['min_data_points']:
            return None
        
        # Extract price data and timestamps
        prices = [float(p['price_usd']) for p in price_history]
        timestamps = [datetime.fromisoformat(p['timestamp']) for p in price_history]
        
        # Basic metrics
        price_start = prices[0]
        price_current = prices[-1]
        price_peak = max(prices)
        price_low = min(prices)
        
        # Duration
        duration_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
        
        if duration_hours < self.config['min_duration_hours']:
            return None
        
        # Change calculations
        percentage_change = ((price_current - price_start) / price_start) * 100
        absolute_change = price_current - price_start
        
        # Volatility (coefficient of variation)
        mean_price = statistics.mean(prices)
        if mean_price > 0 and len(prices) > 1:
            volatility = statistics.stdev(prices) / mean_price
        else:
            volatility = 0
        
        # Trend type classification
        trend_type = self._classify_trend_type(percentage_change, volatility)
        
        # Trend strength
        trend_strength = self._classify_trend_strength(abs(percentage_change))
        
        # Acceleration analysis
        acceleration = self._calculate_acceleration(prices, timestamps)
        
        # Momentum score
        momentum_score = self._calculate_momentum(prices, timestamps)
        
        # Confidence score
        confidence_score = self._calculate_confidence(
            prices, timestamps, trend_type, volatility
        )
        
        # Extract card info from first price record
        first_record = price_history[0]
        
        return TrendAnalysis(
            card_name=first_record.get('card_name', ''),
            set_code=first_record.get('set_code', ''),
            collector_number=first_record.get('collector_number', ''),
            is_foil=first_record.get('is_foil', False),
            trend_type=trend_type,
            trend_strength=trend_strength,
            percentage_change=percentage_change,
            absolute_change=absolute_change,
            duration_hours=duration_hours,
            confidence_score=confidence_score,
            price_start=price_start,
            price_current=price_current,
            price_peak=price_peak,
            price_low=price_low,
            volatility=volatility,
            acceleration=acceleration,
            momentum_score=momentum_score,
            data_points=len(prices),
            last_updated=timestamps[-1]
        )
    
    def _classify_trend_type(self, percentage_change: float, volatility: float) -> TrendType:
        """Classify the type of trend based on change and volatility."""
        if volatility > self.config['volatility_threshold']:
            return TrendType.VOLATILE
        elif percentage_change > 5.0:
            return TrendType.UPWARD
        elif percentage_change < -5.0:
            return TrendType.DOWNWARD
        else:
            return TrendType.STABLE
    
    def _classify_trend_strength(self, abs_percentage_change: float) -> TrendStrength:
        """Classify the strength of the trend."""
        if abs_percentage_change >= self.config['extreme_threshold']:
            return TrendStrength.EXTREME
        elif abs_percentage_change >= self.config['strong_threshold']:
            return TrendStrength.STRONG
        elif abs_percentage_change >= self.config['moderate_threshold']:
            return TrendStrength.MODERATE
        else:
            return TrendStrength.WEAK
    
    def _calculate_acceleration(self, prices: List[float], timestamps: List[datetime]) -> float:
        """Calculate price acceleration (rate of change of rate of change)."""
        if len(prices) < 3:
            return 0.0
        
        try:
            # Simple acceleration calculation using differences
            if len(prices) < 3:
                return 0.0
            
            # Calculate velocity (price change per hour)
            velocities = []
            for i in range(1, len(prices)):
                time_diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600
                if time_diff > 0:
                    velocity = (prices[i] - prices[i-1]) / time_diff
                    velocities.append(velocity)
            
            if len(velocities) < 2:
                return 0.0
            
            # Calculate acceleration (velocity change)
            accelerations = []
            for i in range(1, len(velocities)):
                acceleration = velocities[i] - velocities[i-1]
                accelerations.append(acceleration)
            
            # Return average acceleration
            return statistics.mean(accelerations) if accelerations else 0.0
        except Exception as e:
            logger.error(f"Error calculating acceleration: {e}")
            return 0.0
    
    def _calculate_momentum(self, prices: List[float], timestamps: List[datetime]) -> float:
        """Calculate momentum score based on recent price movement."""
        if len(prices) < 2:
            return 0.0
        
        try:
            # Calculate momentum as recent rate of change
            recent_window = min(len(prices), 6)  # Last 6 data points
            recent_prices = prices[-recent_window:]
            
            if len(recent_prices) < 2:
                return 0.0
            
            # Simple momentum: (current - start) / time
            momentum = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
            
            # Normalize by starting price
            if recent_prices[0] > 0:
                momentum_score = (momentum / recent_prices[0]) * 100
            else:
                momentum_score = 0.0
            
            return float(momentum_score)
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return 0.0
    
    def _calculate_confidence(self, prices: List[float], timestamps: List[datetime], 
                            trend_type: TrendType, volatility: float) -> float:
        """Calculate confidence score for the trend analysis."""
        confidence = 0.0
        
        # Base confidence from data quality
        data_quality_score = min(len(prices) / 10.0, 1.0)  # More data = higher confidence
        confidence += data_quality_score * 30
        
        # Duration factor
        duration_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
        duration_score = min(duration_hours / 168.0, 1.0)  # 1 week = max duration score
        confidence += duration_score * 25
        
        # Trend consistency (lower volatility = higher confidence)
        consistency_score = max(0, 1.0 - (volatility / 0.5))
        confidence += consistency_score * 25
        
        # Trend clarity (stronger trends = higher confidence)
        if trend_type in [TrendType.UPWARD, TrendType.DOWNWARD]:
            clarity_score = 1.0
        elif trend_type == TrendType.STABLE:
            clarity_score = 0.5
        else:  # VOLATILE
            clarity_score = 0.2
        confidence += clarity_score * 20
        
        return min(confidence, 100.0)
    
    def identify_fast_movers(self, trends: List[TrendAnalysis], 
                           min_percentage: float = 20.0,
                           min_absolute: float = 0.50,
                           max_duration_hours: float = 72.0) -> List[TrendAnalysis]:
        """Identify cards with fast upward price movements."""
        fast_movers = []
        
        for trend in trends:
            # Must be upward trend
            if trend.trend_type != TrendType.UPWARD:
                continue
            
            # Check percentage and absolute thresholds
            meets_percentage = trend.percentage_change >= min_percentage
            meets_absolute = trend.absolute_change >= min_absolute
            
            # Check duration (fast = within specified hours)
            is_fast = trend.duration_hours <= max_duration_hours
            
            # Must meet at least one threshold and be fast
            if (meets_percentage or meets_absolute) and is_fast:
                fast_movers.append(trend)
        
        # Sort by combination of speed and magnitude
        fast_movers.sort(
            key=lambda t: (t.percentage_change / max(t.duration_hours, 1)) * t.momentum_score,
            reverse=True
        )
        
        return fast_movers
    
    def detect_breakout_patterns(self, trends: List[TrendAnalysis]) -> List[TrendAnalysis]:
        """Detect potential breakout patterns in price trends."""
        breakouts = []
        
        for trend in trends:
            # Look for strong upward trends with high momentum
            if (trend.trend_type == TrendType.UPWARD and 
                trend.trend_strength in [TrendStrength.STRONG, TrendStrength.EXTREME] and
                trend.momentum_score > 5.0 and
                trend.acceleration > 0):
                
                breakouts.append(trend)
        
        # Sort by momentum score
        breakouts.sort(key=lambda t: t.momentum_score, reverse=True)
        
        return breakouts
    
    def calculate_alert_score(self, trend: TrendAnalysis) -> float:
        """Calculate a composite alert score for prioritizing notifications."""
        score = 0.0
        
        # Percentage change weight (max 40 points)
        percentage_score = min(trend.percentage_change / 100.0, 1.0) * 40
        score += percentage_score
        
        # Momentum weight (max 25 points)
        momentum_score = min(abs(trend.momentum_score) / 20.0, 1.0) * 25
        score += momentum_score
        
        # Speed weight (faster = higher score, max 20 points)
        speed_score = max(0, (72 - trend.duration_hours) / 72.0) * 20
        score += speed_score
        
        # Confidence weight (max 15 points)
        confidence_score = (trend.confidence_score / 100.0) * 15
        score += confidence_score
        
        return min(score, 100.0)
    
    def update_config(self, **kwargs):
        """Update analyzer configuration."""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
                logger.info(f"Updated trend analyzer config: {key} = {value}")
            else:
                logger.warning(f"Unknown config key: {key}")