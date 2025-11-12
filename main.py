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

        # Side Bar
        self.side_bar = QWidget()
        sidebar_layout = QVBoxLayout(self.side_bar)
        self.stacked.addWidget(self.side_bar)

        # state
        self.records = []
        self.by_date = {}
        self.user_classes = []
        self.year = None

        # load settings and data, then paint
        self.filterReleventData()
        self.load_records()
        self.refresh_index()
        self.paint_calendar()

    def filterReleventData(self):
        # Load user data and store what classes the user does
        with open(SETTINGS_DIR / "settings.json", 'r', encoding="utf-8") as file:
            data = json.load(file)
        self.user_classes = data.get("classes", [])
        self.year = data.get("user", {}).get("year", None)

    def load_records(self):
        # try combined first
        self.records = []
        try:
            self.records = json.loads((DATA_DIR / "combined.json").read_text(encoding="utf-8"))
        except:
            pass
        # if not present, try both year files
        if not self.records:
            for name in ["year11.json", "year12.json"]:
                p = DATA_DIR / name
                try:
                    rows = json.loads(p.read_text(encoding="utf-8"))
                    if isinstance(rows, list):
                        self.records.extend(rows)
                except:
                    pass

    def refresh_index(self):
        # group all records by date, keep only the student's classes
        self.by_date = {}
        for r in self.records:
            d = str(r.get("Date", "")).strip()
            if not d:
                continue
            if self.user_classes and r.get("Class") not in self.user_classes:
                continue
            self.by_date.setdefault(d, []).append(r)

    def class_colour_for_date(self, items_for_date):
        # classes on this date that the student actually takes
        matches = []
        for r in items_for_date:
            c = r.get("Class", "")
            if c in self.user_classes:
                matches.append(c)

        if not matches:
            return QColor(180, 180, 180)  # grey if no match

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
            # choose class to color by: most frequent class on that date that the student actually takes
            matches = []
            for r in items:
                c = r.get("Class", "")
                if c in self.user_classes:
                    matches.append(c)

            # default grey if nothing matches
            col = QColor(180, 180, 180)

            if matches:
                class_choice = max(set(matches), key=matches.count)
                hx = self.class_colors.get(class_choice)
                if isinstance(hx, str):
                    s = hx.strip()
                    if not s.startswith("#"):
                        s = "#" + s
                    if len(s) == 8:
                        s = s[:7]
                    if len(s) == 7:
                        try:
                            col = QColor(s)
                        except:
                            pass

            # paint the date cell
            y, m, dd = [int(x) for x in d.split("-")]
            qd = QDate(y, m, dd)
            fmt = QTextCharFormat()
            fmt.setBackground(QBrush(col))
            self.calendar.setDateTextFormat(qd, fmt)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = CalendarApp()
    sys.exit(app.exec())


