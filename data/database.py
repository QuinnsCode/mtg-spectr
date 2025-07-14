"""
Database operations for MTG card pricing data storage and retrieval.
Handles SQLite database operations with proper schema management and indexing.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import os
from config.input_validator import InputValidator
from .unified_api_client import CardPricing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for MTG card pricing data."""
    
    def __init__(self, db_path: str = "mtg_pricing.db"):
        """
        Initialize database manager with specified database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._persistent_conn = None
        
        # For in-memory databases, keep a persistent connection
        if db_path == ':memory:':
            self._persistent_conn = sqlite3.connect(db_path)
            self._persistent_conn.row_factory = sqlite3.Row
        
        try:
            self.initialize_database()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with proper cleanup.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        if self._persistent_conn:
            # Use persistent connection for in-memory databases
            try:
                yield self._persistent_conn
            except sqlite3.Error as e:
                logger.error(f"Database error: {e}")
                self._persistent_conn.rollback()
                raise
        else:
            # Use temporary connection for file databases
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
                yield conn
            except sqlite3.Error as e:
                logger.error(f"Database error: {e}")
                if conn:
                    conn.rollback()
                raise
            finally:
                if conn:
                    conn.close()
    
    def initialize_database(self):
        """Create database tables and indexes if they don't exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create card_prices table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS card_prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        card_name TEXT NOT NULL,
                        set_code TEXT,
                        printing_info TEXT,
                        price_cents INTEGER NOT NULL,
                        condition TEXT,
                        foil BOOLEAN DEFAULT FALSE,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        source TEXT DEFAULT 'JustTCG',
                        UNIQUE(card_name, set_code, printing_info, condition, foil, source)
                    )
                ''')
                
                # Create indexes for performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_card_name 
                    ON card_prices(card_name)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_set_code 
                    ON card_prices(set_code)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON card_prices(timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_card_set_condition 
                    ON card_prices(card_name, set_code, condition)
                ''')
                
                conn.commit()
                
                # Verify table was created
                cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="card_prices"')
                if cursor.fetchone():
                    logger.info("Database initialized successfully")
                else:
                    raise sqlite3.Error("Table creation failed")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def insert_price_data(self, card_data: Dict) -> bool:
        """
        Insert or update card pricing data.
        
        Args:
            card_data: Dictionary containing card pricing information
                Required keys: card_name, price_cents
                Optional keys: set_code, printing_info, condition, foil, source
        
        Returns:
            bool: True if insertion/update was successful
        """
        try:
            # Convert CardPricing object to dict if needed
            if hasattr(card_data, 'to_dict'):
                card_data = card_data.to_dict()
            
            # Basic validation - just check if it's a dictionary
            if not isinstance(card_data, dict):
                raise ValueError("Card data must be a dictionary")
            
            if 'card_name' not in card_data:
                raise ValueError("Card data must contain 'card_name'")
            
            validated_data = card_data
            
            # Validate specific fields
            card_name = InputValidator.validate_card_name(validated_data['card_name'])
            set_code = InputValidator.validate_set_code(validated_data.get('set_code', '')) if validated_data.get('set_code') else None
            
            # Validate price
            price_cents = validated_data.get('price_cents')
            if price_cents is None and 'price' in validated_data:
                price_cents = InputValidator.validate_numeric_input(validated_data['price'], min_value=0) * 100
            
            if price_cents is not None:
                price_cents = int(InputValidator.validate_numeric_input(price_cents, min_value=0))
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO card_prices 
                    (card_name, set_code, printing_info, price_cents, condition, foil, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    card_name,
                    set_code,
                    validated_data.get('printing_info'),
                    price_cents,
                    validated_data.get('condition', 'NM'),
                    bool(validated_data.get('foil', False)),
                    validated_data.get('source', 'JustTCG')
                ))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to insert price data: {e}")
            return False
    
    def insert_batch_price_data(self, card_data_list: List[Dict]) -> int:
        """
        Insert multiple card pricing records in a single transaction.
        
        Args:
            card_data_list: List of dictionaries containing card pricing information
        
        Returns:
            int: Number of records successfully inserted
        """
        inserted_count = 0
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for card_data in card_data_list:
                    try:
                        # Convert price to cents if it's in dollars
                        price_cents = card_data.get('price_cents')
                        if price_cents is None and 'price' in card_data:
                            price_cents = int(float(card_data['price']) * 100)
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO card_prices 
                            (card_name, set_code, printing_info, price_cents, condition, foil, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            card_data['card_name'],
                            card_data.get('set_code'),
                            card_data.get('printing_info'),
                            price_cents,
                            card_data.get('condition', 'NM'),
                            card_data.get('foil', False),
                            card_data.get('source', 'JustTCG')
                        ))
                        inserted_count += 1
                        
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Skipping invalid card data: {e}")
                        continue
                
                conn.commit()
                logger.info(f"Inserted {inserted_count} records successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to insert batch price data: {e}")
        
        return inserted_count
    
    def get_card_prices(self, card_name: str, set_code: Optional[str] = None, 
                       condition: Optional[str] = None) -> List[Dict]:
        """
        Retrieve card pricing data for a specific card.
        
        Args:
            card_name: Name of the card
            set_code: Optional set code filter
            condition: Optional condition filter
        
        Returns:
            List[Dict]: List of pricing records
        """
        try:
            # Validate inputs
            card_name = InputValidator.validate_card_name(card_name)
            if set_code:
                set_code = InputValidator.validate_set_code(set_code)
            if condition:
                condition = InputValidator.validate_search_term(condition)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM card_prices WHERE card_name = ?"
                params = [card_name]
                
                if set_code:
                    query += " AND set_code = ?"
                    params.append(set_code)
                
                if condition:
                    query += " AND condition = ?"
                    params.append(condition)
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve card prices: {e}")
            return []
    
    def get_historical_prices(self, card_name: str, set_code: Optional[str] = None, 
                             days: int = 30) -> List[Dict]:
        """
        Retrieve historical pricing data for analysis.
        
        Args:
            card_name: Name of the card
            set_code: Optional set code filter
            days: Number of days of history to retrieve
        
        Returns:
            List[Dict]: Historical pricing records
        """
        try:
            # Validate inputs
            card_name = InputValidator.validate_card_name(card_name)
            if set_code:
                set_code = InputValidator.validate_set_code(set_code)
            days = int(InputValidator.validate_numeric_input(days, min_value=1, max_value=365))
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT * FROM card_prices 
                    WHERE card_name = ? 
                    AND timestamp >= datetime('now', '-' || ? || ' days')
                '''
                
                params = [card_name, days]
                
                if set_code:
                    query += " AND set_code = ?"
                    params.append(set_code)
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve historical prices: {e}")
            return []
    
    def get_unique_card_names(self, search_term: str = "") -> List[str]:
        """
        Get list of unique card names, optionally filtered by search term.
        
        Args:
            search_term: Optional search term to filter card names
        
        Returns:
            List[str]: List of unique card names
        """
        try:
            # Validate search term if provided
            if search_term:
                search_term = InputValidator.validate_search_term(search_term)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if search_term:
                    cursor.execute('''
                        SELECT DISTINCT card_name FROM card_prices 
                        WHERE card_name LIKE ? 
                        ORDER BY card_name
                    ''', (f'%{search_term}%',))
                else:
                    cursor.execute('''
                        SELECT DISTINCT card_name FROM card_prices 
                        ORDER BY card_name
                    ''')
                
                rows = cursor.fetchall()
                return [row[0] for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve card names: {e}")
            return []
    
    def get_set_codes(self) -> List[str]:
        """
        Get list of unique set codes in the database.
        
        Returns:
            List[str]: List of unique set codes
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT set_code FROM card_prices 
                    WHERE set_code IS NOT NULL 
                    ORDER BY set_code
                ''')
                
                rows = cursor.fetchall()
                return [row[0] for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve set codes: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """
        Get database statistics for monitoring.
        
        Returns:
            Dict: Database statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute("SELECT COUNT(*) FROM card_prices")
                total_records = cursor.fetchone()[0]
                
                # Unique cards
                cursor.execute("SELECT COUNT(DISTINCT card_name) FROM card_prices")
                unique_cards = cursor.fetchone()[0]
                
                # Unique sets
                cursor.execute("SELECT COUNT(DISTINCT set_code) FROM card_prices")
                unique_sets = cursor.fetchone()[0]
                
                # Latest update
                cursor.execute("SELECT MAX(timestamp) FROM card_prices")
                latest_update = cursor.fetchone()[0]
                
                return {
                    'total_records': total_records,
                    'unique_cards': unique_cards,
                    'unique_sets': unique_sets,
                    'latest_update': latest_update
                }
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve database stats: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Clean up old pricing data to manage database size.
        
        Args:
            days_to_keep: Number of days of data to retain
        
        Returns:
            int: Number of records deleted
        """
        try:
            # Validate days parameter
            days_to_keep = int(InputValidator.validate_numeric_input(days_to_keep, min_value=1, max_value=3650))
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM card_prices 
                    WHERE timestamp < datetime('now', '-' || ? || ' days')
                ''', (days_to_keep,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Deleted {deleted_count} old records")
                return deleted_count
                
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0