from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QCalendarWidget, QLabel, QListWidget, QListWidgetItem, QTextEdit,
    QSplitter, QMessageBox
)
from PyQt6.QtGui import QTextCharFormat, QBrush, QColor
from PyQt6.QtCore import QDate, Qt
import sys
from pathlib import Path
import pandas as pd

APP_DIR = Path(".")
DATA_DIR = APP_DIR / "data"

CLASS_COLORS = {
    "English": "#80002f", "Chemistry": "#00800f", "Essential Maths": "#F5F5DC",
    "Maths Methods": "#00ffff", "Specialist Maths": "#0047AB", "Psychology": "#800080",
    "Textiles": "#ffc0cb", "History": "#dc143c", "IT": "#03a062",
    "Human Biology": "#9fe2bf", "Exercise Science": "#009e4f", "Physics": "#ffff00",
    "Design Tech": "#a52a2a", "Visual Arts": "#FF8C00", "Drama": "#9966cc", "Music": "#70193d",
}

Y11_COLS = {"class": "11 - Class", "task": "11 - Task Name", "weight": "11 - Weighting", "type": "11 - Task Type", "notes": "11 - Other Notes"}
Y12_COLS = {"class": "12 - Class", "task": "12 - Task Name", "weight": "12 - Weighting", "type": "12 - Task Type", "notes": "12 - Other Notes"}
FIXED = ["Week", "Day", "Date", "Events"]


def read_year_json(path: Path, cols: dict) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_json(path)
    except Exception:
        return pd.DataFrame()
    need = FIXED + list(cols.values())
    for c in need:
        if c not in df.columns:
            df[c] = ""
    out = pd.DataFrame({
        "Date": pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d"),
        "Class": df[cols["class"]].fillna(""),
        "Task": df[cols["task"]].fillna(""),
        "Weighting": df[cols["weight"]].fillna(""),
        "Type": df[cols["type"]].fillna(""),
        "Notes": df[cols["notes"]].fillna(""),
        "Events": df["Events"].fillna(""),
    })
    return out.dropna(subset=["Date"])


class StudentCalendarApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prototype 3 - Calendar + Sidebar")
        self.resize(1100, 680)

        self.df = self.load_data()

        self.split = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.split)

        left = QWidget(); left_v = QVBoxLayout(left)
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        left_v.addWidget(QLabel("Calendar"))
        left_v.addWidget(self.calendar)

        right = QWidget(); right_v = QVBoxLayout(right)
        right_v.addWidget(QLabel("Tasks for date"))
        self.task_list = QListWidget(); right_v.addWidget(self.task_list, 1)
        right_v.addWidget(QLabel("Details"))
        self.details = QTextEdit(); self.details.setReadOnly(True); right_v.addWidget(self.details, 2)

        self.split.addWidget(left)
        self.split.addWidget(right)
        self.split.setSizes([760, 340])

        if self.df.empty:
            QMessageBox.information(self, "Data", "No assessment data found in data/year11.json or data/year12.json.")
        else:
            self.paint_calendar_by_dominant()

        self.calendar.selectionChanged.connect(self.fill_tasks_for_selected)
        self.task_list.itemClicked.connect(self.show_details)
        self.fill_tasks_for_selected()
        self.show()

    def load_data(self) -> pd.DataFrame:
        y11 = DATA_DIR / "year11.json"
        y12 = DATA_DIR / "year12.json"
        a = read_year_json(y11, Y11_COLS)
        b = read_year_json(y12, Y12_COLS)
        if a.empty and b.empty:
            return pd.DataFrame()
        df = pd.concat([a, b], ignore_index=True)
        df = df[pd.to_datetime(df["Date"], errors="coerce").notna()].copy()
        return df

    def paint_calendar_by_dominant(self):
        clear = QTextCharFormat()
        for d in getattr(self, "_painted", set()):
            self.calendar.setDateTextFormat(d, clear)
        self._painted = set()
        counts = self.df.groupby(["Date", "Class"]).size().reset_index(name="n")
        for date_str, sub in counts.groupby("Date"):
            top = sub.sort_values("n", ascending=False).iloc[0]
            top_class = str(top["Class"]).strip()
            color = CLASS_COLORS.get(top_class, "#cccccc")
            qd = QDate.fromString(date_str, "yyyy-MM-dd")
            if not qd.isValid():
                continue
            fmt = QTextCharFormat(); fmt.setBackground(QBrush(QColor(color)))
            self.calendar.setDateTextFormat(qd, fmt)
            self._painted.add(qd)

    def fill_tasks_for_selected(self):
        self.task_list.clear(); self.details.clear()
        if self.df.empty:
            return
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        day = self.df[self.df["Date"] == date_str].sort_values(["Class", "Task"])
        for _, r in day.iterrows():
            label = f"{r['Class']} - {r['Task']}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, r.to_dict())
            bg = CLASS_COLORS.get(str(r["Class"]), "#eeeeee")
            item.setBackground(QBrush(QColor(bg)))
            self.task_list.addItem(item)
        if self.task_list.count() > 0:
            self.task_list.setCurrentRow(0)
            self.show_details(self.task_list.item(0))

    def show_details(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        html = (
            f"<b>Class:</b> {data['Class']}<br>"
            f"<b>Task:</b> {data['Task']}<br>"
            f"<b>Type:</b> {data['Type']}<br>"
            f"<b>Weighting:</b> {data['Weighting']}<br>"
            f"<b>Events:</b> {data['Events']}<br>"
            f"<b>Notes:</b> {data['Notes']}"
        )
        self.details.setHtml(html)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = StudentCalendarApp()
    sys.exit(app.exec())
