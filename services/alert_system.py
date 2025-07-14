"""
Alert system for MTG card price trend notifications.

This module handles various types of alerts including system tray notifications,
desktop notifications, and optional email alerts for price trend monitoring.
"""

import logging
import smtplib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
try:
    from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
    from PySide6.QtCore import QObject, Signal, QTimer
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
except ImportError:
    # Fallback for testing without GUI
    class QObject:
        pass
    def Signal(*args):
        def decorator(func):
            return func
        return decorator
    class QTimer:
        def __init__(self):
            pass
        def start(self, ms):
            pass
        def stop(self):
            pass
        timeout = Signal()
    class QSystemTrayIcon:
        @staticmethod
        def isSystemTrayAvailable():
            return False
    class QColor:
        def __init__(self, *args):
            pass
    class QIcon:
        def __init__(self, *args):
            pass
    class QPixmap:
        def __init__(self, *args):
            pass
        def fill(self, *args):
            pass
    class QPainter:
        def __init__(self, *args):
            pass
        def setRenderHint(self, *args):
            pass
        def setBrush(self, *args):
            pass
        def setPen(self, *args):
            pass
        def drawEllipse(self, *args):
            pass
        def setFont(self, *args):
            pass
        def drawText(self, *args):
            pass
        def end(self):
            pass
        Antialiasing = None
    class QFont:
        def __init__(self, *args):
            pass
        Bold = None

from data.trend_database import TrendDatabase

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """Types of alerts."""
    SYSTEM_TRAY = "system_tray"
    DESKTOP_NOTIFICATION = "desktop_notification"
    SOUND = "sound"
    EMAIL = "email"

class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AlertConfig:
    """Configuration for alert system."""
    enabled: bool = True
    system_tray_enabled: bool = True
    desktop_notifications_enabled: bool = True
    sound_enabled: bool = False
    email_enabled: bool = False
    email_address: str = ""
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    min_alert_interval_minutes: int = 15  # Minimum time between same card alerts
    max_alerts_per_hour: int = 10
    max_emails_per_hour: int = 1  # Maximum emails per hour
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 8     # 8 AM

class PriceTrendAlert:
    """Represents a price trend alert."""
    
    def __init__(self, card_name: str, set_code: str, alert_data: Dict):
        self.card_name = card_name
        self.set_code = set_code
        self.alert_data = alert_data
        self.timestamp = datetime.now()
        self.priority = self._calculate_priority()
    
    def _calculate_priority(self) -> AlertPriority:
        """Calculate alert priority based on trend data."""
        percentage_change = abs(self.alert_data.get('percentage_change', 0))
        alert_score = self.alert_data.get('alert_score', 0)
        
        if percentage_change >= 100 or alert_score >= 90:
            return AlertPriority.CRITICAL
        elif percentage_change >= 50 or alert_score >= 75:
            return AlertPriority.HIGH
        elif percentage_change >= 25 or alert_score >= 60:
            return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW
    
    def get_title(self) -> str:
        """Get alert title."""
        change_pct = self.alert_data.get('percentage_change', 0)
        return f"Price Alert: {self.card_name} (+{change_pct:.1f}%)"
    
    def get_message(self) -> str:
        """Get alert message."""
        price_current = self.alert_data.get('price_current', 0)
        change_pct = self.alert_data.get('percentage_change', 0)
        change_abs = self.alert_data.get('absolute_change', 0)
        foil_text = " (Foil)" if self.alert_data.get('is_foil', False) else ""
        
        return (f"{self.card_name} ({self.set_code}){foil_text}\n"
                f"Current: ${price_current:.2f}\n"
                f"Change: +{change_pct:.1f}% (+${change_abs:.2f})")

