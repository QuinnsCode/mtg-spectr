# Changelog

All notable changes to the MTG Card Pricing Analysis Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-07-12

### Added
- **🆕 Price Trend Tracker**: Complete automated price monitoring system
  - Background monitoring service with configurable 6-hour intervals
  - Advanced trend analysis algorithms (upward, downward, stable, volatile)
  - Fast mover detection for rapid price increases
  - Multi-channel alert system: system tray, desktop, and email notifications
  - Separate database for price trend data (price_trends.db)
  - Real-time statistics and monitoring dashboard
  - Configurable alert thresholds (percentage and absolute changes)
  - Data retention management with automatic cleanup
  - GUI integration with dedicated "Trend Tracker" tab (Ctrl+T)

- **📧 Email Notifications**: Full email alert system for price trends
  - Gmail SMTP integration with TLS encryption
  - Rate limiting (1 email per hour maximum)
  - Quiet hours support (10 PM - 8 AM default)
  - Encrypted credential storage for security
  - Priority-based alert content with detailed price information
  - Easy setup with `configure_email.py` script
  - Comprehensive testing with `test_email_alert.py`

- **Interactive Card Display**: Cards in results are now clickable and interactive
  - Click any card name to open TCGPlayer search
  - Hover over cards to see full-size card images
  - Visual feedback with blue text indicating clickable cards
  - Works in all result tables (search results, anomalies, set scanner)

### Changed
- **Expected Price Calculation**: More conservative approach for better anomaly detection
  - Now uses the **minimum price** from other printings instead of average
  - Helps identify cards priced below even the cheapest alternative
  - More reliable for arbitrage opportunities
  
- **Foil/Non-foil Price Separation**: Improved price comparison accuracy
  - Foil prices now only compared with other foil prices
  - Non-foil prices only compared with other non-foil prices
  - Prevents misleading anomalies from foil/non-foil price differences

- **Anomaly Detection Threshold**: More sensitive detection
  - Lowered from 0.8 to 0.7 for catching borderline cases
  - Better detection of cards like "Bane of Progress" (score: 0.722)

### Fixed
- Fixed issue where valuable cards weren't being flagged as anomalies
- Improved accuracy of cross-printing price comparisons
- Enhanced user experience with visual card previews
- **Performance Fix**: Resolved trend analysis hanging issue
  - Added card processing limits (1000 cards max per cycle)
  - Implemented progress indicators for long operations
  - Added error handling for individual card trend calculations
  - Optimized database queries with LIMIT clauses

### Technical Improvements
- Added complete trend tracking infrastructure:
  - `TrendDatabase` class for price snapshot storage and trend analysis
  - `TrendAnalyzer` with sophisticated algorithms for trend detection
  - `PriceMonitorService` for background monitoring with Qt integration
  - `AlertSystem` with multi-channel notifications and rate limiting
  - `TrendTrackerWidget` with comprehensive GUI for trend management
- Email notification system:
  - SMTP client integration with secure TLS encryption
  - Encrypted credential storage using cryptography library
  - Rate limiting and quiet hours management
  - Priority-based alert formatting with detailed price information
- Added `ClickableCardItem` and `ClickableCardTable` classes for interactive tables
- Implemented `CardImageManager` for efficient image caching
- Added TCGPlayer URL generation for direct market access
- Extended configuration system with `TrendTrackerSettings` dataclass
- Comprehensive test suite covering all trend tracking components

## [2.0.0] - 2025-07-09

### Added
- **Set Scanner Feature**: New comprehensive set scanning functionality
  - Full set analysis for pricing anomalies
  - Batch processing of entire MTG sets
  - Progress tracking with real-time updates
  - Categorized results (All, Undervalued, Overvalued)
  - JSON export functionality
  - Keyboard shortcut (Ctrl+S) for quick access

- **Scryfall API Integration**: Complete implementation with pagination
  - Automatic pagination handling for large result sets
  - Better rate limits (10 requests/second)
  - No API key required
  - Comprehensive card data including all variations

- **Enhanced Expected Price Calculation**
  - Sophisticated algorithm considering multiple factors
  - Base rarity prices: Common ($0.15), Uncommon ($0.40), Rare ($1.50), Mythic ($4.00)
  - Type multipliers: Legendary (2.5x), Planeswalker (3.0x), Creature (1.3x)
  - Set-based adjustments for Commander and Masters sets
  - Age-based value adjustments for older cards
  - Mana cost considerations

### Changed
- **Improved Set Filtering**
  - Expanded from 207 to support more set types
  - Now includes "arsenal", "premium", and "duel_deck" sets
  - Reduced minimum card count from 50 to 8 cards
  - Sets now sorted alphabetically instead of by release date

- **Updated Anomaly Detection Thresholds**
  - Price deviation threshold: 2.0 → 1.5 (more sensitive)
  - Confidence threshold: 0.7 → 0.6 (60% minimum)
  - Better detection of pricing anomalies

### Fixed
- **Pagination Issue**: Fixed set scanner only retrieving first 175 cards
  - Now properly handles multiple pages of results
  - Correctly scans sets with 400+ cards
  - Includes all card variations and extras

- **Data Format Compatibility**
  - Fixed "Input must be a dictionary" errors
  - Added `to_dict()` method to `CardPricing` class
  - Updated database manager to handle object conversions

- **Search Query Issues**
  - Improved query sanitization
  - Better handling of special characters
  - Fixed 404 "Resource not found" errors

- **Rate Limiting**
  - Implemented exponential backoff for retries
  - More conservative rate limits for JustTCG
  - Better error handling for 429 responses

### Technical Improvements
- Unified API client architecture supporting multiple providers
- Better separation of concerns between API clients
- Comprehensive test coverage for new features
- Improved error handling and logging throughout

## [1.5.0] - 2025-07-08

### Added
- Initial Scryfall API support (without pagination)
- Unified API client for provider abstraction
- Mock API clients for testing

### Changed
- Restructured API client architecture
- Improved error handling for API responses

### Fixed
- JustTCG API 429 rate limiting errors
- Search returning empty results
- Import path issues in GUI modules

## [1.0.0] - 2025-07-07

### Initial Release
- Basic MTG card price analysis functionality
- JustTCG API integration
- SQLite database for historical tracking
- PySide6 GUI with search and results display
- Three anomaly detection methods (IQR, Z-Score, Isolation Forest)
- Settings management and configuration
- Basic filtering and sorting capabilities