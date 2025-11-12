from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QCalendarWidget,
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QTextCharFormat, QBrush, QColor
import json
import sys
from pathlib import Path

DATA_DIR = Path("data")
SETTINGS_DIR = Path("settings")
COLOR_FILE = SETTINGS_DIR / "classColor.json"

from extractdata import extract_to_json

# build jsons on launch (remove if you already have data/*.json)
extract_to_json(xlsx_path="Test Senior Assessment Calendar (6).xlsx", outdir=DATA_DIR)

# KEEP Special Comment
'''
COOLEST PROJECT EVER. *EXPLOSION SFX*
'''

def load_class_colors():
    with open(COLOR_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def qcolor_from_hex(hx):
    if not isinstance(hx, str):
        return None
    s = hx.strip()
    if not s.startswith("#"):
        s = "#" + s
    if len(s) == 8:  # fix "#03a062D"
        s = s[:7]
    if len(s) == 7:
        try:
            return QColor(s)
        except:
            return None
    return None


class CalendarApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Assessment Calendar")
        self.setGeometry(200, 100, 1000, 600)

        # calendar only
        self.central = QWidget()
        self.setCentralWidget(self.central)
        v = QVBoxLayout(self.central)

        self.calendar = QCalendarWidget()
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.NoHorizontalHeader)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        v.addWidget(self.calendar)

        # state
        self.class_colors = load_class_colors()
        self.user_classes = []
        self.records = []
        self.by_date = {}
        self._highlighted_dates = set()

        # load settings and data, then paint
        self.load_settings()
        self.load_records()
        self.build_index()
        self.highlight_by_class()

        # repaint when month changes
        self.calendar.currentPageChanged.connect(lambda *_: self.highlight_by_class())

    def load_settings(self):
        with open(SETTINGS_DIR / "settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.user_classes = data.get("classes", [])

    def load_records(self):
        # try combined first
        try:
            self.records = json.loads((DATA_DIR / "combined.json").read_text(encoding="utf-8"))
            if not isinstance(self.records, list):
                self.records = []
        except:
            self.records = []

        # if not present, try both years
        if not self.records:
            out = []
            for name in ["year11.json", "year12.json"]:
                p = DATA_DIR / name
                try:
                    rows = json.loads(p.read_text(encoding="utf-8"))
                    if isinstance(rows, list):
                        out.extend(rows)
                except:
                    pass
            self.records = out

    def build_index(self):
        self.by_date = {}
        for r in self.records:
            d = str(r.get("Date", "")).strip()
            if not d:
                continue
            if self.user_classes and r.get("Class") not in self.user_classes:
                continue
            self.by_date.setdefault(d, []).append(r)

    def _clear_calendar_formats(self):
        if self._highlighted_dates:
            default_fmt = QTextCharFormat()
            for qd in self._highlighted_dates:
                self.calendar.setDateTextFormat(qd, default_fmt)
            self._highlighted_dates.clear()

    def highlight_by_class(self):
        # refresh data groups each time in case something changed
        self.build_index()

        # clear previous highlights
        self._clear_calendar_formats()

        for date_str, items in self.by_date.items():
            # pick class by most frequent among the student's classes for that date
            matches = []
            for r in items:
                c = r.get("Class", "")
                if c in self.user_classes:
                    matches.append(c)

            col = QColor(180, 180, 180)  # default grey

            chosen_class = None
            if matches:
                chosen_class = max(set(matches), key=matches.count)
            else:
                # fallback: first class with a defined colour
                for r in items:
                    c = r.get("Class", "")
                    if c in self.class_colors:
                        chosen_class = c
                        break

            if chosen_class:
                qc = qcolor_from_hex(self.class_colors.get(chosen_class))
                if qc:
                    col = qc

            qd = QDate.fromString(date_str, "yyyy-MM-dd")
            if qd.isValid():
                fmt = QTextCharFormat()
                fmt.setBackground(QBrush(col))
                self.calendar.setDateTextFormat(qd, fmt)
                self._highlighted_dates.add(qd)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CalendarApp()
    win.show()
    sys.exit(app.exec())
