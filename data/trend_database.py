"""
Database manager for MTG card price trend tracking.

This module handles the separate database for tracking price trends
and identifying fast upward movements in card prices.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class TrendDatabase:
    """Database manager for price trend tracking."""
    
    def __init__(self, db_path: str = None):
        """Initialize trend database connection."""
        if db_path is None:
            db_path = Path.home() / ".mtg_card_pricing" / "price_trends.db"
        
        if db_path == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _get_connection(self):
        """Get database connection."""
        db_path_str = self.db_path if isinstance(self.db_path, str) else str(self.db_path)
        return sqlite3.connect(db_path_str)
    
    def _init_database(self):
        """Initialize database schema."""
        try:
            conn = self._get_connection()
            # Create tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_name TEXT NOT NULL,
                set_code TEXT NOT NULL,
                collector_number TEXT,
                is_foil BOOLEAN NOT NULL DEFAULT 0,
                price_usd REAL NOT NULL,
                timestamp DATETIME NOT NULL,
                market_source TEXT DEFAULT 'scryfall',
                UNIQUE(card_name, set_code, collector_number, is_foil, timestamp)
            )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trend_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_name TEXT NOT NULL,
                set_code TEXT NOT NULL,
                collector_number TEXT,
                is_foil BOOLEAN NOT NULL DEFAULT 0,
                price_start REAL NOT NULL,
                price_current REAL NOT NULL,
                percentage_change REAL NOT NULL,
                absolute_change REAL NOT NULL,
                trend_duration_hours INTEGER NOT NULL,
                first_detected DATETIME NOT NULL,
                last_updated DATETIME NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                alert_threshold_type TEXT NOT NULL, -- 'percentage' or 'absolute'
                alert_threshold_value REAL NOT NULL
            )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_card ON price_snapshots(card_name, set_code, is_foil)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON price_snapshots(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_active ON trend_alerts(is_active)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_card ON trend_alerts(card_name, set_code, is_foil)")
            
            conn.commit()
            conn.close()
            logger.info("Trend database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    # Price snapshot recording methods removed - trend tracker now only analyzes existing data
    
    def get_last_price(self, card_name: str, set_code: str, 
                      collector_number: str, is_foil: bool = False) -> Optional[float]:
        """Get the most recent price for a card."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT price_usd FROM price_snapshots
                WHERE card_name = ? AND set_code = ? AND collector_number = ? AND is_foil = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (card_name, set_code, collector_number, is_foil))
            
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_price_history(self, card_name: str, set_code: str, 
                         collector_number: str, is_foil: bool = False,
                         hours_back: int = 168) -> List[Dict]:
        """Get price history for a card over specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT price_usd, timestamp, market_source
                FROM price_snapshots
                WHERE card_name = ? AND set_code = ? AND collector_number = ? 
                AND is_foil = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """, (card_name, set_code, collector_number, is_foil, cutoff_time))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def calculate_trend(self, card_name: str, set_code: str, 
                       collector_number: str, is_foil: bool = False) -> Optional[Dict]:
        """Calculate price trend for a specific card."""
        history = self.get_price_history(card_name, set_code, collector_number, is_foil)
        
        if len(history) < 2:
            return None
        
        first_price = history[0]['price_usd']
        last_price = history[-1]['price_usd']
        
        # Calculate percentage change
        percentage_change = ((last_price - first_price) / first_price) * 100
        absolute_change = last_price - first_price
        
        # Calculate time duration
        first_time = datetime.fromisoformat(history[0]['timestamp'])
        last_time = datetime.fromisoformat(history[-1]['timestamp'])
        duration_hours = (last_time - first_time).total_seconds() / 3600
        
        return {
            'card_name': card_name,
            'set_code': set_code,
            'collector_number': collector_number,
            'is_foil': is_foil,
            'price_start': first_price,
            'price_current': last_price,
            'percentage_change': percentage_change,
            'absolute_change': absolute_change,
            'duration_hours': duration_hours,
            'data_points': len(history)
        }
    
    def find_trending_cards(self, min_percentage_change: float = 20.0,
                           min_absolute_change: float = 0.50,
                           min_price_threshold: float = 0.50,
                           hours_back: int = 168,
                           max_cards: int = 1000) -> List[Dict]:
        """Find cards with significant upward price trends."""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT DISTINCT card_name, set_code, collector_number, is_foil
                FROM price_snapshots
                WHERE timestamp > ? AND price_usd >= ?
                ORDER BY price_usd DESC
                LIMIT ?
            """, (cutoff_time, min_price_threshold, max_cards))
            
            cards = cursor.fetchall()
        
        trending_cards = []
        processed_count = 0
        
        # Only show processing message if there are cards to process
        if len(cards) > 0:
            print(f"Processing {len(cards)} cards for trend analysis...")
            
            for i, card in enumerate(cards):
                # Progress indicator every 100 cards
                if i % 100 == 0 and i > 0:
                    print(f"  Processed {i}/{len(cards)} cards, found {len(trending_cards)} trending...")
                
                try:
                    trend = self.calculate_trend(
                        card['card_name'], card['set_code'], 
                        card['collector_number'], card['is_foil']
                    )
                    
                    if trend and (
                        trend['percentage_change'] >= min_percentage_change or
                        trend['absolute_change'] >= min_absolute_change
                    ):
                        trending_cards.append(trend)
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error calculating trend for {card['card_name']}: {e}")
                    continue
            
            print(f"  Completed: {processed_count}/{len(cards)} cards processed, {len(trending_cards)} trending cards found")
        else:
            print("No price data available for trend analysis")
        
        # Sort by percentage change descending
        trending_cards.sort(key=lambda x: x['percentage_change'], reverse=True)
        
        return trending_cards
    
    def create_trend_alert(self, trend_data: Dict, threshold_type: str, 
                          threshold_value: float) -> bool:
        """Create a new trend alert."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO trend_alerts
                    (card_name, set_code, collector_number, is_foil, price_start, 
                     price_current, percentage_change, absolute_change, 
                     trend_duration_hours, first_detected, last_updated, 
                     alert_threshold_type, alert_threshold_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trend_data['card_name'], trend_data['set_code'],
                    trend_data['collector_number'], trend_data['is_foil'],
                    trend_data['price_start'], trend_data['price_current'],
                    trend_data['percentage_change'], trend_data['absolute_change'],
                    trend_data['duration_hours'], datetime.now(), datetime.now(),
                    threshold_type, threshold_value
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating trend alert: {e}")
            return False
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all active trend alerts."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM trend_alerts
                WHERE is_active = 1
                ORDER BY percentage_change DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def dismiss_alert(self, alert_id: int) -> bool:
        """Dismiss/deactivate a trend alert."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE trend_alerts 
                    SET is_active = 0 
                    WHERE id = ?
                """, (alert_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error dismissing alert: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """Remove old price snapshots and inactive alerts."""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            with self._get_connection() as conn:
                # Remove old price snapshots
                cursor = conn.execute("""
                    DELETE FROM price_snapshots 
                    WHERE timestamp < ?
                """, (cutoff_time,))
                snapshots_deleted = cursor.rowcount
                
                # Remove old inactive alerts
                cursor = conn.execute("""
                    DELETE FROM trend_alerts 
                    WHERE is_active = 0 AND last_updated < ?
                """, (cutoff_time,))
                alerts_deleted = cursor.rowcount
                
                conn.commit()
                logger.info(f"Cleanup: removed {snapshots_deleted} old snapshots, {alerts_deleted} old alerts")
                return True
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return False
    
    def get_config_value(self, key: str, default: str = None) -> Optional[str]:
        """Get configuration value."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT value FROM monitoring_config 
                WHERE key = ?
            """, (key,))
            
            result = cursor.fetchone()
            return result[0] if result else default
    
    def set_config_value(self, key: str, value: str) -> bool:
        """Set configuration value."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO monitoring_config 
                    (key, value, updated_at)
                    VALUES (?, ?, ?)
                """, (key, value, datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting config value: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM price_snapshots")
            snapshot_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM trend_alerts WHERE is_active = 1")
            active_alerts = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT MIN(timestamp), MAX(timestamp) 
                FROM price_snapshots
            """)
            time_range = cursor.fetchone()
            
            return {
                'total_snapshots': snapshot_count,
                'active_alerts': active_alerts,
                'earliest_data': time_range[0],
                'latest_data': time_range[1],
                'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            }