"""
Background price monitoring service for MTG card trend tracking.

This service runs in the background to continuously monitor card prices
and detect trending movements across the entire MTG collection.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
try:
    from PySide6.QtCore import QThread, QTimer, Signal, QObject
except ImportError:
    # Fallback for testing without GUI
    class QObject:
        pass
    def Signal(*args):
        def decorator(func):
            return func
        return decorator
    class QTimer:
        def __init__(self):
            pass
        def start(self, ms):
            pass
        def stop(self):
            pass
        timeout = Signal()
import requests

from data.trend_database import TrendDatabase
from data.scryfall_client import create_scryfall_client
from analysis.trend_analyzer import TrendAnalyzer, TrendAnalysis, TrendType

logger = logging.getLogger(__name__)

@dataclass
class MonitoringStats:
    """Statistics for analysis session."""
    trends_detected: int = 0
    alerts_generated: int = 0
    errors_encountered: int = 0
    last_run_time: Optional[datetime] = None
    next_run_time: Optional[datetime] = None

class PriceMonitorService(QObject):
    """Background service for monitoring MTG card prices."""
    
    # Signals for GUI integration
    monitoring_started = Signal()
    monitoring_stopped = Signal()
    progress_updated = Signal(str, int, int)  # status, current, total
    trend_detected = Signal(dict)  # trend data
    alert_generated = Signal(dict)  # alert data
    error_occurred = Signal(str)  # error message
    stats_updated = Signal(dict)  # monitoring stats
    
    def __init__(self):
        """Initialize price monitoring service."""
        super().__init__()
        
        self.trend_db = TrendDatabase()
        self.analyzer = TrendAnalyzer()
        self.scryfall_client = create_scryfall_client()
        
        self.is_monitoring = False
        self.monitor_timer = QTimer()
        
        # Only connect signal if it exists (GUI mode)
        if hasattr(self.monitor_timer.timeout, 'connect'):
            self.monitor_timer.timeout.connect(self._run_monitoring_cycle)
        
        self.stats = MonitoringStats()
        
        # Load configuration
        self.config = {
            'monitoring_interval_hours': 6,
            'min_price_threshold': 0.50,  # Keep at $0.50 - track all cards above 50 cents
            'percentage_alert_threshold': 50.0,  # Increased to 50% - only extreme percentage moves
            'max_cards_per_cycle': 1000,
            'sets_to_monitor': 'all',  # or list of set codes
            'auto_cleanup_days': 30,
            'rate_limit_delay': 0.05  # seconds between API calls (20 requests/second, well under Scryfall's 10/sec limit)
        }
        
        # Load saved configuration
        self._load_config()
    
    def start_monitoring(self):
        """Start the background monitoring service."""
        if self.is_monitoring:
            logger.warning("Monitoring service is already running")
            return
        
        self.is_monitoring = True
        interval_ms = int(self.config['monitoring_interval_hours'] * 3600 * 1000)
        self.monitor_timer.start(interval_ms)
        
        # Terminal notification
        print(f"\n🚀 TREND TRACKER: Monitoring service STARTED")
        print(f"   Interval: Every {self.config['monitoring_interval_hours']} hours")
        print(f"   Max cards per cycle: {self.config['max_cards_per_cycle']:,}")
        print(f"   Language filter: English cards only")
        
        # Run initial cycle immediately
        self._run_monitoring_cycle()
        
        self.monitoring_started.emit()
        logger.info(f"Price monitoring started with {self.config['monitoring_interval_hours']}h interval")
    
    def stop_monitoring(self):
        """Stop the background monitoring service."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.monitor_timer.stop()
        
        # Terminal notification
        print(f"\n⏹️  TREND TRACKER: Monitoring service STOPPED")
        
        self.monitoring_stopped.emit()
        logger.info("Price monitoring stopped")
    
    def _run_monitoring_cycle(self):
        """Execute a complete analysis cycle - no data collection."""
        try:
            self.stats.last_run_time = datetime.now()
            self.stats.next_run_time = datetime.now() + timedelta(hours=self.config['monitoring_interval_hours'])
            
            # Terminal status messages
            print("\n" + "="*80)
            print(f"TREND TRACKER: Starting analysis cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*80)
            print("📊 Analyzing existing price data for trends (no data collection)")
            
            logger.info("Starting trend analysis cycle")
            
            start_time = time.time()
            
            # Analyze trends and generate alerts
            print("\nAnalyzing price trends and generating alerts...")
            self._analyze_trends_and_alerts()
            
            # Cleanup old data
            self._cleanup_old_data()
            
            # Update statistics
            self._update_stats()
            
            # Calculate and log performance summary
            total_duration = time.time() - start_time
            
            # Terminal completion message
            print("\n" + "="*80)
            print(f"TREND TRACKER: Analysis cycle COMPLETED at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*80)
            print(f"Summary:")
            print(f"  • Existing data analyzed")
            print(f"  • Trends detected: {self.stats.trends_detected:,}")
            print(f"  • Alerts generated: {self.stats.alerts_generated:,}")
            print(f"  • Duration: {total_duration:.1f} seconds")
            print(f"\nNext analysis cycle scheduled for: {self.stats.next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*80 + "\n")
            
            logger.info(f"Analysis cycle completed:")
            logger.info(f"  - Trends detected: {self.stats.trends_detected:,}")
            logger.info(f"  - Alerts generated: {self.stats.alerts_generated:,}")
            logger.info(f"  - Duration: {total_duration:.1f} seconds")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            self.error_occurred.emit(str(e))
            self.stats.errors_encountered += 1
            
            # Terminal error message
            print("\n" + "="*80)
            print(f"❌ TREND TRACKER: Error during monitoring cycle")
            print(f"   Error: {str(e)}")
            print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*80 + "\n")
    
    # Data collection methods removed - trend tracker now only analyzes existing data
    
    def _analyze_trends_and_alerts(self):
        """Analyze recorded prices for trends and generate alerts."""
        try:
            # Get time window configuration (default to 24 hours for volatility)
            trend_hours = int(self.trend_db.get_config_value('trend_analysis_hours') or 24)
            
            # Get absolute threshold from database or use high default to focus on percentage
            absolute_threshold = float(self.trend_db.get_config_value('absolute_alert_threshold') or 100.0)
            
            # Find trending cards with limits to prevent hanging
            trending_cards = self.trend_db.find_trending_cards(
                min_percentage_change=self.config['percentage_alert_threshold'],
                min_absolute_change=absolute_threshold,  # Use configured absolute threshold
                min_price_threshold=self.config['min_price_threshold'],
                hours_back=trend_hours,  # Use configurable time window for volatility
                max_cards=self.config['max_cards_per_cycle']  # Limit processing to prevent hanging
            )
            
            self.stats.trends_detected = len(trending_cards)
            
            for trend_data in trending_cards:
                # Create detailed trend analysis
                price_history = self.trend_db.get_price_history(
                    trend_data['card_name'], trend_data['set_code'],
                    trend_data['collector_number'], trend_data['is_foil']
                )
                
                # Add required fields for trend analysis
                for record in price_history:
                    record['card_name'] = trend_data['card_name']
                    record['set_code'] = trend_data['set_code']
                    record['collector_number'] = trend_data['collector_number']
                    record['is_foil'] = trend_data['is_foil']
                
                trend_analysis = self.analyzer.analyze_trend(price_history)
                
                if trend_analysis and trend_analysis.trend_type == TrendType.UPWARD:
                    # Generate alert
                    alert_score = self.analyzer.calculate_alert_score(trend_analysis)
                    
                    if alert_score >= 50.0:  # Threshold for generating alerts
                        self._generate_alert(trend_analysis, alert_score)
                    
                    # Emit trend detected signal
                    self.trend_detected.emit({
                        'card_name': trend_analysis.card_name,
                        'set_code': trend_analysis.set_code,
                        'percentage_change': trend_analysis.percentage_change,
                        'absolute_change': trend_analysis.absolute_change,
                        'price_current': trend_analysis.price_current,
                        'alert_score': alert_score
                    })
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            self.stats.errors_encountered += 1
    
    def _generate_alert(self, trend_analysis: TrendAnalysis, alert_score: float):
        """Generate and store a trend alert."""
        try:
            # Only use percentage threshold since absolute threshold is removed
            threshold_type = 'percentage'
            threshold_value = self.config['percentage_alert_threshold']
            
            # Create trend data dict for database
            trend_data = {
                'card_name': trend_analysis.card_name,
                'set_code': trend_analysis.set_code,
                'collector_number': trend_analysis.collector_number,
                'is_foil': trend_analysis.is_foil,
                'price_start': trend_analysis.price_start,
                'price_current': trend_analysis.price_current,
                'percentage_change': trend_analysis.percentage_change,
                'absolute_change': trend_analysis.absolute_change,
                'duration_hours': trend_analysis.duration_hours
            }
            
            # Store alert in database
            self.trend_db.create_trend_alert(trend_data, threshold_type, threshold_value)
            
            # Emit alert signal for GUI
            self.alert_generated.emit({
                'card_name': trend_analysis.card_name,
                'set_code': trend_analysis.set_code,
                'is_foil': trend_analysis.is_foil,
                'percentage_change': trend_analysis.percentage_change,
                'absolute_change': trend_analysis.absolute_change,
                'price_current': trend_analysis.price_current,
                'alert_score': alert_score,
                'trend_strength': trend_analysis.trend_strength.value,
                'momentum_score': trend_analysis.momentum_score
            })
            
            self.stats.alerts_generated += 1
            logger.info(f"Generated alert for {trend_analysis.card_name} ({trend_analysis.set_code})")
            
        except Exception as e:
            logger.error(f"Error generating alert: {e}")
            self.stats.errors_encountered += 1
    
    def _cleanup_old_data(self):
        """Clean up old price data and inactive alerts."""
        try:
            self.trend_db.cleanup_old_data(self.config['auto_cleanup_days'])
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _update_stats(self):
        """Update and emit monitoring statistics."""
        stats_dict = {
            'trends_detected': self.stats.trends_detected,
            'alerts_generated': self.stats.alerts_generated,
            'errors_encountered': self.stats.errors_encountered,
            'last_run_time': self.stats.last_run_time.isoformat() if self.stats.last_run_time else None,
            'next_run_time': self.stats.next_run_time.isoformat() if self.stats.next_run_time else None,
            'is_monitoring': self.is_monitoring
        }
        
        self.stats_updated.emit(stats_dict)
    
    def _load_config(self):
        """Load configuration from database."""
        try:
            # Load saved configuration values
            for key in self.config.keys():
                saved_value = self.trend_db.get_config_value(key)
                if saved_value:
                    # Convert string values back to appropriate types
                    if key in ['monitoring_interval_hours', 'max_cards_per_cycle', 'auto_cleanup_days']:
                        self.config[key] = int(saved_value)
                    elif key in ['min_price_threshold', 'percentage_alert_threshold', 
                                'rate_limit_delay']:
                        self.config[key] = float(saved_value)
                    elif key == 'sets_to_monitor' and saved_value != 'all':
                        self.config[key] = saved_value.split(',')
                    else:
                        self.config[key] = saved_value
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def update_config(self, **kwargs):
        """Update monitoring configuration."""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
                
                # Save to database
                if isinstance(value, list):
                    save_value = ','.join(value)
                else:
                    save_value = str(value)
                    
                self.trend_db.set_config_value(key, save_value)
                logger.info(f"Updated monitoring config: {key} = {value}")
                
                # Restart timer if interval changed
                if key == 'monitoring_interval_hours' and self.is_monitoring:
                    self.stop_monitoring()
                    self.start_monitoring()
    
    def get_monitoring_stats(self) -> Dict:
        """Get current monitoring statistics."""
        db_stats = self.trend_db.get_database_stats()
        
        return {
            **db_stats,
            'service_stats': {
                'trends_detected': self.stats.trends_detected,
                'alerts_generated': self.stats.alerts_generated,
                'errors_encountered': self.stats.errors_encountered,
                'is_monitoring': self.is_monitoring,
                'last_run': self.stats.last_run_time.isoformat() if self.stats.last_run_time else None,
                'next_run': self.stats.next_run_time.isoformat() if self.stats.next_run_time else None
            },
            'config': self.config.copy()
        }
    
    def force_monitoring_cycle(self):
        """Force an immediate monitoring cycle (for testing/manual refresh)."""
        if not self.is_monitoring:
            logger.warning("Cannot force cycle: monitoring service not running")
            return
        
        logger.info("Forcing immediate monitoring cycle")
        self._run_monitoring_cycle()