"""Fast smoke test for scripts/run_shadow_numeric_authorities_benchmark_v1.py
-- the full script (~30s, 4 league profiles x 7 roster scenarios plus
Pick Score/optimizer sweeps) is meant to be run on demand to regenerate
the benchmark CSVs in docs/codex/, not on every test run. This exercises
the same real functions the script uses, at a fraction of the profile/
trial count, so a real regression in the benchmark's own building blocks
still fails CI quickly.
"""

from __future__ import annotations

from scripts.run_shadow_numeric_authorities_benchmark_v1 import (
    build_ranking,
    empty_adp,
    injury_hypotheses_for,
    manual_assets,
    roster_scenarios,
)
from src.services.redraft_draft_room_v1_service import _asset_pool
from src.services.shadow_numeric_authorities_service import (
    availability_adjusted_players,
    roster_composition_report,
    simulate_comparable_leagues,
    team_score,
)


def test_benchmark_building_blocks_run_end_to_end_at_small_scale() -> None:
    ranking = build_ranking(10, 15)
    profile = ranking.profile
    adp = empty_adp(profile)
    assets = manual_assets()
    pool = _asset_pool(ranking, assets)

    leagues = simulate_comparable_leagues(profile, ranking, assets, adp, trials=3, base_seed=1)
    assert len(leagues) == 3

    scenarios = roster_scenarios(pool)
    assert set(scenarios) == {
        "star_heavy_thin_bench", "balanced", "qb_heavy_1qb", "rb_heavy",
        "wr_heavy", "missing_te", "injury_risk_heavy",
    }
    for roster in scenarios.values():
        assert roster  # every scenario resolves to a non-empty player list

    balanced = scenarios["balanced"]
    composition = roster_composition_report(balanced, profile)
    assert composition.total_roster_value > 0

    score = team_score(
        [p.player_id for p in balanced], profile, ranking, assets, comparable_leagues=leagues
    )
    assert 0.0 <= score.percentile <= 100.0


def test_injury_hypotheses_zero_the_flagged_players_value() -> None:
    ranking = build_ranking(10, 15)
    pool = _asset_pool(ranking, manual_assets())
    scenarios = roster_scenarios(pool)
    injury_roster = scenarios["injury_risk_heavy"]

    hypotheses = injury_hypotheses_for(injury_roster)
    assert len(hypotheses) == 2
    flagged_ids = {h.subject_player_id for h in hypotheses}

    adjusted = availability_adjusted_players(injury_roster, hypotheses)
    for player in adjusted:
        if player.player_id in flagged_ids:
            assert player.value == 0.0
        else:
            original = next(p for p in injury_roster if p.player_id == player.player_id)
            assert player.value == original.value
