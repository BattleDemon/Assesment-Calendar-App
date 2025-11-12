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
from pathlib import Path

DATA_DIR =  Path("data")
SETTINGS_DIR = Path("settings")

COLOR_FILE = SETTINGS_DIR / "classColor.json"

from extractdata import extract_to_json

extract_to_json(xlsx_path="Test Senior Assessment Calendar (6).xlsx", outdir=DATA_DIR)

# KEEP Special Comment
'''
COOLEST PROJECT EVER. *EXPLOSION SFX*
'''


def load_class_colors():
    with open(COLOR_FILE, "r", encoding="utf-8") as f:
        COLORS = json.load(f)
    return COLORS

def qcolor_from_hex(hx):
    if not isinstance(hx, str):
        return None
    s = hx.strip()
    if not s.startswith("#"):
        s = "#" + s
    # fix accidental 7-digit hex like "#03a062D" by trimming
    if len(s) == 8:
        s = s[:7]
    if len(s) == 7:
        return QColor(s)
    


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

        self.class_colors = load_class_colors()
        

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

        self.paint_calendar()

    def filterReleventData(self):

        # Load user Data and store what classes the user does
        
        with open(SETTINGS_DIR / "settings.json", 'r') as file:
            data = json.load(file)
            print(data)
            self.userclasses = data["classes"]
            self.year = data["user"]["year"]

    def class_colour_for_date(self, items_for_date):
        # look at all classes on this date that match the student's class list
        matches = []
        for r in items_for_date:
            c = r.get("Class", "")
            if c in self.user_classes:
                matches.append(c)

        if not matches:
            return QColor(180, 180, 180)   # grey if no match

        # pick whichever class appears most
        best = max(set(matches), key=matches.count)
        qc = qcolor_from_hex(self.class_colors.get(best))
        if qc:
            return qc

        # fallback colour if missing from file
        n = len(items_for_date)
        if n == 1:
            return QColor(60, 170, 90)
        elif n == 2:
            return QColor(200, 120, 50)
        else:
            return QColor(200, 60, 60)


    def paint_calendar(self):
        for d, items in self.by_date.items():
            try:
                y, m, dd = [int(x) for x in d.split("-")]
                qd = QDate(y, m, dd)
            except:
                continue
            col = self.class_colour_for_date(items)
            fmt = QTextCharFormat()
            fmt.setBackground(QBrush(col))
            self.calendar.setDateTextFormat(qd, fmt)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = CalendarApp()
    sys.exit(app.exec())


