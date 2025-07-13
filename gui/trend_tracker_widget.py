"""
GUI widget for the MTG Card Price Trend Tracker.

This widget provides a comprehensive interface for monitoring price trends,
viewing alerts, and configuring the background monitoring service.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QGroupBox, QProgressBar, QTextEdit,
    QSplitter, QFrame, QGridLayout, QScrollArea, QMessageBox,
    QHeaderView, QAbstractItemView, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont

from services.price_monitor import PriceMonitorService
from data.trend_database import TrendDatabase
from gui.results_widget import ClickableCardItem, ClickableCardTable

logger = logging.getLogger(__name__)

class TrendStatsWidget(QWidget):
    """Widget displaying monitoring statistics."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QGridLayout(self)
        
        # Create stat labels
        self.stats_labels = {
            'status': QLabel("Status: Not Started"),
            'cards_processed': QLabel("Cards Processed: 0"),
            'prices_recorded': QLabel("Prices Recorded: 0"),
            'trends_detected': QLabel("Trends Detected: 0"),
            'alerts_generated': QLabel("Alerts Generated: 0"),
            'last_run': QLabel("Last Run: Never"),
            'next_run': QLabel("Next Run: Not Scheduled"),
            'db_size': QLabel("Database Size: 0 MB")
        }
        
        # Add labels to layout
        row = 0
        for key, label in self.stats_labels.items():
            label.setFont(QFont("Arial", 10))
            layout.addWidget(label, row // 2, row % 2)
            row += 1
    
    def update_stats(self, stats: Dict):
        """Update displayed statistics."""
        service_stats = stats.get('service_stats', {})
        
        # Update labels
        status = "Running" if service_stats.get('is_monitoring', False) else "Stopped"
        self.stats_labels['status'].setText(f"Status: {status}")
        
        self.stats_labels['cards_processed'].setText(f"Cards Processed: {service_stats.get('cards_processed', 0)}")
        self.stats_labels['prices_recorded'].setText(f"Prices Recorded: {service_stats.get('prices_recorded', 0)}")
        self.stats_labels['trends_detected'].setText(f"Trends Detected: {service_stats.get('trends_detected', 0)}")
        self.stats_labels['alerts_generated'].setText(f"Alerts Generated: {service_stats.get('alerts_generated', 0)}")
        
        # Format timestamps
        last_run = service_stats.get('last_run')
        if last_run:
            last_run_dt = datetime.fromisoformat(last_run)
            self.stats_labels['last_run'].setText(f"Last Run: {last_run_dt.strftime('%Y-%m-%d %H:%M')}")
        
        next_run = service_stats.get('next_run')
        if next_run:
            next_run_dt = datetime.fromisoformat(next_run)
            self.stats_labels['next_run'].setText(f"Next Run: {next_run_dt.strftime('%Y-%m-%d %H:%M')}")
        
        # Database stats
        db_size = stats.get('database_size_mb', 0)
        self.stats_labels['db_size'].setText(f"Database Size: {db_size:.1f} MB")

class TrendConfigWidget(QWidget):
    """Widget for configuring trend monitoring settings."""
    
    config_changed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Monitoring Settings Group
        monitor_group = QGroupBox("Monitoring Settings")
        monitor_layout = QGridLayout(monitor_group)
        
        # Monitoring interval
        monitor_layout.addWidget(QLabel("Check Interval (hours):"), 0, 0)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 168)  # 1 hour to 1 week
        self.interval_spin.setValue(6)
        self.interval_spin.valueChanged.connect(self._on_config_changed)
        monitor_layout.addWidget(self.interval_spin, 0, 1)
        
        # Max cards per cycle
        monitor_layout.addWidget(QLabel("Max Cards per Cycle:"), 1, 0)
        self.max_cards_edit = QLineEdit()
        self.max_cards_edit.setText("1000")
        self.max_cards_edit.setPlaceholderText("Enter value (100-999999)")
        self.max_cards_edit.textChanged.connect(self._on_config_changed)
        monitor_layout.addWidget(self.max_cards_edit, 1, 1)
        
        layout.addWidget(monitor_group)
        
        # Alert Thresholds Group
        alert_group = QGroupBox("Alert Thresholds")
        alert_layout = QGridLayout(alert_group)
        
        # Minimum price threshold
        alert_layout.addWidget(QLabel("Minimum Price ($):"), 0, 0)
        self.min_price_spin = QDoubleSpinBox()
        self.min_price_spin.setRange(0.01, 100.0)
        self.min_price_spin.setValue(0.50)
        self.min_price_spin.setSingleStep(0.25)
        self.min_price_spin.valueChanged.connect(self._on_config_changed)
        alert_layout.addWidget(self.min_price_spin, 0, 1)
        
        # Percentage threshold
        alert_layout.addWidget(QLabel("Percentage Change (%):"), 1, 0)
        self.percentage_spin = QDoubleSpinBox()
        self.percentage_spin.setRange(5.0, 500.0)
        self.percentage_spin.setValue(50.0)
        self.percentage_spin.setSingleStep(5.0)
        self.percentage_spin.valueChanged.connect(self._on_config_changed)
        alert_layout.addWidget(self.percentage_spin, 1, 1)
        
        layout.addWidget(alert_group)
        
        # Cleanup Settings Group
        cleanup_group = QGroupBox("Data Management")
        cleanup_layout = QGridLayout(cleanup_group)
        
        # Auto cleanup days
        cleanup_layout.addWidget(QLabel("Keep Data (days):"), 0, 0)
        self.cleanup_spin = QSpinBox()
        self.cleanup_spin.setRange(7, 365)
        self.cleanup_spin.setValue(30)
        self.cleanup_spin.valueChanged.connect(self._on_config_changed)
        cleanup_layout.addWidget(self.cleanup_spin, 0, 1)
        
        layout.addWidget(cleanup_group)
        
        layout.addStretch()
    
    def _on_config_changed(self):
        """Emit config changed signal with current values."""
        try:
            max_cards_text = self.max_cards_edit.text()
            max_cards_value = int(max_cards_text) if max_cards_text.isdigit() else 1000
            max_cards_value = max(100, min(999999, max_cards_value))  # Clamp to valid range
        except (ValueError, AttributeError):
            max_cards_value = 1000
            
        config = {
            'monitoring_interval_hours': self.interval_spin.value(),
            'max_cards_per_cycle': max_cards_value,
            'min_price_threshold': self.min_price_spin.value(),
            'percentage_alert_threshold': self.percentage_spin.value(),
            'auto_cleanup_days': self.cleanup_spin.value()
        }
        self.config_changed.emit(config)
    
    def load_config(self, config: Dict):
        """Load configuration values into the UI."""
        self.interval_spin.setValue(config.get('monitoring_interval_hours', 6))
        self.max_cards_edit.setText(str(config.get('max_cards_per_cycle', 1000)))
        self.min_price_spin.setValue(config.get('min_price_threshold', 0.50))
        self.percentage_spin.setValue(config.get('percentage_alert_threshold', 50.0))
        self.cleanup_spin.setValue(config.get('auto_cleanup_days', 30))

