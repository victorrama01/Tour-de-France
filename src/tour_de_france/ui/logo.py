"""Logo helpers for the Tour De France app."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap

from tour_de_france.constants import LOGO_RELATIVE_PATH


def _resolve_custom_logo_path() -> Path | None:
    """Find a user-provided logo file if available."""
    project_root = Path(__file__).resolve().parents[3]
    candidates = [
        project_root / LOGO_RELATIVE_PATH,
        project_root / "logo.png",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _build_fallback_logo_pixmap(size: int = 128) -> QPixmap:
    """Create an in-memory fallback logo pixmap."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background badge
    badge_rect = QRectF(2, 2, size - 4, size - 4)
    painter.setPen(QPen(QColor("#1e3a8a"), 2))
    painter.setBrush(QColor("#dbeafe"))
    painter.drawRoundedRect(badge_rect, 18, 18)

    # Wheels
    wheel_radius = size * 0.16
    left_center = QPointF(size * 0.32, size * 0.65)
    right_center = QPointF(size * 0.68, size * 0.65)
    wheel_pen = QPen(QColor("#0f172a"), max(2, int(size * 0.025)))
    painter.setPen(wheel_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(left_center, wheel_radius, wheel_radius)
    painter.drawEllipse(right_center, wheel_radius, wheel_radius)

    # Rider + bike frame
    frame_pen = QPen(QColor("#dc2626"), max(3, int(size * 0.03)))
    frame_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(frame_pen)
    painter.drawLine(
        QPointF(size * 0.32, size * 0.65),
        QPointF(size * 0.50, size * 0.46),
    )
    painter.drawLine(
        QPointF(size * 0.50, size * 0.46),
        QPointF(size * 0.68, size * 0.65),
    )
    painter.drawLine(
        QPointF(size * 0.50, size * 0.46),
        QPointF(size * 0.58, size * 0.36),
    )
    painter.drawLine(
        QPointF(size * 0.58, size * 0.36),
        QPointF(size * 0.66, size * 0.42),
    )

    # Tour text
    painter.setPen(QColor("#0f172a"))
    font = QFont("Segoe UI", max(8, int(size * 0.12)))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(QRectF(0, size * 0.08, size, size * 0.26), Qt.AlignmentFlag.AlignCenter, "TDF")

    painter.end()
    return pixmap


def build_logo_pixmap(size: int = 128) -> QPixmap:
    """Create logo pixmap from file when present, else fallback."""
    custom_path = _resolve_custom_logo_path()
    if custom_path is not None:
        from_file = QPixmap(str(custom_path))
        if not from_file.isNull():
            return from_file.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
    return _build_fallback_logo_pixmap(size)


def build_app_icon() -> QIcon:
    """Create app icon from custom file or fallback logo."""
    custom_path = _resolve_custom_logo_path()
    if custom_path is not None:
        icon = QIcon(str(custom_path))
        if not icon.isNull():
            return icon

    icon = QIcon()
    for icon_size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(_build_fallback_logo_pixmap(icon_size))
    return icon
