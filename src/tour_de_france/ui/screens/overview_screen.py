"""Inter-stage overview screen."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QProgressBar, QVBoxLayout, QWidget

from tour_de_france.constants import GREEN_PRIMARY, GREEN_PRIMARY_HOVER
from tour_de_france.models.game_config import TeamConfig


class OverviewScreen(QWidget):
    """Shows race progress before the next stage."""

    next_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bars: list[QProgressBar] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        title = QLabel("Samlet overblik")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        root.addWidget(title)

        self._subtitle = QLabel("")
        self._subtitle.setStyleSheet("font-size: 16px; color: #334155;")
        root.addWidget(self._subtitle)

        self._bars_host = QWidget()
        self._bars_layout = QVBoxLayout(self._bars_host)
        self._bars_layout.setSpacing(10)
        root.addWidget(self._bars_host, 1)

        self._next_button = QPushButton("Næste")
        self._next_button.setMinimumHeight(54)
        self._next_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {GREEN_PRIMARY};
                color: white;
                font-size: 20px;
                font-weight: 700;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {GREEN_PRIMARY_HOVER};
            }}
            """
        )
        self._next_button.clicked.connect(self.next_requested.emit)
        root.addWidget(self._next_button)

    def set_overview_data(
        self,
        teams: list[TeamConfig],
        total_distances: list[int],
        total_points: list[int],
        target_distance: int,
        completed_stage_count: int,
        stage_count: int,
    ) -> None:
        self._subtitle.setText(
            f"Etaper kørt: {completed_stage_count}/{stage_count} | Samlet måldistance: {target_distance}"
        )
        while self._bars_layout.count():
            item = self._bars_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        axis_max = max(target_distance, max(total_distances, default=0), 1)
        for idx, team in enumerate(teams):
            label = QLabel(
                f"{team.name}: {total_distances[idx]} / {target_distance} | Point: {total_points[idx]}"
            )
            label.setStyleSheet(f"font-weight: 700; color: {team.color_hex};")
            self._bars_layout.addWidget(label)

            bar = QProgressBar()
            bar.setRange(0, axis_max)
            bar.setValue(total_distances[idx])
            bar.setFormat(f"{total_distances[idx]}")
            bar.setTextVisible(True)
            bar.setMinimumHeight(26)
            bar.setStyleSheet(
                f"""
                QProgressBar {{
                    border: 1px solid #a1a1aa;
                    border-radius: 6px;
                    background-color: #e5e7eb;
                }}
                QProgressBar::chunk {{
                    background-color: {team.color_hex};
                }}
                """
            )
            self._bars_layout.addWidget(bar)
