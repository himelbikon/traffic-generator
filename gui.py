import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QTableWidget, 
                             QTableWidgetItem, QLabel, QHeaderView, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
import pandas as pd
from automation import visit_website


class ProcessorThread(QThread):
    """Thread for processing CSV rows without blocking the UI"""
    row_processed = pyqtSignal(int)  # Signal emitted when a row is processed
    processing_complete = pyqtSignal()  # Signal when all rows are done
    
    def __init__(self, csv_data, process_function):
        super().__init__()
        self.csv_data = csv_data
        self.process_function = process_function
        self.is_running = True
        
    def run(self):
        """Process each row of the CSV data"""
        for index, row in self.csv_data.iterrows():
            if not self.is_running:
                break
                
            # Call your automation script here
            # Pass the row data to your processing function
            self.process_function(row)
            
            # Emit signal that this row is processed
            self.row_processed.emit(row.name)
        
        self.processing_complete.emit()
    
    def stop(self):
        """Stop the processing"""
        self.is_running = False


class CSVProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.csv_data = None
        self.last_processed_row = 0
        self.total_rows = 0
        self.processor_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("CSV Processor - Selenium Automation")
        self.setGeometry(100, 100, 900, 600)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # File selection section
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.browse_btn = QPushButton("Browse CSV")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(QLabel("CSV File:"))
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.browse_btn)
        file_layout.addStretch()
        main_layout.addLayout(file_layout)
        
        # Table for CSV data
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.table)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_status)
        self.reset_btn.setEnabled(False)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.progress_bar = QProgressBar()
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide() # Hide initially
        self.statusBar().showMessage("Ready")
        
    def browse_file(self):
        """Open file dialog to select CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                self.load_csv(file_path)
                self.file_label.setText(file_path.split('/')[-1])
                self.start_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
                self.statusBar().showMessage("CSV loaded successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")
                
    def load_csv(self, file_path):
        """Load and display CSV data in table"""
        self.csv_data = pd.read_csv(file_path)
        
        self.total_rows = len(self.csv_data)
        self.progress_bar.setMaximum(self.total_rows)
        self.progress_bar.setValue(0)
        self.last_processed_row = 0
        
        # Set up table
        self.table.setRowCount(len(self.csv_data))
        self.table.setColumnCount(len(self.csv_data.columns) + 1)  # +1 for status column
        
        # Set headers
        headers = ["Status"] + list(self.csv_data.columns)
        self.table.setHorizontalHeaderLabels(headers)
        
        # Populate table with data
        for row_idx in range(len(self.csv_data)):
            # Status indicator column
            status_item = QTableWidgetItem("●")
            status_item.setForeground(QColor(255, 0, 0))  # Red
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, status_item)
            
            # Data columns
            for col_idx, col_name in enumerate(self.csv_data.columns):
                value = str(self.csv_data.iloc[row_idx, col_idx])
                item = QTableWidgetItem(value)
                self.table.setItem(row_idx, col_idx + 1, item)
        
        # Adjust column widths
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
    def start_processing(self):
        """Start processing CSV rows"""
        if self.csv_data is None:
            return
            
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.browse_btn.setEnabled(False)
        self.start_btn.setText("Continue")
        self.progress_bar.show()
        self.statusBar().showMessage("Processing...")
        
        # Create and start processing thread
        remaining_data = self.csv_data.iloc[self.last_processed_row:]
        self.processor_thread = ProcessorThread(remaining_data, self.process_row)
        self.processor_thread.row_processed.connect(self.update_row_status)
        self.processor_thread.processing_complete.connect(self.processing_finished)
        self.processor_thread.start()
        
    def stop_processing(self):
        """Stop the processing"""
        if self.processor_thread:
            self.processor_thread.stop()
            self.stop_btn.setEnabled(False)
            self.start_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.start_btn.setText("Continue")
            self.statusBar().showMessage("Processing stopped")
            
    def process_row(self, row_data):
        """
        This is where you integrate your automation script.
        Replace this function with your actual processing logic.
        
        Args:
            row_data: A pandas Series containing the row data
        """
        
        # visit_website(row_data['URL'])

        import time
        time.sleep(1)
        
    def update_row_status(self, row_index):
        """Update the status indicator for a processed row"""
        status_item = self.table.item(row_index, 0)
        status_item.setForeground(QColor(0, 255, 0))  # Green

        # Update progress bar
        self.progress_bar.setValue(row_index + 1)
        percentage = int(((row_index + 1) / self.total_rows) * 100)
        self.statusBar().showMessage(f"Processing... {percentage}%")

        self.last_processed_row = row_index + 1
        
    def processing_finished(self):
        """Called when all rows are processed"""
        self.progress_bar.hide()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.browse_btn.setEnabled(True)

        if self.processor_thread.is_running:
            proccess_message = f"All rows have been processed!"
            self.statusBar().showMessage("Processing complete!")
            self.last_processed_row = 0
            self.start_btn.setText("Start Processing")
        else:
            proccess_message = f"Processing stopped!"
            self.statusBar().showMessage("Processing stopped!")
            self.start_btn.setText("Continue")

        QMessageBox.information(self, "Complete", proccess_message)
        
    def reset_status(self):
        """Reset all status indicators to red"""
        for row_idx in range(self.table.rowCount()):
            status_item = self.table.item(row_idx, 0)
            status_item.setForeground(QColor(255, 0, 0))  # Red
        self.statusBar().showMessage("Status reset")
        self.last_processed_row = 0
        self.start_btn.setText("Start Processing")
        self.progress_bar.setValue(0)
        self.progress_bar.hide()


def main():
    app = QApplication(sys.argv)
    window = CSVProcessorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()