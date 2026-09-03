"""QB pathology shadow replay (section 13).

Replays the owner-observed QB-heavy failure state (section 6/QB audit:
suggestions/rankings dominated by QBs even after the owner had enough QB
depth) against the SHADOW Team Score prototype -- checking whether
marginal roster value naturally suppresses QB3-in-1QB without any
hardcoded QB_BAD/NO_QB_EARLY rule, and that Superflex changes the
economics automatically rather than needing a separate code path.

No production ranking formula is touched or promoted from this file.
"""

from __future__ import annotations

from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.shadow_numeric_authorities_service import (
    RosterPlayer,
    optimal_starting_lineup_value,
)


def _ranking(*, superflex: int = 0) -> RankingResult:
    rows: list[RedraftRankingRow] = []
    for position, count in (("QB", 30), ("RB", 80), ("WR", 100), ("TE", 30)):
        for index in range(count):
            rank = len(rows) + 1
            rows.append(
                RedraftRankingRow(
                    rank,
                    index + 1,
                    f"{position}-{index}",
                    f"{position} {index}",
                    position,
                    "TST",
                    400 - rank,
                    0,
                    400 - rank,
                    0,
                    "HIGH",
                    1,
                    "fixture",
                    "Fixture",
                    "GOVERNED",
                    "AVAILABLE",
                    "2026-08-17",
                    False,
                )
            )
    roster = RosterSettings(
        qb=1, rb=2, wr=2, te=1, flex=1, superflex=superflex, k=1, dst=1, bench_size=6
    )
    profile = LeagueProfile(
        "fixture-league",
        "Fixture League",
        2026,
        10,
        roster,
        ScoringSettings(reception=1),
        DraftContext(rounds=15, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def _roster_value(ranking: RankingResult, player_ids: list[str]) -> float:
    by_id = {row.player_id: row for row in ranking.rows}
    players = [
        RosterPlayer(pid, by_id[pid].position, by_id[pid].replacement_adjusted_value)
        for pid in player_ids
    ]
    return optimal_starting_lineup_value(players, ranking.profile)


def test_1qb_league_qb_max_reached_gives_near_zero_marginal_value_for_a_third_qb() -> None:
    """0 QBs -> 1 QB rostered: real marginal value (fills the only QB
    starting slot). 1 QB -> 2 QBs (QB max reached at 2, matching the real
    KHA profile's roster_limits.QB=2): the second QB is bench-only in a
    1QB league and must contribute strictly less marginal Team Score than
    a genuinely needed starter at a scarce position -- with no QB-specific
    code anywhere in optimal_starting_lineup_value."""
    ranking = _ranking(superflex=0)

    empty_roster_value = _roster_value(ranking, [])
    with_qb1_value = _roster_value(ranking, ["QB-0"])
    with_qb1_and_qb2_value = _roster_value(ranking, ["QB-0", "QB-1"])
    with_qb1_and_rb1_value = _roster_value(ranking, ["QB-0", "RB-0"])

    marginal_first_qb = with_qb1_value - empty_roster_value
    marginal_second_qb = with_qb1_and_qb2_value - with_qb1_value
    marginal_rb_starter = with_qb1_and_rb1_value - with_qb1_value

    assert marginal_first_qb > 0  # filling the only starting QB slot has real value
    assert marginal_second_qb == 0  # 1QB league: a second QB never starts, ever
    assert marginal_rb_starter > 0  # a real starting slot elsewhere has real value
    assert marginal_second_qb < marginal_rb_starter


def test_superflex_changes_the_economics_automatically_no_special_case_needed() -> None:
    """Same code path, same function, only the league's roster.superflex
    count differs -- a second QB now has real marginal value because it
    can start in the superflex slot, without any format-specific QB code
    anywhere in optimal_starting_lineup_value."""
    ranking = _ranking(superflex=1)

    with_qb1_value = _roster_value(ranking, ["QB-0"])
    with_qb1_and_qb2_value = _roster_value(ranking, ["QB-0", "QB-1"])
    marginal_second_qb_superflex = with_qb1_and_qb2_value - with_qb1_value

    assert marginal_second_qb_superflex > 0  # unlike the 1QB case above


def test_superflex_shifts_the_zero_marginal_value_boundary_by_exactly_one_qb() -> None:
    """1QB has exactly 1 QB-eligible starting slot; Superflex (superflex=1)
    has exactly 2. So the *2nd* QB has real marginal value in Superflex
    but not 1QB (already covered above), while the *3rd* QB has zero
    marginal value in BOTH formats -- the zero-value boundary shifts by
    precisely one QB, matching the one extra QB-eligible slot Superflex
    actually adds, not an arbitrary/unlimited superflex bonus."""
    ranking_1qb = _ranking(superflex=0)
    ranking_superflex = _ranking(superflex=1)

    base_1qb = _roster_value(ranking_1qb, ["QB-0", "QB-1"])
    marginal_qb3_1qb = _roster_value(ranking_1qb, ["QB-0", "QB-1", "QB-2"]) - base_1qb

    base_superflex = _roster_value(ranking_superflex, ["QB-0", "QB-1"])
    marginal_qb3_superflex = (
        _roster_value(ranking_superflex, ["QB-0", "QB-1", "QB-2"]) - base_superflex
    )

    assert marginal_qb3_1qb == 0
    assert marginal_qb3_superflex == 0  # the extra slot was already used by QB-1


def test_replaying_the_owner_reported_state_qb_never_outranks_a_real_starting_need() -> None:
    """Direct replay of the reported failure mode: owner already has
    'enough QB depth' (QB1 + bench QB2, 1QB league) but a missing starter
    elsewhere. The marginal Team Score value of a 3rd bench QB must be
    zero and therefore can never outrank filling the missing starter
    slot -- reproduced structurally, not asserted by fiat."""
    ranking = _ranking(superflex=0)
    base = _roster_value(ranking, ["QB-0", "QB-1"])  # QB1 starter + QB2 bench, "enough QB depth"

    candidates = {
        "another_bench_qb": _roster_value(ranking, ["QB-0", "QB-1", "QB-2"]) - base,
        "missing_rb_starter": _roster_value(ranking, ["QB-0", "QB-1", "RB-0"]) - base,
        "missing_wr_starter": _roster_value(ranking, ["QB-0", "QB-1", "WR-0"]) - base,
        "missing_te_starter": _roster_value(ranking, ["QB-0", "QB-1", "TE-0"]) - base,
    }
    assert candidates["another_bench_qb"] == 0
    assert all(
        candidates["another_bench_qb"] < value
        for key, value in candidates.items()
        if key != "another_bench_qb"
    )
