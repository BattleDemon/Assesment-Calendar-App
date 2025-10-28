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
from PyQt6.QtGui import QTextCharFormat, QBrush, QColor, QFont
from PyQt6.QtCore import QTime
from datetime import datetime
import json
import os
import sys



class EntryPage():
    pass

class MainPage():
        def __init__(self):
            # Central widget and main horizontal layout
            self.central_widget = QWidget() 
            self.setCentralWidget(self.central_widget)
            main_layout = QHBoxLayout(self.central_widget)

            calendar = QCalendarWidget()

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

    def importDataFromExcel(self):
         pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = CalendarApp()
    sys.exit(app.exec())


