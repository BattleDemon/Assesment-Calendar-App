from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QCalendarWidget, QLabel, QMessageBox
)
from PyQt6.QtGui import QTextCharFormat, QBrush, QColor
from PyQt6.QtCore import QDate
import sys, json
from pathlib import Path
import pandas as pd

APP_DIR = Path(".")
DATA_DIR = APP_DIR / "data"

# Simple palette. You can grow this later.
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
    "Music": "#70193d",
}

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
FIXED = ["Week", "Day", "Date", "Events"]

def read_year_json(path: Path, cols_map: dict) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=[])
    df = pd.read_json(path)
    keep = FIXED + list(cols_map.values())
    # add any missing columns so selection does not crash
    for col in keep:
        if col not in df.columns:
            df[col] = ""
    df = df[keep].copy()
    df.rename(
        columns={
            cols_map["class"]: "Class",
            cols_map["task"]: "Task",
            cols_map["weight"]: "Weighting",
            cols_map["type"]: "Type",
            cols_map["notes"]: "Notes",
        },
        inplace=True,
    )
    # normalize date strings
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    return df

class StudentCalendarApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Senior Assessment — Calendar")
        self.setGeometry(200, 120, 1024, 640)

        # UI
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Calendar"))
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        layout.addWidget(self.calendar)
        self.setCentralWidget(page)

        # Data
        self.df = self.load_data()
        if self.df is None or self.df.empty:
            QMessageBox.information(self, "Data", "No assessment data found in data/year11.json or data/year12.json.")
        else:
            self.paint_calendar_simple()

        self.show()

    def load_data(self) -> pd.DataFrame:
        y11 = DATA_DIR / "year11.json"
        y12 = DATA_DIR / "year12.json"
        df11 = read_year_json(y11, Y11_COLS)
        df12 = read_year_json(y12, Y12_COLS)
        if df11.empty and df12.empty:
            return pd.DataFrame()
        df = pd.concat([df11, df12], ignore_index=True)
        # keep only rows with valid date
        df = df[pd.to_datetime(df["Date"], errors="coerce").notna()].copy()
        return df

    # simple coloring: pick the first class color for the date
    def paint_calendar_simple(self):
        # clear previous formats
        default_fmt = QTextCharFormat()
        # make a set to wipe old formats if needed in future refreshes
        self._painted = getattr(self, "_painted", set())
        for d in self._painted:
            self.calendar.setDateTextFormat(d, default_fmt)
        self._painted.clear()

        # group classes by date
        by_date = {}
        for _, row in self.df.iterrows():
            date_str = str(row["Date"])
            by_date.setdefault(date_str, []).append(str(row["Class"]))

        for date_str, classes in by_date.items():
            d = QDate.fromString(date_str, "yyyy-MM-dd")
            if not d.isValid():
                continue
            # choose a color using the first class present on that day
            chosen_class = classes[0] if classes else None
            col_hex = CLASS_COLORS.get(chosen_class, None)
            if not col_hex:
                continue
            fmt = QTextCharFormat()
            fmt.setBackground(QBrush(QColor(col_hex)))
            self.calendar.setDateTextFormat(d, fmt)
            self._painted.add(d)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = StudentCalendarApp()
    sys.exit(app.exec())
