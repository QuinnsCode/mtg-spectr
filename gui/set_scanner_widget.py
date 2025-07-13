"""
GUI widget for set scanning functionality.
Provides an interface for scanning entire MTG sets for price anomalies.
"""

import logging
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QComboBox, QTextEdit, QProgressBar, QTableWidget,
    QTableWidgetItem, QGroupBox, QSplitter, QTabWidget, QSpinBox,
    QCheckBox, QMessageBox, QFileDialog, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QColor

# Import clickable card functionality from results widget
from .results_widget import ClickableCardTable, ClickableCardItem

from analysis.set_scanner import SetScanner, SetScanResult
from data.unified_api_client import UnifiedAPIClient

logger = logging.getLogger(__name__)


class SetScanWorker(QThread):
    """Worker thread for set scanning operations."""
    
    progress_updated = Signal(int, int, str)  # current, total, card_name
    scan_completed = Signal(object)  # SetScanResult
    scan_error = Signal(str)
    
    def __init__(self, api_client: UnifiedAPIClient):
        super().__init__()
        self.api_client = api_client
        self.scanner = SetScanner(api_client)
        self.set_code = ""
        self.max_cards = None
        self.should_stop = False
    
    def set_scan_params(self, set_code: str, max_cards: Optional[int] = None):
        """Set parameters for the scan."""
        self.set_code = set_code
        self.max_cards = max_cards
    
    def stop_scan(self):
        """Stop the current scan."""
        self.should_stop = True
    
    def run(self):
        """Run the set scan."""
        try:
            def progress_callback(current, total, card_name):
                if not self.should_stop:
                    self.progress_updated.emit(current, total, card_name)
            
            # Perform the scan
            result = self.scanner.scan_set(
                set_code=self.set_code,
                progress_callback=progress_callback,
                max_cards=self.max_cards
            )
            
            if not self.should_stop:
                self.scan_completed.emit(result)
                
        except Exception as e:
            if not self.should_stop:
                self.scan_error.emit(str(e))


