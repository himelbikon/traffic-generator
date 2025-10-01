import time
from pathlib import Path
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QFileDialog, QTableWidget, QTableWidgetItem, 
                             QSpinBox, QMessageBox, QTextEdit)
from PyQt6.QtCore import QThread, pyqtSignal
import pandas as pd
import db
from visit_automation import visit_website
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QDialogButtonBox


class ProxyDialog(QDialog):
    def __init__(self, proxies, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Proxies")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.proxy_input = QTextEdit()
        self.proxy_input.setPlaceholderText("IP:PORT or IP:PORT:USER:PASS\nEach proxy on a new line.")
        self.proxy_input.setText("\n".join(proxies))
        layout.addWidget(self.proxy_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_proxies(self):
        proxies = self.proxy_input.toPlainText().split('\n')
        return [p.strip() for p in proxies if p.strip()]



class VisitWorker(QThread):
    """Worker thread to handle URL visits without blocking the GUI"""
    progress_update = pyqtSignal(str, int)  # url, visit_count
    status_update = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, csv_path, proxy=None):
        super().__init__()
        self.csv_path = csv_path
        self.proxy = proxy

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
                
            self.visit_all_sites()
            
            # Calculate sleep time
            sleep_time = 5
            # sleep_time = 10
            doped_sleep_time = sleep_time
            
            remaining_time = int(doped_sleep_time)
            while remaining_time > 0 and self.is_running:
                while self.is_paused and self.is_running:
                    time.sleep(0.1)

                if not self.is_running:
                    break

                self.status_update.emit("💤 Taking a short break... planning the next visit.")
                time.sleep(1)
                remaining_time -= 1
        
        self.finished.emit()
    
    def visit_all_sites(self):
        """Visit all sites from CSV"""
        try:
            df = pd.read_csv(self.csv_path, encoding='latin-1')
            
            for index, row in df.iterrows():
                if not self.is_running:
                    break
                    
                while self.is_paused and self.is_running:
                    time.sleep(0.1)
                
                url = row['URL']
                visits_target = row['Visits Target']
                
                if self.should_avoid_visit(url, visits_target):
                    continue
                
                # Try to visit (with retry logic)
                for attempt in range(3):
                    print(f'--> Attepting to visit {url} (Attempt {attempt + 1}/3)...')
                    try:
                        self.status_update.emit(f"Visiting: {url}")
                        # This visit website function will automatically stores visited url. Do not need to store here.
                        visit_website(url, self, self.proxy)
                        # db.add_visit(url)
                        
                        # Update progress
                        visit_count = db.count_visits_today(url)
                        self.progress_update.emit(url, visit_count)
                        break
                    except Exception as e:
                        self.status_update.emit(f"Error visiting {url}: {str(e)}")
                        if attempt == 2:
                            self.status_update.emit(f"Failed to visit {url} after 3 attempts")
                        print(f"❌ Error visiting {url}: {str(e)}")
            
            return
        except Exception as e:
            self.status_update.emit(f"Error reading CSV: {str(e)}")
            print(f"❌ Error reading CSV: {str(e)}")
            return True
    
    def should_avoid_visit(self, url, visits_target):
        """
        Check if we should avoid visiting a website due to enough visits or time since last visit.

        Args:
            url (str): URL of the website
            visits_target (int): Target number of visits for the website

        Returns:
            bool: True if we should avoid visiting the website, False otherwise
        """

        visits = db.count_visits_today(url)
        if visits >= visits_target:
            self.status_update.emit(f"Already had enough visits ({visits}) for {url}")
            return True

        last_visit_time = db.last_visit_time(url)

        if last_visit_time:
            time_diff = datetime.now() - last_visit_time

            wait_time = 10 * 3600 / visits_target

            if time_diff < timedelta(seconds=wait_time):
                self.status_update.emit(f"Not enough time has passed since last visit for {url}")
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
        self.setWindowTitle("Traffic Generator")
        self.setWindowIcon(QIcon("assets/logo.ico"))
        self.setMinimumSize(800, 600)
        
        self.csv_path = ""
        self.worker = None
        self.proxies = []
        
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
        
        # Proxy Section
        proxy_layout = QHBoxLayout()
        proxy_layout.addWidget(QLabel("Proxies:"))
        self.proxy_btn = QPushButton("Manage Proxies")
        self.proxy_btn.clicked.connect(self.open_proxy_dialog)
        proxy_layout.addWidget(self.proxy_btn)
        layout.addLayout(proxy_layout)
        

        
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
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["URL", "Visits Target", "Visits Today"])
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
            df = pd.read_csv(self.csv_path, encoding='latin-1')
            
            # Update table with current visit counts
            self.table.setRowCount(len(df))
            for i, row in df.iterrows():
                url = row['URL']
                visits_target = row['Visits Target']
                self.table.setItem(i, 0, QTableWidgetItem(url))
                self.table.setItem(i, 1, QTableWidgetItem(str(visits_target)))
                count = db.count_visits_today(url)
                self.table.setItem(i, 2, QTableWidgetItem(str(count)))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
    
    def open_proxy_dialog(self):
        """Open the proxy management dialog"""
        dialog = ProxyDialog(self.proxies, self)
        if dialog.exec():
            self.proxies = dialog.get_proxies()

    def start_automation(self):
        """Start the automation process"""
        if not self.csv_path:
            QMessageBox.warning(self, "Warning", "Please select a CSV file first")
            return
        
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.csv_btn.setEnabled(False)

        self.worker = VisitWorker(
            self.csv_path,
            proxy=self.proxies
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
            self.worker.proxy = self.proxies
            self.worker.resume()
            self.pause_btn.setEnabled(True)
            self.continue_btn.setEnabled(False)
            self.status_label.setText("Automation running...")
    
    def update_table_row(self, url, count):
        """Update a specific row in the table"""
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).text() == url:
                self.table.setItem(i, 2, QTableWidgetItem(str(count)))
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
                # self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

