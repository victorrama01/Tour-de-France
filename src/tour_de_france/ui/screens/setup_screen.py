"""Setup screen where users configure teams and stage counts."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QColorDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from tour_de_france.constants import (
    DEFAULT_LONG_STAGES,
    DEFAULT_MEDIUM_STAGES,
    DEFAULT_SHORT_STAGES,
    DEFAULT_TEAM_COLORS,
    DEFAULT_TEAM_COUNT,
    GREEN_PRIMARY,
    GREEN_PRIMARY_HOVER,
    MAX_STAGES_PER_CATEGORY,
    MAX_TEAM_COUNT,
    MIN_TEAM_COUNT,
)
from tour_de_france.models.game_config import GameConfig, StageCategoryConfig, TeamConfig
from tour_de_france.services.validation import validate_setup
from tour_de_france.ui.logo import build_logo_pixmap


@dataclass
class TeamDraft:
    """Mutable setup data for one team row."""

    name: str
    color_hex: str


class TeamRowWidget(QFrame):
    """Editor row for one team: name and color."""

    def __init__(self, team_index: int, draft: TeamDraft, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._team_index = team_index
        self._draft = draft
        self._build_ui()
        self._set_color(self._draft.color_hex)

    @property
    def team_name(self) -> str:
        return self._name_edit.text().strip()

    @property
    def color_hex(self) -> str:
        return self._draft.color_hex

    def _build_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)

        layout = QHBoxLayout()
        layout.setSpacing(12)
        root.addLayout(layout)

        number_label = QLabel(f"Hold {self._team_index + 1}")
        number_label.setMinimumWidth(75)
        layout.addWidget(number_label)

        self._name_edit = QLineEdit(self._draft.name)
        self._name_edit.setPlaceholderText(f"Hold {self._team_index + 1}")
        layout.addWidget(self._name_edit, 1)

        self._color_preview = QLabel()
        self._color_preview.setFixedSize(44, 28)
        self._color_preview.setStyleSheet("border: 1px solid #999; border-radius: 4px;")
        layout.addWidget(self._color_preview)

        choose_color_btn = QPushButton("Vælg farve")
        choose_color_btn.clicked.connect(self._open_color_picker)
        layout.addWidget(choose_color_btn)

        presets_row = QHBoxLayout()
        presets_row.setSpacing(6)
        presets_label = QLabel("Hurtigfarver:")
        presets_label.setStyleSheet("color: #475569;")
        presets_row.addWidget(presets_label)
        for color in DEFAULT_TEAM_COLORS[:8]:
            button = QPushButton()
            button.setFixedSize(22, 22)
            button.setToolTip(color)
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color};
                    border: 1px solid #64748b;
                    border-radius: 11px;
                }}
                """
            )
            button.clicked.connect(partial(self._set_color, color))
            presets_row.addWidget(button)
        presets_row.addStretch(1)
        root.addLayout(presets_row)

    def _open_color_picker(self) -> None:
        chosen = QColorDialog.getColor(QColor(self._draft.color_hex), self, "Vælg holdfarve")
        if chosen.isValid():
            self._set_color(chosen.name())

    def _set_color(self, color_hex: str) -> None:
        self._draft.color_hex = color_hex
        self._color_preview.setStyleSheet(
            f"background-color: {color_hex}; border: 1px solid #666; border-radius: 4px;"
        )


