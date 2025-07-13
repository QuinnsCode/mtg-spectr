#!/usr/bin/env python3
"""
Test email alert functionality for MTG Price Tracker.
This script tests the email notification system without requiring actual email credentials.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mtg_card_pricing.services.alert_system import AlertSystem, PriceTrendAlert

def test_email_alert_system():
    """Test the email alert system functionality."""
    
    print("Testing email alert system...")
    
    # Initialize alert system
    alert_system = AlertSystem()
    
    # Create a test alert
    test_data = {
        'card_name': 'Lightning Bolt',
        'set_code': 'LEA',
        'percentage_change': 25.5,
        'absolute_change': 2.50,
        'price_current': 12.50,
        'is_foil': False,
        'alert_score': 75
    }
    
    alert = PriceTrendAlert(
        test_data['card_name'],
        test_data['set_code'],
        test_data
    )
    
    # Test email body creation
    print("\n--- Testing email body creation ---")
    email_body = alert_system._create_email_body(alert)
    print("Email body:")
    print(email_body)
    
    # Test email rate limiting
    print("\n--- Testing email rate limiting ---")
    print(f"Current email count: {alert_system.email_counts['hour']}")
    print(f"Max emails per hour: {alert_system.config.max_emails_per_hour}")
    
    # Update email count to simulate rate limiting
    alert_system._update_email_hourly_count()
    print(f"Email count after update: {alert_system.email_counts['hour']}")
    
    # Test configuration
    print("\n--- Testing email configuration ---")
    print(f"Email enabled: {alert_system.config.email_enabled}")
    print(f"Email address: {alert_system.config.email_address}")
    print(f"SMTP server: {alert_system.config.email_smtp_server}")
    print(f"SMTP port: {alert_system.config.email_smtp_port}")
    print(f"Max emails per hour: {alert_system.config.max_emails_per_hour}")
    
    # Test alert processing (will skip actual email sending due to missing credentials)
    print("\n--- Testing alert processing ---")
    try:
        result = alert_system.process_trend_alert(test_data)
        print(f"Alert processed successfully: {result}")
    except Exception as e:
        print(f"Error processing alert: {e}")
    
    print("\n--- Email Alert System Test Complete ---")
    print("Note: Actual email sending will require valid SMTP credentials.")
    print("Configure email_username and email_password in the alert system settings.")

if __name__ == "__main__":
    test_email_alert_system()