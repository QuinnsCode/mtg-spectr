#!/usr/bin/env python3
"""
Fix for search results not displaying in the GUI.
This script identifies and provides solutions for the issue.
"""

import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def analyze_issue():
    """Analyze the search display issue."""
    
    print("=== ANALYZING SEARCH DISPLAY ISSUE ===\n")
    
    print("Based on code analysis, the likely issues are:\n")
    
    print("1. FILTER INITIALIZATION:")
    print("   - In results_widget.py, filters might be too restrictive")
    print("   - The condition_filter_combo starts with 'All Conditions' but has empty data")
    print("   - This could cause filtering to exclude all results\n")
    
    print("2. TABLE UPDATE ISSUE:")
    print("   - The results_table might not be properly refreshing")
    print("   - Qt table widgets sometimes need explicit refresh calls\n")
    
    print("3. SIGNAL TIMING:")
    print("   - Results might be emitted before the widget is ready")
    print("   - Thread timing issues could cause race conditions\n")

def generate_fix():
    """Generate the fix for the issue."""
    
    print("\n=== RECOMMENDED FIXES ===\n")
    
    print("Fix 1: Update results_widget.py apply_filters method")
    print("----------------------------------------------")
    print("""
In results_widget.py, around line 330, modify the apply_filters method:

    def apply_filters(self):
        '''Apply current filters to results.'''
        if not self.current_results:
            self.filtered_results = []
            self.update_results_table()
            self.update_anomalies_table()
            return
        
        filtered = []
        
        # Get filter values
        set_filter = self.set_filter_combo.currentData()
        condition_filter = self.condition_filter_combo.currentData()
        
        # FIX: Check if filter has valid data, not just current text
        if self.condition_filter_combo.currentIndex() == 0:
            condition_filter = None  # "All Conditions" selected
""")
    
    print("\nFix 2: Add logging to display_results")
    print("------------------------------------")
    print("""
In results_widget.py, add logging to the display_results method:

    def display_results(self, results: List[Dict]):
        '''Display search results in the tables.'''
        logger.info(f"ResultsWidget: Received {len(results)} results to display")
        
        self.current_results = results
        
        # Update filter options
        self.update_filter_options()
        
        # Apply current filters
        self.apply_filters()
        
        # Log filtered results count
        logger.info(f"ResultsWidget: After filtering, showing {len(self.filtered_results)} results")
        
        # Update summary
        self.update_summary()
        
        self.status_message.emit(f"Displaying {len(results)} results")
""")
    
    print("\nFix 3: Force table refresh in update_results_table")
    print("------------------------------------------------")
    print("""
In results_widget.py, at the end of update_results_table method, add:

        # Auto-resize columns
        self.results_table.resizeColumnsToContents()
        
        # Force table refresh
        self.results_table.viewport().update()
        
        # Ensure table is visible
        if self.results_table.rowCount() > 0:
            self.results_table.setVisible(True)
            self.results_table.scrollToTop()
""")
    
    print("\nFix 4: Debug SearchWorker signal emission")
    print("---------------------------------------")
    print("""
In search_widget.py, modify on_search_completed to add logging:

    def on_search_completed(self, results: List[Dict]):
        '''Handle search completion.'''
        logger.info(f"SearchWidget: Search completed with {len(results)} results")
        
        # Emit the signal
        self.search_completed.emit(results)
        logger.info(f"SearchWidget: Emitted search_completed signal")
        
        count = len(results)
        anomaly_count = sum(1 for r in results if r.get('is_anomaly', False))
        
        self.status_label.setText(f"Found {count} results ({anomaly_count} anomalies)")
        self.status_message.emit(f"Search completed: {count} results found")
""")

def create_patch_file():
    """Create a patch file with the fixes."""
    
    patch_content = """--- a/mtg_card_pricing/gui/results_widget.py
+++ b/mtg_card_pricing/gui/results_widget.py
@@ -280,6 +280,7 @@ class ResultsWidget(QWidget):
     def display_results(self, results: List[Dict]):
         '''Display search results in the tables.'''
+        logger.info(f"ResultsWidget: Received {len(results)} results to display")
         self.current_results = results
         
         # Update filter options
@@ -288,6 +289,9 @@ class ResultsWidget(QWidget):
         # Apply current filters
         self.apply_filters()
         
+        # Log filtered results count
+        logger.info(f"ResultsWidget: After filtering, showing {len(self.filtered_results)} results")
+        
         # Update summary
         self.update_summary()
         
@@ -328,6 +332,10 @@ class ResultsWidget(QWidget):
         set_filter = self.set_filter_combo.currentData()
         condition_filter = self.condition_filter_combo.currentData()
         
+        # FIX: Check if filter has valid data
+        if self.condition_filter_combo.currentIndex() == 0:
+            condition_filter = None  # "All Conditions" selected
+        
         foil_only = self.foil_filter_check.isChecked()
         anomaly_only = self.anomaly_filter_check.isChecked()
         
@@ -456,6 +464,12 @@ class ResultsWidget(QWidget):
         # Auto-resize columns
         self.results_table.resizeColumnsToContents()
         
+        # Force table refresh
+        self.results_table.viewport().update()
+        
+        # Ensure table is visible
+        if self.results_table.rowCount() > 0:
+            self.results_table.scrollToTop()
+        
         # Update info label
         total_results = len(self.current_results)

--- a/mtg_card_pricing/gui/search_widget.py
+++ b/mtg_card_pricing/gui/search_widget.py
@@ -514,6 +514,10 @@ class SearchWidget(QWidget):
     
     def on_search_completed(self, results: List[Dict]):
         '''Handle search completion.'''
+        logger.info(f"SearchWidget: Search completed with {len(results)} results")
+        
+        # Emit the signal
         self.search_completed.emit(results)
+        logger.info(f"SearchWidget: Emitted search_completed signal")
         
         count = len(results)
"""
    
    with open('fix_search_display.patch', 'w') as f:
        f.write(patch_content)
    
    print("\n\nPatch file created: fix_search_display.patch")
    print("To apply the patch, run: patch -p1 < fix_search_display.patch")

if __name__ == "__main__":
    analyze_issue()
    generate_fix()
    create_patch_file()
    
    print("\n\n=== IMMEDIATE WORKAROUND ===")
    print("If you need an immediate fix without modifying code:")
    print("1. After searching, click 'Clear Filters' button in the results panel")
    print("2. This will reset any problematic filter states")
    print("3. Results should then be visible")