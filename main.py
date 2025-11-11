from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QStackedWidget,
    QCalendarWidget,
    QLabel,
    QSpinBox,
    QTextEdit,
    QInputDialog,
    QComboBox,
    QListWidgetItem,
    QMessageBox,
    QTimeEdit,
    QLineEdit,
    QTabWidget,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView
) 
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QTextCharFormat, QBrush, QColor, QFont, QPainter
from PyQt6.QtCore import QTime, QRect
from datetime import datetime
import json
import os
import sys

from extractdata import extract_sheet1_json

extract_sheet1_json(xlsx_path="Test Senior Assessment Calendar (6).xlsx", outdir="./data")

# KEEP Special Comment
'''
COOLEST PROJECT EVER. *EXPLOSION SFX*
'''

class EntryPage():
    pass


class CalendarApp(QMainWindow):
    def __init__(self):
        super(CalendarApp, self).__init__()

        self.setWindowTitle("Assessment Calendar")
        self.setGeometry(200, 100, 1000, 600)

        # Central widget and main horizontal layout
        self.central_widget = QWidget() 
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)

        self.stacked = QStackedWidget()
        main_layout.addWidget(self.stacked, 3)

        self.show()
        

        # Calendar page setup
        self.calendar_page = QWidget()
        cal_layout = QVBoxLayout(self.calendar_page)
        self.calendar = QCalendarWidget()
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.NoHorizontalHeader)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        cal_layout.addWidget(self.calendar)
        self.stacked.addWidget(self.calendar_page)

        testDate = QDate()
        austrianPainter = QPainter()

        # Side Bar
        self.side_bar = QWidget()
        sidebar_layout = QVBoxLayout(self.side_bar)

        self.stacked.addWidget(self.side_bar)

        self.filterReleventData()

    def filterReleventData(self):

        # Load user Data and store what classes the user does
        
        try:
            with open('settings/settings.json', 'r') as file:
                data = json.load(file)
                print(data)
                self.userclasses = data["classes"]
                self.year = data["user"]["year"]
        except FileNotFoundError:
            print("Error: 'data.json' not found.")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in 'data.json'.")

    def ColorAssesmentTasks(self):
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = CalendarApp()
    sys.exit(app.exec())


