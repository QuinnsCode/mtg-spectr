# Interactive Features Guide

## Overview

The MTG Card Pricing Analysis Tool now includes interactive features that enhance the user experience when browsing card results. All card names in result tables are now clickable and show card images on hover.

## Features

### 1. Clickable Card Names

**What it does**: Click any card name to instantly search for it on TCGPlayer.com

**How to use**:
- Look for card names displayed in **blue text** (indicates clickable)
- Click the card name to open your default browser
- Automatically navigates to TCGPlayer search results for that card

**Where it works**:
- Search Results table (All Results tab)
- Anomalies table (Anomalies tab)
- Set Scanner results (all three tabs)
- Any table displaying card names

### 2. Card Image Previews

**What it does**: Hover over any card name to see a full-size card image

**How to use**:
- Move your mouse over any clickable card name
- Wait a moment for the image to load
- Card image appears as a tooltip near your cursor
- Move away to hide the image

**Features**:
- Images are cached for faster subsequent viewing
- Shows card name below the image
- Includes "Click to view on TCGPlayer" reminder

### 3. Visual Feedback

**Design elements**:
- **Blue text**: Indicates clickable card names
- **Hover cursor**: Changes to pointer when over clickable cards
- **Tooltips**: Show helpful hints when hovering

## Technical Implementation

### Classes Added

#### `ClickableCardItem`
- Custom QTableWidgetItem for card names
- Handles click events and styling
- Stores card data for TCGPlayer URL generation

#### `ClickableCardTable`
- Enhanced QTableWidget with click handling
- Manages mouse tracking for hover effects
- Handles card image display

#### `CardImageManager`
- Manages asynchronous image downloading
- Implements image caching for performance
- Scales images to appropriate display size (223x311 pixels)

### Integration

The interactive features are automatically integrated into:
- `results_widget.py`: Main results display
- `set_scanner_widget.py`: Set scanner results

No configuration needed - features work out of the box!

## Browser Compatibility

The TCGPlayer links open in your system's default web browser. Supported browsers include:
- Chrome
- Firefox
- Safari
- Edge
- Any modern web browser

## Troubleshooting

### Card images not showing
- Ensure you have an active internet connection
- Some older or promo cards may not have images available
- Images are loaded from Scryfall's image servers

### Links not opening
- Check that you have a default browser set
- Verify TCGPlayer.com is accessible in your region
- Try manually navigating to tcgplayer.com

### Performance
- First hover may take a moment to load the image
- Subsequent hovers use cached images for instant display
- Large result sets may take longer to initialize

## Privacy Note

- Card images are fetched from Scryfall's CDN
- No personal data is sent when clicking TCGPlayer links
- Image cache is stored locally in memory only