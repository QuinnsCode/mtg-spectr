# MTG Card Pricing API

A serverless REST API for Magic: The Gathering card pricing and data analysis, powered by Scryfall and hosted on Vercel.

## 🚀 Base URL

```
https://mtg-spectr.vercel.app
```

## 📋 Available Endpoints

### Health Check
```bash
curl https://mtg-spectr.vercel.app/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-14T06:28:42.671574",
  "services": {
    "scryfall_api": true,
    "serverless": true
  }
}
```

---

## 🔍 Card Search

### Search Cards
Search for MTG cards by name, with optional set filtering.

```bash
curl -X POST https://mtg-spectr.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "card_name": "Lightning Bolt",
    "limit": 5
  }'
```

**Parameters:**
- `card_name` (required): Card name to search for
- `set_code` (optional): Filter by set code (e.g., "dom", "m21")
- `limit` (optional): Max results (default: 10, max: 100)

**Example with set filter:**
```bash
curl -X POST https://mtg-spectr.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "card_name": "Lightning Bolt",
    "set_code": "lea",
    "limit": 3
  }'
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "id": "77c6fa74-5543-42ac-9ead-0e890b188e99",
      "name": "Lightning Bolt",
      "set": "clu",
      "set_name": "Ravnica: Clue Edition",
      "collector_number": "141",
      "rarity": "uncommon",
      "prices": {
        "usd": "0.90",
        "usd_foil": null,
        "eur": "1.40",
        "eur_foil": null,
        "tix": "0.02"
      },
      "foil": false,
      "nonfoil": true,
      "image_uris": {
        "normal": "https://cards.scryfall.io/normal/front/7/7/77c6fa74-5543-42ac-9ead-0e890b188e99.jpg",
        "large": "https://cards.scryfall.io/large/front/7/7/77c6fa74-5543-42ac-9ead-0e890b188e99.jpg"
      },
      "scryfall_uri": "https://scryfall.com/card/clu/141/lightning-bolt",
      "released_at": "2024-02-23"
    }
  ],
  "count": 1,
  "search_params": {
    "card_name": "Lightning Bolt",
    "set_code": null,
    "limit": 5
  },
  "timestamp": "2025-07-14T06:29:02.839708"
}
```

### Autocomplete Suggestions
Get card name suggestions for autocomplete functionality.

```bash
curl "https://mtg-spectr.vercel.app/api/search/suggestions?q=Lightning"
```

**Response:**
```json
[
  "Lightning Bolt",
  "Lightning Strike",
  "Lightning Helix",
  "Lightning Angel",
  "Lightning Greaves"
]
```

---

## 🃏 Card Details

### Get All Printings
Get all printings of a specific card across all sets.

```bash
curl https://mtg-spectr.vercel.app/api/cards/printings/Lightning%20Bolt
```

**Response:**
```json
{
  "status": "success",
  "card_name": "Lightning Bolt",
  "printings": [
    {
      "card_name": "Lightning Bolt",
      "set_code": "lea",
      "set_name": "Limited Edition Alpha",
      "collector_number": "161",
      "rarity": "common",
      "prices": {
        "usd": "450.00",
        "usd_foil": null,
        "eur": "399.99",
        "eur_foil": null
      },
      "foil_available": false,
      "nonfoil_available": true,
      "source": "Scryfall",
      "card_id": "8e0f1cd6-8f4e-4e8d-ad0e-b30d8c7a8f0e",
      "image_url": "https://cards.scryfall.io/normal/front/8/e/8e0f1cd6.jpg",
      "released_at": "1993-08-05",
      "scryfall_uri": "https://scryfall.com/card/lea/161"
    }
  ],
  "count": 45,
  "timestamp": "2025-07-14T06:35:22.123456"
}
```

---

## 📦 Sets

### List All Sets
Get a list of all MTG sets, sorted by release date (newest first).

```bash
curl https://mtg-spectr.vercel.app/api/sets
```

**Response:**
```json
{
  "status": "success",
  "sets": [
    {
      "id": "fdde66b9-027a-43e8-9aa4-5d338f379ade",
      "code": "tla",
      "name": "The Lost Caverns of Ixalan",
      "card_count": 291,
      "digital": false,
      "foil_only": false,
      "released_at": "2023-11-17",
      "set_type": "expansion",
      "icon_svg_uri": "https://svgs.scryfall.io/sets/tla.svg"
    }
  ],
  "count": 978,
  "timestamp": "2025-07-14T06:29:15.187575"
}
```

### Scan Entire Set
Analyze all cards in a specific set, sorted by value.

```bash
curl -X POST https://mtg-spectr.vercel.app/api/sets/dsk/scan
```

