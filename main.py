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

class CalendarApp(QMainWindow):
    def __init__(self):
        super(CalendarApp, self).__init__()

        self.setWindowTitle("Assesment Calendar")

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = CalendarApp()
    sys.exit(app.exec())


