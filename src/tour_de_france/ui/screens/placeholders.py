"""Placeholder screens for yet-to-be implemented phases."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from tour_de_france.constants import GREEN_PRIMARY, GREEN_PRIMARY_HOVER


class PlaceholderScreen(QWidget):
    """Simple reusable placeholder screen with optional continue button."""

    next_requested = Signal()

    def __init__(
        self,
        title: str,
        subtitle: str,
        button_text: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("font-size: 16px; color: #444;")
        layout.addWidget(subtitle_label)

        layout.addStretch(1)

        if button_text:
            next_button = QPushButton(button_text)
            next_button.setMinimumHeight(52)
            next_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {GREEN_PRIMARY};
                    color: white;
                    font-size: 18px;
                    font-weight: 700;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {GREEN_PRIMARY_HOVER};
                }}
                """
            )
            next_button.clicked.connect(self.next_requested.emit)
            layout.addWidget(next_button)
