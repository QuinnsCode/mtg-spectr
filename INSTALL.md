# MTG Card Pricing Analysis Tool - Installation & Setup

## Quick Fix for Import Error

The import error you encountered has been **FIXED**. The issue was that `QAction` was being imported from both `QtWidgets` and `QtGui` modules, but in PySide6, `QAction` is only available in `QtGui`.

### What was fixed:
- Removed duplicate `QAction` import from `QtWidgets`
- Kept only the correct import from `QtGui`

## Installation Instructions

### 1. Install Dependencies
```bash
# Navigate to the project directory
cd C:\Users\mikeb\PycharmProjects\PythonProject\mtg_card_pricing

# Install required packages
pip install -r requirements.txt
```

### 2. Test the Installation
```bash
# Run the import test to verify everything works
python test_imports.py
```

### 3. Run the Application
```bash
# Launch the MTG Card Pricing Analysis Tool
python main.py
```

## Dependencies Required

The application requires the following packages (as specified in `requirements.txt`):

```
PySide6>=6.5.0          # GUI framework
requests>=2.28.0        # API client
pandas>=1.5.0           # Data processing
numpy>=1.24.0           # Numerical computing
scikit-learn>=1.3.0     # Machine learning
matplotlib>=3.6.0       # Visualization
cryptography>=41.0.0    # Security encryption
```

## Troubleshooting

### If you get import errors:
1. Make sure you're using the correct Python environment
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Run the test script: `python test_imports.py`

### If PySide6 installation fails:
```bash
# Try upgrading pip first
python -m pip install --upgrade pip

# Then install PySide6
pip install PySide6
```

### Virtual Environment (Recommended):
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix/MacOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## First Run

1. **Install dependencies**: Follow the installation instructions above
2. **Run the application**: `python main.py`
3. **Configure API**: Go to Settings → API Configuration and enter your JustTCG API key
4. **Start analyzing**: Use the search interface to find underpriced MTG cards

## Security Notes

- API keys are encrypted and stored securely
- All user inputs are validated to prevent security issues
- The application uses parameterized database queries to prevent SQL injection

## Support

If you encounter any issues:
1. Run `python test_imports.py` to verify all imports work
2. Check that all dependencies are properly installed
3. Ensure you're using Python 3.8 or higher

The QAction import issue has been resolved and the application should now run correctly!