class AlertSystem(QObject):
    """Comprehensive alert system for price trend notifications."""
    
    alert_triggered = Signal(dict)  # Emitted when an alert is triggered
    
    def __init__(self):
        super().__init__()
        
        self.config = AlertConfig()
        self.trend_db = TrendDatabase()
        
        # Alert tracking
        self.recent_alerts: List[PriceTrendAlert] = []
        self.alert_counts = {'hour': 0, 'last_hour_reset': datetime.now()}
        self.email_counts = {'hour': 0, 'last_hour_reset': datetime.now()}
        
        # System tray icon
        self.tray_icon = None
        self._init_system_tray()
        
        # Cleanup timer
        self.cleanup_timer = QTimer()
        
        # Only connect signal if it exists (GUI mode)
        if hasattr(self.cleanup_timer.timeout, 'connect'):
            self.cleanup_timer.timeout.connect(self._cleanup_old_alerts)
            self.cleanup_timer.start(300000)  # Clean up every 5 minutes
        
        # Load configuration
        self._load_config()
    
    def _init_system_tray(self):
        """Initialize system tray icon."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray is not available")
            return
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        
        # Create icon (simple colored circle)
        icon = self._create_tray_icon()
        self.tray_icon.setIcon(icon)
        
        # Create context menu
        menu = QMenu()
        
        show_action = menu.addAction("Show MTG Price Tracker")
        show_action.triggered.connect(self._show_main_window)
        
        menu.addSeparator()
        
        alerts_action = menu.addAction("View Alerts")
        alerts_action.triggered.connect(self._show_alerts)
        
        settings_action = menu.addAction("Alert Settings")
        settings_action.triggered.connect(self._show_alert_settings)
        
        menu.addSeparator()
        
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip("MTG Card Price Tracker")
        
        # Show tray icon
        if self.config.system_tray_enabled:
            self.tray_icon.show()
    
    def _create_tray_icon(self, color: QColor = QColor(0, 150, 0)) -> QIcon:
        """Create a simple tray icon."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(color)
        painter.setPen(QColor(0, 0, 0))
        painter.drawEllipse(2, 2, 12, 12)
        
        # Add "$" symbol
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.drawText(5, 11, "$")
        
        painter.end()
        
        return QIcon(pixmap)
    
    def process_trend_alert(self, trend_data: Dict) -> bool:
        """Process a new trend alert."""
        if not self.config.enabled:
            return False
        
        # Create alert object
        alert = PriceTrendAlert(
            trend_data.get('card_name', ''),
            trend_data.get('set_code', ''),
            trend_data
        )
        
        # Check if we should show this alert
        if not self._should_show_alert(alert):
            return False
        
        # Add to recent alerts
        self.recent_alerts.append(alert)
        
        # Increment hourly count
        self._update_hourly_count()
        
        # Show alerts based on configuration
        self._show_alert(alert)
        
        # Emit signal (if available)
        if hasattr(self.alert_triggered, 'emit'):
            self.alert_triggered.emit(trend_data)
        
        logger.info(f"Alert triggered for {alert.card_name} ({alert.set_code})")
        return True
    
    def _should_show_alert(self, alert: PriceTrendAlert) -> bool:
        """Determine if an alert should be shown."""
        # Check if alerts are enabled
        if not self.config.enabled:
            return False
        
        # Check quiet hours
        if self._is_quiet_hours():
            return False
        
        # Check hourly limit
        if self.alert_counts['hour'] >= self.config.max_alerts_per_hour:
            return False
        
        # Check for recent duplicate alerts
        cutoff_time = datetime.now() - timedelta(minutes=self.config.min_alert_interval_minutes)
        for recent_alert in self.recent_alerts:
            if (recent_alert.card_name == alert.card_name and 
                recent_alert.set_code == alert.set_code and
                recent_alert.timestamp > cutoff_time):
                return False
        
        return True
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        current_hour = datetime.now().hour
        start = self.config.quiet_hours_start
        end = self.config.quiet_hours_end
        
        if start <= end:
            return start <= current_hour < end
        else:  # Quiet hours span midnight
            return current_hour >= start or current_hour < end
    
    def _update_hourly_count(self):
        """Update hourly alert count."""
        now = datetime.now()
        last_reset = self.alert_counts['last_hour_reset']
        
        # Reset count if it's been an hour
        if (now - last_reset).total_seconds() >= 3600:
            self.alert_counts['hour'] = 0
            self.alert_counts['last_hour_reset'] = now
        
        self.alert_counts['hour'] += 1
    
    def _show_alert(self, alert: PriceTrendAlert):
        """Show alert using configured methods."""
        # System tray notification
        if self.config.system_tray_enabled and self.tray_icon:
            self.tray_icon.showMessage(
                alert.get_title(),
                alert.get_message(),
                QSystemTrayIcon.Information,
                5000  # 5 seconds
            )
            
            # Change tray icon color based on priority
            if alert.priority == AlertPriority.CRITICAL:
                icon = self._create_tray_icon(QColor(255, 0, 0))  # Red
            elif alert.priority == AlertPriority.HIGH:
                icon = self._create_tray_icon(QColor(255, 165, 0))  # Orange
            else:
                icon = self._create_tray_icon(QColor(0, 150, 0))  # Green
            
            self.tray_icon.setIcon(icon)
            
            # Reset icon after 10 seconds
            QTimer.singleShot(10000, lambda: self.tray_icon.setIcon(self._create_tray_icon()))
        
        # Desktop notification (platform-specific)
        if self.config.desktop_notifications_enabled:
            self._show_desktop_notification(alert)
        
        # Email notification
        if self.config.email_enabled:
            self._send_email_alert(alert)
    
    def _show_desktop_notification(self, alert: PriceTrendAlert):
        """Show platform-specific desktop notification."""
        try:
            import plyer
            plyer.notification.notify(
                title=alert.get_title(),
                message=alert.get_message(),
                app_name="MTG Price Tracker",
                timeout=10
            )
        except ImportError:
            logger.warning("plyer not available for desktop notifications")
        except Exception as e:
            logger.error(f"Error showing desktop notification: {e}")
    
    def _send_email_alert(self, alert: PriceTrendAlert):
        """Send email alert notification."""
        if not self.config.email_address or not self.config.email_username or not self.config.email_password:
            logger.warning("Email configuration incomplete, skipping email alert")
            return
        
        # Check email rate limit
        self._update_email_hourly_count()
        if self.email_counts['hour'] >= self.config.max_emails_per_hour:
            logger.info(f"Email rate limit reached ({self.config.max_emails_per_hour}/hour), skipping email alert")
            return
        
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.config.email_username
            msg['To'] = self.config.email_address
            msg['Subject'] = f"MTG Price Alert: {alert.card_name}"
            
            # Create email body
            body = self._create_email_body(alert)
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port)
            server.starttls()
            server.login(self.config.email_username, self.config.email_password)
            
            text = msg.as_string()
            server.sendmail(self.config.email_username, self.config.email_address, text)
            server.quit()
            
            # Update email count
            self.email_counts['hour'] += 1
            logger.info(f"Email alert sent to {self.config.email_address}")
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def _create_email_body(self, alert: PriceTrendAlert) -> str:
        """Create email body for alert notification."""
        price_current = alert.alert_data.get('price_current', 0)
        change_pct = alert.alert_data.get('percentage_change', 0)
        change_abs = alert.alert_data.get('absolute_change', 0)
        foil_text = " (Foil)" if alert.alert_data.get('is_foil', False) else ""
        
        body = f"""MTG Card Price Alert
        
Card: {alert.card_name} ({alert.set_code}){foil_text}
Current Price: ${price_current:.2f}
Price Change: +{change_pct:.1f}% (+${change_abs:.2f})
Alert Priority: {alert.priority.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from your MTG Card Price Tracker.
"""
        return body
    
    def _update_email_hourly_count(self):
        """Update hourly email count."""
        now = datetime.now()
        last_reset = self.email_counts['last_hour_reset']
        
        # Reset count if it's been an hour
        if (now - last_reset).total_seconds() >= 3600:
            self.email_counts['hour'] = 0
            self.email_counts['last_hour_reset'] = now
    
    def _cleanup_old_alerts(self):
        """Clean up old alerts from memory."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.recent_alerts = [
            alert for alert in self.recent_alerts 
            if alert.timestamp > cutoff_time
        ]
    
    def _show_main_window(self):
        """Show main application window."""
        # This would be connected to the main window show method
        logger.info("Request to show main window")
    
    def _show_alerts(self):
        """Show alerts window/tab."""
        # This would switch to the alerts tab
        logger.info("Request to show alerts")
    
    def _show_alert_settings(self):
        """Show alert settings dialog."""
        # This would open alert settings
        logger.info("Request to show alert settings")
    
    def _load_config(self):
        """Load alert configuration from database."""
        try:
            # Load configuration values
            config_mapping = {
                'alert_system_enabled': 'enabled',
                'alert_system_tray_enabled': 'system_tray_enabled',
                'alert_desktop_enabled': 'desktop_notifications_enabled',
                'alert_sound_enabled': 'sound_enabled',
                'alert_email_enabled': 'email_enabled',
                'alert_email_address': 'email_address',
                'alert_email_smtp_server': 'email_smtp_server',
                'alert_email_smtp_port': 'email_smtp_port',
                'alert_email_username': 'email_username',
                'alert_email_password': 'email_password',
                'alert_min_interval': 'min_alert_interval_minutes',
                'alert_max_per_hour': 'max_alerts_per_hour',
                'alert_max_emails_per_hour': 'max_emails_per_hour',
                'alert_quiet_start': 'quiet_hours_start',
                'alert_quiet_end': 'quiet_hours_end'
            }
            
            for db_key, config_attr in config_mapping.items():
                saved_value = self.trend_db.get_config_value(db_key)
                if saved_value:
                    # Convert to appropriate type
                    if config_attr in ['enabled', 'system_tray_enabled', 'desktop_notifications_enabled', 
                                     'sound_enabled', 'email_enabled']:
                        setattr(self.config, config_attr, saved_value.lower() == 'true')
                    elif config_attr in ['min_alert_interval_minutes', 'max_alerts_per_hour', 'max_emails_per_hour',
                                       'quiet_hours_start', 'quiet_hours_end', 'email_smtp_port']:
                        setattr(self.config, config_attr, int(saved_value))
                    else:
                        setattr(self.config, config_attr, saved_value)
        except Exception as e:
            logger.error(f"Error loading alert config: {e}")
    
    def update_config(self, **kwargs):
        """Update alert configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                
                # Save to database
                db_key = f"alert_{key}"
                self.trend_db.set_config_value(db_key, str(value))
                
                logger.info(f"Updated alert config: {key} = {value}")
                
                # Apply changes immediately
                if key == 'system_tray_enabled':
                    if value and self.tray_icon:
                        self.tray_icon.show()
                    elif self.tray_icon:
                        self.tray_icon.hide()
    
    def get_recent_alerts(self, hours: int = 24) -> List[PriceTrendAlert]:
        """Get recent alerts from the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.recent_alerts 
            if alert.timestamp > cutoff_time
        ]
    
    def get_alert_statistics(self) -> Dict:
        """Get alert system statistics."""
        recent_24h = self.get_recent_alerts(24)
        recent_1h = self.get_recent_alerts(1)
        
        priority_counts = {priority.value: 0 for priority in AlertPriority}
        for alert in recent_24h:
            priority_counts[alert.priority.value] += 1
        
        return {
            'total_alerts_24h': len(recent_24h),
            'total_alerts_1h': len(recent_1h),
            'alerts_this_hour': self.alert_counts['hour'],
            'priority_breakdown': priority_counts,
            'system_tray_available': QSystemTrayIcon.isSystemTrayAvailable(),
            'config': {
                'enabled': self.config.enabled,
                'system_tray_enabled': self.config.system_tray_enabled,
                'desktop_notifications_enabled': self.config.desktop_notifications_enabled,
                'max_alerts_per_hour': self.config.max_alerts_per_hour,
                'quiet_hours': f"{self.config.quiet_hours_start:02d}:00-{self.config.quiet_hours_end:02d}:00"
            }
        }
    
    def test_alert(self):
        """Send a test alert for configuration testing."""
        test_data = {
            'card_name': 'Lightning Bolt',
            'set_code': 'LEA',
            'percentage_change': 25.5,
            'absolute_change': 2.50,
            'price_current': 12.50,
            'is_foil': False,
            'alert_score': 75
        }
        
        self.process_trend_alert(test_data)
    
    def cleanup(self):
        """Cleanup alert system resources."""
        if self.tray_icon:
            self.tray_icon.hide()
        
        self.cleanup_timer.stop()