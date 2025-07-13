# JustTCG API Setup Guide

## Getting Your API Key

### Step 1: Create an Account
1. Go to [JustTCG.com](https://justtcg.com/)
2. Sign up for a new account or log in to your existing account
3. Navigate to your user dashboard

### Step 2: Subscribe to a Plan
To get an API key, you need to subscribe to one of the available plans:

- **Free Plan**: 1,000 monthly requests
- **Starter Plan**: 10,000 monthly requests  
- **Professional Plan**: 50,000 monthly requests
- **Enterprise Plan**: 500,000 monthly requests

### Step 3: Retrieve Your API Key
1. After subscribing to a plan, go to your dashboard
2. Look for the API section or API keys section
3. Your API key will be displayed there
4. Copy the API key (format: `tcg_your_api_key_here`)

## Configuring the Application

### Method 1: Settings Interface (Recommended)
1. Launch the MTG Card Pricing Analysis Tool
2. Go to **Settings** → **API Configuration**
3. Enter your API key in the "JustTCG API Key" field
4. Click "Save" to store the encrypted API key

### Method 2: Environment Variable
Set the environment variable before running the application:
```bash
export JUSTTCG_API_KEY="tcg_your_api_key_here"
python main.py
```

### Method 3: Configuration File
Create a config file at `~/.mtg_card_pricing/config.json`:
```json
{
  "api": {
    "justtcg_api_key": "tcg_your_api_key_here"
  }
}
```

## Authentication Details

The application uses **X-API-Key header authentication**:
- Header: `X-API-Key: tcg_your_api_key_here`
- All API requests include this header automatically
- API keys are encrypted when stored locally

## Rate Limits

Your rate limit depends on your subscription plan:
- The application automatically handles rate limiting
- Requests are throttled to stay within your plan's limits
- You'll see progress indicators during batch processing

## API Key Security

### Important Security Notes:
- **Never expose your API key in client-side code**
- **Keep your API key secure and private**
- **If compromised, immediately regenerate it from your dashboard**
- **The application encrypts your API key when storing it locally**

### Best Practices:
1. Store API keys in environment variables or encrypted configuration
2. Never commit API keys to version control
3. Regenerate API keys periodically
4. Monitor your API usage in the JustTCG dashboard

## Testing Your API Key

Once configured, you can test your API key:
1. Launch the application
2. Go to the search interface
3. Try searching for a card (e.g., "Lightning Bolt")
4. If configured correctly, you should see pricing data

## Troubleshooting

### Common Issues:

**"Invalid API Key" Error**:
- Check that you've entered the correct API key
- Ensure your subscription is active
- Verify the API key hasn't expired

**Rate Limit Exceeded**:
- Wait for the rate limit window to reset
- Consider upgrading to a higher plan
- Use batch processing efficiently

**Network Errors**:
- Check your internet connection
- Verify JustTCG API is accessible
- Try again after a short delay

## Support

If you encounter issues:
1. Check the JustTCG documentation: https://justtcg.com/docs
2. Contact JustTCG support for API-related issues
3. Check the application logs for detailed error messages

## Example Usage

Once your API key is configured, you can:
- Search for individual cards and see all printings
- Identify underpriced cards automatically
- Process multiple cards in batch mode
- Export results for further analysis

The application will handle all API authentication automatically once your key is configured!