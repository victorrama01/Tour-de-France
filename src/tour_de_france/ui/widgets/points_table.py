"""Persistent points table shown alongside the game screens."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tour_de_france.models.race_models import StandingsView

_EMPTY_TEXT = "Løbet er ikke startet endnu.\nTryk på 'Generér Løb' for at begynde."


class PointsTablePanel(QFrame):
    """Sidebar with total points and current placement per team."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pointsTablePanel")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            """
            QFrame#pointsTablePanel {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
            }
            """
        )
        self._build_ui()
        self.clear()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(8)

        self._title = QLabel("Pointoversigt")
        self._title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a; border: none;")
        root.addWidget(self._title)

        self._subtitle = QLabel("")
        self._subtitle.setWordWrap(True)
        self._subtitle.setStyleSheet("font-size: 12px; color: #64748b; border: none;")
        root.addWidget(self._subtitle)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["#", "Hold", "Point", "Km"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            """
            QTableWidget {
                border: none;
                background-color: #ffffff;
                alternate-background-color: #f8fafc;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                border: none;
                border-bottom: 1px solid #cbd5e1;
                padding: 6px 4px;
                font-weight: 700;
                color: #334155;
            }
            """
        )

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self._table, 1)

        self._empty_label = QLabel(_EMPTY_TEXT)
        self._empty_label.setWordWrap(True)
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("font-size: 13px; color: #94a3b8; border: none;")
        root.addWidget(self._empty_label, 1)

        self._leader_label = QLabel("")
        self._leader_label.setWordWrap(True)
        self._leader_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #0f172a; border: none;")
        root.addWidget(self._leader_label)

    def clear(self) -> None:
        """Reset the panel to its pre-race state."""
        self._table.setRowCount(0)
        self._table.setVisible(False)
        self._empty_label.setVisible(True)
        self._subtitle.setText("Ingen etaper kørt")
        self._leader_label.setText("")

    def set_standings(self, standings: StandingsView) -> None:
        """Render the current points standings."""
        self._empty_label.setVisible(False)
        self._table.setVisible(True)

        if standings.is_final:
            self._subtitle.setText(
                f"Slutresultat efter {standings.stage_count} etaper (inkl. bonuspoint)"
            )
        else:
            self._subtitle.setText(
                f"Etaper kørt: {standings.completed_stage_count}/{standings.stage_count}"
            )

        self._table.setRowCount(len(standings.teams))
        for row, team in enumerate(standings.teams):
            self._table.setItem(row, 0, self._make_rank_item(team.rank))
            self._table.setItem(row, 1, self._make_team_item(team.team_name, team.team_color))
            self._table.setItem(row, 2, self._make_number_item(str(team.total_points), bold=True))
            self._table.setItem(row, 3, self._make_number_item(str(team.total_distance)))

        self._leader_label.setText(self._build_leader_text(standings))

    @staticmethod
    def _make_rank_item(rank: int) -> QTableWidgetItem:
        item = QTableWidgetItem(f"{rank}.")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    @staticmethod
    def _make_team_item(name: str, color_hex: str) -> QTableWidgetItem:
        item = QTableWidgetItem(name)
        item.setForeground(QBrush(QColor(color_hex)))
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        return item

    @staticmethod
    def _make_number_item(text: str, bold: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if bold:
            font = QFont()
            font.setBold(True)
            item.setFont(font)
        return item

    @staticmethod
    def _build_leader_text(standings: StandingsView) -> str:
        if not standings.teams:
            return ""
        leaders = [team for team in standings.teams if team.rank == 1]
        label = "Vinder" if standings.is_final else "Fører"
        names = ", ".join(team.team_name for team in leaders)
        return f"{label}: {names} ({leaders[0].total_points} point)"
