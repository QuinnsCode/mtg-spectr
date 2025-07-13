"""
Main entry point for the MTG Card Pricing Analysis Tool.
Initializes the application and handles startup procedures.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont

from config.settings import get_settings
from gui.main_window import MainWindow

# Configure logging
def setup_logging():
    """Set up application logging."""
    settings = get_settings()
    log_level = getattr(logging, settings.settings.log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = Path.home() / ".mtg_card_pricing" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up logging configuration
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "application.log"),
            logging.StreamHandler() if settings.settings.debug_mode else logging.NullHandler()
        ]
    )
    
    # Set up logger for this module
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")
    return logger


def create_splash_screen():
    """Create a splash screen for application startup."""
    # Create a simple splash screen
    splash_pixmap = QPixmap(400, 300)
    splash_pixmap.fill(Qt.white)
    
    splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pixmap.mask())
    
    # Add text to splash screen
    splash.showMessage(
        "MTG Card Pricing Analysis Tool\nLoading...",
        Qt.AlignCenter | Qt.AlignBottom,
        Qt.black
    )
    
    return splash


def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    # Check critical dependencies
    try:
        import PySide6
    except ImportError:
        missing_deps.append("PySide6")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import sklearn
    except ImportError:
        missing_deps.append("scikit-learn")
    
    if missing_deps:
        return False, missing_deps
    
    return True, []


def setup_application():
    """Set up the QApplication with proper settings."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("MTG Card Pricing Analysis Tool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MTG Tools")
    app.setOrganizationDomain("mtgtools.local")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    # Set global font
    settings = get_settings()
    font = QFont(settings.settings.gui.font_family, settings.settings.gui.font_size)
    app.setFont(font)
    
    # Set style sheet for better appearance
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QGroupBox {
            font-weight: bold;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QTableWidget {
            gridline-color: #d0d0d0;
            background-color: white;
            alternate-background-color: #f8f8f8;
        }
        QTableWidget::item:selected {
            background-color: #316AC5;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #a0a0a0;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #c0c0c0;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            border: 1px solid #a0a0a0;
            border-radius: 3px;
            padding: 2px;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 2px solid #316AC5;
        }
        QProgressBar {
            border: 1px solid #a0a0a0;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #316AC5;
            border-radius: 2px;
        }
        QStatusBar {
            background-color: #e0e0e0;
            border-top: 1px solid #a0a0a0;
        }
        QMenuBar {
            background-color: #e0e0e0;
            border-bottom: 1px solid #a0a0a0;
        }
        QMenuBar::item {
            padding: 4px 8px;
        }
        QMenuBar::item:selected {
            background-color: #316AC5;
            color: white;
        }
        QToolBar {
            background-color: #e0e0e0;
            border: 1px solid #a0a0a0;
            spacing: 3px;
        }
        QTabWidget::pane {
            border: 1px solid #a0a0a0;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #e0e0e0;
            border: 1px solid #a0a0a0;
            padding: 5px 10px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 1px solid white;
        }
        QTabBar::tab:hover {
            background-color: #d0d0d0;
        }
    """)
    
    return app


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler."""
    logger = logging.getLogger(__name__)
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Show error dialog to user
    QMessageBox.critical(
        None,
        "Critical Error",
        f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}\n\n"
        "Please check the log file for more details."
    )


def main():
    """Main application entry point."""
    # Set up logging first
    logger = setup_logging()
    logger.info("Starting MTG Card Pricing Analysis Tool")
    
    # Set up global exception handler
    sys.excepthook = handle_exception
    
    try:
        # Check dependencies
        deps_ok, missing_deps = check_dependencies()
        if not deps_ok:
            error_msg = f"Missing required dependencies: {', '.join(missing_deps)}\n\n" \
                       "Please install them using:\n" \
                       f"pip install {' '.join(missing_deps)}"
            
            # Try to show GUI error if PySide6 is available
            try:
                app = QApplication(sys.argv)
                QMessageBox.critical(None, "Missing Dependencies", error_msg)
            except:
                print(error_msg)
            
            sys.exit(1)
        
        # Create application
        app = setup_application()
        logger.info("Application created successfully")
        
        # Show splash screen
        splash = create_splash_screen()
        splash.show()
        app.processEvents()
        
        # Initialize main window
        splash.showMessage("Initializing database...", Qt.AlignCenter | Qt.AlignBottom, Qt.black)
        app.processEvents()
        
        main_window = MainWindow()
        
        splash.showMessage("Loading interface...", Qt.AlignCenter | Qt.AlignBottom, Qt.black)
        app.processEvents()
        
        # Show main window
        main_window.show()
        
        # Close splash screen after a delay
        QTimer.singleShot(2000, splash.close)
        
        logger.info("Application started successfully")
        
        # Run application event loop
        exit_code = app.exec()
        
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        
        # Try to show error dialog
        try:
            if 'app' in locals():
                QMessageBox.critical(None, "Startup Error", f"Failed to start application:\n\n{e}")
        except:
            print(f"Failed to start application: {e}")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())