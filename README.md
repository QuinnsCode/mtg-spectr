# MTG Card Pricing Analysis Tool

A comprehensive desktop application for analyzing Magic: The Gathering card prices and identifying pricing anomalies using statistical analysis.

## Features

### Core Functionality
- **Multi-API Support**: Seamlessly switch between Scryfall (free) and JustTCG APIs
- **Real-time Price Data**: Fetches current pricing with automatic pagination support
- **Historical Tracking**: Stores and analyzes price history in SQLite database
- **Statistical Analysis**: Multiple anomaly detection methods (IQR, Z-Score, Isolation Forest)
- **Professional GUI**: Built with PySide6 for a modern desktop experience

### Interactive Features (New!)
- **Clickable Cards**: Click any card name to view on TCGPlayer.com
- **Card Image Preview**: Hover over cards to see full-size images
- **Visual Feedback**: Blue text and hover effects for better UX

### Set Scanner
- **Full Set Analysis**: Scan entire MTG sets for pricing anomalies
- **Batch Processing**: Analyze hundreds of cards automatically
- **Progress Tracking**: Real-time updates during set scanning
- **Anomaly Classification**: Identifies undervalued, overvalued, and volatile cards
- **Export Results**: Save scan results to JSON for further analysis

### 🆕 Price Trend Tracker
- **Automated Monitoring**: Background monitoring of price trends across all MTG cards
- **Fast Mover Detection**: Identifies cards with rapid upward price movements
- **Multi-Channel Alerts**: System tray, desktop, and email notifications for trend alerts
- **Real-time Analysis**: Continuous tracking with 6-hour intervals (configurable)
- **Trend Classification**: Detects upward, downward, stable, and volatile trends
- **Investment Insights**: Helps identify arbitrage opportunities and market movements
- **Performance Optimized**: Limited processing to prevent system hang (1000 cards max per cycle)

### Search & Analysis
- **Smart Search**: Advanced query sanitization for reliable results
- **Multiple Printings**: View all printings of a card across sets
- **Filtering & Sorting**: Advanced results filtering and sorting capabilities
- **Data Export**: Export analysis results for further processing

## Installation

1. **Clone or download the project**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application
```bash
python main.py
```

### First-time Setup
1. Go to File → Settings
2. Choose API provider (Scryfall recommended - no API key required)
3. Adjust analysis parameters as needed

### Card Search
1. Enter card name in the search box
2. Select set code (optional)
3. Choose analysis options
4. Click "Search"

### Set Scanner
1. Click the "Set Scanner" tab or use Ctrl+S
2. Select a set from the dropdown (207+ sets available)
3. Click "Start Scan"
4. View results in categorized tabs:
   - All Anomalies
   - Undervalued Cards
   - Overvalued Cards
5. Export results using "Export Results" button

### 🆕 Price Trend Tracker
1. Click the "Trend Tracker" tab or use Ctrl+T
2. Configure monitoring settings:
   - Check interval (default: 6 hours)
   - Alert thresholds (percentage/absolute changes)
   - Notification preferences (system tray, desktop, email)
   - Email notifications (requires Gmail app password setup)
3. Click "Start Monitoring" to begin background tracking
4. View results in dedicated tabs:
   - **Trending Cards**: Cards showing significant price movements
   - **Active Alerts**: Current trend alerts requiring attention
   - **Statistics**: Monitoring performance and database metrics
   - **Configuration**: Adjust all trend tracking settings

### View Results
- **All Results**: Complete price data for all printings
- **Anomalies**: Only cards with unusual pricing
- **Summary**: Statistical overview and insights
- **Interactive Features**: 
  - Click any card name to view on TCGPlayer
  - Hover over cards to see full-size card images
  - Blue text indicates clickable cards

## Configuration

Settings are stored in `~/.mtg_card_pricing/settings.json`:

### API Settings
- **Provider**: Choose between Scryfall (recommended) or JustTCG
- **Rate Limits**: Automatic rate limiting (10 req/sec for Scryfall)
- **Mock Mode**: Use mock data for testing

### Analysis Parameters
- **Anomaly Detection Threshold**: 0.7 (lower = more sensitive, was 0.8)
- **Confidence Threshold**: 0.4 (40% minimum confidence)
- **Minimum Price Filter**: $0.50 (ignore very cheap cards)
- **Cross-Printing Thresholds**: 
  - Undervalued: 60% or less of minimum price
  - Overvalued: 180% or more of minimum price
- **Trend Tracking Settings**:
  - Monitoring interval: 1-168 hours (default: 6 hours)
  - Alert thresholds: 5-500% change, $0.25-$100 absolute
  - Data retention: 7-365 days (default: 30 days)

### Database
- **Main Database**: Card search results and analysis data
- **Trend Database**: Separate database for price monitoring (price_trends.db)
- **Storage Location**: Configurable database paths
- **Cleanup Settings**: Automatic old data removal
- **Backup Options**: Scheduled database backups

### Email Notifications
Configure email alerts for price trend notifications:

1. **Run the configuration script:**
   ```bash
   python configure_email.py
   ```

2. **Setup Gmail App Password:**
   - Enable 2-factor authentication in your Gmail account
   - Generate an app password in Gmail settings
   - Use this app password (not your regular password)

3. **Configure credentials:**
   - Set `email_username` to your Gmail address
   - Set `email_password` to your Gmail app password
   - Email address is pre-configured to `shmikey@gmail.com`

