"""Stage input screen where users enter start and end weights."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from tour_de_france.constants import GREEN_PRIMARY, GREEN_PRIMARY_HOVER
from tour_de_france.models.game_config import TeamConfig
from tour_de_france.models.race_models import StageInputView, TeamStageInput


@dataclass
class TeamInputRow:
    """Live widgets for one team in stage input."""

    team_index: int
    start_spin: QSpinBox
    end_spin: QSpinBox


class StageInputScreen(QWidget):
    """Collects start/end values for each team in current stage."""

    stage_run_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._team_rows: list[TeamInputRow] = []
        self._teams: list[TeamConfig] = []
        self._stage_view: StageInputView | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        self._title = QLabel("Etape")
        self._title.setStyleSheet("font-size: 28px; font-weight: 700;")
        root.addWidget(self._title)

        self._stage_length_label = QLabel("")
        self._stage_length_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        root.addWidget(self._stage_length_label)

        self._remaining_label = QLabel("")
        self._remaining_label.setWordWrap(True)
        self._remaining_label.setStyleSheet("font-size: 14px; color: #444;")
        root.addWidget(self._remaining_label)

        self._lock_info_label = QLabel("")
        self._lock_info_label.setWordWrap(True)
        self._lock_info_label.setStyleSheet("font-size: 13px; color: #64748b;")
        root.addWidget(self._lock_info_label)

        self._teams_box = QGroupBox("Hold-input")
        self._teams_layout = QVBoxLayout(self._teams_box)
        self._teams_layout.setSpacing(10)
        root.addWidget(self._teams_box, 1)

        self._run_button = QPushButton("Kør Etape")
        self._run_button.setMinimumHeight(56)
        self._run_button.setStyleSheet(
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
        self._run_button.clicked.connect(self._emit_stage_run)
        root.addWidget(self._run_button)

    def configure_stage(self, teams: list[TeamConfig], stage_view: StageInputView) -> None:
        self._teams = list(teams)
        self._stage_view = stage_view
        self._title.setText(f"Etape {stage_view.stage_number} af {stage_view.stage_count}")
        self._stage_length_label.setText(f"Aktuel etapelængde: {stage_view.stage_length} km")
        if stage_view.stage_number > 1:
            self._lock_info_label.setText(
                "Startvægt er redigerbar. Forslag er sat til sidste etapes slutvægt."
            )
        else:
            self._lock_info_label.setText("Første etape: Startvægt kan indtastes frit for alle hold.")
        if stage_view.is_last_stage:
            segments = [
                f"{team.name}: {stage_view.remaining_to_total[idx]} km"
                for idx, team in enumerate(self._teams)
            ]
            self._remaining_label.setText(
                "Sidste etape - afstand til samlet løbsdistance:\n" + " | ".join(segments)
            )
        else:
            self._remaining_label.setText("")

        self._clear_team_rows()
        for idx, team in enumerate(self._teams):
            row = self._make_team_row(team, idx, stage_view)
            self._teams_layout.addWidget(row)
        self._teams_layout.addStretch(1)

    def _clear_team_rows(self) -> None:
        self._team_rows.clear()
        while self._teams_layout.count():
            item = self._teams_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _make_team_row(self, team: TeamConfig, team_index: int, stage_view: StageInputView) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(f"QFrame {{ border-left: 8px solid {team.color_hex}; border-radius: 4px; }}")
        layout = QGridLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)

        name_label = QLabel(team.name)
        name_label.setStyleSheet("font-size: 17px; font-weight: 700;")
        layout.addWidget(name_label, 0, 0, 1, 2)

        start_spin = QSpinBox()
        start_spin.setRange(0, 100000)
        start_spin.setValue(stage_view.team_start_defaults[team_index])
        start_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        start_spin.setEnabled(True)

        end_spin = QSpinBox()
        end_spin.setRange(0, 100000)
        end_spin.setValue(stage_view.team_start_defaults[team_index])
        end_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        end_spin.setMaximum(start_spin.value())
        start_spin.valueChanged.connect(end_spin.setMaximum)
        start_spin.valueChanged.connect(lambda value, spin=end_spin: self._normalize_end_spin(spin, value))

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow("Startvægt (enheder):", start_spin)
        form.addRow("Slutvægt (enheder):", end_spin)
        layout.addLayout(form, 1, 0, 1, 2)

        self._team_rows.append(TeamInputRow(team_index=team_index, start_spin=start_spin, end_spin=end_spin))
        return frame

    @staticmethod
    def _normalize_end_spin(end_spin: QSpinBox, max_value: int) -> None:
        if end_spin.value() > max_value:
            end_spin.setValue(max_value)

    def _emit_stage_run(self) -> None:
        if not self._stage_view:
            return
        inputs: list[TeamStageInput] = []
        for row in self._team_rows:
            start = row.start_spin.value()
            end = row.end_spin.value()
            if end > start:
                QMessageBox.warning(self, "Ugyldigt input", "Slutvægt må ikke være højere end startvægt.")
                return
            inputs.append(
                TeamStageInput(
                    team_index=row.team_index,
                    start_weight=start,
                    end_weight=end,
                )
            )
        self.stage_run_requested.emit(inputs)
