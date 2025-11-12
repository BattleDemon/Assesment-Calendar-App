# Assessment App (split side panels: Setup + Date Sidebar)
# - Left slide-in panel for Setup (file/year/classes)
# - Main view uses a splitter: Calendar on the left, a **date sidebar** on the right
# - Date sidebar lists all dates (in current month) that have tasks; clicking a date selects it
# - Calendar colouring now uses the **dominant class** for that date (no RGB averaging)

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QCalendarWidget,
    QLabel,
    QListWidgetItem,
    QMessageBox,
    QTextEdit,
    QFileDialog,
    QComboBox,
    QSplitter,
    QSizePolicy,
)
from PyQt6.QtGui import QTextCharFormat, QBrush, QColor, QFont
from PyQt6.QtCore import QDate, Qt

import os
import sys
import json
from pathlib import Path
import importlib.util
import pandas as pd
from datetime import datetime

APP_DIR = Path(os.path.dirname(__file__))
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATE_PATH = DATA_DIR / "ui_state.json"
EXTRACTOR_PATH = APP_DIR / "extractdata.py"

CLASS_COLORS = {
    "English": "#80002f",
    "Chemistry": "#00800f",
    "Essential Maths": "#F5F5DC",
    "Maths Methods": "#00ffff",
    "Specialist Maths": "#0047AB",
    "Psychology": "#800080",
    "Textiles": "#ffc0cb",
    "History": "#dc143c",
    "IT": "#03a062",
    "Human Biology": "#9fe2bf",
    "Exersise Science": "#009e4f",
    "Physics": "#ffff00",
    "Design Tech": "#a52a2a",
    "Visual Arts": "#FF8C00",
    "Drama": "#9966cc",
    "Music": "#70193d",
}

Y11_COLS = {"class": "11 - Class", "task": "11 - Task Name", "weight": "11 - Weighting", "type": "11 - Task Type", "notes": "11 - Other Notes"}
Y12_COLS = {"class": "12 - Class", "task": "12 - Task Name", "weight": "12 - Weighting", "type": "12 - Task Type", "notes": "12 - Other Notes"}
FIXED_COLUMNS = ["Week", "Day", "Date", "Events"]

# --- Minimal helpers ---

