# Price Trend Tracker User Guide

## Overview

The Price Trend Tracker is an advanced feature that automatically monitors Magic: The Gathering card prices across the entire collection to identify fast upward trends and investment opportunities. It runs continuously in the background, analyzing price movements and alerting you to significant changes.

## Key Features

### 🔄 Automated Monitoring
- **Background Service**: Runs continuously with configurable check intervals (default: 6 hours)
- **Comprehensive Coverage**: Monitors all MTG sets automatically
- **Rate Limited**: Respects API limits with built-in delays
- **Fresh Data**: Uses current market prices without requiring historical imports

### 📈 Advanced Trend Analysis
- **Trend Classification**: Detects upward, downward, stable, and volatile price movements
- **Trend Strength**: Classifies trends as weak, moderate, strong, or extreme
- **Fast Mover Detection**: Identifies cards with rapid price increases
- **Confidence Scoring**: Provides reliability metrics for each trend analysis

### 🚨 Smart Alert System
- **System Tray Notifications**: Unobtrusive alerts in your system tray
- **Desktop Notifications**: Cross-platform notification support
- **Quiet Hours**: Configurable quiet periods (default: 10 PM - 8 AM)
- **Alert Rate Limiting**: Prevents spam with configurable hourly limits
- **Priority Scoring**: Higher priority alerts for more significant movements

### 📊 Comprehensive Dashboard
- **Real-time Statistics**: Monitor system performance and database metrics
- **Trending Cards View**: See all cards with significant price movements
- **Active Alerts Management**: Review and dismiss trend alerts
- **Progress Tracking**: Visual feedback during monitoring cycles

## Getting Started

### Accessing the Trend Tracker

1. **Via GUI**: Click the "Trend Tracker" tab in the main window
2. **Via Keyboard**: Press `Ctrl+T`
3. **Via Menu**: Tools → Trend Tracker

### Initial Setup

1. **Open Configuration Tab**: Click the "Configuration" tab within Trend Tracker
2. **Configure Monitoring Settings**:
   - **Check Interval**: How often to scan for price changes (1-168 hours)
   - **Max Cards per Cycle**: Limit processing load (100-5000 cards)
3. **Set Alert Thresholds**:
   - **Minimum Price**: Only track cards above this value (default: $0.50)
   - **Percentage Threshold**: Alert on price increases above this % (default: 20%)
   - **Absolute Threshold**: Alert on price increases above this $ amount (default: $0.50)
4. **Configure Notifications**:
   - **Enable Alerts**: Turn the alert system on/off
   - **System Tray**: Show notifications in system tray
   - **Desktop Notifications**: Show desktop popup notifications
5. **Data Management**:
   - **Keep Data**: How long to retain price history (7-365 days)

### Starting Monitoring

1. **Click "Start Monitoring"** in the main control panel
2. **Monitor Progress**: Watch the progress bar during initial scan
3. **View Status**: Check the status indicator for current state
4. **Review Results**: Switch between tabs to see trending cards and alerts

## Understanding Results

### Trending Cards Tab

Displays all cards showing significant price movements:

- **Card Name**: Clickable link to TCGPlayer (hover for card image)
- **Set**: Set code where the card appears
- **Current Price**: Latest market price with foil indicator (F)
- **Start Price**: Price at beginning of trend period
- **Change %**: Percentage increase (green = positive)
- **Change $**: Absolute dollar increase
- **Duration**: How long the trend has been active
- **Alert Score**: Computed priority score (0-100)

### Active Alerts Tab

Shows alerts requiring your attention:

- **Card Information**: Name, set, and foil status
- **Price Data**: Current vs. starting prices
- **Change Metrics**: Both percentage and absolute changes
- **First Detected**: When the trend was first identified
- **Actions**: Dismiss individual alerts

### Statistics Tab

Monitor system performance:

- **Service Status**: Current monitoring state
- **Processing Metrics**: Cards processed, prices recorded
- **Detection Results**: Trends found, alerts generated
- **Timing Information**: Last run, next scheduled run
- **Database Stats**: Total records, size, data range

## Configuration Options

### Monitoring Settings

- **Enable Monitoring**: Master on/off switch
- **Check Interval**: 1-168 hours (default: 6 hours)
  - Lower values = more frequent checks, higher API usage
  - Higher values = less frequent checks, may miss short-term movements
- **Max Cards per Cycle**: 100-5000 (default: 1000)
  - Limits processing load per monitoring cycle
  - Higher values = more comprehensive scanning

### Alert Thresholds

- **Minimum Price**: $0.01-$100 (default: $0.50)
  - Only cards above this price are monitored
  - Filters out very cheap commons and tokens
- **Percentage Alert Threshold**: 5-500% (default: 20%)
  - Triggers alerts when price increases by this percentage
  - Lower values = more sensitive, more alerts
- **Absolute Alert Threshold**: $0.25-$100 (default: $0.50)
  - Triggers alerts when price increases by this dollar amount
  - Useful for finding significant moves on expensive cards

### Alert System

- **Enable Alerts**: Master switch for all notifications
- **System Tray Notifications**: Show alerts in system tray
- **Desktop Notifications**: Show popup notifications
- **Email Notifications**: Send email alerts for price trends
  - Requires Gmail SMTP configuration
  - Rate limited to 1 email per hour maximum
  - Independent from other alert types
- **Max Alerts per Hour**: 1-50 (default: 10)
  - Prevents notification spam
- **Quiet Hours**: 
  - **Start**: 22 (10 PM) - **End**: 8 (8 AM)
  - No alerts during sleep hours (applies to all alert types)

