#!/usr/bin/env python3
"""
Configure email notifications for MTG Price Tracker.
This script sets up email notifications to send to shmikey@gmail.com with a 1 hour rate limit.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.services.alert_system import AlertSystem
from mtg_card_pricing.data.trend_database import TrendDatabase

def configure_email_notifications():
    """Configure email notifications for the alert system."""
    
    # Initialize database and alert system
    trend_db = TrendDatabase()
    alert_system = AlertSystem()
    
    # Configure email settings
    email_config = {
        'email_enabled': True,
        'email_address': 'shmikey@gmail.com',
        'email_smtp_server': 'smtp.gmail.com',
        'email_smtp_port': 587,
        'email_username': '',  # You'll need to set this
        'email_password': '',  # You'll need to set this (use app password for Gmail)
        'max_emails_per_hour': 1
    }
    
    # Update the alert system configuration
    alert_system.update_config(**email_config)
    
    print("Email notifications configured successfully!")
    print(f"Email address: {email_config['email_address']}")
    print(f"Rate limit: {email_config['max_emails_per_hour']} email(s) per hour")
    print()
    print("IMPORTANT: You still need to configure the email credentials:")
    print("1. Set email_username to your Gmail address")
    print("2. Set email_password to your Gmail app password (not your regular password)")
    print("3. Enable 2-factor authentication and create an app password in your Gmail settings")
    print()
    print("You can configure these settings through the GUI or by updating the database directly.")

if __name__ == "__main__":
    configure_email_notifications()