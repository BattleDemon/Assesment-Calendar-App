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

# -------------------------------
# File system locations and state
# -------------------------------
# APP_DIR is the folder that contains this Python file.
APP_DIR = Path(os.path.dirname(__file__))
# DATA_DIR stores generated JSON files and user state.
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# STATE_PATH stores lightweight UI settings such as last Excel path, chosen year, and classes.
STATE_PATH = DATA_DIR / "ui_state.json"
# EXTRACTOR_PATH is the helper script which converts the Excel workbook into JSON files.
EXTRACTOR_PATH = APP_DIR / "extractdata.py"

# -------------------------------
# Display colours per class
# -------------------------------
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

# -------------------------------
# Columns
# -------------------------------

Y11_COLS = {
    "class": "11 - Class",
    "task": "11 - Task Name",
    "weight": "11 - Weighting",
    "type": "11 - Task Type",
    "notes": "11 - Other Notes",
}
Y12_COLS = {
    "class": "12 - Class",
    "task": "12 - Task Name",
    "weight": "12 - Weighting",
    "type": "12 - Task Type",
    "notes": "12 - Other Notes",
}

# FIXED_COLUMNS that exist in both years
FIXED_COLUMNS = ["Week", "Day", "Date", "Events"]


def run_extractor(path: str) -> bool:
    """Run extract_to_json from extractdata.py"""

    if not EXTRACTOR_PATH.exists():
        return False
    try:
        spec = importlib.util.spec_from_file_location("extractdata", str(EXTRACTOR_PATH))
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader  
        spec.loader.exec_module(mod)  
        func = getattr(mod, "extract_to_json", None)
        if callable(func):
            func(xlsx_path=path)
            return True
        return False
    except Exception:
        # If the extractor throws, do not crash the app. 
        return False


def read_data(year: int) -> pd.DataFrame:

    path = DATA_DIR / ("year11.json" if year == 11 else "year12.json")
    cols = Y11_COLS if year == 11 else Y12_COLS

    if not path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_json(path)
    except Exception:
        # If the JSON cannot be read, return an empty DataFrame.
        return pd.DataFrame()

    # Build a new simple DataFrame with the fields we actually use.
    out = pd.DataFrame({
        "Date": pd.to_datetime(df.get("Date", ""), errors="coerce").dt.strftime("%Y-%m-%d"),
        "Class": df.get(cols["class"], "").fillna(""),
        "Task": df.get(cols["task"], "").fillna(""),
        "Weighting": df.get(cols["weight"], "").fillna(""),
        "Type": df.get(cols["type"], "").fillna(""),
        "Notes": df.get(cols["notes"], "").fillna(""),
        "Events": df.get("Events", "").fillna(""),
    })

    # Drop rows where Date failed to parse.
    return out.dropna(subset=["Date"])


