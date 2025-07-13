"""
Main window for the MTG Card Pricing Analysis Tool.
Provides the primary GUI interface with menu bar, toolbars, and widget containers.
"""

import sys
import logging
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QToolBar, QStatusBar, QLabel, QProgressBar,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QTextEdit,
    QApplication, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont, QAction

from config.settings import get_settings, SettingsManager
from data.database import DatabaseManager
from data.unified_api_client import UnifiedAPIClient, create_unified_client
from gui.search_widget import SearchWidget
from gui.results_widget import ResultsWidget
from gui.set_scanner_widget import SetScannerWidget
from gui.trend_tracker_widget import TrendTrackerWidget

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Settings configuration dialog."""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 600)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Set up the settings dialog UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different setting categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # API Settings Tab
        self.setup_api_tab()
        
        # Database Settings Tab
        self.setup_database_tab()
        
        # Analysis Settings Tab
        self.setup_analysis_tab()
        
        # GUI Settings Tab
        self.setup_gui_tab()
        
        # Trend Tracker Settings Tab
        self.setup_trend_tracker_tab()
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)
        layout.addWidget(button_box)
    
    def setup_api_tab(self):
        """Set up API settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key:", self.api_key_edit)
        
        self.base_url_edit = QLineEdit()
        layout.addRow("Base URL:", self.base_url_edit)
        
        self.rate_limit_minute_spin = QSpinBox()
        self.rate_limit_minute_spin.setRange(1, 1000)
        layout.addRow("Rate Limit (per minute):", self.rate_limit_minute_spin)
        
        self.rate_limit_hour_spin = QSpinBox()
        self.rate_limit_hour_spin.setRange(1, 10000)
        layout.addRow("Rate Limit (per hour):", self.rate_limit_hour_spin)
        
        self.request_timeout_spin = QSpinBox()
        self.request_timeout_spin.setRange(1, 300)
        layout.addRow("Request Timeout (seconds):", self.request_timeout_spin)
        
        self.use_mock_api_check = QCheckBox()
        layout.addRow("Use Mock API:", self.use_mock_api_check)
        
        self.tab_widget.addTab(widget, "API")
    
    def setup_database_tab(self):
        """Set up database settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.db_path_edit = QLineEdit()
        layout.addRow("Database Path:", self.db_path_edit)
        
        self.backup_enabled_check = QCheckBox()
        layout.addRow("Backup Enabled:", self.backup_enabled_check)
        
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 365)
        layout.addRow("Backup Interval (days):", self.backup_interval_spin)
        
        self.cleanup_days_spin = QSpinBox()
        self.cleanup_days_spin.setRange(1, 365)
        layout.addRow("Cleanup Old Data (days):", self.cleanup_days_spin)
        
        self.max_db_size_spin = QSpinBox()
        self.max_db_size_spin.setRange(1, 10000)
        layout.addRow("Max Database Size (MB):", self.max_db_size_spin)
        
        self.tab_widget.addTab(widget, "Database")
    
    def setup_analysis_tab(self):
        """Set up analysis settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.anomaly_method_combo = QComboBox()
        self.anomaly_method_combo.addItems(["iqr", "zscore", "isolation_forest"])
        layout.addRow("Anomaly Detection Method:", self.anomaly_method_combo)
        
        self.iqr_threshold_spin = QDoubleSpinBox()
        self.iqr_threshold_spin.setRange(0.1, 10.0)
        self.iqr_threshold_spin.setDecimals(1)
        layout.addRow("IQR Threshold:", self.iqr_threshold_spin)
        
        self.zscore_threshold_spin = QDoubleSpinBox()
        self.zscore_threshold_spin.setRange(0.1, 10.0)
        self.zscore_threshold_spin.setDecimals(1)
        layout.addRow("Z-Score Threshold:", self.zscore_threshold_spin)
        
        self.isolation_contamination_spin = QDoubleSpinBox()
        self.isolation_contamination_spin.setRange(0.01, 0.5)
        self.isolation_contamination_spin.setDecimals(2)
        layout.addRow("Isolation Forest Contamination:", self.isolation_contamination_spin)
        
        self.min_data_points_spin = QSpinBox()
        self.min_data_points_spin.setRange(1, 100)
        layout.addRow("Minimum Data Points:", self.min_data_points_spin)
        
        self.historical_days_spin = QSpinBox()
        self.historical_days_spin.setRange(1, 365)
        layout.addRow("Historical Days:", self.historical_days_spin)
        
        self.confidence_level_spin = QDoubleSpinBox()
        self.confidence_level_spin.setRange(0.5, 0.99)
        self.confidence_level_spin.setDecimals(2)
        layout.addRow("Confidence Level:", self.confidence_level_spin)
        
        self.tab_widget.addTab(widget, "Analysis")
    
    def setup_gui_tab(self):
        """Set up GUI settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "auto"])
        layout.addRow("Theme:", self.theme_combo)
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2000)
        layout.addRow("Window Width:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1500)
        layout.addRow("Window Height:", self.window_height_spin)
        
        self.font_family_edit = QLineEdit()
        layout.addRow("Font Family:", self.font_family_edit)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        layout.addRow("Font Size:", self.font_size_spin)
        
        self.show_tooltips_check = QCheckBox()
        layout.addRow("Show Tooltips:", self.show_tooltips_check)
        
        self.auto_refresh_spin = QSpinBox()
        self.auto_refresh_spin.setRange(30, 3600)
        layout.addRow("Auto Refresh Interval (seconds):", self.auto_refresh_spin)
        
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(10, 1000)
        layout.addRow("Max Search Results:", self.max_results_spin)
        
        self.tab_widget.addTab(widget, "GUI")
    
    def setup_trend_tracker_tab(self):
        """Set up trend tracker settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Monitoring settings
        self.monitoring_enabled_check = QCheckBox()
        layout.addRow("Enable Monitoring:", self.monitoring_enabled_check)
        
        self.monitoring_interval_spin = QSpinBox()
        self.monitoring_interval_spin.setRange(1, 168)  # 1 hour to 1 week
        self.monitoring_interval_spin.setSuffix(" hours")
        layout.addRow("Check Interval:", self.monitoring_interval_spin)
        
        self.max_cards_cycle_spin = QSpinBox()
        self.max_cards_cycle_spin.setRange(100, 999999)
        layout.addRow("Max Cards per Cycle:", self.max_cards_cycle_spin)
        
        # Alert thresholds
        self.min_price_spin = QDoubleSpinBox()
        self.min_price_spin.setRange(0.01, 100.0)
        self.min_price_spin.setPrefix("$")
        self.min_price_spin.setSingleStep(0.25)
        layout.addRow("Minimum Price:", self.min_price_spin)
        
        self.percentage_threshold_spin = QDoubleSpinBox()
        self.percentage_threshold_spin.setRange(5.0, 500.0)
        self.percentage_threshold_spin.setSuffix("%")
        self.percentage_threshold_spin.setSingleStep(5.0)
        layout.addRow("Percentage Alert Threshold:", self.percentage_threshold_spin)
        
        # Alert system settings
        self.alert_system_check = QCheckBox()
        layout.addRow("Enable Alerts:", self.alert_system_check)
        
        self.system_tray_check = QCheckBox()
        layout.addRow("System Tray Notifications:", self.system_tray_check)
        
        self.desktop_notifications_check = QCheckBox()
        layout.addRow("Desktop Notifications:", self.desktop_notifications_check)
        
        # Data management
        self.cleanup_days_trend_spin = QSpinBox()
        self.cleanup_days_trend_spin.setRange(7, 365)
        self.cleanup_days_trend_spin.setSuffix(" days")
        layout.addRow("Keep Trend Data:", self.cleanup_days_trend_spin)
        
        self.tab_widget.addTab(widget, "Trend Tracker")
    
    def load_settings(self):
        """Load current settings into the dialog."""
        settings = self.settings_manager.settings
        
        # API settings
        self.api_key_edit.setText(settings.api.justtcg_api_key or "")
        self.base_url_edit.setText(settings.api.justtcg_base_url)
        self.rate_limit_minute_spin.setValue(settings.api.rate_limit_per_minute)
        self.rate_limit_hour_spin.setValue(settings.api.rate_limit_per_hour)
        self.request_timeout_spin.setValue(settings.api.request_timeout)
        self.use_mock_api_check.setChecked(settings.api.use_mock_api)
        
        # Database settings
        self.db_path_edit.setText(settings.database.database_path)
        self.backup_enabled_check.setChecked(settings.database.backup_enabled)
        self.backup_interval_spin.setValue(settings.database.backup_interval_days)
        self.cleanup_days_spin.setValue(settings.database.cleanup_old_data_days)
        self.max_db_size_spin.setValue(settings.database.max_database_size_mb)
        
        # Analysis settings
        self.anomaly_method_combo.setCurrentText(settings.analysis.anomaly_detection_method)
        self.iqr_threshold_spin.setValue(settings.analysis.iqr_threshold)
        self.zscore_threshold_spin.setValue(settings.analysis.zscore_threshold)
        self.isolation_contamination_spin.setValue(settings.analysis.isolation_forest_contamination)
        self.min_data_points_spin.setValue(settings.analysis.minimum_data_points)
        self.historical_days_spin.setValue(settings.analysis.historical_days)
        self.confidence_level_spin.setValue(settings.analysis.confidence_level)
        
        # GUI settings
        self.theme_combo.setCurrentText(settings.gui.theme)
        self.window_width_spin.setValue(settings.gui.window_width)
        self.window_height_spin.setValue(settings.gui.window_height)
        self.font_family_edit.setText(settings.gui.font_family)
        self.font_size_spin.setValue(settings.gui.font_size)
        self.show_tooltips_check.setChecked(settings.gui.show_tooltips)
        self.auto_refresh_spin.setValue(settings.gui.auto_refresh_interval)
        self.max_results_spin.setValue(settings.gui.max_search_results)
        
        # Trend tracker settings
        self.monitoring_enabled_check.setChecked(settings.trend_tracker.monitoring_enabled)
        self.monitoring_interval_spin.setValue(settings.trend_tracker.monitoring_interval_hours)
        self.max_cards_cycle_spin.setValue(settings.trend_tracker.max_cards_per_cycle)
        self.min_price_spin.setValue(settings.trend_tracker.min_price_threshold)
        self.percentage_threshold_spin.setValue(settings.trend_tracker.percentage_alert_threshold)
        self.alert_system_check.setChecked(settings.trend_tracker.alert_system_enabled)
        self.system_tray_check.setChecked(settings.trend_tracker.system_tray_enabled)
        self.desktop_notifications_check.setChecked(settings.trend_tracker.desktop_notifications_enabled)
        self.cleanup_days_trend_spin.setValue(settings.trend_tracker.auto_cleanup_days)
    
    def save_settings(self):
        """Save settings from dialog to settings manager."""
        settings = self.settings_manager.settings
        
        # API settings
        settings.api.justtcg_api_key = self.api_key_edit.text() or None
        settings.api.justtcg_base_url = self.base_url_edit.text()
        settings.api.rate_limit_per_minute = self.rate_limit_minute_spin.value()
        settings.api.rate_limit_per_hour = self.rate_limit_hour_spin.value()
        settings.api.request_timeout = self.request_timeout_spin.value()
        settings.api.use_mock_api = self.use_mock_api_check.isChecked()
        
        # Database settings
        settings.database.database_path = self.db_path_edit.text()
        settings.database.backup_enabled = self.backup_enabled_check.isChecked()
        settings.database.backup_interval_days = self.backup_interval_spin.value()
        settings.database.cleanup_old_data_days = self.cleanup_days_spin.value()
        settings.database.max_database_size_mb = self.max_db_size_spin.value()
        
        # Analysis settings
        settings.analysis.anomaly_detection_method = self.anomaly_method_combo.currentText()
        settings.analysis.iqr_threshold = self.iqr_threshold_spin.value()
        settings.analysis.zscore_threshold = self.zscore_threshold_spin.value()
        settings.analysis.isolation_forest_contamination = self.isolation_contamination_spin.value()
        settings.analysis.minimum_data_points = self.min_data_points_spin.value()
        settings.analysis.historical_days = self.historical_days_spin.value()
        settings.analysis.confidence_level = self.confidence_level_spin.value()
        
        # GUI settings
        settings.gui.theme = self.theme_combo.currentText()
        settings.gui.window_width = self.window_width_spin.value()
        settings.gui.window_height = self.window_height_spin.value()
        settings.gui.font_family = self.font_family_edit.text()
        settings.gui.font_size = self.font_size_spin.value()
        settings.gui.show_tooltips = self.show_tooltips_check.isChecked()
        settings.gui.auto_refresh_interval = self.auto_refresh_spin.value()
        settings.gui.max_search_results = self.max_results_spin.value()
        
        # Trend tracker settings
        settings.trend_tracker.monitoring_enabled = self.monitoring_enabled_check.isChecked()
        settings.trend_tracker.monitoring_interval_hours = self.monitoring_interval_spin.value()
        settings.trend_tracker.max_cards_per_cycle = self.max_cards_cycle_spin.value()
        settings.trend_tracker.min_price_threshold = self.min_price_spin.value()
        settings.trend_tracker.percentage_alert_threshold = self.percentage_threshold_spin.value()
        settings.trend_tracker.alert_system_enabled = self.alert_system_check.isChecked()
        settings.trend_tracker.system_tray_enabled = self.system_tray_check.isChecked()
        settings.trend_tracker.desktop_notifications_enabled = self.desktop_notifications_check.isChecked()
        settings.trend_tracker.auto_cleanup_days = self.cleanup_days_trend_spin.value()
        
        self.settings_manager.save_settings()
    
    def restore_defaults(self):
        """Restore default settings."""
        self.settings_manager.reset_to_defaults()
        self.load_settings()
    
    def accept(self):
        """Accept dialog and save settings."""
        self.save_settings()
        super().accept()


