# Set Scanner User Guide

## Overview

The Set Scanner is a powerful feature that analyzes entire Magic: The Gathering sets to identify pricing anomalies. It can help you find undervalued cards, overpriced cards, and volatile market opportunities.

## Getting Started

### Accessing the Set Scanner

1. **Via GUI**: Click the "Set Scanner" tab in the main window
2. **Via Keyboard**: Press `Ctrl+S`
3. **Via Menu**: Tools → Set Scanner

### Basic Scanning

1. **Select a Set**: Choose from 207+ available sets in the dropdown
2. **Click "Start Scan"**: Begin the analysis
3. **Monitor Progress**: Watch the progress bar and status updates
4. **Review Results**: Browse anomalies in categorized tabs

## Understanding Results

### Anomaly Types

#### Undervalued Cards
- Current price significantly below expected value
- Good buying opportunities
- Often overlooked cards with potential

#### Overvalued Cards
- Current price significantly above expected value
- May indicate market hype or speculation
- Consider selling opportunities

#### Volatile Cards
- High price variance across printings
- Market uncertainty or manipulation
- Requires careful analysis

### Result Metrics

- **Current Price**: Actual market price (foil/non-foil separated)
- **Expected Price**: Market-based or calculated fair value
- **Anomaly Score**: Strength of the anomaly (higher = stronger, threshold: 0.7)
- **Confidence**: Reliability of the detection (0-100%)

## Expected Price Calculation

The scanner uses a market-based approach to determine expected prices:

### Primary Method: Cross-Printing Comparison
- Compares prices across different printings of the same card
- **Expected Price**: Uses the **minimum price** from other printings
- **Foil Separation**: Foil prices only compared with foil, non-foil with non-foil
- **Benefits**: More conservative approach for identifying arbitrage opportunities

### Fallback Method: Rule-Based Calculation
Used when a card has limited printings:

#### Base Prices by Rarity
- Common: $0.15
- Uncommon: $0.40
- Rare: $1.50
- Mythic: $4.00

#### Multipliers Applied

##### Card Type Multipliers
- Legendary: 2.5x
- Planeswalker: 3.0x
- Creature: 1.3x
- Artifact: 1.2x
- Land: 1.2x

##### Set-Based Adjustments
- Commander sets: 1.8x
- Masters sets: 1.3x
- Core sets: 0.8x

##### Age Adjustments
- 10+ years old: 1.5x
- 5-9 years old: 1.2x
- 2-4 years old: 1.1x

##### Mana Cost Factors
- Free (0 mana): 1.5x
- Very cheap (1 mana): 1.3x
- Cheap (2 mana): 1.1x
- Expensive (5-6 mana): 0.8x
- Very expensive (7+ mana): 0.6x

## Available Sets

### Set Types Included
- **Expansion Sets**: Main storyline sets (109 sets)
- **Core Sets**: Annual core releases (25 sets)
- **Masters Sets**: Reprint sets (20 sets)
- **Commander Products**: EDH-focused sets (38 sets)
- **Draft Innovation**: Unique draft experiences (15 sets)
- **Arsenal Sets**: Premium products like Commander Collections
- **Premium/Duel Decks**: Special releases

### Recent Sets (2024)
- Duskmourn: House of Horror (dsk)
- Bloomburrow (blb)
- Outlaws of Thunder Junction (otj)
- Murders at Karlov Manor (mkm)

## Performance Expectations

### Scan Times
- **Small sets** (8-50 cards): 5-10 seconds
- **Medium sets** (100-200 cards): 20-30 seconds
- **Large sets** (300-400 cards): 40-60 seconds
- **Very large sets** (500+ cards): 60-90 seconds

### Rate Limiting
- Scryfall: 10 requests/second (automatic)
- Includes built-in delays to respect API limits
- No manual configuration needed

## Exporting Results

### Export Options
1. Click "Export Results" button
2. Choose save location
3. File saved as JSON format

### Export Format
```json
{
  "set_code": "dsk",
  "set_name": "Duskmourn: House of Horror",
  "scan_timestamp": "2025-07-09T10:30:00",
  "total_cards": 276,
  "anomalies_found": 15,
  "anomaly_cards": [
    {
      "card_name": "Overlord of the Hauntwoods",
      "current_price": 25.99,
      "expected_price": 12.00,
      "anomaly_type": "overvalued",
      "confidence": 0.89
    }
  ]
}
```

## Advanced Usage

### Filtering Results
- Use the search box to filter by card name
- Sort columns by clicking headers
- Export filtered results only

### Batch Scanning
```python
# Scan multiple sets programmatically
sets_to_scan = ['dsk', 'blb', 'otj']
for set_code in sets_to_scan:
    result = scanner.scan_set(set_code)
    scanner.export_results(result, f'{set_code}_scan.json')
```

### Custom Thresholds
Adjust in Settings → Analysis:
- Anomaly Detection Threshold: Lower = more sensitive (default: 0.7)
- Confidence Threshold: Minimum confidence required (default: 0.4)
- Cross-Printing Thresholds:
  - Undervalued: 60% or less of minimum price
  - Overvalued: 180% or more of minimum price

## Tips for Best Results

### When to Scan
- **New Set Releases**: First 2-4 weeks for volatility
- **Before Major Tournaments**: Identify undervalued cards
- **Rotation Announcements**: Find format staples
- **Reprint Announcements**: Check price impacts

### What to Look For
1. **Undervalued Rares/Mythics** in older sets
2. **Commander Staples** in standard sets
3. **Combo Pieces** before they're discovered
4. **Reserved List** adjacent cards

### Market Considerations
- Check multiple sources before buying
- Consider condition and language
- Factor in shipping costs
- Be aware of reprints

## Troubleshooting

### No Anomalies Found
- Set may have stable, efficient pricing
- Try adjusting sensitivity thresholds
- Some sets have fewer anomalies

### Scan Takes Too Long
- Large sets require more API calls
- Check internet connection
- Consider scanning during off-peak hours

### Missing Sets
- Some promotional/special sets excluded
- Digital-only sets not included
- Sets with <8 cards filtered out

## Examples of Anomalies

### Example 1: Cross-Printing Anomaly
```
Card: Bane of Progress
Set: Foundations Jumpstart (FIC)
Current: $0.90
Expected: $0.20 (minimum from other printings)
Type: Overvalued (4.5x minimum price)
Confidence: 72.2%
```

### Example 2: Tournament Breakout
```
Card: Temporary Lockdown
Set: Dominaria United
Current: $0.45
Expected: $1.95
Type: Undervalued
Confidence: 92.3%
```

## Best Practices

1. **Regular Scanning**: Check favorite sets weekly
2. **Multiple Confirmations**: Verify prices on multiple platforms
3. **Track History**: Export and compare scans over time
4. **Set Alerts**: Note interesting anomalies for monitoring
5. **Diversify**: Don't invest heavily in single anomalies

## Future Enhancements

Planned features:
- Historical anomaly tracking
- Price alerts for specific cards
- Automated scheduled scans
- Machine learning predictions
- Portfolio management integration