# -------------------------------
# Main window class
# -------------------------------
class AssessmentApp(QMainWindow):
    """Main application window.

    Layout overview
      Outer QSplitter: [Setup panel] | [Main area]
      Main area contains a second splitter:
        Left side: Calendar and a label that shows the currently selected date
        Right side: Date sidebar with two lists and a details panel

    User flow
      1. Click the Setup button to select the Excel file, year, and classes
      2. Save and close the setup panel
      3. Calendar colours update based on the dominant class per date
      4. Use the date sidebar to jump across busy dates in the current month
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assessment Calendar")
        self.setGeometry(200, 100, 1200, 700)

        # Keep a small amount of state to remember last choices across runs.
        self.state = self.load_state()
        self.excel_path = self.state.get("excel_path", "")
        self.year = self.state.get("year", 11)
        self.classes = self.state.get("classes", [])

        # DataFrame holding all filtered rows for the chosen year and classes.
        self.df = pd.DataFrame()

        # Build the outer structure: a horizontal splitter for a slide-in setup panel.
        self.outer_split = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.outer_split)

        # Create child panels.
        self.build_setup_panel()
        self.build_main_area()

        # Add both panels to the splitter. Start with the setup panel hidden.
        self.outer_split.addWidget(self.setup_panel)
        self.outer_split.addWidget(self.main_area)
        self.outer_split.setSizes([0, 1])

        # Show window now. If we have saved state, try to load data immediately.
        self.show()
        if self.excel_path and self.classes:
            self.load_data()

    # ---------------- UI building helpers ----------------
    def build_setup_panel(self):
        """Create the slide-in setup panel on the left.

        Contains: file picker, year selector, class checklist, and a save button.
        """
        self.setup_panel = QWidget()
        layout = QVBoxLayout(self.setup_panel)

        # File selection
        self.file_label = QLabel(self.excel_path or "No Excel selected")
        self.btn_browse = QPushButton("Choose Excel…")
        layout.addWidget(self.file_label)
        layout.addWidget(self.btn_browse)

        # Year selection
        layout.addWidget(QLabel("Year:"))
        self.year_box = QComboBox()
        self.year_box.addItems(["11", "12"])
        # Try to restore previously chosen year.
        idx = self.year_box.findText(str(self.year))
        if idx >= 0:
            self.year_box.setCurrentIndex(idx)
        layout.addWidget(self.year_box)

        # Class selection list
        layout.addWidget(QLabel("Select Classes:"))
        self.class_list = QListWidget()
        self.class_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.class_list, 1)

        # Buttons to scan and save
        self.btn_scan = QPushButton("Scan for Classes")
        self.btn_save = QPushButton("Save & Close")
        layout.addWidget(self.btn_scan)
        layout.addWidget(self.btn_save)

        # Connect signals for the setup panel.
        self.btn_browse.clicked.connect(self.choose_file)
        self.btn_scan.clicked.connect(self.scan_excel)
        self.btn_save.clicked.connect(self.save_and_hide)

    def build_main_area(self):
        """Create the right-hand main area.

        Top row contains a button to toggle the setup panel.
        Below that an inner splitter divides the calendar and the date sidebar.
        """
        self.main_area = QWidget()
        main_v = QVBoxLayout(self.main_area)

        # Top controls row with a simple toggle for the setup panel.
        top = QHBoxLayout()
        self.btn_toggle_setup = QPushButton("☰ Setup")
        top.addWidget(self.btn_toggle_setup)
        top.addStretch()  # keep the button on the left
        main_v.addLayout(top)

        # Inner splitter to place calendar and date sidebar side by side.
        self.inner_split = QSplitter(Qt.Orientation.Horizontal)
        main_v.addWidget(self.inner_split, 1)

        # Left side: the calendar and a label showing the selected date.
        cal_wrap = QWidget()
        cal_v = QVBoxLayout(cal_wrap)
        self.calendar = QCalendarWidget()
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.NoHorizontalHeader)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        cal_v.addWidget(self.calendar)
        self.date_label = QLabel("No date selected")
        cal_v.addWidget(self.date_label)

        # Right side: the date sidebar and details view.
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

        # Add both sides to the inner splitter. Give the calendar more space.
        self.inner_split.addWidget(cal_wrap)
        self.inner_split.addWidget(right_wrap)
        self.inner_split.setSizes([800, 400])

        # Connect main-area signals.
        self.btn_toggle_setup.clicked.connect(self.toggle_setup_panel)
        self.calendar.selectionChanged.connect(self.on_calendar_selected)
        self.calendar.currentPageChanged.connect(self.populate_date_sidebar)
        self.date_list.itemClicked.connect(self.on_date_sidebar_clicked)
        self.task_list.itemClicked.connect(self.show_details)

    # ---------------- Setup panel actions ----------------
    def toggle_setup_panel(self):
        """Show or hide the setup panel by resizing the outer splitter.

        If the left side is zero width, open it to 350 px. Otherwise collapse it.
        """
        if self.outer_split.sizes()[0] == 0:
            self.outer_split.setSizes([350, 850])
        else:
            self.outer_split.setSizes([0, 1])

    def choose_file(self):
        """Open a file picker to choose the Excel workbook."""
        path, _ = QFileDialog.getOpenFileName(self, "Choose Excel", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.excel_path = path
            self.file_label.setText(path)

    def scan_excel(self):
        """Run the extractor and fill the class checklist based on the selected year."""
        if not self.excel_path:
            QMessageBox.information(self, "Select file", "Choose an Excel file first.")
            return
        run_extractor(self.excel_path)
        year = int(self.year_box.currentText())
        df = read_data(year)
        if df.empty:
            QMessageBox.information(self, "No Data", "Could not read any classes.")
            return
        # Populate the class list with unique names. Pre-select any previously saved classes.
        self.class_list.clear()
        for c in sorted(df["Class"].dropna().unique()):
            item = QListWidgetItem(c)
            if c in self.classes:
                item.setSelected(True)
            self.class_list.addItem(item)

    def save_and_hide(self):
        """Save year and class choices, load data, then hide the setup panel."""
        selected = [i.text() for i in self.class_list.selectedItems()]
        self.classes = selected
        self.year = int(self.year_box.currentText())
        self.save_state()
        self.load_data()
        self.toggle_setup_panel()

    # ---------------- Data loading and view updates ----------------
    def load_data(self):
        """Run the extractor, read the JSON for the chosen year, filter by classes, then refresh views."""
        run_extractor(self.excel_path)
        df = read_data(self.year)
        if df.empty:
            self.df = pd.DataFrame()
        else:
            # If no classes are selected, show nothing. Otherwise filter down.
            self.df = df[df["Class"].isin(self.classes)] if self.classes else pd.DataFrame()
        self.paint_calendar()
        self.populate_date_sidebar()
        self.on_calendar_selected()

    def paint_calendar(self):
        """Colour each date in the calendar using the dominant class for that date.

        Dominant class is defined as the class with the highest number of tasks on that date.
        The chosen colour comes from CLASS_COLORS. Unknown classes fall back to a neutral grey.
        """
        # Clear any previous formatting.
        clear_fmt = QTextCharFormat()
        for d in getattr(self, "_painted_dates", []):
            self.calendar.setDateTextFormat(d, clear_fmt)
        self._painted_dates = set()

        if self.df.empty:
            return

        # Build a frequency table: (Date, Class) -> count of tasks.
        counts = self.df.groupby(["Date", "Class"]).size().reset_index(name="n")

        # For each date, pick the class with the maximum count and colour that date.
        for date_str, sub in counts.groupby("Date"):
            top_row = sub.sort_values("n", ascending=False).iloc[0]
            top_class = str(top_row["Class"]).strip()
            color = CLASS_COLORS.get(top_class, "#888888")
            qd = QDate.fromString(date_str, "yyyy-MM-dd")
            if not qd.isValid():
                continue
            fmt = QTextCharFormat()
            fmt.setBackground(QBrush(QColor(color)))
            self.calendar.setDateTextFormat(qd, fmt)
            self._painted_dates.add(qd)

    def populate_date_sidebar(self):
        """Fill the date sidebar with all dates in the visible month that have tasks."""
        self.date_list.clear()
        if self.df.empty:
            return
        # Determine which year and month the calendar is showing.
        year = self.calendar.yearShown()
        month = self.calendar.monthShown()
        # Keep only rows in that month, then list unique dates.
        mask = self.df["Date"].str.slice(0, 7) == f"{year:04d}-{month:02d}"
        dates_in_month = sorted(self.df.loc[mask, "Date"].unique())
        for d in dates_in_month:
            self.date_list.addItem(QListWidgetItem(d))
        # Try to keep the sidebar selection in sync with the calendar selection.
        cur = self.calendar.selectedDate().toString("yyyy-MM-dd")
        matches = self.date_list.findItems(cur, Qt.MatchFlag.MatchExactly)
        if matches:
            self.date_list.setCurrentItem(matches[0])

    def on_date_sidebar_clicked(self, item: QListWidgetItem):
        """When the user clicks a date in the sidebar, select that date in the calendar."""
        date_str = item.text()
        qd = QDate.fromString(date_str, "yyyy-MM-dd")
        if qd.isValid():
            self.calendar.setSelectedDate(qd)
            self.on_calendar_selected()

    def on_calendar_selected(self):
        """When a calendar date is selected, update the label and list the tasks for that date."""
        if self.df.empty:
            self.date_label.setText("No date selected")
            self.task_list.clear()
            self.details.clear()
            return

        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.date_label.setText(date)

        # Keep the date sidebar focused on the same date.
        matches = self.date_list.findItems(date, Qt.MatchFlag.MatchExactly)
        if matches:
            self.date_list.setCurrentItem(matches[0])

        # List all tasks for the selected date. Sort for stable, readable order.
        day = self.df[self.df["Date"] == date].copy()
        day = day.sort_values(["Class", "Task"])  # simple, predictable sort
        self.task_list.clear()
        for _, r in day.iterrows():
            item = QListWidgetItem(f"{r['Class']} — {r['Task']}")
            # Store the full row on the item so the details panel can read it later.
            item.setData(Qt.ItemDataRole.UserRole, r.to_dict())
            # Tint the item with its class colour to make scanning easier.
            col = CLASS_COLORS.get(str(r["Class"]), "#eeeeee")
            item.setBackground(QBrush(QColor(col)))
            self.task_list.addItem(item)

        # If there is at least one task, show its details by default. Otherwise clear the panel.
        first = self.task_list.item(0)
        if first:
            self.task_list.setCurrentItem(first)
            self.show_details(first)
        else:
            self.details.clear()

    def show_details(self, item: QListWidgetItem):
        """Render a simple HTML view of the selected task in the details panel."""
        data = item.data(Qt.ItemDataRole.UserRole)
        html = (
            f"<b>Class:</b> {data['Class']}<br>"
            f"<b>Task:</b> {data['Task']}<br>"
            f"<b>Type:</b> {data['Type']}<br>"
            f"<b>Weighting:</b> {data['Weighting']}<br>"
            f"<b>Notes:</b> {data['Notes']}<br>"
            f"<b>Events:</b> {data['Events']}"
        )
        self.details.setHtml(html)

    # ---------------- Persistence helpers ----------------
    def save_state(self):
        """Write a tiny JSON file with the last used Excel path, year, and classes."""
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "excel_path": self.excel_path,
                "year": self.year,
                "classes": self.classes,
            }, f, indent=2)

    def load_state(self) -> dict:
        """Read the tiny JSON state file. If missing, return an empty dict."""
        if STATE_PATH.exists():
            try:
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}


# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    # QApplication owns the event loop. Keep a reference in a local variable.
    app = QApplication(sys.argv)
    # Create and show the main window.
    w = AssessmentApp()
    # Enter the event loop and keep the app running until the window is closed.
    sys.exit(app.exec())
