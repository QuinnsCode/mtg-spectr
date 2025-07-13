# Email Notifications Setup Guide

This guide explains how to configure email notifications for MTG Card Price Tracker alerts.

## Overview

The email notification system sends price trend alerts to your email address when significant price movements are detected. Email notifications are rate-limited to prevent spam and respect quiet hours.

## Features

- **Automated Alerts**: Receive email notifications for significant price trends
- **Rate Limiting**: Maximum 1 email per hour to prevent inbox flooding
- **Quiet Hours**: No emails during 10 PM - 8 AM (configurable)
- **Priority-based**: Email content includes alert priority levels
- **Secure**: Uses encrypted credential storage

## Quick Setup

1. **Run the configuration script:**
   ```bash
   python configure_email.py
   ```

2. **Configure your Gmail credentials** (see detailed setup below)

3. **Test the system:**
   ```bash
   python test_email_alert.py
   ```

## Detailed Setup Instructions

### Step 1: Enable Gmail App Passwords

1. **Enable 2-Factor Authentication:**
   - Go to your Google Account settings
   - Navigate to "Security" → "2-Step Verification"
   - Follow the prompts to enable 2FA

2. **Generate App Password:**
   - In Google Account settings, go to "Security"
   - Click "App passwords" (you need 2FA enabled first)
   - Select "Mail" and "Other (custom name)"
   - Enter "MTG Price Tracker" as the app name
   - Copy the generated 16-character password

### Step 2: Configure Email Settings

You can configure email settings through the GUI or by directly updating the database:

#### Option A: GUI Configuration
1. Open MTG Price Tracker
2. Go to "Trend Tracker" tab
3. Click "Configuration" sub-tab
4. Enable email notifications
5. Enter your Gmail address and app password

#### Option B: Direct Database Configuration
```python
from mtg_card_pricing.services.alert_system import AlertSystem

# Initialize alert system
alert_system = AlertSystem()

# Configure email settings
email_config = {
    'email_enabled': True,
    'email_address': 'your-email@gmail.com',  # Where to send alerts
    'email_username': 'your-gmail@gmail.com',  # Your Gmail address
    'email_password': 'your-app-password',     # 16-character app password
    'email_smtp_server': 'smtp.gmail.com',
    'email_smtp_port': 587,
    'max_emails_per_hour': 1
}

# Update configuration
alert_system.update_config(**email_config)
```

### Step 3: Test Your Setup

Run the test script to verify email functionality:

```bash
python test_email_alert.py
```

This will:
- Test email body creation
- Verify rate limiting works
- Check configuration settings
- Show what would be sent (without actually sending)

## Email Content Format

Email alerts include:

```
Subject: MTG Price Alert: [Card Name]

Body:
MTG Card Price Alert

Card: Lightning Bolt (LEA)
Current Price: $12.50
Price Change: +25.5% (+$2.50)
Alert Priority: HIGH
Time: 2025-07-11 13:30:18

This is an automated alert from your MTG Card Price Tracker.
```

## Configuration Options

### Rate Limiting Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `max_emails_per_hour` | 1 | Maximum emails sent per hour |
| `quiet_hours_start` | 22 | Start of quiet hours (10 PM) |
| `quiet_hours_end` | 8 | End of quiet hours (8 AM) |
| `min_alert_interval_minutes` | 15 | Minimum time between same card alerts |

### SMTP Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `email_smtp_server` | smtp.gmail.com | SMTP server address |
| `email_smtp_port` | 587 | SMTP port (TLS) |
| `email_username` | (required) | Your Gmail address |
| `email_password` | (required) | Gmail app password |

## Security Considerations

1. **App Passwords**: Never use your regular Gmail password - always use app passwords
2. **Credential Storage**: Passwords are encrypted and stored locally
3. **Local Storage**: All data stays on your machine - no cloud storage
4. **TLS Encryption**: All email communications use TLS encryption

## Troubleshooting

### Common Issues

**1. "Email configuration incomplete"**
- Ensure `email_username` and `email_password` are set
- Verify you're using an app password, not your regular password

**2. "Authentication failed"**
- Double-check your app password
- Ensure 2-factor authentication is enabled in Gmail
- Try generating a new app password

**3. "SMTP connection failed"**
- Check your internet connection
- Verify SMTP settings (smtp.gmail.com:587)
- Ensure TLS is supported

**4. "No emails received"**
- Check spam/junk folder
- Verify rate limiting hasn't blocked the email
- Check if you're in quiet hours (10 PM - 8 AM)

### Debug Steps

1. **Check configuration:**
   ```bash
   python test_email_alert.py
   ```

2. **Verify credentials:**
   - Test login to Gmail with your app password
   - Ensure app password hasn't expired

3. **Check logs:**
   - Look for error messages in the application logs
   - Enable debug mode for detailed SMTP logging

## Alternative Email Providers

While this guide focuses on Gmail, you can configure other email providers:

### Outlook/Hotmail
```python
email_config = {
    'email_smtp_server': 'smtp-mail.outlook.com',
    'email_smtp_port': 587,
    # ... other settings
}
```

### Yahoo Mail
```python
email_config = {
    'email_smtp_server': 'smtp.mail.yahoo.com',
    'email_smtp_port': 587,
    # ... other settings
}
```

## Best Practices

1. **Use Dedicated Email**: Consider using a dedicated email account for price alerts
2. **Regular Testing**: Test email functionality monthly to ensure it's working
3. **Monitor Rate Limits**: Adjust thresholds if you receive too many/few emails
4. **Backup Configuration**: Export your settings regularly
5. **Security Updates**: Regenerate app passwords periodically

## Support

If you encounter issues:

1. Check this troubleshooting guide first
2. Run the test script for diagnostics
3. Check application logs for error messages
4. Verify your Gmail settings and app password

For additional help, consult the main README.md or create an issue in the project repository.