from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QCalendarWidget, QLabel
)
import sys
from pathlib import Path

from extractdata import extract_to_json

DATA_DIR =  Path("data")

extract_to_json(xlsx_path="Test Senior Assessment Calendar.xlsx", outdir=DATA_DIR)

class StudentCalendarApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Senior Assessment — Calendar")
        self.setGeometry(200, 120, 1024, 640)

        page = QWidget()
        lay = QVBoxLayout(page)

        title = QLabel("Calendar")
        cal = QCalendarWidget()

        lay.addWidget(title)
        lay.addWidget(cal)
        self.setCentralWidget(page)
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = StudentCalendarApp()
    sys.exit(app.exec())