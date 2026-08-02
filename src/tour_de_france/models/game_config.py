"""Typed game configuration models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeamConfig:
    """Configuration for one team selected on setup."""

    name: str
    color_hex: str


@dataclass(frozen=True)
class StageCategoryConfig:
    """How many stages exist in each distance category."""

    short_count: int
    medium_count: int
    long_count: int

    @property
    def total_count(self) -> int:
        return self.short_count + self.medium_count + self.long_count


@dataclass(frozen=True)
class GameConfig:
    """Full setup payload emitted by the setup screen."""

    teams: list[TeamConfig]
    stages: StageCategoryConfig

    @property
    def team_count(self) -> int:
        return len(self.teams)