class SetScannerWidget(QWidget):
    """Widget for scanning MTG sets for price anomalies."""
    
    def __init__(self, api_client: UnifiedAPIClient):
        super().__init__()
        self.api_client = api_client
        self.scanner = SetScanner(api_client)
        self.scan_worker = None
        self.current_results = None
        
        self.setup_ui()
        self.load_available_sets()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("MTG Set Scanner - Anomaly Detection")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Set selection group
        set_group = QGroupBox("Set Selection")
        set_layout = QFormLayout(set_group)
        
        self.set_combo = QComboBox()
        self.set_combo.setMinimumWidth(300)
        set_layout.addRow("Set:", self.set_combo)
        
        self.set_info_label = QLabel("Select a set to see information")
        self.set_info_label.setWordWrap(True)
        set_layout.addRow("Info:", self.set_info_label)
        
        left_layout.addWidget(set_group)
        
        # Scan options group
        options_group = QGroupBox("Scan Options")
        options_layout = QFormLayout(options_group)
        
        self.max_cards_spin = QSpinBox()
        self.max_cards_spin.setMinimum(0)
        self.max_cards_spin.setMaximum(1000)
        self.max_cards_spin.setValue(0)
        self.max_cards_spin.setSpecialValueText("All cards")
        options_layout.addRow("Max cards:", self.max_cards_spin)
        
        self.export_results_check = QCheckBox("Export results to JSON")
        self.export_results_check.setChecked(True)
        options_layout.addRow("", self.export_results_check)
        
        left_layout.addWidget(options_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.scan_button = QPushButton("Start Scan")
        self.scan_button.clicked.connect(self.start_scan)
        button_layout.addWidget(self.scan_button)
        
        self.stop_button = QPushButton("Stop Scan")
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        left_layout.addLayout(button_layout)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready to scan")
        progress_layout.addWidget(self.progress_label)
        
        left_layout.addWidget(progress_group)
        
        # Statistics section
        stats_group = QGroupBox("Statistics")
        self.stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("No scan results yet")
        self.stats_layout.addWidget(self.stats_label)
        
        left_layout.addWidget(stats_group)
        
        left_layout.addStretch()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Results tabs
        self.results_tabs = QTabWidget()
        
        # Anomalies tab
        self.anomalies_table = ClickableCardTable()
        self.anomalies_table.setColumnCount(7)
        self.anomalies_table.setHorizontalHeaderLabels([
            "Card Name", "Rarity", "Current Price", "Expected Price", 
            "Anomaly Type", "Score", "Confidence"
        ])
        self.anomalies_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_tabs.addTab(self.anomalies_table, "Anomalies")
        
        # Undervalued tab
        self.undervalued_table = ClickableCardTable()
        self.undervalued_table.setColumnCount(6)
        self.undervalued_table.setHorizontalHeaderLabels([
            "Card Name", "Rarity", "Current Price", "Expected Price", 
            "Savings", "Confidence"
        ])
        self.undervalued_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_tabs.addTab(self.undervalued_table, "Undervalued")
        
        # Overvalued tab
        self.overvalued_table = ClickableCardTable()
        self.overvalued_table.setColumnCount(6)
        self.overvalued_table.setHorizontalHeaderLabels([
            "Card Name", "Rarity", "Current Price", "Expected Price", 
            "Difference", "Confidence"
        ])
        self.overvalued_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_tabs.addTab(self.overvalued_table, "Overvalued")
        
        right_layout.addWidget(self.results_tabs)
        
        # Export button
        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        right_layout.addWidget(self.export_button)
        
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 800])
        
        # Connect signals
        self.set_combo.currentTextChanged.connect(self.on_set_changed)
    
    def load_available_sets(self):
        """Load available sets into the combo box."""
        try:
            sets = self.scanner.get_available_sets()
            
            self.set_combo.clear()
            for set_info in sets:
                display_text = f"{set_info['name']} ({set_info['code']}) - {set_info['card_count']} cards"
                self.set_combo.addItem(display_text, set_info)
            
            if sets:
                self.on_set_changed()
            
        except Exception as e:
            logger.error(f"Error loading sets: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load available sets: {e}")
    
    def on_set_changed(self):
        """Handle set selection change."""
        current_data = self.set_combo.currentData()
        if current_data:
            set_info = current_data
            info_text = f"Released: {set_info.get('released_at', 'Unknown')}\n"
            info_text += f"Type: {set_info.get('set_type', 'Unknown')}\n"
            info_text += f"Cards: {set_info.get('card_count', 0)}"
            self.set_info_label.setText(info_text)
    
    def start_scan(self):
        """Start the set scan."""
        current_data = self.set_combo.currentData()
        if not current_data:
            QMessageBox.warning(self, "Error", "Please select a set to scan")
            return
        
        set_code = current_data['code']
        max_cards = self.max_cards_spin.value() if self.max_cards_spin.value() > 0 else None
        
        # Clear previous results
        self.clear_results()
        
        # Update UI
        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting scan...")
        
        # Start worker thread
        self.scan_worker = SetScanWorker(self.api_client)
        self.scan_worker.set_scan_params(set_code, max_cards)
        
        self.scan_worker.progress_updated.connect(self.on_progress_updated)
        self.scan_worker.scan_completed.connect(self.on_scan_completed)
        self.scan_worker.scan_error.connect(self.on_scan_error)
        
        self.scan_worker.start()
        logger.info(f"Started scan for set: {set_code}")
    
    def stop_scan(self):
        """Stop the current scan."""
        if self.scan_worker:
            self.scan_worker.stop_scan()
            self.scan_worker.wait()
        
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_label.setText("Scan stopped")
    
    def on_progress_updated(self, current: int, total: int, card_name: str):
        """Handle progress updates."""
        percentage = (current / total) * 100 if total > 0 else 0
        self.progress_bar.setValue(int(percentage))
        self.progress_label.setText(f"Scanning: {current}/{total} - {card_name}")
    
    def on_scan_completed(self, result: SetScanResult):
        """Handle scan completion."""
        self.current_results = result
        
        # Update UI
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_label.setText("Scan completed")
        
        # Update statistics
        self.update_statistics(result)
        
        # Update results tables
        self.update_results_tables(result)
        
        # Auto-export if enabled
        if self.export_results_check.isChecked():
            self.export_results()
        
        logger.info(f"Scan completed: {result.anomalies_found} anomalies found")
    
    def on_scan_error(self, error_message: str):
        """Handle scan errors."""
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_label.setText(f"Scan failed: {error_message}")
        
        QMessageBox.critical(self, "Scan Error", f"Scan failed: {error_message}")
        logger.error(f"Scan error: {error_message}")
    
    def update_statistics(self, result: SetScanResult):
        """Update the statistics display."""
        stats = result.price_statistics
        
        stats_text = f"<b>Scan Results:</b><br>"
        stats_text += f"Cards scanned: {result.scanned_cards}<br>"
        stats_text += f"Anomalies found: {result.anomalies_found}<br>"
        stats_text += f"Scan duration: {result.scan_duration:.1f} seconds<br><br>"
        
        if stats:
            stats_text += f"<b>Price Statistics:</b><br>"
            stats_text += f"Average price: ${stats.get('average_price', 0):.2f}<br>"
            stats_text += f"Median price: ${stats.get('median_price', 0):.2f}<br>"
            stats_text += f"Price range: ${stats.get('min_price', 0):.2f} - ${stats.get('max_price', 0):.2f}<br>"
            stats_text += f"Anomaly rate: {stats.get('anomaly_rate', 0):.1%}<br><br>"
            
            stats_text += f"<b>Anomaly Breakdown:</b><br>"
            stats_text += f"Undervalued: {stats.get('undervalued_count', 0)}<br>"
            stats_text += f"Overvalued: {stats.get('overvalued_count', 0)}<br>"
            stats_text += f"Volatile: {stats.get('volatile_count', 0)}<br>"
        
        self.stats_label.setText(stats_text)
    
    def update_results_tables(self, result: SetScanResult):
        """Update the results tables with scan data."""
        # All anomalies table
        self.populate_anomalies_table(self.anomalies_table, result.anomaly_cards)
        
        # Undervalued table
        undervalued = [a for a in result.anomaly_cards if a['anomaly_type'] == 'undervalued']
        self.populate_undervalued_table(self.undervalued_table, undervalued)
        
        # Overvalued table
        overvalued = [a for a in result.anomaly_cards if a['anomaly_type'] == 'overvalued']
        self.populate_overvalued_table(self.overvalued_table, overvalued)
    
    def populate_anomalies_table(self, table: QTableWidget, anomalies: List[Dict]):
        """Populate the anomalies table."""
        table.setRowCount(len(anomalies))
        
        for row, anomaly in enumerate(anomalies):
            # Create clickable card name item
            card_item = ClickableCardItem(anomaly['card_name'], anomaly)
            table.setItem(row, 0, card_item)
            table.setItem(row, 1, QTableWidgetItem(anomaly['rarity']))
            table.setItem(row, 2, QTableWidgetItem(f"${anomaly['current_price']:.2f}"))
            table.setItem(row, 3, QTableWidgetItem(f"${anomaly['expected_price']:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(anomaly['anomaly_type']))
            table.setItem(row, 5, QTableWidgetItem(f"{anomaly['anomaly_score']:.2f}"))
            table.setItem(row, 6, QTableWidgetItem(f"{anomaly['confidence']:.1%}"))
            
            # Color code by anomaly type
            if anomaly['anomaly_type'] == 'undervalued':
                color = QColor(144, 238, 144)  # Light green
            elif anomaly['anomaly_type'] == 'overvalued':
                color = QColor(255, 182, 193)  # Light pink
            else:
                color = QColor(255, 255, 224)  # Light yellow
            
            for col in range(table.columnCount()):
                table.item(row, col).setBackground(color)
    
    def populate_undervalued_table(self, table: QTableWidget, anomalies: List[Dict]):
        """Populate the undervalued table."""
        table.setRowCount(len(anomalies))
        
        for row, anomaly in enumerate(anomalies):
            savings = anomaly['expected_price'] - anomaly['current_price']
            
            # Create clickable card name item
            card_item = ClickableCardItem(anomaly['card_name'], anomaly)
            table.setItem(row, 0, card_item)
            table.setItem(row, 1, QTableWidgetItem(anomaly['rarity']))
            table.setItem(row, 2, QTableWidgetItem(f"${anomaly['current_price']:.2f}"))
            table.setItem(row, 3, QTableWidgetItem(f"${anomaly['expected_price']:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(f"${savings:.2f}"))
            table.setItem(row, 5, QTableWidgetItem(f"{anomaly['confidence']:.1%}"))
    
    def populate_overvalued_table(self, table: QTableWidget, anomalies: List[Dict]):
        """Populate the overvalued table."""
        table.setRowCount(len(anomalies))
        
        for row, anomaly in enumerate(anomalies):
            difference = anomaly['current_price'] - anomaly['expected_price']
            
            # Create clickable card name item
            card_item = ClickableCardItem(anomaly['card_name'], anomaly)
            table.setItem(row, 0, card_item)
            table.setItem(row, 1, QTableWidgetItem(anomaly['rarity']))
            table.setItem(row, 2, QTableWidgetItem(f"${anomaly['current_price']:.2f}"))
            table.setItem(row, 3, QTableWidgetItem(f"${anomaly['expected_price']:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(f"${difference:.2f}"))
            table.setItem(row, 5, QTableWidgetItem(f"{anomaly['confidence']:.1%}"))
    
    def clear_results(self):
        """Clear all results from the tables."""
        self.anomalies_table.setRowCount(0)
        self.undervalued_table.setRowCount(0)
        self.overvalued_table.setRowCount(0)
        self.stats_label.setText("No scan results yet")
        self.export_button.setEnabled(False)
    
    def export_results(self):
        """Export scan results to JSON file."""
        if not self.current_results:
            QMessageBox.warning(self, "Error", "No scan results to export")
            return
        
        try:
            filename = f"scan_results_{self.current_results.set_code}.json"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Scan Results", filename, "JSON Files (*.json)"
            )
            
            if file_path:
                self.scanner.export_results(self.current_results, file_path)
                QMessageBox.information(self, "Success", f"Results exported to {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export results: {e}")
            logger.error(f"Export error: {e}")