def run_extractor(path):
    if not EXTRACTOR_PATH.exists():
        return False
    spec = importlib.util.spec_from_file_location("extractdata", str(EXTRACTOR_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    func = getattr(mod, "extract_to_json", None)
    if callable(func):
        func(xlsx_path=path)
        return True
    return False


def read_data(year):
    path = DATA_DIR / ("year11.json" if year == 11 else "year12.json")
    cols = Y11_COLS if year == 11 else Y12_COLS
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_json(path)
    except Exception:
        return pd.DataFrame()
    out = pd.DataFrame({
        "Date": pd.to_datetime(df.get("Date", ""), errors='coerce').dt.strftime('%Y-%m-%d'),
        "Class": df.get(cols['class'], "").fillna(""),
        "Task": df.get(cols['task'], "").fillna(""),
        "Weighting": df.get(cols['weight'], "").fillna(""),
        "Type": df.get(cols['type'], "").fillna(""),
        "Notes": df.get(cols['notes'], "").fillna(""),
        "Events": df.get("Events", "").fillna(""),
    })
    return out.dropna(subset=['Date'])


class AssessmentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assessment Calendar")
        self.setGeometry(200, 100, 1200, 700)

        self.state = self.load_state()
        self.excel_path = self.state.get("excel_path", "")
        self.year = self.state.get("year", 11)
        self.classes = self.state.get("classes", [])
        self.df = pd.DataFrame()

        # Outer splitter: left slide-in setup panel, right main area
        self.outer_split = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.outer_split)

        self.build_setup_panel()
        self.build_main_area()

        self.outer_split.addWidget(self.setup_panel)
        self.outer_split.addWidget(self.main_area)
        self.outer_split.setSizes([0, 1])  # setup hidden by default

        self.show()
        if self.excel_path and self.classes:
            self.load_data()

    # ---------------- UI ----------------
    def build_setup_panel(self):
        self.setup_panel = QWidget()
        layout = QVBoxLayout(self.setup_panel)

        self.file_label = QLabel(self.excel_path or "No Excel selected")
        self.btn_browse = QPushButton("Choose Excel…")
        self.btn_scan = QPushButton("Scan for Classes")

        layout.addWidget(self.file_label)
        layout.addWidget(self.btn_browse)
        layout.addWidget(QLabel("Year:"))
        self.year_box = QComboBox()
        self.year_box.addItems(["11", "12"])
        # restore previous year
        idx = self.year_box.findText(str(self.year))
        if idx >= 0:
            self.year_box.setCurrentIndex(idx)
        layout.addWidget(self.year_box)

        layout.addWidget(QLabel("Select Classes:"))
        self.class_list = QListWidget()
        self.class_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.class_list, 1)

        self.btn_save = QPushButton("Save & Close")
        layout.addWidget(self.btn_scan)
        layout.addWidget(self.btn_save)

        self.btn_browse.clicked.connect(self.choose_file)
        self.btn_scan.clicked.connect(self.scan_excel)
        self.btn_save.clicked.connect(self.save_and_hide)

    def build_main_area(self):
        self.main_area = QWidget()
        main_v = QVBoxLayout(self.main_area)

        # Top row with toggle button
        top = QHBoxLayout()
        self.btn_toggle_setup = QPushButton("☰ Setup")
        top.addWidget(self.btn_toggle_setup)
        top.addStretch()
        main_v.addLayout(top)

        # Inner splitter: calendar on left, date sidebar on right
        self.inner_split = QSplitter(Qt.Orientation.Horizontal)
        main_v.addWidget(self.inner_split, 1)

        # Left: Calendar widget
        cal_wrap = QWidget()
        cal_v = QVBoxLayout(cal_wrap)
        self.calendar = QCalendarWidget()
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.NoHorizontalHeader)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        cal_v.addWidget(self.calendar)
        self.date_label = QLabel("No date selected")
        cal_v.addWidget(self.date_label)

        # Right: Date sidebar + tasks + details
        right_wrap = QWidget()
        right_v = QVBoxLayout(right_wrap)
        right_v.addWidget(QLabel("Dates with tasks (this month)"))
        self.date_list = QListWidget()
        right_v.addWidget(self.date_list, 1)
        right_v.addWidget(QLabel("Tasks on selected date"))
        self.task_list = QListWidget()
        right_v.addWidget(self.task_list, 1)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        right_v.addWidget(self.details, 2)

        self.inner_split.addWidget(cal_wrap)
        self.inner_split.addWidget(right_wrap)
        self.inner_split.setSizes([800, 400])

        # Signals
        self.btn_toggle_setup.clicked.connect(self.toggle_setup_panel)
        self.calendar.selectionChanged.connect(self.on_calendar_selected)
        self.calendar.currentPageChanged.connect(self.populate_date_sidebar)
        self.date_list.itemClicked.connect(self.on_date_sidebar_clicked)
        self.task_list.itemClicked.connect(self.show_details)

    # ------------- Setup panel logic -------------
    def toggle_setup_panel(self):
        if self.outer_split.sizes()[0] == 0:
            self.outer_split.setSizes([350, 850])
        else:
            self.outer_split.setSizes([0, 1])

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Excel", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.excel_path = path
            self.file_label.setText(path)

    def scan_excel(self):
        if not self.excel_path:
            QMessageBox.information(self, "Select file", "Choose an Excel file first.")
            return
        run_extractor(self.excel_path)
        year = int(self.year_box.currentText())
        df = read_data(year)
        if df.empty:
            QMessageBox.information(self, "No Data", "Could not read any classes.")
            return
        self.class_list.clear()
        for c in sorted(df['Class'].dropna().unique()):
            item = QListWidgetItem(c)
            if c in self.classes:
                item.setSelected(True)
            self.class_list.addItem(item)

    def save_and_hide(self):
        selected = [i.text() for i in self.class_list.selectedItems()]
        self.classes = selected
        self.year = int(self.year_box.currentText())
        self.save_state()
        self.load_data()
        self.toggle_setup_panel()

    # ------------- Data logic -------------
    def load_data(self):
        run_extractor(self.excel_path)
        df = read_data(self.year)
        self.df = df[df['Class'].isin(self.classes)] if not df.empty else pd.DataFrame()
        self.paint_calendar()
        self.populate_date_sidebar()
        self.on_calendar_selected()

    def paint_calendar(self):
        # Clear previous colouring
        clear_fmt = QTextCharFormat()
        for d in getattr(self, '_painted_dates', []):
            self.calendar.setDateTextFormat(d, clear_fmt)
        self._painted_dates = set()

        if self.df.empty:
            return

        # Choose dominant class per date (most tasks that day)
        # Build a frequency table: (Date, Class) -> count
        counts = self.df.groupby(['Date', 'Class']).size().reset_index(name='n')
        # For each date, pick the class with the max count
        for date_str, sub in counts.groupby('Date'):
            top_row = sub.sort_values('n', ascending=False).iloc[0]
            top_class = str(top_row['Class'])
            color = CLASS_COLORS.get(top_class, '#888888')
            qd = QDate.fromString(date_str, 'yyyy-MM-dd')
            if not qd.isValid():
                continue
            fmt = QTextCharFormat()
            fmt.setBackground(QBrush(QColor(color)))
            self.calendar.setDateTextFormat(qd, fmt)
            self._painted_dates.add(qd)

    def populate_date_sidebar(self):
        self.date_list.clear()
        if self.df.empty:
            return
        # Compute current visible month in the calendar
        year = self.calendar.yearShown()
        month = self.calendar.monthShown()
        # All dates in that month which have at least one task
        mask = self.df['Date'].str.slice(0, 7) == f"{year:04d}-{month:02d}"
        dates_in_month = sorted(self.df.loc[mask, 'Date'].unique())
        for d in dates_in_month:
            item = QListWidgetItem(d)
            self.date_list.addItem(item)
        # Try to select current date in the list
        cur = self.calendar.selectedDate().toString('yyyy-MM-dd')
        matches = self.date_list.findItems(cur, Qt.MatchFlag.MatchExactly)
        if matches:
            self.date_list.setCurrentItem(matches[0])

    def on_date_sidebar_clicked(self, item: QListWidgetItem):
        # Sync selection back to calendar
        date_str = item.text()
        qd = QDate.fromString(date_str, 'yyyy-MM-dd')
        if qd.isValid():
            self.calendar.setSelectedDate(qd)
            self.on_calendar_selected()

    def on_calendar_selected(self):
        if self.df.empty:
            return
        date = self.calendar.selectedDate().toString('yyyy-MM-dd')
        self.date_label.setText(date)
        # Keep sidebar selection in sync
        matches = self.date_list.findItems(date, Qt.MatchFlag.MatchExactly)
        if matches:
            self.date_list.setCurrentItem(matches[0])
        # Fill tasks
        day = self.df[self.df['Date'] == date].copy()
        day = day.sort_values(['Class', 'Task'])
        self.task_list.clear()
        for _, r in day.iterrows():
            item = QListWidgetItem(f"{r['Class']} — {r['Task']}")
            item.setData(Qt.ItemDataRole.UserRole, r.to_dict())
            # Color task item with its class colour
            col = CLASS_COLORS.get(str(r['Class']), '#eeeeee')
            item.setBackground(QBrush(QColor(col)))
            self.task_list.addItem(item)
        # Auto-show first task's details
        first = self.task_list.item(0)
        if first:
            self.task_list.setCurrentItem(first)
            self.show_details(first)
        else:
            self.details.clear()

    def show_details(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        html = (f"<b>Class:</b> {data['Class']}<br>"
                f"<b>Task:</b> {data['Task']}<br>"
                f"<b>Type:</b> {data['Type']}<br>"
                f"<b>Weighting:</b> {data['Weighting']}<br>"
                f"<b>Notes:</b> {data['Notes']}<br>"
                f"<b>Events:</b> {data['Events']}")
        self.details.setHtml(html)

    # ------------- Save/Load -------------
    def save_state(self):
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump({'excel_path': self.excel_path, 'year': self.year, 'classes': self.classes}, f, indent=2)

    def load_state(self):
        if STATE_PATH.exists():
            with open(STATE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = AssessmentApp()
    sys.exit(app.exec())