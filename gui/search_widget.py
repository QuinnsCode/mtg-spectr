"""
Search widget for the MTG Card Pricing Analysis Tool.
Provides card search interface with filters and options.
"""

import logging
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QSpinBox, QLabel,
    QGroupBox, QCompleter, QProgressBar, QTextEdit,
    QSplitter, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QStringListModel
from PySide6.QtGui import QFont

from data.database import DatabaseManager
from data.unified_api_client import UnifiedAPIClient
from analysis.price_analyzer import PriceAnalyzer
from config.input_validator import InputValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchWorker(QThread):
    """Worker thread for performing card searches."""
    
    search_completed = Signal(list)
    search_progress = Signal(int, int)
    search_error = Signal(str)
    
    def __init__(self, api_client: UnifiedAPIClient, database_manager: DatabaseManager,
                 price_analyzer: PriceAnalyzer):
        super().__init__()
        self.api_client = api_client
        self.database_manager = database_manager
        self.price_analyzer = price_analyzer
        self.search_params = {}
        self.should_stop = False
    
    def set_search_params(self, params: Dict):
        """Set search parameters."""
        self.search_params = params
    
    def stop_search(self):
        """Stop the current search."""
        self.should_stop = True
    
    def run(self):
        """Execute the search in background thread."""
        try:
            self.should_stop = False
            card_name = self.search_params.get('card_name', '')
            set_code = self.search_params.get('set_code')
            search_mode = self.search_params.get('search_mode', 'single')
            include_analysis = self.search_params.get('include_analysis', True)
            
            # Validate inputs
            try:
                if search_mode == 'single':
                    card_name = InputValidator.validate_card_name(card_name)
                else:
                    # For multiple cards, validate the entire input string first
                    card_name = InputValidator.validate_search_term(card_name)
                
                if set_code:
                    set_code = InputValidator.validate_set_code(set_code)
                    
            except ValueError as e:
                self.search_error.emit(f"Invalid input: {e}")
                return
            
            if search_mode == 'single':
                results = self._search_single_card(card_name, set_code, include_analysis)
            else:
                results = self._search_multiple_cards(card_name, include_analysis)
            
            if not self.should_stop:
                self.search_completed.emit(results)
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            self.search_error.emit(str(e))
    
    def _search_single_card(self, card_name: str, set_code: Optional[str],
                           include_analysis: bool) -> List[Dict]:
        """Search for a single card."""
        results = []
        
        try:
            # Get card printings from API
            self.search_progress.emit(0, 100)
            printings = self.api_client.get_card_printings(card_name)
            
            if self.should_stop:
                return results
            
            # Filter by set code if specified
            if set_code:
                printings = [p for p in printings if getattr(p, 'set_code', None) == set_code]
            
            # Store in database
            self.search_progress.emit(25, 100)
            for printing in printings:
                if self.should_stop:
                    break
                self.database_manager.insert_price_data(printing)
            
            # Get updated data from database
            self.search_progress.emit(50, 100)
            db_data = self.database_manager.get_card_prices(card_name, set_code)
            
            if self.should_stop:
                return results
            
            # Perform analysis if requested
            if include_analysis and db_data:
                self.search_progress.emit(75, 100)
                analysis_results = self.price_analyzer.analyze_card_prices(card_name, set_code)
                
                # Merge analysis results with price data
                for data in db_data:
                    # Find matching analysis result
                    analysis = None
                    for result in analysis_results:
                        if (result.get('set_code') == data.get('set_code') and
                            result.get('printing_info') == data.get('printing_info') and
                            result.get('condition') == data.get('condition')):
                            analysis = result
                            break
                    
                    result_item = {
                        'card_name': data['card_name'],
                        'set_code': data['set_code'],
                        'printing_info': data['printing_info'],
                        'price_cents': data['price_cents'],
                        'price_dollars': data['price_cents'] / 100.0,
                        'condition': data['condition'],
                        'foil': data['foil'],
                        'timestamp': data['timestamp'],
                        'source': data['source'],
                        'is_anomaly': analysis.get('is_anomaly', False) if analysis else False,
                        'anomaly_score': analysis.get('anomaly_score', 0.0) if analysis else 0.0,
                        'expected_price': analysis.get('expected_price', 0.0) if analysis else 0.0,
                        'savings_potential': analysis.get('savings_potential', 0.0) if analysis else 0.0
                    }
                    results.append(result_item)
            else:
                # Just return price data without analysis
                for data in db_data:
                    result_item = {
                        'card_name': data['card_name'],
                        'set_code': data['set_code'],
                        'printing_info': data['printing_info'],
                        'price_cents': data['price_cents'],
                        'price_dollars': data['price_cents'] / 100.0,
                        'condition': data['condition'],
                        'foil': data['foil'],
                        'timestamp': data['timestamp'],
                        'source': data['source'],
                        'is_anomaly': False,
                        'anomaly_score': 0.0,
                        'expected_price': 0.0,
                        'savings_potential': 0.0
                    }
                    results.append(result_item)
            
            self.search_progress.emit(100, 100)
            
        except Exception as e:
            logger.error(f"Single card search error: {e}")
            raise
        
        return results
    
    def _search_multiple_cards(self, card_names: str, include_analysis: bool) -> List[Dict]:
        """Search for multiple cards."""
        results = []
        
        try:
            # Validate and parse card names
            names = InputValidator.validate_multiple_card_names(card_names)
            
            if not names:
                return results
            
            total_cards = len(names)
            
            for i, card_name in enumerate(names):
                if self.should_stop:
                    break
                
                self.search_progress.emit(i, total_cards)
                
                try:
                    # Get single card results
                    card_results = self._search_single_card(card_name, None, include_analysis)
                    results.extend(card_results)
                    
                except Exception as e:
                    logger.error(f"Error searching for '{card_name}': {e}")
                    continue
            
            self.search_progress.emit(total_cards, total_cards)
            
        except Exception as e:
            logger.error(f"Multiple card search error: {e}")
            raise
        
        return results


