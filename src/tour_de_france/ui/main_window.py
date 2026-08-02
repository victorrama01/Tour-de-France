"""Main window and screen navigation."""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

from tour_de_france.constants import APP_NAME, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH
from tour_de_france.models.game_config import GameConfig
from tour_de_france.models.race_models import TeamStageInput
from tour_de_france.services.race_engine import RaceEngine
from tour_de_france.ui.logo import build_app_icon
from tour_de_france.ui.screens.finale_screen import FinaleScreen
from tour_de_france.ui.screens.overview_screen import OverviewScreen
from tour_de_france.ui.screens.route_generation_screen import RouteGenerationScreen
from tour_de_france.ui.screens.setup_screen import SetupScreen
from tour_de_france.ui.screens.stage_input_screen import StageInputScreen
from tour_de_france.ui.screens.stage_result_screen import StageResultScreen


class MainWindow(QMainWindow):
    """Root window that controls screen changes for the full game."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(build_app_icon())
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._game_config: GameConfig | None = None
        self._engine = RaceEngine()
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._init_screens()
        self.show_setup()

    def _init_screens(self) -> None:
        self.setup_screen = SetupScreen()
        self.setup_screen.setup_submitted.connect(self._on_setup_submitted)
        self._stack.addWidget(self.setup_screen)

        self.route_generation_screen = RouteGenerationScreen()
        self.route_generation_screen.proceed_requested.connect(self._show_current_stage_input)
        self._stack.addWidget(self.route_generation_screen)

        self.stage_input_screen = StageInputScreen()
        self.stage_input_screen.stage_run_requested.connect(self._on_stage_run_requested)
        self._stack.addWidget(self.stage_input_screen)

        self.stage_result_screen = StageResultScreen()
        self.stage_result_screen.next_requested.connect(self._on_stage_result_next)
        self._stack.addWidget(self.stage_result_screen)

        self.overview_screen = OverviewScreen()
        self.overview_screen.next_requested.connect(self._show_current_stage_input)
        self._stack.addWidget(self.overview_screen)

        self.finale_screen = FinaleScreen()
        self.finale_screen.restart_requested.connect(self._reset_to_setup)
        self._stack.addWidget(self.finale_screen)

    def _on_setup_submitted(self, config: GameConfig) -> None:
        self._game_config = config
        stages = self._engine.start_race(config)
        self.route_generation_screen.start_animation(stages)
        self.show_route_generation()

    def _show_current_stage_input(self) -> None:
        if not self._engine.has_active_race:
            return
        if not self._engine.has_next_stage:
            self._show_finale()
            return
        stage_view = self._engine.get_current_stage_input_view()
        self.stage_input_screen.configure_stage(list(self._engine.teams), stage_view)
        self.show_stage_input()

    def _on_stage_run_requested(self, inputs: list[TeamStageInput]) -> None:
        try:
            result = self._engine.run_stage(inputs)
        except ValueError as exc:
            QMessageBox.warning(self, "Ugyldig etape-input", str(exc))
            return
        self.stage_result_screen.set_stage_result(result)
        self.show_stage_result()

    def _on_stage_result_next(self) -> None:
        if self._engine.has_next_stage:
            self.overview_screen.set_overview_data(
                teams=list(self._engine.teams),
                total_distances=self._engine.total_distances,
                total_points=self._engine.total_points,
                target_distance=self._engine.total_target_distance,
                completed_stage_count=self._engine.completed_stage_count,
                stage_count=self._engine.stage_count,
            )
            self.show_overview()
        else:
            self._show_finale()

    def _show_finale(self) -> None:
        final_result = self._engine.finalize_race()
        self.finale_screen.set_final_result(final_result)
        self.show_finale()

    def _reset_to_setup(self) -> None:
        self._engine.reset()
        self._game_config = None
        self.show_setup()

    def show_setup(self) -> None:
        self._stack.setCurrentWidget(self.setup_screen)

    def show_route_generation(self) -> None:
        self._stack.setCurrentWidget(self.route_generation_screen)

    def show_stage_input(self) -> None:
        self._stack.setCurrentWidget(self.stage_input_screen)

    def show_stage_result(self) -> None:
        self._stack.setCurrentWidget(self.stage_result_screen)

    def show_overview(self) -> None:
        self._stack.setCurrentWidget(self.overview_screen)

    def show_finale(self) -> None:
        self._stack.setCurrentWidget(self.finale_screen)