class SetupScreen(QWidget):
    """Start screen for game setup."""

    setup_submitted = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._team_rows: list[TeamRowWidget] = []
        self._build_ui()
        self._rebuild_team_rows(DEFAULT_TEAM_COUNT)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("Tour De France - Setup")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        title_row = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(build_logo_pixmap(40))
        logo.setFixedSize(40, 40)
        title_row.addWidget(logo)
        title_row.addWidget(title)
        title_row.addStretch(1)
        root.addLayout(title_row)

        description = QLabel(
            "Vælg hold og etaper, og tryk derefter på 'Generér Løb' for at starte."
        )
        description.setStyleSheet("color: #444;")
        root.addWidget(description)

        root.addWidget(self._build_general_settings_box())
        root.addWidget(self._build_team_box(), 1)
        root.addWidget(self._build_generate_button())

    def _build_general_settings_box(self) -> QGroupBox:
        box = QGroupBox("Løbsindstillinger")
        form = QFormLayout(box)
        form.setLabelAlignment(form.labelAlignment())
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(10)

        self._team_count_spin = QSpinBox()
        self._team_count_spin.setRange(MIN_TEAM_COUNT, MAX_TEAM_COUNT)
        self._team_count_spin.setValue(DEFAULT_TEAM_COUNT)
        self._team_count_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._team_count_spin.valueChanged.connect(self._rebuild_team_rows)
        form.addRow("Antal hold:", self._team_count_spin)

        self._short_stages_spin = QSpinBox()
        self._short_stages_spin.setRange(0, MAX_STAGES_PER_CATEGORY)
        self._short_stages_spin.setValue(DEFAULT_SHORT_STAGES)
        self._short_stages_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        form.addRow("Korte etaper (10-60):", self._short_stages_spin)

        self._medium_stages_spin = QSpinBox()
        self._medium_stages_spin.setRange(0, MAX_STAGES_PER_CATEGORY)
        self._medium_stages_spin.setValue(DEFAULT_MEDIUM_STAGES)
        self._medium_stages_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        form.addRow("Mellem etaper (60-150):", self._medium_stages_spin)

        self._long_stages_spin = QSpinBox()
        self._long_stages_spin.setRange(0, MAX_STAGES_PER_CATEGORY)
        self._long_stages_spin.setValue(DEFAULT_LONG_STAGES)
        self._long_stages_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        form.addRow("Lange etaper (150-300):", self._long_stages_spin)

        return box

    def _build_team_box(self) -> QGroupBox:
        box = QGroupBox("Hold")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 12, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_host = QWidget()
        self._team_rows_layout = QVBoxLayout(scroll_host)
        self._team_rows_layout.setContentsMargins(6, 6, 6, 6)
        self._team_rows_layout.setSpacing(8)
        self._team_rows_layout.addStretch(1)
        scroll.setWidget(scroll_host)
        layout.addWidget(scroll)

        return box

    def _build_generate_button(self) -> QPushButton:
        button = QPushButton("Generér Løb")
        button.setMinimumHeight(56)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {GREEN_PRIMARY};
                color: white;
                font-size: 20px;
                font-weight: 700;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
            }}
            QPushButton:hover {{
                background-color: {GREEN_PRIMARY_HOVER};
            }}
            """
        )
        button.clicked.connect(self._submit)
        return button

    def _rebuild_team_rows(self, team_count: int) -> None:
        previous = [TeamDraft(row.team_name or f"Hold {i + 1}", row.color_hex) for i, row in enumerate(self._team_rows)]
        while self._team_rows_layout.count() > 1:
            item = self._team_rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._team_rows.clear()

        for idx in range(team_count):
            if idx < len(previous):
                draft = previous[idx]
            else:
                draft = TeamDraft(
                    name=f"Hold {idx + 1}",
                    color_hex=DEFAULT_TEAM_COLORS[idx % len(DEFAULT_TEAM_COLORS)],
                )
            row = TeamRowWidget(team_index=idx, draft=draft)
            self._team_rows_layout.insertWidget(self._team_rows_layout.count() - 1, row)
            self._team_rows.append(row)

    def _submit(self) -> None:
        stage_categories = StageCategoryConfig(
            short_count=self._short_stages_spin.value(),
            medium_count=self._medium_stages_spin.value(),
            long_count=self._long_stages_spin.value(),
        )

        teams = [
            TeamConfig(
                name=(row.team_name or f"Hold {index + 1}").strip(),
                color_hex=row.color_hex,
            )
            for index, row in enumerate(self._team_rows)
        ]
        errors = validate_setup([team.name for team in teams], stage_categories)
        if errors:
            QMessageBox.warning(self, "Ugyldig opsætning", "\n".join(errors))
            return

        self.setup_submitted.emit(GameConfig(teams=teams, stages=stage_categories))
