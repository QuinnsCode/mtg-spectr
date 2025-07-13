"""
Configuration management for the MTG Card Pricing Analysis Tool.
Handles API keys, application settings, and user preferences.
"""

import os
import json
import logging
import base64
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .input_validator import InputValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APISettings:
    """Configuration for API connections."""
    # Primary API - Scryfall (free, no key required)
    api_provider: str = "scryfall"  # "scryfall" or "justtcg"
    scryfall_base_url: str = "https://api.scryfall.com"
    
    # JustTCG API (backup option)
    justtcg_api_key: Optional[str] = None  # Format: 'tcg_your_api_key_here' from JustTCG dashboard
    justtcg_base_url: str = "https://api.justtcg.com/v1"
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    request_timeout: int = 30
    use_mock_api: bool = False


@dataclass
class DatabaseSettings:
    """Configuration for database operations."""
    database_path: str = "mtg_pricing.db"
    backup_enabled: bool = True
    backup_interval_days: int = 7
    cleanup_old_data_days: int = 90
    max_database_size_mb: int = 500


@dataclass
class AnalysisSettings:
    """Configuration for price analysis."""
    anomaly_detection_method: str = "iqr"  # iqr, zscore, isolation_forest
    iqr_threshold: float = 1.5
    zscore_threshold: float = 2.0
    isolation_forest_contamination: float = 0.1
    minimum_data_points: int = 5
    historical_days: int = 30
    confidence_level: float = 0.95


@dataclass
class GUISettings:
    """Configuration for GUI appearance and behavior."""
    theme: str = "light"  # light, dark, auto
    window_width: int = 1200
    window_height: int = 800
    font_family: str = "Arial"
    font_size: int = 10
    show_tooltips: bool = True
    auto_refresh_interval: int = 300  # seconds
    max_search_results: int = 100


@dataclass
class TrendTrackerSettings:
    """Configuration for price trend tracking."""
    # Monitoring settings
    monitoring_enabled: bool = False
    monitoring_interval_hours: int = 6
    max_cards_per_cycle: int = 1000
    
    # Alert thresholds
    min_price_threshold: float = 0.50
    percentage_alert_threshold: float = 20.0
    absolute_alert_threshold: float = 0.50
    
    # Data management
    auto_cleanup_days: int = 30
    separate_database: bool = True
    trend_database_path: str = "price_trends.db"
    
    # Alert system
    alert_system_enabled: bool = True
    system_tray_enabled: bool = True
    desktop_notifications_enabled: bool = True
    sound_enabled: bool = False
    email_enabled: bool = False
    email_address: str = ""
    
    # Alert behavior
    min_alert_interval_minutes: int = 15
    max_alerts_per_hour: int = 10
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 8     # 8 AM


@dataclass
class AppSettings:
    """Main application settings container."""
    api: APISettings
    database: DatabaseSettings
    analysis: AnalysisSettings
    gui: GUISettings
    trend_tracker: TrendTrackerSettings
    debug_mode: bool = False
    log_level: str = "INFO"
    version: str = "2.1.0"
    
    def __post_init__(self):
        """Initialize default settings after creation."""
        if not isinstance(self.api, APISettings):
            self.api = APISettings(**self.api) if isinstance(self.api, dict) else APISettings()
        if not isinstance(self.database, DatabaseSettings):
            self.database = DatabaseSettings(**self.database) if isinstance(self.database, dict) else DatabaseSettings()
        if not isinstance(self.analysis, AnalysisSettings):
            self.analysis = AnalysisSettings(**self.analysis) if isinstance(self.analysis, dict) else AnalysisSettings()
        if not isinstance(self.gui, GUISettings):
            self.gui = GUISettings(**self.gui) if isinstance(self.gui, dict) else GUISettings()
        if not isinstance(self.trend_tracker, TrendTrackerSettings):
            self.trend_tracker = TrendTrackerSettings(**self.trend_tracker) if isinstance(self.trend_tracker, dict) else TrendTrackerSettings()


