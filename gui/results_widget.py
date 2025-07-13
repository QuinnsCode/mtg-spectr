"""
Results widget for the MTG Card Pricing Analysis Tool.
Displays price analysis results in tables with sorting and filtering capabilities.
"""

import logging
import webbrowser
import urllib.parse
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QComboBox, QCheckBox, QPushButton, QGroupBox,
    QSplitter, QTextEdit, QTabWidget, QProgressBar, QMenu, QMessageBox,
    QToolTip
)
from PySide6.QtCore import Qt, Signal, QTimer, QSortFilterProxyModel, QAbstractTableModel, QUrl
from PySide6.QtGui import QColor, QFont, QAction, QBrush, QDesktopServices, QPixmap, QCursor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from data.database import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClickableCardItem(QTableWidgetItem):
    """Custom table widget item for card names that supports clicking and hover effects."""
    
    def __init__(self, card_name: str, card_data: Dict):
        super().__init__(card_name)
        self.card_data = card_data
        self.card_name = card_name
        
        # Make it look clickable
        self.setForeground(QBrush(QColor(0, 100, 200)))  # Blue color
        self.setToolTip(f"Click to view {card_name} on TCGPlayer\nHover to see card image")
        
        # Store image URL if available
        self.image_url = card_data.get('image_url', '')
        
    def create_tcgplayer_url(self) -> str:
        """Create a TCGPlayer search URL for this card."""
        # Format card name for URL search
        search_term = urllib.parse.quote_plus(self.card_name)
        return f"https://www.tcgplayer.com/search/magic/product?q={search_term}"


