"""Stage result screen with animated team bars."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tour_de_france.constants import GREEN_PRIMARY, GREEN_PRIMARY_HOVER
from tour_de_france.models.race_models import StageResult, TeamStageResult


@dataclass
class TeamBarWidgets:
    """Widgets used to animate one team result row."""

    bar: "TargetLineBarWidget"
    value_label: QLabel
    target: int
    color: str


class TargetLineBarWidget(QWidget):
    """Custom bar that renders a dashed target line and capped growth."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._max_value = 1
        self._target_value = 1
        self._display_value = 0
        self._fill_color = "#22c55e"
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    @property
    def max_value(self) -> int:
        return self._max_value

    def configure(self, max_value: int, target_value: int, fill_color: str) -> None:
        self._max_value = max(1, max_value)
        self._target_value = max(0, target_value)
        self._display_value = 0
        self._fill_color = fill_color
        self.update()

    def set_display_value(self, value: int) -> None:
        self._display_value = max(0, min(value, self._max_value))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 3, -1, -3)
        painter.setPen(QPen(QColor("#a1a1aa"), 1))
        painter.setBrush(QColor("#f1f5f9"))
        painter.drawRoundedRect(rect, 5, 5)

        if self._display_value > 0:
            width = rect.width() * (self._display_value / self._max_value)
            fill_rect = QRectF(rect.left(), rect.top(), width, rect.height())
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(self._fill_color))
            painter.drawRoundedRect(fill_rect, 5, 5)

        marker_x = rect.left() + rect.width() * (self._target_value / self._max_value)
        painter.setPen(QPen(QColor("#dc2626"), 2, Qt.PenStyle.DashLine))
        painter.drawLine(
            int(marker_x),
            rect.top() - 2,
            int(marker_x),
            rect.bottom() + 2,
        )
        painter.end()