class SearchWidget(QWidget):
    """Widget for card search interface."""
    
    search_completed = Signal(list)
    status_message = Signal(str)
    
    def __init__(self, database_manager: DatabaseManager, api_client: UnifiedAPIClient):
        super().__init__()
        self.database_manager = database_manager
        self.api_client = api_client
        self.price_analyzer = PriceAnalyzer(database_manager)
        
        self.search_worker = None
        self.current_search_params = {}
        
        self.setup_ui()
        self.setup_connections()
        self.load_autocomplete_data()
    
    def setup_ui(self):
        """Set up the search widget UI."""
        layout = QVBoxLayout(self)
        
        # Search input section
        search_group = QGroupBox("Search")
        search_layout = QFormLayout(search_group)
        
        # Card name input with autocomplete
        self.card_name_input = QLineEdit()
        self.card_name_input.setPlaceholderText("Enter card name...")
        self.setup_autocomplete()
        search_layout.addRow("Card Name:", self.card_name_input)
        
        # Set code filter
        self.set_code_combo = QComboBox()
        self.set_code_combo.setEditable(True)
        self.set_code_combo.addItem("Any Set", "")
        self.load_set_codes()
        search_layout.addRow("Set Code:", self.set_code_combo)
        
        # Search mode
        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItems(["Single Card", "Multiple Cards"])
        search_layout.addRow("Search Mode:", self.search_mode_combo)
        
        # Multiple cards input (hidden by default)
        self.multiple_cards_input = QTextEdit()
        self.multiple_cards_input.setPlaceholderText("Enter card names, one per line or comma-separated...")
        self.multiple_cards_input.setMaximumHeight(100)
        self.multiple_cards_input.setVisible(False)
        search_layout.addRow("Card Names:", self.multiple_cards_input)
        
        layout.addWidget(search_group)
        
        # Analysis options
        analysis_group = QGroupBox("Analysis Options")
        analysis_layout = QFormLayout(analysis_group)
        
        self.include_analysis_check = QCheckBox()
        self.include_analysis_check.setChecked(True)
        analysis_layout.addRow("Include Anomaly Analysis:", self.include_analysis_check)
        
        # Analysis method
        self.analysis_method_combo = QComboBox()
        self.analysis_method_combo.addItems(["IQR", "Z-Score", "Isolation Forest"])
        analysis_layout.addRow("Analysis Method:", self.analysis_method_combo)
        
        # Minimum data points
        self.min_data_points_spin = QSpinBox()
        self.min_data_points_spin.setRange(1, 100)
        self.min_data_points_spin.setValue(5)
        analysis_layout.addRow("Min Data Points:", self.min_data_points_spin)
        
        # Historical days
        self.historical_days_spin = QSpinBox()
        self.historical_days_spin.setRange(1, 365)
        self.historical_days_spin.setValue(30)
        analysis_layout.addRow("Historical Days:", self.historical_days_spin)
        
        layout.addWidget(analysis_group)
        
        # Search controls
        controls_layout = QHBoxLayout()
        
        self.search_button = QPushButton("Search")
        self.search_button.setDefault(True)
        controls_layout.addWidget(self.search_button)
        
        self.clear_button = QPushButton("Clear")
        controls_layout.addWidget(self.clear_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        layout.addLayout(controls_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Recent searches
        recent_group = QGroupBox("Recent Searches")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_searches_list = QListWidget()
        self.recent_searches_list.setMaximumHeight(150)
        recent_layout.addWidget(self.recent_searches_list)
        
        layout.addWidget(recent_group)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        font = self.status_label.font()
        font.setPointSize(font.pointSize() - 1)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)
        
        # Add stretch to push everything to top
        layout.addStretch()
    
    def setup_connections(self):
        """Set up signal connections."""
        # Search controls
        self.search_button.clicked.connect(self.start_search)
        self.clear_button.clicked.connect(self.clear_search)
        self.stop_button.clicked.connect(self.stop_search)
        
        # Search mode change
        self.search_mode_combo.currentTextChanged.connect(self.on_search_mode_changed)
        
        # Enter key in card name input
        self.card_name_input.returnPressed.connect(self.start_search)
        
        # Recent searches
        self.recent_searches_list.itemClicked.connect(self.on_recent_search_clicked)
        
        # Analysis options
        self.include_analysis_check.toggled.connect(self.on_analysis_toggled)
    
    def setup_autocomplete(self):
        """Set up autocomplete for card names."""
        self.completer = QCompleter()
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.card_name_input.setCompleter(self.completer)
    
    def load_autocomplete_data(self):
        """Load card names for autocomplete."""
        try:
            card_names = self.database_manager.get_unique_card_names()
            model = QStringListModel(card_names)
            self.completer.setModel(model)
        except Exception as e:
            logger.error(f"Failed to load autocomplete data: {e}")
    
    def load_set_codes(self):
        """Load set codes for the combo box."""
        try:
            set_codes = self.database_manager.get_set_codes()
            for set_code in set_codes:
                self.set_code_combo.addItem(set_code, set_code)
        except Exception as e:
            logger.error(f"Failed to load set codes: {e}")
    
    def on_search_mode_changed(self, mode: str):
        """Handle search mode change."""
        is_multiple = mode == "Multiple Cards"
        self.multiple_cards_input.setVisible(is_multiple)
        self.card_name_input.setVisible(not is_multiple)
        
        # Update labels
        search_group = self.card_name_input.parent()
        if search_group:
            layout = search_group.layout()
            if layout:
                if is_multiple:
                    layout.labelForField(self.card_name_input).setText("Card Names:")
                else:
                    layout.labelForField(self.card_name_input).setText("Card Name:")
    
    def on_analysis_toggled(self, checked: bool):
        """Handle analysis checkbox toggle."""
        self.analysis_method_combo.setEnabled(checked)
        self.min_data_points_spin.setEnabled(checked)
        self.historical_days_spin.setEnabled(checked)
    
    def on_recent_search_clicked(self, item: QListWidgetItem):
        """Handle recent search item click."""
        search_text = item.text()
        if self.search_mode_combo.currentText() == "Multiple Cards":
            self.multiple_cards_input.setPlainText(search_text)
        else:
            self.card_name_input.setText(search_text)
    
    def start_search(self):
        """Start a new search."""
        if self.search_worker and self.search_worker.isRunning():
            return
        
        # Get search parameters
        search_mode = self.search_mode_combo.currentText()
        
        if search_mode == "Multiple Cards":
            card_input = self.multiple_cards_input.toPlainText().strip()
        else:
            card_input = self.card_name_input.text().strip()
        
        if not card_input:
            self.status_message.emit("Please enter a card name")
            return
        
        # Validate inputs before starting search
        try:
            if search_mode == "Multiple Cards":
                # Validate multiple card names
                validated_names = InputValidator.validate_multiple_card_names(card_input)
                if not validated_names:
                    self.status_message.emit("No valid card names found")
                    return
            else:
                # Validate single card name
                InputValidator.validate_card_name(card_input)
            
            # Validate set code if provided
            set_code_input = self.set_code_combo.currentData()
            if set_code_input:
                InputValidator.validate_set_code(set_code_input)
                
        except ValueError as e:
            self.status_message.emit(f"Invalid input: {e}")
            return
        
        # Prepare search parameters
        search_params = {
            'card_name': card_input,
            'set_code': self.set_code_combo.currentData() if self.set_code_combo.currentData() else None,
            'search_mode': 'multiple' if search_mode == "Multiple Cards" else 'single',
            'include_analysis': self.include_analysis_check.isChecked(),
            'analysis_method': self.analysis_method_combo.currentText().lower().replace('-', '_'),
            'min_data_points': self.min_data_points_spin.value(),
            'historical_days': self.historical_days_spin.value()
        }
        
        self.current_search_params = search_params
        
        # Update price analyzer settings
        self.price_analyzer.set_anomaly_method(search_params['analysis_method'])
        self.price_analyzer.set_minimum_data_points(search_params['min_data_points'])
        self.price_analyzer.set_historical_days(search_params['historical_days'])
        
        # Start worker thread
        self.search_worker = SearchWorker(self.api_client, self.database_manager, self.price_analyzer)
        self.search_worker.set_search_params(search_params)
        
        # Connect worker signals
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.search_progress.connect(self.on_search_progress)
        self.search_worker.search_error.connect(self.on_search_error)
        self.search_worker.finished.connect(self.on_search_finished)
        
        # Update UI
        self.search_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Searching...")
        
        # Start the search
        self.search_worker.start()
        
        # Add to recent searches
        self.add_to_recent_searches(card_input)
        
        self.status_message.emit(f"Starting search for: {card_input}")
    
    def stop_search(self):
        """Stop the current search."""
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop_search()
            self.search_worker.wait(5000)  # Wait up to 5 seconds
            
            if self.search_worker.isRunning():
                self.search_worker.terminate()
                self.search_worker.wait()
            
            self.status_message.emit("Search stopped")
    
    def clear_search(self):
        """Clear search inputs."""
        self.card_name_input.clear()
        self.multiple_cards_input.clear()
        self.set_code_combo.setCurrentIndex(0)
        self.status_label.setText("Ready")
        
        # Clear results
        self.search_completed.emit([])
    
    def on_search_completed(self, results: List[Dict]):
        """Handle search completion."""
        self.search_completed.emit(results)
        
        count = len(results)
        anomaly_count = sum(1 for r in results if r.get('is_anomaly', False))
        
        self.status_label.setText(f"Found {count} results ({anomaly_count} anomalies)")
        self.status_message.emit(f"Search completed: {count} results found")
    
    def on_search_progress(self, current: int, total: int):
        """Handle search progress updates."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
        if total > 0:
            percent = (current / total) * 100
            self.status_label.setText(f"Searching... {percent:.0f}%")
    
    def on_search_error(self, error: str):
        """Handle search errors."""
        self.status_label.setText(f"Search error: {error}")
        self.status_message.emit(f"Search error: {error}")
    
    def on_search_finished(self):
        """Handle search thread finished."""
        self.search_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if self.search_worker:
            self.search_worker.deleteLater()
            self.search_worker = None
    
    def add_to_recent_searches(self, search_text: str):
        """Add search to recent searches list."""
        # Remove if already exists
        for i in range(self.recent_searches_list.count()):
            if self.recent_searches_list.item(i).text() == search_text:
                self.recent_searches_list.takeItem(i)
                break
        
        # Add to top
        self.recent_searches_list.insertItem(0, search_text)
        
        # Limit to 10 items
        while self.recent_searches_list.count() > 10:
            self.recent_searches_list.takeItem(self.recent_searches_list.count() - 1)
    
    def refresh_current_search(self):
        """Refresh the current search."""
        if self.current_search_params:
            self.start_search()
    
    def focus_search(self):
        """Focus the search input."""
        if self.search_mode_combo.currentText() == "Multiple Cards":
            self.multiple_cards_input.setFocus()
        else:
            self.card_name_input.setFocus()
    
    def update_api_client(self, api_client: UnifiedAPIClient):
        """Update the API client."""
        self.api_client = api_client
        
        # Update existing worker if running
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.api_client = api_client