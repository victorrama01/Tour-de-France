"""Simple custom bar widgets used by race screens."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class Segment:
    """A segment in a stacked horizontal bar."""

    value: int
    color: str
    label: str


class StackedBarWidget(QWidget):
    """Draw a horizontal stacked bar with labels."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._segments: list[Segment] = []
        self._max_total = 1
        self.setMinimumHeight(64)

    def set_segments(self, segments: list[Segment], max_total: int | None = None) -> None:
        self._segments = segments
        total = sum(max(0, segment.value) for segment in segments)
        if max_total is None:
            self._max_total = max(1, total)
        else:
            self._max_total = max(1, max_total)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        content = self.rect().adjusted(10, 12, -10, -12)
        painter.setPen(QPen(QColor("#bbbbbb"), 1))
        painter.setBrush(QColor("#f0f0f0"))
        painter.drawRoundedRect(content, 8, 8)

        if not self._segments:
            painter.end()
            return

        x = float(content.left())
        available_w = float(content.width())
        for segment in self._segments:
            width = available_w * (max(0, segment.value) / self._max_total)
            if width <= 0:
                continue
            rect = QRectF(x, content.top(), width, content.height())
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(segment.color))
            painter.drawRoundedRect(rect, 6, 6)

            painter.setPen(QColor("#ffffff"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, segment.label)
            x += width

        painter.end()
