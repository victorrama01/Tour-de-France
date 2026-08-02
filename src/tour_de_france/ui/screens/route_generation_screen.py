"""Route generation screen with staged animation."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from tour_de_france.constants import GREEN_PRIMARY, GREEN_PRIMARY_HOVER
from tour_de_france.models.race_models import Stage
from tour_de_france.ui.widgets.bars import Segment, StackedBarWidget


class RouteGenerationScreen(QWidget):
    """Animates stage creation as a stacked horizontal bar."""

    proceed_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._stages: list[Stage] = []
        self._active_stage_index = 0
        self._current_stage_value = 0.0
        self._units_per_second = 80.0
        self._target_total = 1
        self._completed_distance = 0.0
        self._is_complete = False
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick_animation)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Rute-generering")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)

        self._status = QLabel("Klar til at generere etaper.")
        self._status.setStyleSheet("font-size: 16px; color: #334155;")
        layout.addWidget(self._status)

        self._progress_line = QLabel("")
        self._progress_line.setStyleSheet("font-size: 13px; color: #64748b;")
        layout.addWidget(self._progress_line)

        bar_panel = QFrame()
        bar_panel.setStyleSheet(
            """
            QFrame {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
            }
            """
        )
        bar_panel_layout = QVBoxLayout(bar_panel)
        bar_panel_layout.setContentsMargins(12, 12, 12, 12)
        bar_panel_layout.setSpacing(10)

        self._summary = QLabel("")
        self._summary.setStyleSheet("font-size: 14px; color: #0f172a; font-weight: 600;")
        bar_panel_layout.addWidget(self._summary)

        self._bar = StackedBarWidget()
        self._bar.setMinimumHeight(92)
        bar_panel_layout.addWidget(self._bar)

        legend = QLabel("Kort: grøn   •   Mellem: blå   •   Lang: orange")
        legend.setStyleSheet("font-size: 13px; color: #475569;")
        bar_panel_layout.addWidget(legend)
        layout.addWidget(bar_panel)

        self._stage_list = QLabel("")
        self._stage_list.setWordWrap(True)
        self._stage_list.setTextFormat(Qt.TextFormat.RichText)
        self._stage_list.setStyleSheet("font-size: 14px; color: #1e293b;")
        layout.addWidget(self._stage_list)

        layout.addStretch(1)

        self._next_button = QPushButton("Start Etape 1")
        self._next_button.setEnabled(False)
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
            QPushButton:disabled {{
                background-color: #94a3b8;
            }}
            """
        )
        self._next_button.clicked.connect(self.proceed_requested.emit)
        layout.addWidget(self._next_button)

    def start_animation(self, stages: list[Stage]) -> None:
        self._timer.stop()
        self._stages = list(stages)
        self._active_stage_index = 0
        self._current_stage_value = 0.0
        self._completed_distance = 0.0
        self._is_complete = False
        self._target_total = max(1, sum(stage.length for stage in self._stages))
        self._bar.set_segments([], max_total=self._target_total)
        self._next_button.setEnabled(False)
        self._stage_list.setText("")
        self._summary.setText(
            f"Etaper i alt: {len(self._stages)} | Samlet distance: {self._target_total} km"
        )
        self._progress_line.setText("Færdig: 0%")
        self._status.setText("Genererer rute...")
        if not self._stages:
            self._status.setText("Ingen etaper blev genereret.")
            self._next_button.setEnabled(True)
            return
        self._timer.start()

    def _tick_animation(self) -> None:
        if self._is_complete:
            return
        if self._active_stage_index >= len(self._stages):
            self._timer.stop()
            self._status.setText("Rute klar! Tryk på knappen for at starte Etape 1.")
            self._next_button.setEnabled(True)
            self._is_complete = True
            self._progress_line.setText("Færdig: 100%")
            return

        delta_value = self._units_per_second * (self._timer.interval() / 1000.0)
        completed_segments = self._stages[: self._active_stage_index]
        current_stage = self._stages[self._active_stage_index]
        self._current_stage_value = min(current_stage.length, self._current_stage_value + delta_value)
        current_value = int(round(self._current_stage_value))
        segments = []
        for stage in completed_segments:
            segments.append(
                Segment(value=stage.length, color=self._color_for_category(stage.category), label=str(stage.length))
            )
        segments.append(
            Segment(
                value=current_value,
                color=self._color_for_category(current_stage.category),
                label=str(current_stage.length) if self._current_stage_value >= current_stage.length else "",
            )
        )
        self._bar.set_segments(segments, max_total=self._target_total)

        total_progress = (self._completed_distance + self._current_stage_value) / max(1, self._target_total)
        self._progress_line.setText(f"Færdig: {int(round(total_progress * 100))}%")
        self._status.setText(
            f"Bygger etape {self._active_stage_index + 1}/{len(self._stages)} (konstant hastighed)"
        )

        completed_count = self._active_stage_index + (1 if self._current_stage_value >= current_stage.length else 0)
        stage_text = " | ".join(
            f"<b>E{stage.number}</b>: {stage.length} km ({stage.category})"
            for stage in self._stages[:completed_count]
        )
        if stage_text:
            self._stage_list.setText(stage_text)

        if self._current_stage_value >= current_stage.length:
            self._completed_distance += current_stage.length
            self._active_stage_index += 1
            self._current_stage_value = 0.0

    @staticmethod
    def _color_for_category(category: str) -> str:
        if category == "kort":
            return "#22c55e"
        if category == "mellem":
            return "#3b82f6"
        return "#f97316"
