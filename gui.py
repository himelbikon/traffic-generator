import sys
import time
import random
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QFileDialog, QTableWidget, QTableWidgetItem, 
                             QSpinBox, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import pandas as pd
import db
from visit_automation import visit_website


class VisitWorker(QThread):
    """Worker thread to handle URL visits without blocking the GUI"""
    progress_update = pyqtSignal(str, int)  # url, visit_count
    status_update = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, csv_path, visits_per_day):
        super().__init__()
        self.csv_path = csv_path
        self.visits_per_day = visits_per_day
        self.is_running = True
        self.is_paused = False
        
    def run(self):
        """Main worker loop"""
        while self.is_running:
            # Check if paused
            while self.is_paused and self.is_running:
                time.sleep(0.1)
            
            if not self.is_running:
                break
                
            all_sites_visited = self.visit_all_sites()
            
            if all_sites_visited:
                self.status_update.emit("All sites have enough visits for today")
                break
            
            # Calculate sleep time
            sleep_time = 10 * 3600 / max(self.visits_per_day - 2, 2)
            doped_sleep_time = sleep_time + random.randint(-int(sleep_time * 0.2), int(sleep_time * 0.2))
            
            hour = int(doped_sleep_time // 3600)
            minute = int((doped_sleep_time % 3600) // 60)
            
            self.status_update.emit(f"Sleeping for {hour}h {minute}m")
            
            # Sleep in small intervals to check for pause/stop
            sleep_intervals = int(doped_sleep_time / 0.5)
            for _ in range(sleep_intervals):
                if not self.is_running:
                    break
                while self.is_paused and self.is_running:
                    time.sleep(0.1)
                time.sleep(0.5)
        
        self.finished.emit()
    
    def visit_all_sites(self):
        """Visit all sites from CSV"""
        try:
            df = pd.read_csv(self.csv_path)
            all_site_visited = True
            
            for index, row in df.iterrows():
                if not self.is_running:
                    break
                    
                while self.is_paused and self.is_running:
                    time.sleep(0.1)
                
                url = row['URL']
                
                if self.had_enough_visits(url):
                    continue
                
                all_site_visited = False
                
                # Try to visit (with retry logic)
                for attempt in range(3):
                    try:
                        self.status_update.emit(f"Visiting: {url}")
                        # This visit website function will automatically stores visited url. Do not need to store here.
                        visit_website(url)
                        # db.add_visit(url)
                        
                        # Update progress
                        visit_count = db.count_visits_today(url)
                        self.progress_update.emit(url, visit_count)
                        break
                    except Exception as e:
                        self.status_update.emit(f"Error visiting {url}: {str(e)}")
                        if attempt == 2:
                            self.status_update.emit(f"Failed to visit {url} after 3 attempts")
            
            return all_site_visited
        except Exception as e:
            self.status_update.emit(f"Error reading CSV: {str(e)}")
            return True
    
    def had_enough_visits(self, url):
        """Check if URL has enough visits today"""
        visits = db.count_visits_today(url)
        if visits >= self.visits_per_day:
            self.status_update.emit(f"Already had enough visits ({visits}) for {url}")
            return True
        return False
    
    def stop(self):
        """Stop the worker"""
        self.is_running = False
    
    def pause(self):
        """Pause the worker"""
        self.is_paused = True
    
    def resume(self):
        """Resume the worker"""
        self.is_paused = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("URL Visit Automation")
        self.setMinimumSize(800, 600)
        
        self.csv_path = ""
        self.worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # CSV Upload Section
        csv_layout = QHBoxLayout()
        csv_layout.addWidget(QLabel("CSV File:"))
        self.csv_label = QLabel("No file selected")
        csv_layout.addWidget(self.csv_label)
        self.csv_btn = QPushButton("Browse")
        self.csv_btn.clicked.connect(self.browse_csv)
        csv_layout.addWidget(self.csv_btn)
        layout.addLayout(csv_layout)
        
        # Visits Per Day Section
        visits_layout = QHBoxLayout()
        visits_layout.addWidget(QLabel("Visits Per Day:"))
        self.visits_spinbox = QSpinBox()
        self.visits_spinbox.setMinimum(1)
        self.visits_spinbox.setMaximum(1000)
        self.visits_spinbox.setValue(20)
        visits_layout.addWidget(self.visits_spinbox)
        visits_layout.addStretch()
        layout.addLayout(visits_layout)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_automation)
        button_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_automation)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)
        
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.clicked.connect(self.continue_automation)
        self.continue_btn.setEnabled(False)
        button_layout.addWidget(self.continue_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Status Label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Visit Count Table
        layout.addWidget(QLabel("Today's Visit Counts:"))
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["URL", "Visits Today"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 500)
        layout.addWidget(self.table)
        
    def browse_csv(self):
        """Open file dialog to select CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.csv_path = file_path
            self.csv_label.setText(Path(file_path).name)
            self.load_initial_data()
    
    def load_initial_data(self):
        """Load initial visit counts from db.json"""
        try:
            # Load CSV
            df = pd.read_csv(self.csv_path)
            
            # Update table with current visit counts
            self.table.setRowCount(len(df))
            for i, row in df.iterrows():
                url = row['URL']
                self.table.setItem(i, 0, QTableWidgetItem(url))
                count = db.count_visits_today(url)
                self.table.setItem(i, 1, QTableWidgetItem(str(count)))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
    
    def start_automation(self):
        """Start the automation process"""
        if not self.csv_path:
            QMessageBox.warning(self, "Warning", "Please select a CSV file first")
            return
        
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.csv_btn.setEnabled(False)
        self.visits_spinbox.setEnabled(False)
        
        # Create and start worker
        self.worker = VisitWorker(
            self.csv_path, 
            self.visits_spinbox.value()
        )
        self.worker.progress_update.connect(self.update_table_row)
        self.worker.status_update.connect(self.update_status)
        self.worker.finished.connect(self.automation_finished)
        self.worker.start()
        
        self.status_label.setText("Automation running...")
    
    def pause_automation(self):
        """Pause the automation"""
        if self.worker:
            self.worker.pause()
            self.pause_btn.setEnabled(False)
            self.continue_btn.setEnabled(True)
            self.status_label.setText("Paused")
    
    def continue_automation(self):
        """Continue the automation"""
        if self.worker:
            self.worker.resume()
            self.pause_btn.setEnabled(True)
            self.continue_btn.setEnabled(False)
            self.status_label.setText("Automation running...")
    
    def update_table_row(self, url, count):
        """Update a specific row in the table"""
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).text() == url:
                self.table.setItem(i, 1, QTableWidgetItem(str(count)))
                break
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.setText(message)
    
    def automation_finished(self):
        """Handle automation completion"""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)
        self.csv_btn.setEnabled(True)
        self.visits_spinbox.setEnabled(True)
        self.status_label.setText("Automation completed")
        
        QMessageBox.information(self, "Complete", "Automation has finished")
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                'Automation is still running. Are you sure you want to exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