class MainWindow(QMainWindow):
    """Main application window for the MTG Card Pricing Analysis Tool."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.settings_manager = get_settings()
        self.database_manager = DatabaseManager(self.settings_manager.get_database_path())
        
        # Initialize API client
        provider = getattr(self.settings_manager.settings.api, 'api_provider', 'scryfall')
        api_key = self.settings_manager.get_api_key() if provider == 'justtcg' else None
        use_mock = self.settings_manager.settings.api.use_mock_api
        
        self.api_client = create_unified_client(
            provider=provider,
            api_key=api_key,
            use_mock=use_mock
        )
        
        # Initialize UI
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_tool_bar()
        self.setup_status_bar()
        
        # Set up timers
        self.setup_timers()
        
        # Load initial data
        self.load_initial_data()
    
    def setup_ui(self):
        """Set up the main user interface."""
        self.setWindowTitle("MTG Card Pricing Analysis Tool")
        
        # Apply GUI settings
        settings = self.settings_manager.settings.gui
        self.resize(settings.window_width, settings.window_height)
        
        # Set application font
        font = QFont(settings.font_family, settings.font_size)
        self.setFont(font)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget for different functionality
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create card search tab
        search_tab = QWidget()
        search_layout = QVBoxLayout(search_tab)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        search_layout.addWidget(splitter)
        
        # Create search widget
        self.search_widget = SearchWidget(self.database_manager, self.api_client)
        splitter.addWidget(self.search_widget)
        
        # Create results widget
        self.results_widget = ResultsWidget(self.database_manager)
        splitter.addWidget(self.results_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Add search tab
        self.tab_widget.addTab(search_tab, "Card Search")
        
        # Create set scanner tab
        self.set_scanner_widget = SetScannerWidget(self.api_client)
        self.tab_widget.addTab(self.set_scanner_widget, "Set Scanner")
        
        # Create trend tracker tab
        self.trend_tracker_widget = TrendTrackerWidget()
        self.tab_widget.addTab(self.trend_tracker_widget, "Trend Tracker")
        
        # Connect signals
        self.search_widget.search_completed.connect(self.results_widget.display_results)
        self.search_widget.status_message.connect(self.show_status_message)
        self.results_widget.status_message.connect(self.show_status_message)
    
    def setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Import/Export actions
        import_action = QAction("Import Data...", self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        export_action = QAction("Export Data...", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        # Set scanner tool
        set_scanner_action = QAction("Set Scanner", self)
        set_scanner_action.setShortcut("Ctrl+S")
        set_scanner_action.triggered.connect(self.open_set_scanner)
        tools_menu.addAction(set_scanner_action)
        
        # Trend tracker tool
        trend_tracker_action = QAction("Trend Tracker", self)
        trend_tracker_action.setShortcut("Ctrl+T")
        trend_tracker_action.triggered.connect(self.open_trend_tracker)
        tools_menu.addAction(trend_tracker_action)
        
        tools_menu.addSeparator()
        
        # Database tools
        db_stats_action = QAction("Database Statistics", self)
        db_stats_action.triggered.connect(self.show_database_stats)
        tools_menu.addAction(db_stats_action)
        
        cleanup_action = QAction("Cleanup Old Data", self)
        cleanup_action.triggered.connect(self.cleanup_old_data)
        tools_menu.addAction(cleanup_action)
        
        tools_menu.addSeparator()
        
        # API tools
        test_api_action = QAction("Test API Connection", self)
        test_api_action.triggered.connect(self.test_api_connection)
        tools_menu.addAction(test_api_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_tool_bar(self):
        """Set up the tool bar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Search action
        search_action = QAction("Search", self)
        search_action.triggered.connect(self.search_widget.focus_search)
        toolbar.addAction(search_action)
        
        # Set scanner action
        set_scanner_action = QAction("Set Scanner", self)
        set_scanner_action.triggered.connect(self.open_set_scanner)
        toolbar.addAction(set_scanner_action)
        
        toolbar.addSeparator()
        
        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
    
    def setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Database status
        self.db_status_label = QLabel()
        self.status_bar.addPermanentWidget(self.db_status_label)
        
        # API status
        self.api_status_label = QLabel()
        self.status_bar.addPermanentWidget(self.api_status_label)
    
    def setup_timers(self):
        """Set up periodic timers."""
        # Auto-refresh timer
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
    
    def load_initial_data(self):
        """Load initial data and update status."""
        self.update_status()
        
        # Start auto-refresh if enabled
        interval = self.settings_manager.settings.gui.auto_refresh_interval
        if interval > 0:
            self.auto_refresh_timer.start(interval * 1000)
    
    def show_status_message(self, message: str, timeout: int = 5000):
        """Show a status message."""
        self.status_label.setText(message)
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.status_label.setText("Ready"))
    
    def show_progress(self, value: int, maximum: int = 100):
        """Show progress bar with value."""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(True)
        
        if value >= maximum:
            QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))
    
    def update_status(self):
        """Update status bar information."""
        # Database status
        try:
            stats = self.database_manager.get_database_stats()
            db_text = f"DB: {stats.get('total_records', 0)} records"
            self.db_status_label.setText(db_text)
        except Exception as e:
            self.db_status_label.setText("DB: Error")
            logger.error(f"Database status error: {e}")
        
        # API status
        try:
            if self.api_client.test_connection():
                self.api_status_label.setText("API: Connected")
            else:
                self.api_status_label.setText("API: Disconnected")
        except Exception as e:
            self.api_status_label.setText("API: Error")
            logger.error(f"API status error: {e}")
    
    def auto_refresh(self):
        """Perform auto-refresh of data."""
        self.show_status_message("Auto-refreshing data...")
        self.search_widget.refresh_current_search()
    
    def refresh_data(self):
        """Manually refresh data."""
        self.show_status_message("Refreshing data...")
        self.search_widget.refresh_current_search()
        self.update_status()
    
    def open_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec() == QDialog.Accepted:
            self.show_status_message("Settings saved")
            self.apply_settings()
    
    def apply_settings(self):
        """Apply changed settings."""
        # Update window size and font
        settings = self.settings_manager.settings.gui
        self.resize(settings.window_width, settings.window_height)
        
        font = QFont(settings.font_family, settings.font_size)
        self.setFont(font)
        
        # Update auto-refresh timer
        interval = settings.auto_refresh_interval
        if interval > 0:
            self.auto_refresh_timer.start(interval * 1000)
        else:
            self.auto_refresh_timer.stop()
        
        # Recreate API client if settings changed
        provider = getattr(self.settings_manager.settings.api, 'api_provider', 'scryfall')
        api_key = self.settings_manager.get_api_key() if provider == 'justtcg' else None
        use_mock = self.settings_manager.settings.api.use_mock_api
        
        self.api_client = create_unified_client(
            provider=provider,
            api_key=api_key,
            use_mock=use_mock
        )
        
        # Update widgets
        self.search_widget.update_api_client(self.api_client)
        
        # Update set scanner widget API client
        self.set_scanner_widget.api_client = self.api_client
        self.set_scanner_widget.scanner.api_client = self.api_client
    
    def open_set_scanner(self):
        """Open the set scanner tab."""
        self.tab_widget.setCurrentIndex(1)  # Set scanner is the second tab
        self.show_status_message("Set Scanner opened")
    
    def open_trend_tracker(self):
        """Open the trend tracker tab."""
        self.tab_widget.setCurrentIndex(2)  # Trend tracker is the third tab
        self.show_status_message("Trend Tracker opened")
    
    def import_data(self):
        """Import data from file."""
        # TODO: Implement data import functionality
        self.show_status_message("Data import not yet implemented")
    
    def export_data(self):
        """Export data to file."""
        # TODO: Implement data export functionality
        self.show_status_message("Data export not yet implemented")
    
    def show_database_stats(self):
        """Show database statistics dialog."""
        try:
            stats = self.database_manager.get_database_stats()
            
            message = f"""Database Statistics:
            
Total Records: {stats.get('total_records', 0)}
Unique Cards: {stats.get('unique_cards', 0)}
Unique Sets: {stats.get('unique_sets', 0)}
Latest Update: {stats.get('latest_update', 'None')}
Database Path: {self.settings_manager.get_database_path()}"""
            
            QMessageBox.information(self, "Database Statistics", message)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get database statistics: {e}")
    
    def cleanup_old_data(self):
        """Clean up old data from database."""
        try:
            days = self.settings_manager.settings.database.cleanup_old_data_days
            deleted = self.database_manager.cleanup_old_data(days)
            
            message = f"Cleaned up {deleted} old records (older than {days} days)"
            QMessageBox.information(self, "Cleanup Complete", message)
            
            self.update_status()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to cleanup old data: {e}")
    
    def test_api_connection(self):
        """Test API connection."""
        try:
            self.show_status_message("Testing API connection...")
            
            if self.api_client.test_connection():
                rate_limit = self.api_client.get_rate_limit_status()
                message = f"""API Connection Test: SUCCESS
                
Rate Limit Status:
- Calls per minute: {rate_limit.get('calls_this_minute', 0)}/{rate_limit.get('calls_per_minute_limit', 0)}
- Calls per hour: {rate_limit.get('calls_this_hour', 0)}/{rate_limit.get('calls_per_hour_limit', 0)}"""
                
                QMessageBox.information(self, "API Test", message)
                self.show_status_message("API connection successful")
            else:
                QMessageBox.warning(self, "API Test", "API connection failed")
                self.show_status_message("API connection failed")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"API test error: {e}")
            self.show_status_message("API test error")
    
    def show_about(self):
        """Show about dialog."""
        message = f"""MTG Card Pricing Analysis Tool
        
Version: {self.settings_manager.settings.version}

A desktop application for analyzing Magic: The Gathering card prices
and identifying underpriced printings using statistical analysis.

Features:
- Real-time price data from JustTCG API
- Historical price tracking
- Statistical anomaly detection
- Batch processing capabilities
- Professional GUI interface

© 2024 MTG Card Pricing Analysis Tool"""
        
        QMessageBox.about(self, "About", message)
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Save current window state
        settings = self.settings_manager.settings.gui
        size = self.size()
        settings.window_width = size.width()
        settings.window_height = size.height()
        self.settings_manager.save_settings()
        
        # Stop timers
        self.auto_refresh_timer.stop()
        self.status_timer.stop()
        
        event.accept()