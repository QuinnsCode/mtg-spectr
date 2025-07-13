"""
Input validation and sanitization utilities for security.
Provides comprehensive validation for all user inputs to prevent injection attacks.
"""

import re
import html
import logging
from typing import Optional, Union, List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InputValidator:
    """Comprehensive input validation and sanitization utilities."""
    
    # Maximum lengths for different input types
    MAX_CARD_NAME_LENGTH = 200
    MAX_SET_CODE_LENGTH = 20
    MAX_SEARCH_TERM_LENGTH = 500
    MAX_PATH_LENGTH = 1000
    
    # Allowed characters for different input types
    CARD_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\'\"\,\.\(\)\!\?\:]+$')
    SET_CODE_PATTERN = re.compile(r'^[a-zA-Z0-9\-\_]+$')
    NUMERIC_PATTERN = re.compile(r'^[0-9]+(\.[0-9]+)?$')
    
    # SQL injection patterns to detect
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
        r'(--|\#|\/\*|\*\/)',
        r'(\b(OR|AND)\b\s+[\w\s]*\s*(=|<|>|LIKE))',
        r'(\'|\"|;|\||&|\$|\`)',
        r'(\bxp_\w+)',
        r'(\bsp_\w+)',
    ]
    
    # XSS patterns to detect
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'javascript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<applet[^>]*>',
    ]
    
    @staticmethod
    def validate_card_name(card_name: str) -> str:
        """
        Validate and sanitize card name input.
        
        Args:
            card_name: Card name to validate
            
        Returns:
            str: Sanitized card name
            
        Raises:
            ValueError: If card name is invalid
        """
        if not card_name:
            raise ValueError("Card name cannot be empty")
        
        # Convert to string and strip whitespace
        card_name = str(card_name).strip()
        
        # Check length
        if len(card_name) > InputValidator.MAX_CARD_NAME_LENGTH:
            raise ValueError(f"Card name too long (max {InputValidator.MAX_CARD_NAME_LENGTH} characters)")
        
        # Check for null bytes
        if '\x00' in card_name:
            raise ValueError("Card name contains null bytes")
        
        # Check for SQL injection patterns
        InputValidator._check_sql_injection(card_name)
        
        # Check for XSS patterns
        InputValidator._check_xss(card_name)
        
        # Validate allowed characters
        if not InputValidator.CARD_NAME_PATTERN.match(card_name):
            raise ValueError("Card name contains invalid characters")
        
        # HTML escape for additional safety
        return html.escape(card_name, quote=True)
    
    @staticmethod
    def validate_set_code(set_code: str) -> str:
        """
        Validate and sanitize set code input.
        
        Args:
            set_code: Set code to validate
            
        Returns:
            str: Sanitized set code
            
        Raises:
            ValueError: If set code is invalid
        """
        if not set_code:
            return ""
        
        # Convert to string and strip whitespace
        set_code = str(set_code).strip().upper()
        
        # Check length
        if len(set_code) > InputValidator.MAX_SET_CODE_LENGTH:
            raise ValueError(f"Set code too long (max {InputValidator.MAX_SET_CODE_LENGTH} characters)")
        
        # Check for null bytes
        if '\x00' in set_code:
            raise ValueError("Set code contains null bytes")
        
        # Check for SQL injection patterns
        InputValidator._check_sql_injection(set_code)
        
        # Validate allowed characters
        if not InputValidator.SET_CODE_PATTERN.match(set_code):
            raise ValueError("Set code contains invalid characters")
        
        return set_code
    
    @staticmethod
    def validate_search_term(search_term: str) -> str:
        """
        Validate and sanitize search term input.
        
        Args:
            search_term: Search term to validate
            
        Returns:
            str: Sanitized search term
            
        Raises:
            ValueError: If search term is invalid
        """
        if not search_term:
            return ""
        
        # Convert to string and strip whitespace
        search_term = str(search_term).strip()
        
        # Check length
        if len(search_term) > InputValidator.MAX_SEARCH_TERM_LENGTH:
            raise ValueError(f"Search term too long (max {InputValidator.MAX_SEARCH_TERM_LENGTH} characters)")
        
        # Check for null bytes
        if '\x00' in search_term:
            raise ValueError("Search term contains null bytes")
        
        # Check for SQL injection patterns
        InputValidator._check_sql_injection(search_term)
        
        # Check for XSS patterns
        InputValidator._check_xss(search_term)
        
        # HTML escape for additional safety
        return html.escape(search_term, quote=True)
    
    @staticmethod
    def validate_numeric_input(value: Union[str, int, float], 
                             min_value: Optional[float] = None,
                             max_value: Optional[float] = None,
                             allow_negative: bool = False) -> float:
        """
        Validate numeric input.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_negative: Whether negative values are allowed
            
        Returns:
            float: Validated numeric value
            
        Raises:
            ValueError: If value is invalid
        """
        if value is None:
            raise ValueError("Value cannot be None")
        
        # Convert to string for pattern matching
        str_value = str(value).strip()
        
        # Check for null bytes
        if '\x00' in str_value:
            raise ValueError("Value contains null bytes")
        
        # Check for SQL injection patterns
        InputValidator._check_sql_injection(str_value)
        
        # Validate numeric pattern
        if not InputValidator.NUMERIC_PATTERN.match(str_value):
            raise ValueError("Value is not a valid number")
        
        # Convert to float
        try:
            numeric_value = float(str_value)
        except ValueError:
            raise ValueError("Value is not a valid number")
        
        # Check for negative values
        if not allow_negative and numeric_value < 0:
            raise ValueError("Negative values not allowed")
        
        # Check range
        if min_value is not None and numeric_value < min_value:
            raise ValueError(f"Value must be at least {min_value}")
        
        if max_value is not None and numeric_value > max_value:
            raise ValueError(f"Value must be at most {max_value}")
        
        return numeric_value
    
    @staticmethod
    def validate_path(path: str, base_dir: Optional[Path] = None) -> str:
        """
        Validate file path (reused from settings.py).
        
        Args:
            path: Path to validate
            base_dir: Base directory to restrict path to
            
        Returns:
            str: Validated path
            
        Raises:
            ValueError: If path is invalid
        """
        if not path:
            raise ValueError("Path cannot be empty")
        
        # Convert to string and strip whitespace
        path = str(path).strip()
        
        # Check length
        if len(path) > InputValidator.MAX_PATH_LENGTH:
            raise ValueError(f"Path too long (max {InputValidator.MAX_PATH_LENGTH} characters)")
        
        # Remove null bytes and normalize
        path = path.replace('\x00', '')
        path = path.replace('\\', '/')  # Normalize separators
        
        # Check for dangerous patterns
        dangerous_patterns = ['..', '~', '$', '|', ';', '&', '`', '>', '<', '*', '?', '[', ']']
        for pattern in dangerous_patterns:
            if pattern in path:
                raise ValueError(f"Path contains dangerous pattern: {pattern}")
        
        # Check for SQL injection patterns
        InputValidator._check_sql_injection(path)
        
        return path
    
    @staticmethod
    def validate_multiple_card_names(card_names: str) -> List[str]:
        """
        Validate multiple card names input.
        
        Args:
            card_names: String containing multiple card names
            
        Returns:
            List[str]: List of validated card names
            
        Raises:
            ValueError: If any card name is invalid
        """
        if not card_names:
            return []
        
        # Parse card names (comma-separated or newline-separated)
        names = [name.strip() for name in card_names.replace('\n', ',').split(',')]
        names = [name for name in names if name]
        
        # Validate each name
        validated_names = []
        for name in names:
            try:
                validated_name = InputValidator.validate_card_name(name)
                validated_names.append(validated_name)
            except ValueError as e:
                logger.warning(f"Invalid card name '{name}': {e}")
                # Skip invalid names but continue processing others
                continue
        
        return validated_names
    
    @staticmethod
    def validate_api_key(api_key: str) -> str:
        """
        Validate API key input.
        
        Args:
            api_key: API key to validate
            
        Returns:
            str: Validated API key
            
        Raises:
            ValueError: If API key is invalid
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        # Convert to string and strip whitespace
        api_key = str(api_key).strip()
        
        # Check length (reasonable bounds for API keys)
        if len(api_key) < 10 or len(api_key) > 200:
            raise ValueError("API key length is invalid")
        
        # Check for null bytes
        if '\x00' in api_key:
            raise ValueError("API key contains null bytes")
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '|', ';', '`', '$']
        for char in dangerous_chars:
            if char in api_key:
                raise ValueError(f"API key contains dangerous character: {char}")
        
        # API keys should typically be alphanumeric with some special chars
        if not re.match(r'^[a-zA-Z0-9\-\_\.\+\/\=]+$', api_key):
            raise ValueError("API key contains invalid characters")
        
        return api_key
    
    @staticmethod
    def sanitize_output(text: str) -> str:
        """
        Sanitize text for safe output display.
        
        Args:
            text: Text to sanitize
            
        Returns:
            str: Sanitized text
        """
        if not text:
            return ""
        
        # Convert to string
        text = str(text)
        
        # HTML escape
        text = html.escape(text, quote=True)
        
        # Remove any remaining dangerous patterns
        for pattern in InputValidator.XSS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    @staticmethod
    def _check_sql_injection(text: str) -> None:
        """
        Check for SQL injection patterns.
        
        Args:
            text: Text to check
            
        Raises:
            ValueError: If SQL injection patterns are detected
        """
        text_lower = text.lower()
        
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise ValueError("Input contains potential SQL injection pattern")
    
    @staticmethod
    def _check_xss(text: str) -> None:
        """
        Check for XSS patterns.
        
        Args:
            text: Text to check
            
        Raises:
            ValueError: If XSS patterns are detected
        """
        text_lower = text.lower()
        
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise ValueError("Input contains potential XSS pattern")
    
    @staticmethod
    def validate_dict_input(data: Dict[str, Any], 
                           required_keys: List[str] = None,
                           max_keys: int = 50) -> Dict[str, Any]:
        """
        Validate dictionary input.
        
        Args:
            data: Dictionary to validate
            required_keys: List of required keys
            max_keys: Maximum number of keys allowed
            
        Returns:
            Dict[str, Any]: Validated dictionary
            
        Raises:
            ValueError: If dictionary is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
        
        # Check number of keys
        if len(data) > max_keys:
            raise ValueError(f"Dictionary has too many keys (max {max_keys})")
        
        # Check required keys
        if required_keys:
            missing_keys = set(required_keys) - set(data.keys())
            if missing_keys:
                raise ValueError(f"Missing required keys: {missing_keys}")
        
        # Validate keys and values
        validated_data = {}
        for key, value in data.items():
            # Validate key
            if not isinstance(key, str):
                raise ValueError("Dictionary keys must be strings")
            
            validated_key = InputValidator.validate_search_term(key)
            
            # Validate value based on type
            if isinstance(value, str):
                validated_value = InputValidator.validate_search_term(value)
            elif isinstance(value, (int, float)):
                validated_value = InputValidator.validate_numeric_input(value)
            elif isinstance(value, bool):
                validated_value = bool(value)
            elif value is None:
                validated_value = None
            else:
                # For other types, convert to string and validate
                validated_value = InputValidator.validate_search_term(str(value))
            
            validated_data[validated_key] = validated_value
        
        return validated_data