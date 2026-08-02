"""Finale screen with total-distance animation and final standings."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPropertyAnimation, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tour_de_france.constants import GREEN_PRIMARY, GREEN_PRIMARY_HOVER
from tour_de_france.models.race_models import FinalResult


@dataclass
class FinalBar:
    """Widgets for one animated final bar."""

    bar: "TargetLineBarWidget"
    value_label: QLabel
    target: int


class TargetLineBarWidget(QWidget):
    """Custom bar with 140%-cap rendering and dashed target line."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._max_value = 1
        self._target_value = 1
        self._display_value = 0
        self._fill_color = "#22c55e"
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

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
        painter.drawLine(int(marker_x), rect.top() - 2, int(marker_x), rect.bottom() + 2)
        painter.end()


class FinaleScreen(QWidget):
    """Shows final race animation and winner."""

    restart_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._result: FinalResult | None = None
        self._bars: list[FinalBar] = []
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

        title = QLabel("Afslutning")
        title.setStyleSheet("font-size: 30px; font-weight: 800;")
        root.addWidget(title)

        self._subtitle = QLabel("")
        self._subtitle.setStyleSheet("font-size: 16px; color: #334155;")
        root.addWidget(self._subtitle)

        self._bars_host = QWidget()
        self._bars_layout = QGridLayout(self._bars_host)
        self._bars_layout.setHorizontalSpacing(12)
        self._bars_layout.setVerticalSpacing(8)
        self._bars_layout.setContentsMargins(0, 0, 0, 0)
        self._bars_layout.setColumnStretch(1, 1)
        root.addWidget(self._bars_host, 1)

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
        self._ranking_title = QLabel("Slutrangliste")
        self._ranking_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0f172a;")
        ranking_panel_layout.addWidget(self._ranking_title)

        self._ranking = QLabel("")
        self._ranking.setWordWrap(True)
        self._ranking.setTextFormat(Qt.TextFormat.RichText)
        self._ranking.setStyleSheet("font-size: 14px; color: #111827; border: none;")
        ranking_panel_layout.addWidget(self._ranking)
        root.addWidget(self._ranking_panel)

        self._ranking_opacity = QGraphicsOpacityEffect(self._ranking_panel)
        self._ranking_panel.setGraphicsEffect(self._ranking_opacity)
        self._ranking_opacity.setOpacity(0.0)
        self._ranking_panel.setVisible(False)

        self._restart_button = QPushButton("Nyt spil")
        self._restart_button.setEnabled(False)
        self._restart_button.setMinimumHeight(54)
        self._restart_button.setStyleSheet(
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
        self._restart_button.clicked.connect(self.restart_requested.emit)
        root.addWidget(self._restart_button)

    def set_final_result(self, result: FinalResult) -> None:
        self._result = result
        self._restart_button.setEnabled(False)
        self._ranking.setText("")
        self._ranking_panel.setVisible(False)
        self._ranking_opacity.setOpacity(0.0)
        self._subtitle.setText(f"Samlet løbsdistance: {result.target_total_distance} km")
        self._elapsed_ms = 0

        while self._bars_layout.count():
            item = self._bars_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._bars.clear()

        axis_max = max(1, int(round(result.target_total_distance * 1.4)))
        max_team_distance = max((entry.total_distance for entry in result.team_results), default=0)
        self._animation_end_ms = int((max_team_distance / self._units_per_second) * 1000)
        self._animation_end_ms = max(900, self._animation_end_ms)
        ordered_entries = sorted(result.team_results, key=lambda item: item.team_index)
        for row_index, entry in enumerate(ordered_entries):
            label = QLabel(entry.team_name)
            label.setStyleSheet(f"font-weight: 700; color: {entry.team_color};")
            self._bars_layout.addWidget(label, row_index, 0)

            bar = TargetLineBarWidget()
            bar.configure(max_value=axis_max, target_value=result.target_total_distance, fill_color=entry.team_color)
            self._bars_layout.addWidget(bar, row_index, 1)

            value = QLabel("0")
            value.setStyleSheet("font-weight: 600;")
            self._bars_layout.addWidget(value, row_index, 2)

            self._bars.append(FinalBar(bar=bar, value_label=value, target=entry.total_distance))

        self._timer.start()

    def _tick_animation(self) -> None:
        if self._result is None:
            self._timer.stop()
            return
        self._elapsed_ms += self._timer.interval()
        current_distance = self._units_per_second * (self._elapsed_ms / 1000.0)
        for bar in self._bars:
            animated_value = int(min(bar.target, round(current_distance)))
            bar.bar.set_display_value(animated_value)
            bar.value_label.setText(str(animated_value))
        if self._elapsed_ms >= self._animation_end_ms:
            self._timer.stop()
            self._show_final_ranking()
            self._restart_button.setEnabled(True)

    def _show_final_ranking(self) -> None:
        if self._result is None:
            return
        lines: list[str] = []
        winner = min(self._result.team_results, key=lambda item: item.rank)
        lines.append(
            f"<div style='font-size:15px; font-weight:700; margin-bottom:8px;'>Samlet vinder: {winner.team_name}</div>"
        )
        lines.append("<table style='width:100%; border-collapse:collapse;'>")
        lines.append(
            "<tr>"
            "<th style='text-align:left; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Placering</th>"
            "<th style='text-align:left; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Hold</th>"
            "<th style='text-align:right; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Total point</th>"
            "<th style='text-align:right; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Distance</th>"
            "<th style='text-align:right; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Afvigelse</th>"
            "<th style='text-align:right; padding:6px 8px; border-bottom:1px solid #cbd5e1;'>Bonus</th>"
            "</tr>"
        )
        for entry in self._result.team_results:
            lines.append(
                "<tr>"
                f"<td style='padding:6px 8px;'>{entry.rank}</td>"
                f"<td style='padding:6px 8px; color:{entry.team_color}; font-weight:700;'>{entry.team_name}</td>"
                f"<td style='padding:6px 8px; text-align:right; font-weight:700;'>{entry.total_points}</td>"
                f"<td style='padding:6px 8px; text-align:right;'>{entry.total_distance} km</td>"
                f"<td style='padding:6px 8px; text-align:right;'>{entry.distance_deviation} km</td>"
                f"<td style='padding:6px 8px; text-align:right;'>+{entry.bonus_points}</td>"
                "</tr>"
            )
        lines.append("</table>")
        self._ranking.setText("".join(lines))
        self._ranking_panel.setVisible(True)
        self._ranking_animation = QPropertyAnimation(self._ranking_opacity, b"opacity", self)
        self._ranking_animation.setDuration(350)
        self._ranking_animation.setStartValue(0.0)
        self._ranking_animation.setEndValue(1.0)
        self._ranking_animation.start()
