"""Application entrypoint for Tour De France."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from tour_de_france.constants import APP_NAME
from tour_de_france.ui.logo import build_app_icon
from tour_de_france.ui.main_window import MainWindow

APP_STYLESHEET = """
QWidget {
    font-family: Segoe UI, Arial, sans-serif;
    color: #0f172a;
    background-color: #f8fafc;
}
QGroupBox {
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QLineEdit, QSpinBox {
    min-height: 28px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 2px 6px;
    background-color: #ffffff;
}
QPushButton {
    background-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 6px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #cbd5e1;
}
QProgressBar {
    border: 1px solid #94a3b8;
    border-radius: 6px;
    background-color: #e2e8f0;
    text-align: center;
    color: #0f172a;
}
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(APP_STYLESHEET)
    app.setWindowIcon(build_app_icon())
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
