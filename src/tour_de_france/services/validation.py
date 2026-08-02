"""Validation helpers for setup input."""

from __future__ import annotations

from typing import Iterable

from tour_de_france.constants import MIN_TEAM_COUNT
from tour_de_france.models.game_config import StageCategoryConfig


def validate_setup(
    team_names: Iterable[str],
    stage_categories: StageCategoryConfig,
) -> list[str]:
    """Return a list of setup validation errors."""
    errors: list[str] = []

    normalized_names = [name.strip() for name in team_names]
    if len(normalized_names) < MIN_TEAM_COUNT:
        errors.append(f"Du skal have mindst {MIN_TEAM_COUNT} hold.")

    if stage_categories.total_count <= 0:
        errors.append("Du skal vælge mindst 1 etape i alt.")

    if any(not name for name in normalized_names):
        errors.append("Alle hold skal have et navn.")

    lowered = [name.casefold() for name in normalized_names]
    if len(lowered) != len(set(lowered)):
        errors.append("Holdnavne skal være unikke.")

    return errors