### Data Management

- **Keep Trend Data**: 7-365 days (default: 30 days)
  - Older data is automatically cleaned up
  - Longer retention = more historical context
- **Separate Database**: Uses `price_trends.db` for trend data
  - Keeps trend data separate from main analysis database
  - Enables independent backup and maintenance

## Trend Analysis Details

### Trend Types

- **Upward**: Consistent price increases over time
- **Downward**: Consistent price decreases over time  
- **Stable**: Minimal price movement
- **Volatile**: High price fluctuation without clear direction

### Trend Strength

- **Weak**: 10-25% price change
- **Moderate**: 25-50% price change
- **Strong**: 50-100% price change
- **Extreme**: >100% price change

### Alert Scoring

The alert score (0-100) considers:

- **Percentage Change** (40 points max): Higher % = higher score
- **Momentum** (25 points max): Rate of price acceleration
- **Speed** (20 points max): How quickly the change occurred
- **Confidence** (15 points max): Reliability of the trend detection

## Best Practices

### Optimal Settings

- **New Users**: Start with default settings (6-hour intervals, 20% threshold)
- **Active Traders**: Use 2-4 hour intervals for faster detection
- **Casual Monitoring**: Use 12-24 hour intervals to reduce API usage
- **High-Value Focus**: Increase minimum price threshold to $5-10

### Market Timing

- **New Set Releases**: Monitor more frequently during first 2-4 weeks
- **Tournament Season**: Watch for format staples and breakout cards
- **Reprint Announcements**: Track price impacts on affected cards
- **Economic Events**: Monitor during market uncertainty

### Alert Management

1. **Review Daily**: Check active alerts at least once per day
2. **Dismiss Processed**: Clear alerts you've already acted on
3. **Track Patterns**: Note which types of cards trend most often
4. **Verify Sources**: Always confirm prices on multiple platforms
5. **Consider Context**: Factor in reprints, bannings, and meta changes

## Troubleshooting

### No Trends Detected

- **Check Thresholds**: Lower percentage/absolute thresholds
- **Verify API Access**: Ensure Scryfall connection is working
- **Review Time Period**: Market may be stable during monitoring period
- **Expand Scope**: Increase max cards per cycle

### Too Many Alerts

- **Raise Thresholds**: Increase percentage/absolute alert levels
- **Reduce Frequency**: Increase monitoring interval
- **Lower Max Alerts**: Decrease hourly alert limit
- **Enable Quiet Hours**: Configure sleep periods

### Performance Issues

- **Reduce Max Cards**: Lower cards per cycle limit
- **Increase Interval**: Less frequent monitoring
- **Clean Up Data**: Reduce data retention period
- **Check Internet**: Ensure stable connection to APIs

### Missing Notifications

- **Check Alert Settings**: Verify notifications are enabled
- **Test System Tray**: Ensure tray icon is visible
- **Review Quiet Hours**: May be in configured quiet period
- **Check Platform Support**: Desktop notifications may need setup
- **Email Issues**: If email alerts aren't working:
  - Verify Gmail credentials are configured
  - Check email rate limit (1 per hour)
  - Ensure not in quiet hours
  - Check spam/junk folder

## Email Configuration

### Quick Setup

1. **Run the configuration script:**
   ```bash
   python configure_email.py
   ```

2. **Configure Gmail credentials:**
   - Enable 2-factor authentication in Gmail
   - Generate an app password (not your regular password)
   - Set email username and app password in the configuration

3. **Test setup:**
   ```bash
   python test_email_alert.py
   ```

### Email Alert Content

Email alerts include comprehensive price information:

```
Subject: MTG Price Alert: Lightning Bolt

Body:
MTG Card Price Alert

Card: Lightning Bolt (LEA)
Current Price: $12.50
Price Change: +25.5% (+$2.50)
Alert Priority: HIGH
Time: 2025-07-11 13:30:18

This is an automated alert from your MTG Card Price Tracker.
```

### Email Settings

- **Rate Limited**: Maximum 1 email per hour
- **Quiet Hours**: Respects sleep schedule (10 PM - 8 AM)
- **Security**: Credentials stored encrypted locally
- **Priority Based**: Alert priority affects email urgency

For detailed email setup instructions, see `EMAIL_NOTIFICATIONS.md`.

## Advanced Features

### Manual Monitoring Cycle

- Use "Force Refresh" button to trigger immediate scan
- Useful for testing settings or urgent market analysis
- Respects all configured thresholds and limits

### Database Management

- **Statistics View**: Monitor database size and performance
- **Cleanup Control**: Manual cleanup via configuration
- **Backup Strategy**: Separate database enables independent backups

### Integration with Main App

- **Settings Persistence**: All preferences saved with main application
- **Shared Card Display**: Uses same interactive card system
- **Unified API Access**: Leverages existing Scryfall integration

## Data Export and Analysis

While the current version focuses on real-time monitoring, future enhancements may include:

- **Export Trending Data**: Save trend analysis to CSV/JSON
- **Historical Charts**: Visual price trend displays  
- **Portfolio Integration**: Track owned cards specifically
- **Advanced Filtering**: Custom queries on trend data
- **API Integration**: Connect with external tools

## Privacy and Security

- **No Personal Data**: Only stores card price information
- **Local Storage**: All data kept on your machine
- **API Respect**: Follows rate limits and terms of service
- **Secure Connections**: Uses HTTPS for all API calls

For additional support or feature requests, please refer to the main application documentation or submit feedback through the appropriate channels.