class StageResultScreen(QWidget):
    """Displays stage target and animated team distances."""

    next_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._result: StageResult | None = None
        self._team_bars: list[TeamBarWidgets] = []
        self._elapsed_ms = 0
        self._units_per_second = 30.0
        self._animation_end_ms = 0
        self._ranking_animation: QPropertyAnimation | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._tick_animation)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        self._title = QLabel("Etape-resultat")
        self._title.setStyleSheet("font-size: 28px; font-weight: 700;")
        root.addWidget(self._title)

        self._target_label = QLabel("")
        self._target_label.setStyleSheet("font-size: 17px; font-weight: 600;")
        root.addWidget(self._target_label)

        self._target_hint = QLabel("")
        self._target_hint.setStyleSheet("font-size: 13px; color: #b91c1c; font-weight: 600;")
        root.addWidget(self._target_hint)

        self._rows_host = QWidget()
        self._rows_layout = QGridLayout(self._rows_host)
        self._rows_layout.setHorizontalSpacing(12)
        self._rows_layout.setVerticalSpacing(8)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setColumnStretch(1, 1)
        root.addWidget(self._rows_host, 1)

        self._ranking_panel = QWidget()
        ranking_panel_layout = QVBoxLayout(self._ranking_panel)
        ranking_panel_layout.setContentsMargins(12, 10, 12, 10)
        ranking_panel_layout.setSpacing(6)
        self._ranking_panel.setStyleSheet(
            """
            QWidget {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            """
        )
        self._ranking_title = QLabel("Etape Rangliste")
        self._ranking_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0f172a;")
        ranking_panel_layout.addWidget(self._ranking_title)

        self._ranking_label = QLabel("")
        self._ranking_label.setWordWrap(True)
        self._ranking_label.setTextFormat(Qt.TextFormat.RichText)
        self._ranking_label.setStyleSheet("font-size: 14px; color: #1e293b; border: none;")
        ranking_panel_layout.addWidget(self._ranking_label)
        root.addWidget(self._ranking_panel)

        self._ranking_opacity = QGraphicsOpacityEffect(self._ranking_panel)
        self._ranking_panel.setGraphicsEffect(self._ranking_opacity)
        self._ranking_opacity.setOpacity(0.0)
        self._ranking_panel.setVisible(False)

        self._next_button = QPushButton("Næste")
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
        self._next_button.clicked.connect(self.next_requested.emit)
        root.addWidget(self._next_button)

    def set_stage_result(self, result: StageResult) -> None:
        self._result = result
        self._next_button.setEnabled(False)
        self._ranking_label.setText("")
        self._ranking_panel.setVisible(False)
        self._ranking_opacity.setOpacity(0.0)
        self._elapsed_ms = 0
        self._title.setText(f"Etape {result.stage.number} - Resultat")
        self._target_label.setText(f"Mål for etapen: {result.stage.length} km")
        self._target_hint.setText("")
        axis_max = max(1, int(round(result.stage.length * 1.4)))
        max_team_distance = max((entry.distance for entry in result.team_results), default=0)
        self._animation_end_ms = int((max_team_distance / self._units_per_second) * 1000)
        self._animation_end_ms = max(900, self._animation_end_ms)

        self._clear_rows()
        self._team_bars.clear()
        ordered_entries = sorted(result.team_results, key=lambda item: item.team_index)
        for row_index, entry in enumerate(ordered_entries):
            widgets = self._add_team_row(entry, row_index, axis_max)
            self._team_bars.append(widgets)

        self._timer.start()

    def _clear_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _add_team_row(self, entry: TeamStageResult, row: int, axis_max: int) -> TeamBarWidgets:
        name = QLabel(entry.team_name)
        name.setStyleSheet(f"font-weight: 700; color: {entry.team_color};")
        self._rows_layout.addWidget(name, row, 0)

        bar = TargetLineBarWidget()
        bar.configure(max_value=axis_max, target_value=self._result.stage.length, fill_color=entry.team_color)
        self._rows_layout.addWidget(bar, row, 1)

        value_label = QLabel("0")
        value_label.setMinimumWidth(48)
        value_label.setStyleSheet("font-weight: 600;")
        self._rows_layout.addWidget(value_label, row, 2)
        return TeamBarWidgets(bar=bar, value_label=value_label, target=entry.distance, color=entry.team_color)

    def _tick_animation(self) -> None:
        if self._result is None:
            self._timer.stop()
            return
        self._elapsed_ms += self._timer.interval()
        current_distance = self._units_per_second * (self._elapsed_ms / 1000.0)
        for bar in self._team_bars:
            animated_value = int(min(bar.target, round(current_distance)))
            bar.bar.set_display_value(animated_value)
            bar.value_label.setText(str(animated_value))
        if self._elapsed_ms >= self._animation_end_ms:
            self._timer.stop()
            self._show_ranking()
            self._next_button.setEnabled(True)

    def _show_ranking(self) -> None:
        if self._result is None:
            return
        lines: list[str] = []
        winner = min(self._result.team_results, key=lambda row: row.rank)
        lines.append(
            f"<div style='font-size:15px; font-weight:700; margin-bottom:8px;'>Etapevinder: {winner.team_name}</div>"
        )
        lines.append("<table style='width:100%; border-collapse:collapse;'>")
        lines.append(
            "<tr>"
            "<th style='text-align:left; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Placering</th>"
            "<th style='text-align:left; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Hold</th>"
            "<th style='text-align:right; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Distance</th>"
            "<th style='text-align:right; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Afvigelse</th>"
            "<th style='text-align:right; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Point</th>"
            "</tr>"
        )
        for entry in self._result.team_results:
            lines.append(
                "<tr>"
                f"<td style='padding:6px 8px;'>{entry.rank}</td>"
                f"<td style='padding:6px 8px; color:{entry.team_color}; font-weight:700;'>{entry.team_name}</td>"
                f"<td style='padding:6px 8px; text-align:right;'>{entry.distance} km</td>"
                f"<td style='padding:6px 8px; text-align:right;'>{entry.deviation} km</td>"
                f"<td style='padding:6px 8px; text-align:right; font-weight:700;'>{entry.stage_points}</td>"
                "</tr>"
            )
        lines.append("</table>")
        self._ranking_label.setText("".join(lines))
        self._ranking_panel.setVisible(True)
        self._ranking_animation = QPropertyAnimation(self._ranking_opacity, b"opacity", self)
        self._ranking_animation.setDuration(350)
        self._ranking_animation.setStartValue(0.0)
        self._ranking_animation.setEndValue(1.0)
        self._ranking_animation.start()
