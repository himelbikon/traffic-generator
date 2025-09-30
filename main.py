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
from gui import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()