
# /* ------ Import Used Libraries ------ */
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
    QDateEdit,
    QStackedWidget,
    QSpacerItem,
    QSizePolicy
) 
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QTextCharFormat, QBrush, QColor, QFont
import json
import os
import sys
import importlib.util
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta


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
    "Exercise Science": "#009e4f",
    "Physics": "#ffff00",
    "Design Tech": "#a52a2a",
    "Visual Arts": "#FF8C00",
    "Drama": "#9966cc",
    "Music": "#70193d"
}

# Column maps
Y11_COLS = {
    "class": "11 - Class",
    "task": "11 - Task Name",
    "weight": "11 - Weighting",
    "type": "11 - Task Type",
    "notes": "11 - Other Notes"
}
Y12_COLS = {
    "class": "12 - Class",
    "task": "12 - Task Name",
    "weight": "12 - Weighting",
    "type": "12 - Task Type",
    "notes": "12 - Other Notes"
}
FIXED = ["Week", "Day", "Date", "Events"]

APP_DIR = Path(os.path.dirname(__file__))
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_PATH = DATA_DIR / "ui_state.json"
DEFAULT_EXTRACTOR = APP_DIR / "extractdata.py"


# ----- Helpers -----
def rgb_from_hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def hex_from_rgb(r, g, b):
    return "#{:02x}{:02x}{:02x}".format(max(0, min(255, int(r))), max(0, min(255, int(g))), max(0, min(255, int(b))))

def blend_colors(hex_list):
    if not hex_list:
        return "#cccccc"
    rs, gs, bs = 0, 0, 0
    for h in hex_list:
        r, g, b = rgb_from_hex(h)
        rs += r; gs += g; bs += b
    n = max(1, len(hex_list))
    return hex_from_rgb(rs / n, gs / n, bs / n)

