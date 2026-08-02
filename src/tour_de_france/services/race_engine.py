"""Game engine for Tour De France race flow."""

from __future__ import annotations

import random
from dataclasses import dataclass

from tour_de_france.constants import LONG_STAGE_RANGE, MEDIUM_STAGE_RANGE, SHORT_STAGE_RANGE
from tour_de_france.models.game_config import GameConfig
from tour_de_france.models.race_models import (
    FinalResult,
    Stage,
    StageInputView,
    StageResult,
    TeamFinalResult,
    TeamStageInput,
    TeamStageResult,
)


@dataclass
class RaceState:
    """Mutable race state."""

    config: GameConfig
    stages: list[Stage]
    current_stage_index: int
    total_points: list[int]
    total_distances: list[int]
    latest_end_weights: list[int]
    stage_history: list[StageResult]
    bonus_applied: bool = False


class RaceEngine:
    """Encapsulates race generation and scoring logic."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._state: RaceState | None = None

    @property
    def has_active_race(self) -> bool:
        return self._state is not None

    def reset(self) -> None:
        self._state = None

    def start_race(self, config: GameConfig) -> list[Stage]:
        stages = self._generate_stages(config)
        team_count = config.team_count
        self._state = RaceState(
            config=config,
            stages=stages,
            current_stage_index=0,
            total_points=[0 for _ in range(team_count)],
            total_distances=[0 for _ in range(team_count)],
            latest_end_weights=[0 for _ in range(team_count)],
            stage_history=[],
        )
        return list(stages)

    def get_current_stage_input_view(self) -> StageInputView:
        state = self._require_state()
        stage = state.stages[state.current_stage_index]
        is_last = state.current_stage_index == len(state.stages) - 1
        start_locked = False
        starts = list(state.latest_end_weights) if state.current_stage_index > 0 else [0] * len(state.latest_end_weights)
        remaining = [self.total_target_distance - total for total in state.total_distances]
        return StageInputView(
            stage_number=stage.number,
            stage_count=len(state.stages),
            stage_length=stage.length,
            is_last_stage=is_last,
            start_locked=start_locked,
            team_start_defaults=starts,
            remaining_to_total=remaining,
        )

    def run_stage(self, inputs: list[TeamStageInput]) -> StageResult:
        state = self._require_state()
        if state.current_stage_index >= len(state.stages):
            raise ValueError("Der er ikke flere etaper at køre.")
        if len(inputs) != state.config.team_count:
            raise ValueError("Forkert antal hold-inputs.")
        team_indices = sorted(item.team_index for item in inputs)
        if team_indices != list(range(state.config.team_count)):
            raise ValueError("Alle hold skal have præcis ét input.")

        stage = state.stages[state.current_stage_index]

        deviations: list[int] = []
        for item in inputs:
            if item.team_index < 0 or item.team_index >= state.config.team_count:
                raise ValueError("Ugyldigt holdindeks.")
            if item.end_weight > item.start_weight:
                raise ValueError("Slutvægt må ikke være højere end startvægt.")

            deviations.append(abs((item.start_weight - item.end_weight) - stage.length))

        ranking = self._rank_with_ties(deviations, ascending=True)
        results: list[TeamStageResult] = []
        for item in inputs:
            rank = ranking[item.team_index]
            stage_points = 4 - rank
            team = state.config.teams[item.team_index]
            distance = item.start_weight - item.end_weight
            deviation = abs(distance - stage.length)
            state.total_distances[item.team_index] += distance
            state.total_points[item.team_index] += stage_points
            state.latest_end_weights[item.team_index] = item.end_weight
            results.append(
                TeamStageResult(
                    team_index=item.team_index,
                    team_name=team.name,
                    team_color=team.color_hex,
                    start_weight=item.start_weight,
                    end_weight=item.end_weight,
                    distance=distance,
                    deviation=deviation,
                    rank=rank,
                    stage_points=stage_points,
                )
            )

        results.sort(key=lambda entry: (entry.rank, entry.deviation, entry.team_name.casefold()))
        stage_result = StageResult(stage=stage, team_results=results)
        state.stage_history.append(stage_result)
        state.current_stage_index += 1
        return stage_result

    @property
    def has_next_stage(self) -> bool:
        state = self._require_state()
        return state.current_stage_index < len(state.stages)

    @property
    def total_target_distance(self) -> int:
        state = self._require_state()
        return sum(stage.length for stage in state.stages)

    @property
    def teams(self):
        return self._require_state().config.teams

    @property
    def total_distances(self) -> list[int]:
        return list(self._require_state().total_distances)

    @property
    def total_points(self) -> list[int]:
        return list(self._require_state().total_points)

    @property
    def completed_stage_count(self) -> int:
        return len(self._require_state().stage_history)

    @property
    def stage_count(self) -> int:
        return len(self._require_state().stages)

    def finalize_race(self) -> FinalResult:
        state = self._require_state()
        if self.has_next_stage:
            raise ValueError("Løbet er ikke færdigt endnu.")
        if state.bonus_applied:
            return self._compose_final_result()

        deviations = [abs(total - self.total_target_distance) for total in state.total_distances]
        bonus_ranks = self._rank_with_ties(deviations, ascending=True)

        for team_index, rank in bonus_ranks.items():
            bonus = self._bonus_points_for_rank(rank)
            state.total_points[team_index] += bonus

        state.bonus_applied = True
        return self._compose_final_result()

    def _compose_final_result(self) -> FinalResult:
        state = self._require_state()
        target = self.total_target_distance
        bonus_ranks = self._rank_with_ties(
            [abs(total - target) for total in state.total_distances],
            ascending=True,
        )
        bonus_points = {idx: self._bonus_points_for_rank(rank) for idx, rank in bonus_ranks.items()}

        team_indices = list(range(state.config.team_count))
        final_ranking = self._rank_positions_for_scores(
            team_indices=team_indices,
            points=state.total_points,
            tie_breakers=[abs(state.total_distances[idx] - target) for idx in team_indices],
        )

        results = [
            TeamFinalResult(
                team_index=idx,
                team_name=state.config.teams[idx].name,
                team_color=state.config.teams[idx].color_hex,
                total_distance=state.total_distances[idx],
                distance_deviation=abs(state.total_distances[idx] - target),
                bonus_points=bonus_points[idx],
                total_points=state.total_points[idx],
                rank=final_ranking[idx],
            )
            for idx in team_indices
        ]
        results.sort(key=lambda entry: (entry.rank, -entry.total_points, entry.team_name.casefold()))
        return FinalResult(target_total_distance=target, team_results=results)

    def _generate_stages(self, config: GameConfig) -> list[Stage]:
        generated: list[tuple[str, int]] = []
        generated.extend(
            ("kort", self._rng.randint(SHORT_STAGE_RANGE[0], SHORT_STAGE_RANGE[1]))
            for _ in range(config.stages.short_count)
        )
        generated.extend(
            ("mellem", self._rng.randint(MEDIUM_STAGE_RANGE[0], MEDIUM_STAGE_RANGE[1]))
            for _ in range(config.stages.medium_count)
        )
        generated.extend(
            ("lang", self._rng.randint(LONG_STAGE_RANGE[0], LONG_STAGE_RANGE[1]))
            for _ in range(config.stages.long_count)
        )
        self._rng.shuffle(generated)

        return [
            Stage(number=idx + 1, category=category, length=length)
            for idx, (category, length) in enumerate(generated)
        ]

    @staticmethod
    def _rank_with_ties(values: list[int], ascending: bool) -> dict[int, int]:
        indexed = list(enumerate(values))
        indexed.sort(key=lambda item: item[1], reverse=not ascending)

        ranks: dict[int, int] = {}
        position = 1
        cursor = 0
        while cursor < len(indexed):
            _, value = indexed[cursor]
            group: list[tuple[int, int]] = []
            while cursor < len(indexed) and indexed[cursor][1] == value:
                group.append(indexed[cursor])
                cursor += 1
            for team_index, _ in group:
                ranks[team_index] = position
            position += len(group)
        return ranks

    @staticmethod
    def _rank_positions_for_scores(
        team_indices: list[int],
        points: list[int],
        tie_breakers: list[int],
    ) -> dict[int, int]:
        sortable = [(idx, points[idx], tie_breakers[idx]) for idx in team_indices]
        sortable.sort(key=lambda row: (-row[1], row[2], row[0]))

        ranks: dict[int, int] = {}
        position = 1
        cursor = 0
        while cursor < len(sortable):
            _, pts, tie_break = sortable[cursor]
            group: list[tuple[int, int, int]] = []
            while (
                cursor < len(sortable)
                and sortable[cursor][1] == pts
                and sortable[cursor][2] == tie_break
            ):
                group.append(sortable[cursor])
                cursor += 1
            for team_index, _, _ in group:
                ranks[team_index] = position
            position += len(group)
        return ranks

    @staticmethod
    def _bonus_points_for_rank(rank: int) -> int:
        if rank == 1:
            return 9
        if rank == 2:
            return 6
        if rank == 3:
            return 3
        return 0

    def _require_state(self) -> RaceState:
        if self._state is None:
            raise ValueError("Der er ikke startet et løb endnu.")
        return self._state