class TrendTrackerWidget(QWidget):
    """Main widget for the price trend tracker."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.monitor_service = PriceMonitorService()
        self.trend_db = TrendDatabase()
        
        # Connect signals
        self._connect_signals()
        
        # Initialize UI
        self._init_ui()
        
        # Load initial data
        self._load_initial_data()
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Control Panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Main Content (Tabs)
        self.tab_widget = QTabWidget()
        
        # Trending Cards Tab
        self.trending_tab = self._create_trending_tab()
        self.tab_widget.addTab(self.trending_tab, "Trending Cards")
        
        # Active Alerts Tab
        self.alerts_tab = self._create_alerts_tab()
        self.tab_widget.addTab(self.alerts_tab, "Active Alerts")
        
        # Statistics Tab
        self.stats_tab = self._create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "Statistics")
        
        # Configuration Tab
        self.config_tab = self._create_config_tab()
        self.tab_widget.addTab(self.config_tab, "Configuration")
        
        layout.addWidget(self.tab_widget)
    
    def _create_control_panel(self) -> QWidget:
        """Create the main control panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(panel)
        
        # Start/Stop buttons
        self.start_btn = QPushButton("Start Monitoring")
        self.start_btn.clicked.connect(self._start_monitoring)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Monitoring")
        self.stop_btn.clicked.connect(self._stop_monitoring)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        # Force refresh button
        self.refresh_btn = QPushButton("Force Refresh")
        self.refresh_btn.clicked.connect(self._force_refresh)
        layout.addWidget(self.refresh_btn)
        
        # Status indicator
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def _create_trending_tab(self) -> QWidget:
        """Create the trending cards tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info label
        info_label = QLabel("Cards showing significant upward price trends:")
        layout.addWidget(info_label)
        
        # Trending cards table
        self.trending_table = ClickableCardTable()
        self.trending_table.setColumnCount(8)
        self.trending_table.setHorizontalHeaderLabels([
            "Card Name", "Set", "Current Price", "Start Price", 
            "Change %", "Change $", "Duration", "Alert Score"
        ])
        
        header = self.trending_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Card name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Set
        for i in range(2, 8):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.trending_table)
        
        return widget
    
    def _create_alerts_tab(self) -> QWidget:
        """Create the active alerts tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info label
        info_label = QLabel("Active price trend alerts:")
        layout.addWidget(info_label)
        
        # Alerts table
        self.alerts_table = ClickableCardTable()
        self.alerts_table.setColumnCount(9)
        self.alerts_table.setHorizontalHeaderLabels([
            "Card Name", "Set", "Foil", "Current Price", "Start Price",
            "Change %", "Change $", "First Detected", "Actions"
        ])
        
        header = self.alerts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Card name
        for i in range(1, 9):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.alerts_table)
        
        # Clear all alerts button
        clear_btn = QPushButton("Clear All Alerts")
        clear_btn.clicked.connect(self._clear_all_alerts)
        layout.addWidget(clear_btn)
        
        return widget
    
    def _create_stats_tab(self) -> QWidget:
        """Create the statistics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Statistics widget
        self.stats_widget = TrendStatsWidget()
        layout.addWidget(self.stats_widget)
        
        # Database info
        db_group = QGroupBox("Database Information")
        db_layout = QVBoxLayout(db_group)
        
        self.db_info_text = QTextEdit()
        self.db_info_text.setMaximumHeight(150)
        self.db_info_text.setReadOnly(True)
        db_layout.addWidget(self.db_info_text)
        
        layout.addWidget(db_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_config_tab(self) -> QWidget:
        """Create the configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configuration widget
        self.config_widget = TrendConfigWidget()
        self.config_widget.config_changed.connect(self._on_config_changed)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.config_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        return widget
    
    def _connect_signals(self):
        """Connect monitor service signals."""
        self.monitor_service.monitoring_started.connect(self._on_monitoring_started)
        self.monitor_service.monitoring_stopped.connect(self._on_monitoring_stopped)
        self.monitor_service.progress_updated.connect(self._on_progress_updated)
        self.monitor_service.trend_detected.connect(self._on_trend_detected)
        self.monitor_service.alert_generated.connect(self._on_alert_generated)
        self.monitor_service.error_occurred.connect(self._on_error_occurred)
        self.monitor_service.stats_updated.connect(self._on_stats_updated)
    
    def _load_initial_data(self):
        """Load initial data and configuration."""
        # Load configuration
        stats = self.monitor_service.get_monitoring_stats()
        config = stats.get('config', {})
        self.config_widget.load_config(config)
        
        # Load trending cards and alerts
        self._refresh_data()
    
    def _start_monitoring(self):
        """Start the monitoring service."""
        self.monitor_service.start_monitoring()
    
    def _stop_monitoring(self):
        """Stop the monitoring service."""
        self.monitor_service.stop_monitoring()
    
    def _force_refresh(self):
        """Force an immediate monitoring cycle."""
        self.monitor_service.force_monitoring_cycle()
    
    def _refresh_data(self):
        """Refresh displayed data."""
        self._load_trending_cards()
        self._load_active_alerts()
        self._update_statistics()
    
    def _load_trending_cards(self):
        """Load and display trending cards."""
        try:
            trending_cards = self.trend_db.find_trending_cards()
            
            self.trending_table.setRowCount(len(trending_cards))
            
            for row, card in enumerate(trending_cards):
                # Card name (clickable)
                card_item = ClickableCardItem(card['card_name'], card)
                self.trending_table.setItem(row, 0, card_item)
                
                # Set code
                self.trending_table.setItem(row, 1, QTableWidgetItem(card['set_code']))
                
                # Current price
                current_price = f"${card['price_current']:.2f}"
                if card.get('is_foil', False):
                    current_price += " (F)"
                self.trending_table.setItem(row, 2, QTableWidgetItem(current_price))
                
                # Start price
                self.trending_table.setItem(row, 3, QTableWidgetItem(f"${card['price_start']:.2f}"))
                
                # Percentage change (colored)
                pct_item = QTableWidgetItem(f"{card['percentage_change']:.1f}%")
                if card['percentage_change'] > 0:
                    pct_item.setForeground(QBrush(QColor(0, 150, 0)))  # Green for positive
                self.trending_table.setItem(row, 4, pct_item)
                
                # Absolute change
                abs_item = QTableWidgetItem(f"${card['absolute_change']:.2f}")
                if card['absolute_change'] > 0:
                    abs_item.setForeground(QBrush(QColor(0, 150, 0)))
                self.trending_table.setItem(row, 5, abs_item)
                
                # Duration
                duration_hours = card.get('duration_hours', 0)
                if duration_hours < 24:
                    duration_text = f"{duration_hours:.1f}h"
                else:
                    duration_text = f"{duration_hours/24:.1f}d"
                self.trending_table.setItem(row, 6, QTableWidgetItem(duration_text))
                
                # Alert score (if available)
                alert_score = card.get('alert_score', 0)
                self.trending_table.setItem(row, 7, QTableWidgetItem(f"{alert_score:.0f}"))
                
        except Exception as e:
            logger.error(f"Error loading trending cards: {e}")
    
    def _load_active_alerts(self):
        """Load and display active alerts."""
        try:
            alerts = self.trend_db.get_active_alerts()
            
            self.alerts_table.setRowCount(len(alerts))
            
            for row, alert in enumerate(alerts):
                # Card name (clickable)
                card_data = {
                    'name': alert['card_name'],
                    'set': alert['set_code']
                }
                card_item = ClickableCardItem(alert['card_name'], card_data)
                self.alerts_table.setItem(row, 0, card_item)
                
                # Set code
                self.alerts_table.setItem(row, 1, QTableWidgetItem(alert['set_code']))
                
                # Foil status
                foil_text = "Yes" if alert['is_foil'] else "No"
                self.alerts_table.setItem(row, 2, QTableWidgetItem(foil_text))
                
                # Current price
                self.alerts_table.setItem(row, 3, QTableWidgetItem(f"${alert['price_current']:.2f}"))
                
                # Start price
                self.alerts_table.setItem(row, 4, QTableWidgetItem(f"${alert['price_start']:.2f}"))
                
                # Percentage change
                pct_item = QTableWidgetItem(f"{alert['percentage_change']:.1f}%")
                pct_item.setForeground(QBrush(QColor(0, 150, 0)))
                self.alerts_table.setItem(row, 5, pct_item)
                
                # Absolute change
                abs_item = QTableWidgetItem(f"${alert['absolute_change']:.2f}")
                abs_item.setForeground(QBrush(QColor(0, 150, 0)))
                self.alerts_table.setItem(row, 6, abs_item)
                
                # First detected
                first_detected = datetime.fromisoformat(alert['first_detected'])
                self.alerts_table.setItem(row, 7, QTableWidgetItem(
                    first_detected.strftime('%m/%d %H:%M')
                ))
                
                # Dismiss button
                dismiss_btn = QPushButton("Dismiss")
                dismiss_btn.clicked.connect(lambda checked, aid=alert['id']: self._dismiss_alert(aid))
                self.alerts_table.setCellWidget(row, 8, dismiss_btn)
                
        except Exception as e:
            logger.error(f"Error loading alerts: {e}")
    
    def _update_statistics(self):
        """Update statistics display."""
        try:
            stats = self.monitor_service.get_monitoring_stats()
            self.stats_widget.update_stats(stats)
            
            # Update database info
            db_info = f"""
Total Price Snapshots: {stats.get('total_snapshots', 0)}
Active Alerts: {stats.get('active_alerts', 0)}
Earliest Data: {stats.get('earliest_data', 'None')}
Latest Data: {stats.get('latest_data', 'None')}
Database Size: {stats.get('database_size_mb', 0):.1f} MB
            """.strip()
            
            self.db_info_text.setPlainText(db_info)
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def _dismiss_alert(self, alert_id: int):
        """Dismiss a specific alert."""
        if self.trend_db.dismiss_alert(alert_id):
            self._load_active_alerts()  # Refresh alerts table
        else:
            QMessageBox.warning(self, "Error", "Failed to dismiss alert")
    
    def _clear_all_alerts(self):
        """Clear all active alerts."""
        reply = QMessageBox.question(
            self, "Clear All Alerts",
            "Are you sure you want to clear all active alerts?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            alerts = self.trend_db.get_active_alerts()
            for alert in alerts:
                self.trend_db.dismiss_alert(alert['id'])
            self._load_active_alerts()
    
    def _on_config_changed(self, config: Dict):
        """Handle configuration changes."""
        self.monitor_service.update_config(**config)
        # Refresh the GUI to show the updated configuration
        self._refresh_config_display()
    
    def _refresh_config_display(self):
        """Refresh the configuration display to show current values."""
        stats = self.monitor_service.get_monitoring_stats()
        config = stats.get('config', {})
        self.config_widget.load_config(config)
    
    def _on_monitoring_started(self):
        """Handle monitoring started signal."""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
    
    def _on_monitoring_stopped(self):
        """Handle monitoring stopped signal."""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.progress_bar.setVisible(False)
    
    def _on_progress_updated(self, status: str, current: int, total: int):
        """Handle progress update signal."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Status: {status}")
    
    def _on_trend_detected(self, trend_data: Dict):
        """Handle trend detected signal."""
        # Refresh trending cards table
        self._load_trending_cards()
    
    def _on_alert_generated(self, alert_data: Dict):
        """Handle alert generated signal."""
        # Refresh alerts table
        self._load_active_alerts()
        
        # Show notification (optional)
        card_name = alert_data.get('card_name', 'Unknown')
        change_pct = alert_data.get('percentage_change', 0)
        QMessageBox.information(
            self, "Price Alert",
            f"New trend alert: {card_name} is up {change_pct:.1f}%"
        )
    
    def _on_error_occurred(self, error_message: str):
        """Handle error signal."""
        QMessageBox.warning(self, "Monitoring Error", f"Error: {error_message}")
    
    def _on_stats_updated(self, stats: Dict):
        """Handle stats updated signal."""
        # Stats are updated automatically by the refresh timer
        pass