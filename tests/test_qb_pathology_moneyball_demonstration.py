"""Locks in the real numbers from
scripts/run_qb_pathology_moneyball_demonstration_v1.py (section 13):
in a 1QB league, a redundant 2nd QB contributes zero incremental
starting-lineup value despite a higher individual Player Score than the
alternative RB, and the SAME comparison inverts in Superflex.
"""

from __future__ import annotations

from scripts.run_qb_pathology_moneyball_demonstration_v1 import build_ranking, manual_assets
from src.services.redraft_draft_room_v1_service import AdpSnapshot, _asset_pool
from src.services.redraft_engine_v1_service import RosterSettings
from src.services.shadow_numeric_authorities_service import (
    RosterPlayer,
    roster_composition_report,
    simulate_comparable_leagues,
)

BASE_IDS = ["QB-0", "RB-4", "RB-5", "WR-4", "WR-5", "TE-4"]


def _starting_lineup_delta(roster: RosterSettings, candidate: str) -> tuple[float, float]:
    """Returns (candidate's own Player Score, its starting-lineup-value
    delta over the base roster)."""
    ranking = build_ranking(roster)
    profile = ranking.profile
    assets = manual_assets()
    pool = _asset_pool(ranking, assets)

    def roster_players(ids: list[str]) -> list[RosterPlayer]:
        return [
            RosterPlayer(
                pid, pool[pid]["position"], float(pool[pid]["replacement_adjusted_value"] or 0.0)
            )
            for pid in ids
        ]

    baseline = roster_composition_report(roster_players(BASE_IDS), profile)
    with_candidate = roster_composition_report(roster_players([*BASE_IDS, candidate]), profile)
    player_score = float(pool[candidate]["replacement_adjusted_value"])
    delta = with_candidate.starting_lineup_value - baseline.starting_lineup_value
    return player_score, delta


def test_redundant_qb_contributes_zero_starting_value_in_1qb_despite_higher_player_score() -> None:
    one_qb = RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=6)
    qb_score, qb_delta = _starting_lineup_delta(one_qb, "QB-18")
    rb_score, rb_delta = _starting_lineup_delta(one_qb, "RB-6")

    assert qb_score > rb_score  # the QB really is individually "better" by Player Score
    assert qb_delta == 0.0  # ...but contributes nothing to the current starting lineup
    assert rb_delta == rb_score  # while the RB's full value counts (it fills the FLEX slot)
    assert rb_delta > qb_delta  # the Moneyball inversion: worse Player Score, better pick


def test_same_qb_pick_fully_counts_in_superflex() -> None:
    superflex = RosterSettings(
        qb=1, rb=2, wr=2, te=1, flex=1, superflex=1, k=1, dst=1, bench_size=6
    )
    qb_score, qb_delta = _starting_lineup_delta(superflex, "QB-18")
    rb_score, rb_delta = _starting_lineup_delta(superflex, "RB-6")

    assert qb_delta == qb_score  # now fills the SUPERFLEX slot -- full value counts
    assert rb_delta == rb_score
    assert qb_delta > rb_delta  # and now the higher-Player-Score QB is the better pick again


def test_team_score_confirms_the_same_ordering_against_a_real_simulated_population() -> None:
    one_qb = RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=6)
    ranking = build_ranking(one_qb)
    profile = ranking.profile
    assets = manual_assets()
    adp = AdpSnapshot(profile.profile_id, "", "ppr", profile.team_count, "", "", "", (), ())
    leagues = simulate_comparable_leagues(profile, ranking, assets, adp, trials=10, base_seed=1)

    from src.services.shadow_numeric_authorities_service import team_score

    with_qb = team_score(
        [*BASE_IDS, "QB-18"], profile, ranking, assets, comparable_leagues=leagues
    )
    with_rb = team_score(
        [*BASE_IDS, "RB-6"], profile, ranking, assets, comparable_leagues=leagues
    )
    assert with_rb.percentile > with_qb.percentile