**Popular Set Codes:**
- `dsk` - Duskmourn: House of Horror
- `blb` - Bloomburrow  
- `otj` - Outlaws of Thunder Junction
- `mkm` - Murders at Karlov Manor
- `lci` - The Lost Caverns of Ixalan
- `woe` - Wilds of Eldraine
- `one` - Phyrexia: All Will Be One
- `dom` - Dominaria
- `lea` - Limited Edition Alpha
- `leb` - Limited Edition Beta

**Response:**
```json
{
  "status": "success",
  "set_code": "dsk",
  "cards": [
    {
      "name": "Valgavoth, Terror Eater",
      "set_code": "dsk",
      "collector_number": "123",
      "rarity": "mythic",
      "usd_price": 45.99,
      "prices": {
        "usd": "45.99",
        "usd_foil": "89.99",
        "eur": "42.50"
      },
      "image_uris": {
        "normal": "https://cards.scryfall.io/normal/front/..."
      },
      "scryfall_uri": "https://scryfall.com/card/dsk/123"
    }
  ],
  "summary": {
    "total_cards": 276,
    "total_value": 1247.89,
    "average_value": 4.52,
    "cards_with_price": 245
  },
  "timestamp": "2025-07-14T06:40:15.234567"
}
```

---

## 🛠 Advanced Examples

### Search for Expensive Cards in a Set
```bash
# Get all cards from Duskmourn, then filter client-side for expensive ones
curl -X POST https://mtg-spectr.vercel.app/api/sets/dsk/scan | \
  jq '.cards[] | select(.usd_price > 10) | {name, usd_price, rarity}'
```

### Find All Printings of a Valuable Card
```bash
# Get all Lightning Bolt printings and see price differences
curl https://mtg-spectr.vercel.app/api/cards/printings/Lightning%20Bolt | \
  jq '.printings[] | {set_name, set_code, usd_price: .prices.usd}'
```

### Search Multiple Cards
```bash
# Search for multiple cards (requires multiple requests)
for card in "Lightning Bolt" "Counterspell" "Dark Ritual"; do
  echo "=== $card ==="
  curl -s -X POST https://mtg-spectr.vercel.app/api/search \
    -H "Content-Type: application/json" \
    -d "{\"card_name\": \"$card\", \"limit\": 1}" | \
    jq '.results[0] | {name, set_name, usd_price: .prices.usd}'
done
```

### Get Set Statistics
```bash
# Get summary stats for a set
curl -X POST https://mtg-spectr.vercel.app/api/sets/dom/scan | \
  jq '.summary'
```

---

## 📊 Response Format

All successful responses follow this format:
```json
{
  "status": "success",
  "data": "...",
  "timestamp": "2025-07-14T06:29:02.839708"
}
```

Error responses:
```json
{
  "status": "error", 
  "error": "Error description"
}
```

---

## 🚨 Rate Limits & Best Practices

- **Scryfall Rate Limit**: 10 requests per second
- **Vercel Function Timeout**: 30 seconds max
- **Best Practice**: Cache results when possible
- **Set Scanning**: Large sets (200+ cards) may take 10-15 seconds

### Efficient Usage Tips

1. **Use specific searches**: Include set codes when possible
2. **Limit results**: Don't request more data than needed  
3. **Cache printings**: Card printings rarely change
4. **Batch processing**: For multiple cards, space out requests

---

## 🔧 Error Handling

Common error scenarios:

**Card not found:**
```bash
curl -X POST https://mtg-spectr.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{"card_name": "Nonexistent Card"}'
# Returns: {"status": "success", "results": [], "count": 0}
```

**Invalid set code:**
```bash
curl -X POST https://mtg-spectr.vercel.app/api/sets/invalid/scan
# Returns: {"status": "error", "error": "No cards found for set invalid"}
```

**Missing required parameters:**
```bash
curl -X POST https://mtg-spectr.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{}'
# Returns: {"status": "error", "error": "Card name is required"}
```

---

## 🎯 Quick Start Examples

**Find the most expensive card in Standard:**
```bash
curl -X POST https://mtg-spectr.vercel.app/api/sets/one/scan | \
  jq '.cards[0]'
```

**Search for a specific card:**
```bash
curl -X POST https://mtg-spectr.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{"card_name": "Black Lotus", "limit": 1}'
```

**Get autocomplete for deck building:**
```bash
curl "https://mtg-spectr.vercel.app/api/search/suggestions?q=Swamp"
```

---

## 📝 Notes

- All prices are in USD unless otherwise specified
- Image URLs are high-quality from Scryfall
- Set data includes both paper and digital releases
- Prices update in real-time from market data

**Data Source**: [Scryfall API](https://scryfall.com/docs/api) - The most comprehensive MTG database