4. **Rate limiting:**
   - Maximum 1 email per hour to prevent spam
   - Respects quiet hours (10 PM - 8 AM default)
   - Independent from other alert types

**Email Content:** Alerts include card name, current price, percentage change, priority level, and timestamp.

## Anomaly Detection

### Market-Based Expected Price Calculation
The system now uses a more conservative market-based approach:
- **Primary Method**: Compares prices across different printings of the same card
- **Expected Price**: Uses the **minimum price** from other printings (not average)
- **Foil Separation**: Foil prices only compared with foil, non-foil with non-foil
- **Benefits**: More reliable for identifying true arbitrage opportunities

### Rule-Based Fallback (for cards with limited printings)
When cross-printing comparison isn't available:
- **Base Rarity Prices**: Common ($0.15), Uncommon ($0.40), Rare ($1.50), Mythic ($4.00)
- **Type Multipliers**: Legendary (2.5x), Planeswalker (3.0x), Creature (1.3x)
- **Set Adjustments**: Commander sets (1.8x), Masters sets (1.3x)
- **Age Factor**: Cards 10+ years old (1.5x), 5+ years (1.2x)
- **Mana Cost**: Free spells (1.5x), expensive spells (0.6x)

### Detection Methods

#### IQR (Interquartile Range)
- Identifies outliers beyond Q1 - 1.5*IQR
- Good for skewed price distributions
- Configurable threshold multiplier

#### Z-Score
- Identifies prices more than N standard deviations from mean
- Best for normally distributed prices
- Configurable threshold value

#### Isolation Forest
- Machine learning approach for anomaly detection
- Effective for complex price patterns
- Configurable contamination rate

## File Structure

```
mtg_card_pricing/
├── main.py                    # Application entry point
├── requirements.txt           # Dependencies
├── README.md                  # This file
├── gui/                       # PySide6 GUI components
│   ├── main_window.py         # Main application window
│   ├── search_widget.py       # Card search interface
│   ├── results_widget.py      # Price display tables
│   ├── set_scanner_widget.py  # Set scanning interface
│   └── trend_tracker_widget.py # Price trend monitoring interface
├── data/                      # Data access layer
│   ├── database.py            # SQLite operations  
│   ├── trend_database.py      # Price trend tracking database
│   ├── api_client.py          # JustTCG API integration
│   ├── scryfall_client.py     # Scryfall API with pagination
│   └── unified_api_client.py  # API abstraction layer
├── analysis/                  # Price analysis logic
│   ├── price_analyzer.py      # Statistical analysis
│   ├── set_scanner.py         # Set-wide anomaly detection
│   └── trend_analyzer.py      # Price trend analysis algorithms
├── services/                  # Background services
│   ├── price_monitor.py       # Automated price monitoring
│   └── alert_system.py        # Trend alerts and notifications
└── config/                    # Configuration management
    ├── settings.py            # Settings and preferences
    └── input_validator.py     # Input sanitization
```

## API Support

### Scryfall API (Recommended)
- **Free to use** - No API key required
- **Better rate limits** - 10 requests/second
- **Comprehensive data** - Includes all card variations
- **Automatic pagination** - Handles large result sets

### JustTCG API
- Requires API key
- More restrictive rate limits
- Limited to 175 results per search

## Recent Updates

### Version 2.1 - Price Trend Tracker & Interactive Features
- ✅ **Price Trend Tracker**: Automated monitoring of price trends across all MTG cards
- ✅ **Fast Mover Detection**: Identifies cards with rapid upward price movements
- ✅ **Alert System**: System tray and desktop notifications for trend alerts
- ✅ **Interactive Cards**: Clickable card names and hover image previews
- ✅ **Background Monitoring**: Configurable 6-hour intervals with progress tracking
- ✅ **Trend Analysis**: Advanced algorithms for detecting market movements

### Version 2.0 - Set Scanner & Improved Analysis
- ✅ **Set Scanner**: Analyze entire MTG sets for anomalies
- ✅ **Pagination Support**: Retrieve all cards in large sets (400+ cards)
- ✅ **Enhanced Filtering**: Includes Commander Collections and specialty sets
- ✅ **Improved Expected Prices**: More accurate price calculations
- ✅ **Better Coverage**: 207+ sets available for scanning
- ✅ **Alphabetical Sorting**: Sets listed A-Z for easy navigation

### Bug Fixes
- Fixed incomplete set scans (was limited to 175 cards)
- Fixed "Input must be a dictionary" errors
- Fixed search query sanitization issues
- Fixed rate limiting with exponential backoff

## Requirements

- Python 3.8+
- PySide6 (GUI framework)
- pandas (Data manipulation)
- numpy (Numerical computing)
- scikit-learn (Machine learning)
- requests (HTTP client)

## Troubleshooting

### Common Issues

1. **Incomplete Set Scans**: Update to latest version with pagination fix
2. **Import Errors**: Run `pip install -r requirements.txt`
3. **API Rate Limits**: Switch to Scryfall API for better limits
4. **Search Returns 0 Results**: Check for special characters in card names

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance

- **Small sets** (< 100 cards): 5-10 seconds
- **Medium sets** (100-250 cards): 20-30 seconds
- **Large sets** (400+ cards): 40-60 seconds

Scanning includes rate limiting to respect API limits.

## License

This project is provided as-is for educational and personal use.

## Contributing

When contributing:
1. Follow existing code patterns
2. Add comprehensive error handling
3. Include logging for debugging
4. Update documentation
5. Test with both Scryfall and JustTCG APIs