class CardImageManager:
    """Manages downloading and caching card images for hover effects."""
    
    def __init__(self):
        self.network_manager = QNetworkAccessManager()
        self.image_cache = {}
        
    def get_card_image(self, image_url: str, callback):
        """Download card image and call callback when ready."""
        if not image_url:
            return
            
        if image_url in self.image_cache:
            callback(self.image_cache[image_url])
            return
            
        request = QNetworkRequest(QUrl(image_url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._on_image_downloaded(reply, image_url, callback))
        
    def _on_image_downloaded(self, reply: QNetworkReply, image_url: str, callback):
        """Handle image download completion."""
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                # Scale image to reasonable size for tooltip
                scaled_pixmap = pixmap.scaled(223, 311, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_cache[image_url] = scaled_pixmap
                callback(scaled_pixmap)
        reply.deleteLater()


class ClickableCardTable(QTableWidget):
    """Custom table widget that handles card clicks and hover effects."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_manager = CardImageManager()
        self.setMouseTracking(True)  # Enable mouse tracking for hover effects
        
        # Connect click signal
        self.itemClicked.connect(self._on_item_clicked)
        
    def _on_item_clicked(self, item):
        """Handle clicks on card items."""
        if isinstance(item, ClickableCardItem):
            tcgplayer_url = item.create_tcgplayer_url()
            QDesktopServices.openUrl(QUrl(tcgplayer_url))
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for hover effects."""
        super().mouseMoveEvent(event)
        
        item = self.itemAt(event.pos())
        if isinstance(item, ClickableCardItem) and item.image_url:
            # Show card image in tooltip
            self._show_card_image_tooltip(item, event.globalPos())
            
    def _show_card_image_tooltip(self, item: ClickableCardItem, global_pos):
        """Show card image as tooltip."""
        def show_image(pixmap):
            # Create HTML tooltip with image
            tooltip_html = f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{self._pixmap_to_base64(pixmap)}" 
                     width="{pixmap.width()}" height="{pixmap.height()}">
                <br><b>{item.card_name}</b>
                <br>Click to view on TCGPlayer
            </div>
            """
            QToolTip.showText(global_pos, tooltip_html)
            
        self.image_manager.get_card_image(item.image_url, show_image)
        
    def _pixmap_to_base64(self, pixmap):
        """Convert QPixmap to base64 string for HTML tooltip."""
        from PySide6.QtCore import QByteArray, QBuffer
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.WriteOnly)
        pixmap.save(buffer, "PNG")
        return byte_array.toBase64().data().decode()


class PriceTableModel(QAbstractTableModel):
    """Custom table model for price data."""
    
    def __init__(self, data: List[Dict] = None):
        super().__init__()
        self.data = data or []
        self.headers = [
            'Card Name', 'Set Code', 'Printing', 'Price', 'Condition', 
            'Foil', 'Anomaly', 'Score', 'Expected', 'Savings', 'Updated'
        ]
        self.data_keys = [
            'card_name', 'set_code', 'printing_info', 'price_dollars', 'condition',
            'foil', 'is_anomaly', 'anomaly_score', 'expected_price', 'savings_potential', 'timestamp'
        ]
    
    def rowCount(self, parent=None):
        return len(self.data)
    
    def columnCount(self, parent=None):
        return len(self.headers)
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.data):
            return None
        
        row = self.data[index.row()]
        col = index.column()
        key = self.data_keys[col]
        
        if role == Qt.DisplayRole:
            value = row.get(key, '')
            
            # Format specific columns
            if key == 'price_dollars':
                return f"${value:.2f}" if isinstance(value, (int, float)) else str(value)
            elif key == 'foil':
                return 'Yes' if value else 'No'
            elif key == 'is_anomaly':
                return 'Yes' if value else 'No'
            elif key in ['anomaly_score', 'expected_price', 'savings_potential']:
                if isinstance(value, (int, float)):
                    if key == 'anomaly_score':
                        return f"{value:.3f}"
                    else:
                        return f"${value:.2f}"
                return str(value)
            elif key == 'timestamp':
                # Format timestamp
                if isinstance(value, str):
                    return value[:19]  # Remove microseconds
                return str(value)
            
            return str(value)
        
        elif role == Qt.BackgroundRole:
            # Highlight anomalies
            if row.get('is_anomaly', False):
                return QBrush(QColor(255, 255, 0, 50))  # Light yellow
        
        elif role == Qt.ForegroundRole:
            # Color anomaly scores
            if key == 'anomaly_score':
                score = row.get('anomaly_score', 0)
                if score > 0.7:
                    return QBrush(QColor(255, 0, 0))  # Red for high scores
                elif score > 0.3:
                    return QBrush(QColor(255, 165, 0))  # Orange for medium scores
        
        elif role == Qt.TextAlignmentRole:
            if key in ['price_dollars', 'anomaly_score', 'expected_price', 'savings_potential']:
                return Qt.AlignRight | Qt.AlignVCenter
            elif key in ['foil', 'is_anomaly']:
                return Qt.AlignCenter
        
        return None
    
    def sort(self, column, order=Qt.AscendingOrder):
        """Sort the data by column."""
        if column < 0 or column >= len(self.data_keys):
            return
        
        key = self.data_keys[column]
        reverse = order == Qt.DescendingOrder
        
        try:
            self.layoutAboutToBeChanged.emit()
            
            # Sort with proper type handling
            def sort_key(item):
                value = item.get(key, '')
                if key in ['price_dollars', 'anomaly_score', 'expected_price', 'savings_potential']:
                    return float(value) if isinstance(value, (int, float)) else 0.0
                elif key in ['foil', 'is_anomaly']:
                    return bool(value)
                return str(value).lower()
            
            self.data.sort(key=sort_key, reverse=reverse)
            self.layoutChanged.emit()
            
        except Exception as e:
            logger.error(f"Sort error: {e}")
    
    def update_data(self, data: List[Dict]):
        """Update the model data."""
        self.beginResetModel()
        self.data = data
        self.endResetModel()


class ResultsWidget(QWidget):
    """Widget for displaying price analysis results."""
    
    status_message = Signal(str)
    
    def __init__(self, database_manager: DatabaseManager):
        super().__init__()
        self.database_manager = database_manager
        self.current_results = []
        self.filtered_results = []
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the results widget UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Results table tab
        self.setup_results_tab()
        
        # Anomalies tab
        self.setup_anomalies_tab()
        
        # Summary tab
        self.setup_summary_tab()
    
    def setup_results_tab(self):
        """Set up the main results table tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filters section
        filters_group = QGroupBox("Filters")
        filters_layout = QHBoxLayout(filters_group)
        
        # Set filter
        filters_layout.addWidget(QLabel("Set:"))
        self.set_filter_combo = QComboBox()
        self.set_filter_combo.addItem("All Sets", "")
        filters_layout.addWidget(self.set_filter_combo)
        
        # Condition filter
        filters_layout.addWidget(QLabel("Condition:"))
        self.condition_filter_combo = QComboBox()
        self.condition_filter_combo.addItem("All Conditions", None)
        for condition in ["NM", "LP", "MP", "HP", "DMG"]:
            self.condition_filter_combo.addItem(condition, condition)
        filters_layout.addWidget(self.condition_filter_combo)
        
        # Foil filter
        self.foil_filter_check = QCheckBox("Foil Only")
        filters_layout.addWidget(self.foil_filter_check)
        
        # Anomaly filter
        self.anomaly_filter_check = QCheckBox("Anomalies Only")
        filters_layout.addWidget(self.anomaly_filter_check)
        
        # Price range
        filters_layout.addWidget(QLabel("Min Price:"))
        self.min_price_combo = QComboBox()
        self.min_price_combo.setEditable(True)
        self.min_price_combo.addItems(["", "1.00", "5.00", "10.00", "25.00", "50.00", "100.00"])
        filters_layout.addWidget(self.min_price_combo)
        
        filters_layout.addWidget(QLabel("Max Price:"))
        self.max_price_combo = QComboBox()
        self.max_price_combo.setEditable(True)
        self.max_price_combo.addItems(["", "10.00", "25.00", "50.00", "100.00", "250.00", "500.00"])
        filters_layout.addWidget(self.max_price_combo)
        
        # Clear filters button
        self.clear_filters_button = QPushButton("Clear Filters")
        filters_layout.addWidget(self.clear_filters_button)
        
        filters_layout.addStretch()
        layout.addWidget(filters_group)
        
        # Results table
        self.results_table = ClickableCardTable()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSortingEnabled(True)
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        layout.addWidget(self.results_table)
        
        # Results info
        self.results_info_label = QLabel("No results")
        layout.addWidget(self.results_info_label)
        
        self.tab_widget.addTab(widget, "All Results")
    
    def setup_anomalies_tab(self):
        """Set up the anomalies-only tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Anomalies table
        self.anomalies_table = ClickableCardTable()
        self.anomalies_table.setAlternatingRowColors(True)
        self.anomalies_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.anomalies_table.setSortingEnabled(True)
        self.anomalies_table.setContextMenuPolicy(Qt.CustomContextMenu)
        layout.addWidget(self.anomalies_table)
        
        # Anomalies info
        self.anomalies_info_label = QLabel("No anomalies found")
        layout.addWidget(self.anomalies_info_label)
        
        self.tab_widget.addTab(widget, "Anomalies")
    
    def setup_summary_tab(self):
        """Set up the summary tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Summary statistics
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        layout.addWidget(self.summary_text)
        
        self.tab_widget.addTab(widget, "Summary")
    
    def setup_connections(self):
        """Set up signal connections."""
        # Filter changes
        self.set_filter_combo.currentTextChanged.connect(self.apply_filters)
        self.condition_filter_combo.currentTextChanged.connect(self.apply_filters)
        self.foil_filter_check.toggled.connect(self.apply_filters)
        self.anomaly_filter_check.toggled.connect(self.apply_filters)
        self.min_price_combo.currentTextChanged.connect(self.apply_filters)
        self.max_price_combo.currentTextChanged.connect(self.apply_filters)
        
        # Clear filters
        self.clear_filters_button.clicked.connect(self.clear_filters)
        
        # Context menus
        self.results_table.customContextMenuRequested.connect(self.show_results_context_menu)
        self.anomalies_table.customContextMenuRequested.connect(self.show_anomalies_context_menu)
    
    def display_results(self, results: List[Dict]):
        """Display search results in the tables."""
        self.current_results = results
        
        # Update filter options
        self.update_filter_options()
        
        # Apply current filters
        self.apply_filters()
        
        # Update summary
        self.update_summary()
        
        self.status_message.emit(f"Displaying {len(results)} results")
    
    def update_filter_options(self):
        """Update filter combo box options based on current results."""
        # Get unique sets
        sets = set()
        for result in self.current_results:
            set_code = result.get('set_code', '')
            if set_code:
                sets.add(set_code)
        
        # Update set filter
        current_set = self.set_filter_combo.currentData()
        self.set_filter_combo.clear()
        self.set_filter_combo.addItem("All Sets", "")
        
        for set_code in sorted(sets):
            self.set_filter_combo.addItem(set_code, set_code)
        
        # Restore selection if it still exists
        if current_set:
            index = self.set_filter_combo.findData(current_set)
            if index >= 0:
                self.set_filter_combo.setCurrentIndex(index)
    
    def apply_filters(self):
        """Apply current filters to results."""
        if not self.current_results:
            self.filtered_results = []
            self.update_results_table()
            self.update_anomalies_table()
            return
        
        filtered = []
        
        # Get filter values
        set_filter = self.set_filter_combo.currentData()
        condition_filter = self.condition_filter_combo.currentData()
        foil_only = self.foil_filter_check.isChecked()
        anomaly_only = self.anomaly_filter_check.isChecked()
        
        # Price range filters
        min_price = None
        max_price = None
        
        try:
            min_price_text = self.min_price_combo.currentText().strip()
            if min_price_text:
                min_price = float(min_price_text)
        except ValueError:
            pass
        
        try:
            max_price_text = self.max_price_combo.currentText().strip()
            if max_price_text:
                max_price = float(max_price_text)
        except ValueError:
            pass
        
        # Apply filters
        for result in self.current_results:
            # Set filter
            if set_filter and result.get('set_code') != set_filter:
                continue
            
            # Condition filter
            if condition_filter is not None and result.get('condition') != condition_filter:
                continue
            
            # Foil filter
            if foil_only and not result.get('foil', False):
                continue
            
            # Anomaly filter
            if anomaly_only and not result.get('is_anomaly', False):
                continue
            
            # Price range filters
            price = result.get('price_dollars', 0)
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            
            filtered.append(result)
        
        self.filtered_results = filtered
        self.update_results_table()
        self.update_anomalies_table()
        
        # Force table refresh
        self.results_table.viewport().update()
        if hasattr(self, 'anomalies_table'):
            self.anomalies_table.viewport().update()
    
    def clear_filters(self):
        """Clear all filters."""
        self.set_filter_combo.setCurrentIndex(0)
        self.condition_filter_combo.setCurrentIndex(0)
        self.foil_filter_check.setChecked(False)
        self.anomaly_filter_check.setChecked(False)
        self.min_price_combo.setCurrentText("")
        self.max_price_combo.setCurrentText("")
        self.apply_filters()
    
    def update_results_table(self):
        """Update the main results table."""
        results = self.filtered_results
        
        # Set up table
        self.results_table.setRowCount(len(results))
        self.results_table.setColumnCount(11)
        self.results_table.setHorizontalHeaderLabels([
            'Card Name', 'Set Code', 'Printing', 'Price', 'Condition', 
            'Foil', 'Anomaly', 'Score', 'Expected', 'Savings', 'Updated'
        ])
        
        # Populate table
        for row, result in enumerate(results):
            # Create clickable card name item
            card_name = result.get('card_name', '')
            card_item = ClickableCardItem(card_name, result)
            self.results_table.setItem(row, 0, card_item)
            self.results_table.setItem(row, 1, QTableWidgetItem(result.get('set_code', '')))
            self.results_table.setItem(row, 2, QTableWidgetItem(result.get('printing_info', '')))
            
            # Price with formatting
            price = result.get('price_dollars', 0)
            price_item = QTableWidgetItem(f"${price:.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.results_table.setItem(row, 3, price_item)
            
            self.results_table.setItem(row, 4, QTableWidgetItem(result.get('condition', '')))
            self.results_table.setItem(row, 5, QTableWidgetItem('Yes' if result.get('foil', False) else 'No'))
            
            # Anomaly status
            is_anomaly = result.get('is_anomaly', False)
            anomaly_item = QTableWidgetItem('Yes' if is_anomaly else 'No')
            if is_anomaly:
                anomaly_item.setBackground(QBrush(QColor(255, 255, 0, 100)))
            self.results_table.setItem(row, 6, anomaly_item)
            
            # Anomaly score
            score = result.get('anomaly_score', 0)
            score_item = QTableWidgetItem(f"{score:.3f}")
            score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if score > 0.7:
                score_item.setForeground(QBrush(QColor(255, 0, 0)))
            elif score > 0.3:
                score_item.setForeground(QBrush(QColor(255, 165, 0)))
            self.results_table.setItem(row, 7, score_item)
            
            # Expected price
            expected = result.get('expected_price', 0)
            expected_item = QTableWidgetItem(f"${expected:.2f}")
            expected_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.results_table.setItem(row, 8, expected_item)
            
            # Savings potential
            savings = result.get('savings_potential', 0)
            savings_item = QTableWidgetItem(f"${savings:.2f}")
            savings_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if savings > 0:
                savings_item.setForeground(QBrush(QColor(0, 128, 0)))
            self.results_table.setItem(row, 9, savings_item)
            
            # Timestamp
            timestamp = result.get('timestamp', '')
            if isinstance(timestamp, str):
                timestamp = timestamp[:19]  # Remove microseconds
            self.results_table.setItem(row, 10, QTableWidgetItem(str(timestamp)))
        
        # Auto-resize columns
        self.results_table.resizeColumnsToContents()
        
        # Update info label
        total_results = len(self.current_results)
        filtered_results = len(results)
        anomaly_count = sum(1 for r in results if r.get('is_anomaly', False))
        
        if total_results != filtered_results:
            self.results_info_label.setText(
                f"Showing {filtered_results} of {total_results} results ({anomaly_count} anomalies)"
            )
        else:
            self.results_info_label.setText(
                f"{filtered_results} results ({anomaly_count} anomalies)"
            )
    
    def update_anomalies_table(self):
        """Update the anomalies table."""
        anomalies = [r for r in self.filtered_results if r.get('is_anomaly', False)]
        
        # Set up table
        self.anomalies_table.setRowCount(len(anomalies))
        self.anomalies_table.setColumnCount(10)
        self.anomalies_table.setHorizontalHeaderLabels([
            'Card Name', 'Set Code', 'Printing', 'Price', 'Condition', 
            'Foil', 'Score', 'Expected', 'Savings', 'Updated'
        ])
        
        # Populate table
        for row, result in enumerate(anomalies):
            # Create clickable card name item
            card_name = result.get('card_name', '')
            card_item = ClickableCardItem(card_name, result)
            self.anomalies_table.setItem(row, 0, card_item)
            self.anomalies_table.setItem(row, 1, QTableWidgetItem(result.get('set_code', '')))
            self.anomalies_table.setItem(row, 2, QTableWidgetItem(result.get('printing_info', '')))
            
            # Price with formatting
            price = result.get('price_dollars', 0)
            price_item = QTableWidgetItem(f"${price:.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.anomalies_table.setItem(row, 3, price_item)
            
            self.anomalies_table.setItem(row, 4, QTableWidgetItem(result.get('condition', '')))
            self.anomalies_table.setItem(row, 5, QTableWidgetItem('Yes' if result.get('foil', False) else 'No'))
            
            # Anomaly score
            score = result.get('anomaly_score', 0)
            score_item = QTableWidgetItem(f"{score:.3f}")
            score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if score > 0.7:
                score_item.setForeground(QBrush(QColor(255, 0, 0)))
            elif score > 0.3:
                score_item.setForeground(QBrush(QColor(255, 165, 0)))
            self.anomalies_table.setItem(row, 6, score_item)
            
            # Expected price
            expected = result.get('expected_price', 0)
            expected_item = QTableWidgetItem(f"${expected:.2f}")
            expected_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.anomalies_table.setItem(row, 7, expected_item)
            
            # Savings potential
            savings = result.get('savings_potential', 0)
            savings_item = QTableWidgetItem(f"${savings:.2f}")
            savings_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if savings > 0:
                savings_item.setForeground(QBrush(QColor(0, 128, 0)))
            self.anomalies_table.setItem(row, 8, savings_item)
            
            # Timestamp
            timestamp = result.get('timestamp', '')
            if isinstance(timestamp, str):
                timestamp = timestamp[:19]  # Remove microseconds
            self.anomalies_table.setItem(row, 9, QTableWidgetItem(str(timestamp)))
        
        # Auto-resize columns
        self.anomalies_table.resizeColumnsToContents()
        
        # Update info label
        self.anomalies_info_label.setText(f"{len(anomalies)} anomalies found")
    
    def update_summary(self):
        """Update the summary tab."""
        if not self.current_results:
            self.summary_text.setText("No results to summarize")
            return
        
        # Calculate statistics
        total_results = len(self.current_results)
        anomaly_count = sum(1 for r in self.current_results if r.get('is_anomaly', False))
        
        # Price statistics
        prices = [r.get('price_dollars', 0) for r in self.current_results]
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        
        # Anomaly statistics
        if anomaly_count > 0:
            anomaly_scores = [r.get('anomaly_score', 0) for r in self.current_results if r.get('is_anomaly', False)]
            avg_anomaly_score = sum(anomaly_scores) / len(anomaly_scores) if anomaly_scores else 0
            
            savings_potential = [r.get('savings_potential', 0) for r in self.current_results if r.get('is_anomaly', False)]
            total_savings = sum(savings_potential) if savings_potential else 0
            avg_savings = total_savings / len(savings_potential) if savings_potential else 0
        else:
            avg_anomaly_score = 0
            total_savings = 0
            avg_savings = 0
        
        # Set breakdown
        sets = {}
        for result in self.current_results:
            set_code = result.get('set_code', 'Unknown')
            if set_code not in sets:
                sets[set_code] = {'count': 0, 'anomalies': 0}
            sets[set_code]['count'] += 1
            if result.get('is_anomaly', False):
                sets[set_code]['anomalies'] += 1
        
        # Condition breakdown
        conditions = {}
        for result in self.current_results:
            condition = result.get('condition', 'Unknown')
            if condition not in conditions:
                conditions[condition] = {'count': 0, 'anomalies': 0}
            conditions[condition]['count'] += 1
            if result.get('is_anomaly', False):
                conditions[condition]['anomalies'] += 1
        
        # Generate summary text
        summary = f"""Search Results Summary
========================

Total Results: {total_results}
Anomalies Found: {anomaly_count} ({anomaly_count/total_results*100:.1f}% of results)

Price Statistics:
- Average Price: ${avg_price:.2f}
- Minimum Price: ${min_price:.2f}
- Maximum Price: ${max_price:.2f}

Anomaly Statistics:
- Average Anomaly Score: {avg_anomaly_score:.3f}
- Total Savings Potential: ${total_savings:.2f}
- Average Savings per Anomaly: ${avg_savings:.2f}

Breakdown by Set:
"""
        
        for set_code, data in sorted(sets.items()):
            anomaly_pct = (data['anomalies'] / data['count']) * 100 if data['count'] > 0 else 0
            summary += f"- {set_code}: {data['count']} results, {data['anomalies']} anomalies ({anomaly_pct:.1f}%)\n"
        
        summary += "\nBreakdown by Condition:\n"
        for condition, data in sorted(conditions.items()):
            anomaly_pct = (data['anomalies'] / data['count']) * 100 if data['count'] > 0 else 0
            summary += f"- {condition}: {data['count']} results, {data['anomalies']} anomalies ({anomaly_pct:.1f}%)\n"
        
        # Top anomalies
        top_anomalies = sorted(
            [r for r in self.current_results if r.get('is_anomaly', False)],
            key=lambda x: x.get('anomaly_score', 0),
            reverse=True
        )[:10]
        
        if top_anomalies:
            summary += "\nTop 10 Anomalies (by score):\n"
            for i, anomaly in enumerate(top_anomalies, 1):
                summary += f"{i}. {anomaly.get('card_name', '')} ({anomaly.get('set_code', '')}) - ${anomaly.get('price_dollars', 0):.2f} (Score: {anomaly.get('anomaly_score', 0):.3f})\n"
        
        self.summary_text.setText(summary)
    
    def show_results_context_menu(self, position):
        """Show context menu for results table."""
        if self.results_table.itemAt(position) is None:
            return
        
        menu = QMenu()
        
        # Copy actions
        copy_name_action = QAction("Copy Card Name", self)
        copy_name_action.triggered.connect(lambda: self.copy_cell_value(self.results_table, 0))
        menu.addAction(copy_name_action)
        
        copy_price_action = QAction("Copy Price", self)
        copy_price_action.triggered.connect(lambda: self.copy_cell_value(self.results_table, 3))
        menu.addAction(copy_price_action)
        
        menu.addSeparator()
        
        # Filter actions
        filter_set_action = QAction("Filter by Set", self)
        filter_set_action.triggered.connect(lambda: self.filter_by_cell_value(self.results_table, 1, self.set_filter_combo))
        menu.addAction(filter_set_action)
        
        filter_condition_action = QAction("Filter by Condition", self)
        filter_condition_action.triggered.connect(lambda: self.filter_by_cell_value(self.results_table, 4, self.condition_filter_combo))
        menu.addAction(filter_condition_action)
        
        menu.exec(self.results_table.mapToGlobal(position))
    
    def show_anomalies_context_menu(self, position):
        """Show context menu for anomalies table."""
        if self.anomalies_table.itemAt(position) is None:
            return
        
        menu = QMenu()
        
        # Copy actions
        copy_name_action = QAction("Copy Card Name", self)
        copy_name_action.triggered.connect(lambda: self.copy_cell_value(self.anomalies_table, 0))
        menu.addAction(copy_name_action)
        
        copy_price_action = QAction("Copy Price", self)
        copy_price_action.triggered.connect(lambda: self.copy_cell_value(self.anomalies_table, 3))
        menu.addAction(copy_price_action)
        
        menu.exec(self.anomalies_table.mapToGlobal(position))
    
    def copy_cell_value(self, table, column):
        """Copy cell value to clipboard."""
        current_row = table.currentRow()
        if current_row >= 0:
            item = table.item(current_row, column)
            if item:
                from PySide6.QtWidgets import QApplication
                QApplication.clipboard().setText(item.text())
                self.status_message.emit("Copied to clipboard")
    
    def filter_by_cell_value(self, table, column, filter_combo):
        """Filter by cell value."""
        current_row = table.currentRow()
        if current_row >= 0:
            item = table.item(current_row, column)
            if item:
                value = item.text()
                # Find matching item in combo box
                for i in range(filter_combo.count()):
                    if filter_combo.itemText(i) == value:
                        filter_combo.setCurrentIndex(i)
                        break
                self.status_message.emit(f"Filtered by {value}")
    
    def clear_results(self):
        """Clear all results."""
        self.current_results = []
        self.filtered_results = []
        self.update_results_table()
        self.update_anomalies_table()
        self.update_summary()
        self.status_message.emit("Results cleared")