class SettingsManager:
    """Manages application settings with persistence and validation."""
    
    def __init__(self, config_file: str = "settings.json"):
        """
        Initialize settings manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config_dir = Path.home() / ".mtg_card_pricing"
        self.config_path = self.config_dir / config_file
        self.key_file = self.config_dir / ".key"
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize encryption key
        self._encryption_key = self._get_or_create_key()
        
        # Load or create default settings
        self.settings = self._load_settings()
    
    def _get_or_create_key(self) -> Fernet:
        """
        Get or create encryption key for sensitive data.
        
        Returns:
            Fernet: Encryption key
        """
        try:
            if self.key_file.exists():
                with open(self.key_file, 'r') as f:
                    key_data = json.load(f)
                key = key_data['key'].encode()
                return Fernet(key)
            else:
                # Generate new key based on machine-specific data
                machine_id = self._get_machine_id()
                salt = os.urandom(16)
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
                
                # Store the key and salt
                key_data = {
                    'key': key.decode(),
                    'salt': base64.b64encode(salt).decode()
                }
                
                with open(self.key_file, 'w') as f:
                    json.dump(key_data, f)
                
                # Set restrictive permissions on key file
                os.chmod(self.key_file, 0o600)
                
                return Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption key: {e}")
            # Fallback to a basic key (not ideal but prevents total failure)
            return Fernet(Fernet.generate_key())
    
    def _get_machine_id(self) -> str:
        """
        Get machine-specific identifier for key generation.
        
        Returns:
            str: Machine identifier
        """
        try:
            # Try to get a stable machine identifier
            if hasattr(os, 'getuid'):
                # Unix-like systems
                return f"{os.getuid()}_{os.getgid()}_{os.uname().machine}"
            else:
                # Windows
                import platform
                return f"{platform.node()}_{platform.machine()}"
        except Exception:
            # Fallback to a basic identifier
            return "default_machine"
    
    def _encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            str: Encrypted data (base64 encoded)
        """
        try:
            if not data:
                return ""
            encrypted = self._encryption_key.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            return ""
    
    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data (base64 encoded)
            
        Returns:
            str: Decrypted data
        """
        try:
            if not encrypted_data:
                return ""
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = self._encryption_key.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return ""
    
    def _load_settings(self) -> AppSettings:
        """
        Load settings from file or create default settings.
        
        Returns:
            AppSettings: Application settings
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Decrypt API key if present
                api_data = data.get('api', {})
                if 'justtcg_api_key' in api_data and api_data['justtcg_api_key']:
                    api_data['justtcg_api_key'] = self._decrypt_sensitive_data(api_data['justtcg_api_key'])
                
                # Convert nested dictionaries to dataclasses
                return AppSettings(
                    api=APISettings(**api_data),
                    database=DatabaseSettings(**data.get('database', {})),
                    analysis=AnalysisSettings(**data.get('analysis', {})),
                    gui=GUISettings(**data.get('gui', {})),
                    trend_tracker=TrendTrackerSettings(**data.get('trend_tracker', {})),
                    debug_mode=data.get('debug_mode', False),
                    log_level=data.get('log_level', 'INFO'),
                    version=data.get('version', '2.1.0')
                )
                
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                logger.error(f"Failed to load settings: {e}")
                logger.info("Using default settings")
                return self._create_default_settings()
        else:
            logger.info("No settings file found, creating default settings")
            return self._create_default_settings()
    
    def _create_default_settings(self) -> AppSettings:
        """
        Create default application settings.
        
        Returns:
            AppSettings: Default settings
        """
        return AppSettings(
            api=APISettings(),
            database=DatabaseSettings(),
            analysis=AnalysisSettings(),
            gui=GUISettings(),
            trend_tracker=TrendTrackerSettings()
        )
    
    def save_settings(self) -> bool:
        """
        Save current settings to file.
        
        Returns:
            bool: True if save was successful
        """
        try:
            # Convert dataclasses to dictionaries
            settings_dict = {
                'api': asdict(self.settings.api),
                'database': asdict(self.settings.database),
                'analysis': asdict(self.settings.analysis),
                'gui': asdict(self.settings.gui),
                'trend_tracker': asdict(self.settings.trend_tracker),
                'debug_mode': self.settings.debug_mode,
                'log_level': self.settings.log_level,
                'version': self.settings.version
            }
            
            # Encrypt API key before saving
            if settings_dict['api']['justtcg_api_key']:
                settings_dict['api']['justtcg_api_key'] = self._encrypt_sensitive_data(
                    settings_dict['api']['justtcg_api_key']
                )
            
            with open(self.config_path, 'w') as f:
                json.dump(settings_dict, f, indent=2)
            
            logger.info(f"Settings saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a specific setting value.
        
        Args:
            section: Settings section (api, database, analysis, gui)
            key: Setting key
            default: Default value if not found
        
        Returns:
            Any: Setting value
        """
        try:
            section_obj = getattr(self.settings, section)
            return getattr(section_obj, key, default)
        except AttributeError:
            return default
    
    def set_setting(self, section: str, key: str, value: Any) -> bool:
        """
        Set a specific setting value.
        
        Args:
            section: Settings section (api, database, analysis, gui)
            key: Setting key
            value: New value
        
        Returns:
            bool: True if setting was updated
        """
        try:
            section_obj = getattr(self.settings, section)
            if hasattr(section_obj, key):
                setattr(section_obj, key, value)
                return True
            return False
        except AttributeError:
            return False
    
    def get_api_key(self) -> Optional[str]:
        """
        Get API key from settings or environment (primarily for JustTCG).
        
        Returns:
            Optional[str]: API key if available
        """
        # Check settings first
        if self.settings.api.justtcg_api_key:
            return self.settings.api.justtcg_api_key
        
        # Check environment variable
        env_key = os.getenv('JUSTTCG_API_KEY')
        if env_key:
            return env_key
        
        return None
    
    def set_api_key(self, api_key: str) -> bool:
        """
        Set JustTCG API key.
        
        Args:
            api_key: API key to set
        
        Returns:
            bool: True if successful
        """
        try:
            # Validate API key
            validated_key = InputValidator.validate_api_key(api_key)
            self.settings.api.justtcg_api_key = validated_key
            return self.save_settings()
        except ValueError as e:
            logger.error(f"Invalid API key: {e}")
            return False
    
    def _validate_path(self, path: str, base_dir: Optional[Path] = None) -> str:
        """
        Validate and sanitize file path to prevent directory traversal attacks.
        
        Args:
            path: Path to validate
            base_dir: Base directory to restrict path to (default: config_dir)
            
        Returns:
            str: Validated path
            
        Raises:
            ValueError: If path is invalid or potentially dangerous
        """
        if not path:
            raise ValueError("Path cannot be empty")
            
        # Remove null bytes and normalize
        path = path.replace('\x00', '')
        path = os.path.normpath(path)
        
        # Check for dangerous patterns
        dangerous_patterns = ['..', '~', '$', '|', ';', '&', '`', '>', '<', '*', '?', '[', ']']
        for pattern in dangerous_patterns:
            if pattern in path:
                raise ValueError(f"Path contains dangerous pattern: {pattern}")
        
        # Set base directory
        if base_dir is None:
            base_dir = self.config_dir
        
        # If absolute path, ensure it's within allowed directories
        if os.path.isabs(path):
            resolved_path = Path(path).resolve()
            # Only allow paths within user's home directory or temp directory
            allowed_bases = [Path.home(), Path.cwd(), Path('/tmp'), Path('/var/tmp')]
            if not any(str(resolved_path).startswith(str(base.resolve())) for base in allowed_bases):
                raise ValueError(f"Absolute path not allowed: {path}")
            return str(resolved_path)
        else:
            # Relative path - make it relative to base directory
            full_path = (base_dir / path).resolve()
            # Ensure the resolved path is still within the base directory
            if not str(full_path).startswith(str(base_dir.resolve())):
                raise ValueError(f"Path attempts to escape base directory: {path}")
            return str(full_path)
    
    def get_database_path(self) -> str:
        """
        Get full database path with validation.
        
        Returns:
            str: Full path to database file
            
        Raises:
            ValueError: If database path is invalid
        """
        db_path = self.settings.database.database_path
        
        try:
            return self._validate_path(db_path, self.config_dir)
        except ValueError as e:
            logger.error(f"Invalid database path: {e}")
            # Fall back to default path within config directory
            default_path = "mtg_pricing.db"
            return self._validate_path(default_path, self.config_dir)
    
    def validate_settings(self) -> Dict[str, List[str]]:
        """
        Validate current settings and return any errors.
        
        Returns:
            Dict[str, List[str]]: Validation errors by section
        """
        errors = {}
        
        # Validate API settings
        api_errors = []
        if self.settings.api.rate_limit_per_minute <= 0:
            api_errors.append("Rate limit per minute must be positive")
        if self.settings.api.rate_limit_per_hour <= 0:
            api_errors.append("Rate limit per hour must be positive")
        if self.settings.api.request_timeout <= 0:
            api_errors.append("Request timeout must be positive")
        if api_errors:
            errors['api'] = api_errors
        
        # Validate database settings
        db_errors = []
        if self.settings.database.cleanup_old_data_days <= 0:
            db_errors.append("Cleanup days must be positive")
        if self.settings.database.max_database_size_mb <= 0:
            db_errors.append("Max database size must be positive")
        if db_errors:
            errors['database'] = db_errors
        
        # Validate analysis settings
        analysis_errors = []
        if self.settings.analysis.iqr_threshold <= 0:
            analysis_errors.append("IQR threshold must be positive")
        if self.settings.analysis.zscore_threshold <= 0:
            analysis_errors.append("Z-score threshold must be positive")
        if not 0 < self.settings.analysis.isolation_forest_contamination < 1:
            analysis_errors.append("Isolation forest contamination must be between 0 and 1")
        if self.settings.analysis.minimum_data_points <= 0:
            analysis_errors.append("Minimum data points must be positive")
        if not 0 < self.settings.analysis.confidence_level < 1:
            analysis_errors.append("Confidence level must be between 0 and 1")
        if analysis_errors:
            errors['analysis'] = analysis_errors
        
        # Validate GUI settings
        gui_errors = []
        if self.settings.gui.window_width <= 0:
            gui_errors.append("Window width must be positive")
        if self.settings.gui.window_height <= 0:
            gui_errors.append("Window height must be positive")
        if self.settings.gui.font_size <= 0:
            gui_errors.append("Font size must be positive")
        if self.settings.gui.auto_refresh_interval <= 0:
            gui_errors.append("Auto refresh interval must be positive")
        if gui_errors:
            errors['gui'] = gui_errors
        
        return errors
    
    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to default values.
        
        Returns:
            bool: True if reset was successful
        """
        try:
            self.settings = self._create_default_settings()
            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False
    
    def export_settings(self, export_path: str) -> bool:
        """
        Export settings to a file.
        
        Args:
            export_path: Path to export file
        
        Returns:
            bool: True if export was successful
        """
        try:
            # Validate export path
            validated_path = self._validate_path(export_path, Path.cwd())
            settings_dict = {
                'api': asdict(self.settings.api),
                'database': asdict(self.settings.database),
                'analysis': asdict(self.settings.analysis),
                'gui': asdict(self.settings.gui),
                'debug_mode': self.settings.debug_mode,
                'log_level': self.settings.log_level,
                'version': self.settings.version
            }
            
            # Note: Export will contain unencrypted data for portability
            # Users should secure exported files appropriately
            
            with open(validated_path, 'w') as f:
                json.dump(settings_dict, f, indent=2)
            
            logger.info(f"Settings exported to {validated_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return False
    
    def import_settings(self, import_path: str) -> bool:
        """
        Import settings from a file.
        
        Args:
            import_path: Path to import file
        
        Returns:
            bool: True if import was successful
        """
        try:
            # Validate import path
            validated_path = self._validate_path(import_path, Path.cwd())
            
            with open(validated_path, 'r') as f:
                data = json.load(f)
            
            # Create new settings from imported data
            new_settings = AppSettings(
                api=APISettings(**data.get('api', {})),
                database=DatabaseSettings(**data.get('database', {})),
                analysis=AnalysisSettings(**data.get('analysis', {})),
                gui=GUISettings(**data.get('gui', {})),
                debug_mode=data.get('debug_mode', False),
                log_level=data.get('log_level', 'INFO'),
                version=data.get('version', '1.0.0')
            )
            
            # Validate imported settings
            errors = self.validate_settings()
            if errors:
                logger.error(f"Imported settings validation failed: {errors}")
                return False
            
            self.settings = new_settings
            return self.save_settings()
            
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False


# Global settings instance
_settings_manager = None


def get_settings() -> SettingsManager:
    """
    Get global settings manager instance.
    
    Returns:
        SettingsManager: Global settings manager
    """
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def reload_settings():
    """Reload settings from file."""
    global _settings_manager
    _settings_manager = SettingsManager()