def read_dataset(year_json: Path, cols_map: dict) -> pd.DataFrame:
    df = pd.read_json(year_json)
    keep = FIXED + list(cols_map.values())
    for col in keep:
        if col not in df.columns:
            df[col] = ""
    df = df[keep].copy()
    df.rename(columns={
        cols_map["class"]: "Class",
        cols_map["task"]: "Task",
        cols_map["weight"]: "Weighting",
        cols_map["type"]: "Type",
        cols_map["notes"]: "Notes",
    }, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    return df

def ensure_extract(excel_path: str, extractor_path: str):
    y11 = DATA_DIR / "year11.json"
    y12 = DATA_DIR / "year12.json"
    if y11.exists() and y12.exists():
        return True, ""
    try:
        spec = importlib.util.spec_from_file_location("extractdata", extractor_path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        if hasattr(mod, "extract_to_json"):
            mod.extract_to_json(excel_path, outdir=str(DATA_DIR))
        else:
            return False, "extractdata.py is missing extract_to_json(excel_path, outdir)"
    except Exception as e:
        return False, f"{e}"
    return True, ""

def load_state():
    if STATE_PATH.exists():
        try:
            return json.load(open(STATE_PATH, "r", encoding="utf-8"))
        except Exception:
            pass
    # Defaults
    return {
        "year": None,
        "classes": [],
        "excel_path": "",
        "valid_until": ""  # yyyy-mm-dd
    }

def save_state(state: dict):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def auto_valid_until_date(excel_path: str, year: int) -> QDate:
    """Read the chosen year dataset and compute max(Date) + 14 days as a QDate."""
    ok, err = ensure_extract(excel_path, str(DEFAULT_EXTRACTOR))
    if not ok:
        return QDate.currentDate().addDays(14)
    ypath = DATA_DIR / ("year11.json" if year == 11 else "year12.json")
    cols = Y11_COLS if year == 11 else Y12_COLS
    try:
        df = read_dataset(ypath, cols)
        if df.empty:
            return QDate.currentDate().addDays(14)
        dts = pd.to_datetime(df["Date"], errors="coerce").dropna()
        if dts.empty:
            return QDate.currentDate().addDays(14)
        last = dts.max() + pd.Timedelta(days=14)
        return QDate(last.year, last.month, last.day)
    except Exception:
        return QDate.currentDate().addDays(14)


# /* ----- Main App Class ----- */
class StudentCalendarApp(QMainWindow):
    def __init__(self):
        super(StudentCalendarApp, self).__init__()
        self.setWindowTitle("Senior Assessment — Calendar")
        self.setGeometry(200, 120, 1024, 640)

        self.state = load_state()
        self.excel_path = self.state.get("excel_path", "")
        self.extractor_path = str(DEFAULT_EXTRACTOR)

        # Pages
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Setup page
        self.setup_page = QWidget()
        self.build_setup_page()
        self.stack.addWidget(self.setup_page)

        # Calendar page
        self.calendar_page = QWidget()
        self.build_calendar_page()
        self.stack.addWidget(self.calendar_page)

        # Decide which page to show
        if self.needs_setup():
            self.stack.setCurrentWidget(self.setup_page)
        else:
            self.load_data_and_show_calendar()

        self.show()

    # ----- Setup page -----
    def build_setup_page(self):
        v = QVBoxLayout(self.setup_page)
        v.addWidget(QLabel("Set up your student profile"))

        row_year = QWidget()
        hy = QHBoxLayout(row_year); hy.setContentsMargins(0,0,0,0)
        hy.addWidget(QLabel("Year"))
        self.year_box = QComboBox()
        self.year_box.addItems(["11", "12"])
        # if saved year exists, set it
        if self.state.get("year"):
            self.year_box.setCurrentText(str(self.state["year"]))
        self.year_box.currentTextChanged.connect(self.on_year_changed_recalc_validuntil)
        hy.addWidget(self.year_box)
        v.addWidget(row_year)

        row_excel = QWidget()
        hx = QHBoxLayout(row_excel); hx.setContentsMargins(0,0,0,0)
        hx.addWidget(QLabel("Excel file"))
        self.excel_label = QLabel(self.excel_path if self.excel_path else "No file chosen")
        choose_btn = QPushButton("Choose Excel…")
        choose_btn.clicked.connect(self.choose_excel)
        hx.addWidget(self.excel_label, 1)
        hx.addWidget(choose_btn)
        v.addWidget(row_excel)

        row_valid = QWidget()
        hv = QHBoxLayout(row_valid); hv.setContentsMargins(0,0,0,0)
        hv.addWidget(QLabel("Valid until"))
        self.valid_until = QDateEdit()
        self.valid_until.setCalendarPopup(True)
        # If we have saved state and it's valid, use it; else will be computed after scan/choose
        if self.state.get("valid_until"):
            try:
                dt = datetime.strptime(self.state["valid_until"], "%Y-%m-%d")
                self.valid_until.setDate(QDate(dt.year, dt.month, dt.day))
            except Exception:
                self.valid_until.setDate(QDate.currentDate().addDays(14))
        else:
            self.valid_until.setDate(QDate.currentDate().addDays(14))
        hv.addWidget(self.valid_until)
        v.addWidget(row_valid)

        v.addWidget(QLabel("Select your classes"))
        self.class_list = QListWidget()
        self.class_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        v.addWidget(self.class_list, 1)

        # Buttons
        buttons = QWidget()
        hb = QHBoxLayout(buttons); hb.setContentsMargins(0,0,0,0)
        self.scan_btn = QPushButton("Scan Excel for Classes")
        self.scan_btn.setToolTip("Run extractor and populate classes for chosen year")
        self.scan_btn.clicked.connect(self.scan_classes)
        self.save_btn = QPushButton("Save & Continue")
        self.save_btn.clicked.connect(self.save_setup)
        hb.addWidget(self.scan_btn)
        hb.addStretch(1)
        hb.addWidget(self.save_btn)
        v.addWidget(buttons)

        v.addItem(QSpacerItem(0,0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # If we already have an excel + year and classes, pre-populate list
        if self.excel_path and self.state.get("year"):
            self.populate_classes_from_state()

    def choose_excel(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Choose Excel", str(APP_DIR))
        if fn:
            self.excel_path = fn
            self.excel_label.setText(fn)
            # auto recompute valid-until immediately
            year = int(self.year_box.currentText())
            vu = auto_valid_until_date(self.excel_path, year)
            self.valid_until.setDate(vu)

    def on_year_changed_recalc_validuntil(self):
        if self.excel_path:
            year = int(self.year_box.currentText())
            vu = auto_valid_until_date(self.excel_path, year)
            self.valid_until.setDate(vu)

    def scan_classes(self):
        if not self.excel_path:
            QMessageBox.information(self, "Excel", "Please choose an Excel file first.")
            return
        year = int(self.year_box.currentText())
        ok, err = ensure_extract(self.excel_path, self.extractor_path)
        if not ok:
            QMessageBox.critical(self, "Extract", err)
            return
        # Load dataframe for year and enumerate classes
        ypath = DATA_DIR / ("year11.json" if year == 11 else "year12.json")
        cols_map = Y11_COLS if year == 11 else Y12_COLS
        try:
            df = read_dataset(ypath, cols_map)
        except Exception as e:
            QMessageBox.critical(self, "Read", str(e))
            return
        self.class_list.clear()
        classes = sorted(c for c in df["Class"].dropna().unique() if str(c).strip())
        for c in classes:
            item = QListWidgetItem(str(c))
            if c in CLASS_COLORS:
                item.setSelected(True)
            self.class_list.addItem(item)
        # after scanning, compute valid until = last date + 14 days
        vu = auto_valid_until_date(self.excel_path, year)
        self.valid_until.setDate(vu)

    def populate_classes_from_state(self):
        """If state valid, populate classes list and selection based on saved classes."""
        year = int(self.state.get("year"))
        ok, err = ensure_extract(self.excel_path, self.extractor_path)
        if not ok:
            return
        ypath = DATA_DIR / ("year11.json" if year == 11 else "year12.json")
        cols_map = Y11_COLS if year == 11 else Y12_COLS
        try:
            df = read_dataset(ypath, cols_map)
        except Exception:
            return
        classes = sorted(c for c in df["Class"].dropna().unique() if str(c).strip())
        self.class_list.clear()
        for c in classes:
            item = QListWidgetItem(str(c))
            if c in self.state.get("classes", []):
                item.setSelected(True)
            self.class_list.addItem(item)

    def save_setup(self):
        if not self.excel_path:
            QMessageBox.information(self, "Setup", "Please choose an Excel file.")
            return
        sel = [i.text() for i in self.class_list.selectedItems()]
        if not sel:
            QMessageBox.information(self, "Setup", "Please select at least one class.")
            return
        year = int(self.year_box.currentText())
        # always recalc valid-until from data at save time to keep it in sync
        vu_qdate = auto_valid_until_date(self.excel_path, year)
        self.valid_until.setDate(vu_qdate)
        vu = vu_qdate.toString("yyyy-MM-dd")

        self.state = {
            "year": year,
            "classes": sel,
            "excel_path": self.excel_path,
            "valid_until": vu
        }
        save_state(self.state)
        self.load_data_and_show_calendar()

    def needs_setup(self):
        year = self.state.get("year")
        excel = self.state.get("excel_path", "")
        valid_until = self.state.get("valid_until", "")
        if not year or not excel:
            return True
        if valid_until:
            try:
                today = datetime.now().date()
                vu = datetime.strptime(valid_until, "%Y-%m-%d").date()
                if today > vu:
                    return True
            except Exception:
                return True
        # Also ensure extracted JSON exists; if not, force setup so scanning runs
        if not (DATA_DIR / "year11.json").exists() or not (DATA_DIR / "year12.json").exists():
            return True
        return False

    # ----- Calendar page -----
    def build_calendar_page(self):
        root = QHBoxLayout(self.calendar_page)
        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        root.addWidget(self.calendar, 3)
        # Sidebar
        side_wrap = QWidget()
        side = QVBoxLayout(side_wrap)
        side.addWidget(QLabel("Selected Date"))
        self.date_label = QLabel("-")
        side.addWidget(self.date_label)

        side.addWidget(QLabel("Tasks"))
        self.task_list = QListWidget()
        side.addWidget(self.task_list, 1)

        side.addWidget(QLabel("Details"))
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        side.addWidget(self.details, 2)

        # Button to re-open setup
        self.reconfigure_btn = QPushButton("Change Year/Classes/Excel")
        self.reconfigure_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.setup_page))
        side.addWidget(self.reconfigure_btn)

        root.addWidget(side_wrap, 2)

        # Signals
        self.calendar.selectionChanged.connect(self.refresh_day)
        self.task_list.itemSelectionChanged.connect(self.show_task_details)

    def load_data_and_show_calendar(self):
        # ensure extraction with chosen excel
        ok, err = ensure_extract(self.state["excel_path"], str(DEFAULT_EXTRACTOR))
        if not ok:
            QMessageBox.critical(self, "Extract", err)
            self.stack.setCurrentWidget(self.setup_page)
            return
        # Load correct year and filter classes
        year = int(self.state["year"])
        ypath = DATA_DIR / ("year11.json" if year == 11 else "year12.json")
        cols_map = Y11_COLS if year == 11 else Y12_COLS
        self.df = read_dataset(ypath, cols_map)
        self.df = self.df[self.df["Class"].isin(set(self.state["classes"]))].copy()
        # Paint calendar and show
        self.recolor_calendar()
        self.refresh_day()
        self.stack.setCurrentWidget(self.calendar_page)

    def recolor_calendar(self):
        default_fmt = QTextCharFormat()
        if not hasattr(self, "_painted"):
            self._painted = set()
        for d in self._painted:
            self.calendar.setDateTextFormat(d, default_fmt)
        self._painted.clear()

        by_date = {}
        for _, row in self.df.iterrows():
            by_date.setdefault(str(row["Date"]), set()).add(str(row["Class"]))

        for date_str, classes in by_date.items():
            d = QDate.fromString(date_str, "yyyy-MM-dd")
            if not d.isValid():
                continue
            colors = [CLASS_COLORS[c] for c in classes if c in CLASS_COLORS]
            if not colors:
                continue
            color = blend_colors(colors) if len(colors) > 1 else colors[0]
            fmt = QTextCharFormat()
            fmt.setBackground(QBrush(QColor(color)))
            if len(colors) > 1:
                fmt.setFontWeight(QFont.Weight.Bold)
            self.calendar.setDateTextFormat(d, fmt)
            self._painted.add(d)

    def refresh_day(self):
        self.details.clear()
        self.task_list.clear()
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.date_label.setText(date)
        if not hasattr(self, "df") or self.df is None or self.df.empty:
            return
        day_df = self.df[self.df["Date"] == date].sort_values(["Class", "Task"])
        for _, row in day_df.iterrows():
            label = f"{row['Class']} — {row['Task']}"
            item = QListWidgetItem(label)
            col = CLASS_COLORS.get(row["Class"])
            if col:
                item.setBackground(QColor(col))
            item.setData(Qt.ItemDataRole.UserRole, {
                "Class": row["Class"],
                "Task": row["Task"],
                "Type": row["Type"],
                "Weighting": row["Weighting"],
                "Events": row["Events"],
                "Notes": row["Notes"],
                "Date": row["Date"]
            })
            self.task_list.addItem(item)
        if self.task_list.count() > 0:
            self.task_list.setCurrentRow(0)
            self.show_task_details()

    def show_task_details(self):
        item = self.task_list.currentItem()
        if not item:
            self.details.clear()
            return
        d = item.data(Qt.ItemDataRole.UserRole)
        text = (
            f"<b>{d['Class']}</b><br>"
            f"<b>Task:</b> {d['Task']}<br>"
            f"<b>Type:</b> {d['Type']}<br>"
            f"<b>Weighting:</b> {d['Weighting']}<br>"
            f"<b>Date:</b> {d['Date']}<br>"
            f"<b>Events:</b> {d['Events']}<br>"
            f"<b>Notes:</b><br>{d['Notes']}"
        )
        self.details.setHtml(text)


# /* ----- App entry point ----- */
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = StudentCalendarApp()
    sys.exit(app.exec())
