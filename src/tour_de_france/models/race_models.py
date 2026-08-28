"""Runtime models for race progression and results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    """A generated race stage."""

    number: int
    category: str
    length: int


@dataclass(frozen=True)
class TeamStageInput:
    """Input values for one team on one stage."""

    team_index: int
    start_weight: int
    end_weight: int


@dataclass(frozen=True)
class StageInputView:
    """Prepared values used by stage input screen."""

    stage_number: int
    stage_count: int
    stage_length: int
    is_last_stage: bool
    start_locked: bool
    team_start_defaults: list[int]
    remaining_to_total: list[int]


@dataclass(frozen=True)
class TeamStageResult:
    """Computed stage result for one team."""

    team_index: int
    team_name: str
    team_color: str
    start_weight: int
    end_weight: int
    distance: int
    deviation: int
    rank: int
    stage_points: int


@dataclass(frozen=True)
class StageResult:
    """Result package returned after stage execution."""

    stage: Stage
    team_results: list[TeamStageResult]


@dataclass(frozen=True)
class TeamStanding:
    """Current standing for one team in the overall competition."""

    team_index: int
    team_name: str
    team_color: str
    total_points: int
    total_distance: int
    rank: int


@dataclass(frozen=True)
class StandingsView:
    """Snapshot of the overall competition used by the points table."""

    completed_stage_count: int
    stage_count: int
    target_total_distance: int
    is_final: bool
    teams: list[TeamStanding]


@dataclass(frozen=True)
class TeamFinalResult:
    """Final score card for one team."""

    team_index: int
    team_name: str
    team_color: str
    total_distance: int
    distance_deviation: int
    bonus_points: int
    total_points: int
    rank: int


@dataclass(frozen=True)
class FinalResult:
    """Final package returned at race end."""

    target_total_distance: int
    team_results: list[TeamFinalResult]
