"""Regression tests for race scoring and tie handling."""

from __future__ import annotations

import random
import unittest

from tour_de_france.models.game_config import GameConfig, StageCategoryConfig, TeamConfig
from tour_de_france.models.race_models import TeamStageInput
from tour_de_france.services.race_engine import RaceEngine


class RaceEngineTests(unittest.TestCase):
    def _config(self, team_count: int = 3) -> GameConfig:
        teams = [TeamConfig(name=f"Hold {idx + 1}", color_hex="#000000") for idx in range(team_count)]
        return GameConfig(
            teams=teams,
            stages=StageCategoryConfig(short_count=1, medium_count=0, long_count=0),
        )

    def test_stage_points_with_tie_for_first(self) -> None:
        engine = RaceEngine(rng=random.Random(1))
        stages = engine.start_race(self._config(3))
        target = stages[0].length

        result = engine.run_stage(
            [
                TeamStageInput(team_index=0, start_weight=target, end_weight=0),
                TeamStageInput(team_index=1, start_weight=target, end_weight=0),
                TeamStageInput(team_index=2, start_weight=target - 5, end_weight=0),
            ]
        )

        by_name = {row.team_name: row for row in result.team_results}
        self.assertEqual(by_name["Hold 1"].rank, 1)
        self.assertEqual(by_name["Hold 2"].rank, 1)
        self.assertEqual(by_name["Hold 1"].stage_points, 3)
        self.assertEqual(by_name["Hold 2"].stage_points, 3)
        self.assertEqual(by_name["Hold 3"].rank, 3)
        self.assertEqual(by_name["Hold 3"].stage_points, 1)

    def test_bonus_points_and_final_result(self) -> None:
        engine = RaceEngine(rng=random.Random(2))
        stages = engine.start_race(self._config(4))
        target = stages[0].length

        engine.run_stage(
            [
                TeamStageInput(team_index=0, start_weight=target, end_weight=0),
                TeamStageInput(team_index=1, start_weight=target, end_weight=0),
                TeamStageInput(team_index=2, start_weight=max(0, target - 2), end_weight=0),
                TeamStageInput(team_index=3, start_weight=max(0, target - 4), end_weight=0),
            ]
        )
        final = engine.finalize_race()
        by_name = {row.team_name: row for row in final.team_results}
        self.assertEqual(by_name["Hold 1"].bonus_points, 9)
        self.assertEqual(by_name["Hold 2"].bonus_points, 9)
        self.assertEqual(by_name["Hold 3"].bonus_points, 3)
        self.assertEqual(by_name["Hold 4"].bonus_points, 0)

    def test_standings_share_placement_on_equal_points(self) -> None:
        engine = RaceEngine(rng=random.Random(4))
        stages = engine.start_race(self._config(3))
        target = stages[0].length

        standings = engine.get_standings()
        self.assertEqual(standings.completed_stage_count, 0)
        self.assertEqual([team.rank for team in standings.teams], [1, 1, 1])

        engine.run_stage(
            [
                TeamStageInput(team_index=0, start_weight=target, end_weight=0),
                TeamStageInput(team_index=1, start_weight=target, end_weight=0),
                TeamStageInput(team_index=2, start_weight=max(0, target - 5), end_weight=0),
            ]
        )

        standings = engine.get_standings()
        self.assertEqual(standings.completed_stage_count, 1)
        self.assertFalse(standings.is_final)
        by_name = {team.team_name: team for team in standings.teams}
        self.assertEqual(by_name["Hold 1"].rank, 1)
        self.assertEqual(by_name["Hold 2"].rank, 1)
        self.assertEqual(by_name["Hold 3"].rank, 3)
        self.assertEqual(by_name["Hold 1"].total_points, 3)
        self.assertEqual(by_name["Hold 3"].total_points, 1)
        self.assertEqual([team.rank for team in standings.teams], [1, 1, 3])

        engine.finalize_race()
        final_standings = engine.get_standings()
        self.assertTrue(final_standings.is_final)
        final_by_name = {team.team_name: team for team in final_standings.teams}
        self.assertEqual(final_by_name["Hold 1"].total_points, 12)

    def test_duplicate_or_missing_team_inputs_rejected(self) -> None:
        engine = RaceEngine(rng=random.Random(3))
        engine.start_race(self._config(2))
        with self.assertRaises(ValueError):
            engine.run_stage(
                [
                    TeamStageInput(team_index=0, start_weight=10, end_weight=0),
                    TeamStageInput(team_index=0, start_weight=10, end_weight=0),
                ]
            )


if __name__ == "__main__":
    unittest.main()
