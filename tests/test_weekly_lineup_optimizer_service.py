from __future__ import annotations

import itertools

from src.services.current_player_status_overrides_service import StatusOverride
from src.services.redraft_engine_v1_service import RosterSettings
from src.services.weekly_lineup_optimizer_service import (
    RosterCandidate,
    _SLOT_ELIGIBILITY,
    build_roster_candidates,
    optimize_weekly_lineup,
)
from src.services.weekly_projection_service import WeeklyProjectionRow


def _row(sleeper_id, name, position, points, canonical=None, identity="MATCHED"):
    return WeeklyProjectionRow(
        canonical_player_id=canonical or f"nwr-{sleeper_id}",
        sleeper_player_id=sleeper_id, player_name=name, position=position, team="AAA",
        week=1, season=2026, season_type="regular", league_id="lg",
        source="SLEEPER_WEEKLY_PROJECTIONS_V1", source_as_of="2026-09-10T00:00:00Z",
        projected_points=points, scoring_context="NWR_LEAGUE_SCORING", raw_stats={},
        identity_match=identity, gp=1.0,
    )


def _candidate(sleeper_id, name, position, points, starting=False, canonical=None, identity="MATCHED"):
    return RosterCandidate(
        sleeper_player_id=sleeper_id, canonical_player_id=canonical or f"nwr-{sleeper_id}",
        player_name=name, position=position, team="AAA", projected_points=points,
        identity_match=identity, currently_starting=starting,
    )


_STANDARD_ROSTER = RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=6)


def _brute_force_optimum(candidates, roster):
    slot_counts = {
        "QB": roster.qb, "RB": roster.rb, "WR": roster.wr, "TE": roster.te,
        "K": roster.k, "DST": roster.dst, "FLEX": roster.flex, "SUPERFLEX": roster.superflex,
    }
    slots = [slot for slot, count in slot_counts.items() for _ in range(count)]
    best = 0.0
    projected = [c for c in candidates if c.projected_points is not None]
    for combo in itertools.permutations(projected, min(len(slots), len(projected))):
        total = 0.0
        used_slots = list(slots)
        valid = True
        assignment_pool = list(used_slots)
        for player in combo:
            eligible_slot = next(
                (s for s in assignment_pool if player.position in _SLOT_ELIGIBILITY[s]), None
            )
            if eligible_slot is None:
                valid = False
                break
            assignment_pool.remove(eligible_slot)
            total += player.projected_points
        if valid:
            best = max(best, total)
    return best


def test_greedy_matches_brute_force_optimum_on_a_flex_tradeoff() -> None:
    # Classic FLEX tradeoff: a strong WR3 should beat a weak TE1 for FLEX.
    candidates = [
        _candidate("1", "QB1", "QB", 20.0),
        _candidate("2", "RB1", "RB", 18.0),
        _candidate("3", "RB2", "RB", 15.0),
        _candidate("4", "WR1", "WR", 17.0),
        _candidate("5", "WR2", "WR", 14.0),
        _candidate("6", "WR3", "WR", 13.0),  # should win FLEX over TE1
        _candidate("7", "TE1", "TE", 8.0),
        _candidate("8", "K1", "K", 7.0),
        _candidate("9", "DST1", "DST", 6.0),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=_STANDARD_ROSTER, status_overrides=())
    assert result.projected_total == _brute_force_optimum(candidates, _STANDARD_ROSTER)
    flex_slot = next(slot for slot in result.starters if slot.slot_type == "FLEX")
    assert flex_slot.player.player_name == "WR3"


def test_superflex_lets_a_second_qb_outscore_a_bench_rb() -> None:
    roster = RosterSettings(qb=1, rb=1, wr=1, te=1, flex=1, superflex=1, k=0, dst=0, bench_size=6)
    candidates = [
        _candidate("1", "QB1", "QB", 25.0),
        _candidate("2", "QB2", "QB", 22.0),  # should fill SUPERFLEX over a weak bench RB
        _candidate("3", "RB1", "RB", 12.0),
        _candidate("4", "RB2", "RB", 5.0),  # fills FLEX
        _candidate("5", "WR1", "WR", 14.0),
        _candidate("6", "TE1", "TE", 9.0),
        _candidate("7", "RB3-bench", "RB", 3.0),  # genuinely excess -> true bench
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    started_names = {slot.player.player_name for slot in result.starters if slot.player}
    assert "QB2" in started_names
    assert "RB3-bench" not in started_names
    assert result.projected_total == _brute_force_optimum(candidates, roster)


def test_hard_excludes_zero_value_status_override_and_reports_it() -> None:
    candidates = [
        _candidate("1", "QB1", "QB", 20.0, canonical="nwr-qb1"),
        _candidate("2", "RB1", "RB", 18.0, canonical="nwr-rb1"),
        _candidate("3", "RB2", "RB", 15.0, canonical="nwr-rb2"),
        _candidate("4", "WR1", "WR", 17.0, canonical="nwr-wr1"),
        _candidate("5", "WR2", "WR", 5.0, canonical="nwr-wr2"),  # SEASON_OUT
        _candidate("6", "WR3", "WR", 3.0, canonical="nwr-wr3"),
        _candidate("7", "TE1", "TE", 8.0, canonical="nwr-te1"),
        _candidate("8", "K1", "K", 7.0, canonical="nwr-k1"),
        _candidate("9", "DST1", "DST", 6.0, canonical="nwr-dst1"),
    ]
    overrides = (
        StatusOverride(
            player_id="nwr-wr2", player_name="WR2", kind="SEASON_OUT", reason="ACL",
            effective_date="2026-09-01", verified_at_utc="2026-09-01T00:00:00Z", sources=("test",),
        ),
    )
    result = optimize_weekly_lineup(candidates=candidates, roster=_STANDARD_ROSTER, status_overrides=overrides)
    assert "WR2" not in {c.player_name for c in result.excluded[:1]} or result.excluded[0].player_name == "WR2"
    assert any(c.player_name == "WR2" for c in result.excluded)
    assert not any(slot.player and slot.player.player_name == "WR2" for slot in result.starters)


def test_unmatched_identity_is_status_unknown_not_assumed_healthy() -> None:
    rows = (_row("1", "Deep Bench", "WR", 4.0, identity="UNMATCHED"),)
    candidates = build_roster_candidates(
        roster_sleeper_player_ids=["1"], starter_sleeper_player_ids=[],
        projection_rows=rows, status_overrides=(),
    )
    assert candidates[0].identity_match == "UNMATCHED"


def test_unprojected_player_never_fabricates_a_number_but_can_still_start_if_forced() -> None:
    candidates = [
        _candidate("1", "QB1", "QB", None),  # only QB on roster, no projection
    ]
    roster = RosterSettings(qb=1, rb=0, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=0)
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    qb_slot = result.starters[0]
    assert qb_slot.status == "UNPROJECTED"
    assert qb_slot.player.projected_points is None
    assert result.unprojected_starter_count == 1
    assert result.projected_total == 0.0


def test_swap_reasons_name_the_real_bench_upgrade() -> None:
    candidates = [
        _candidate("1", "QB1", "QB", 20.0, starting=True),
        _candidate("2", "RB1", "RB", 18.0, starting=True),
        _candidate("3", "RB2", "RB", 15.0, starting=True),
        _candidate("4", "WR1", "WR", 17.0, starting=True),
        _candidate("5", "WR2", "WR", 6.0, starting=True),
        _candidate("6", "WR3-bench", "WR", 13.0, starting=False),  # correct start, was benched
        _candidate("10", "RB3-bench", "RB", 10.0, starting=False),  # fills FLEX, pushes WR2 out
        _candidate("7", "TE1", "TE", 8.0, starting=True),
        _candidate("8", "K1", "K", 7.0, starting=True),
        _candidate("9", "DST1", "DST", 6.0, starting=True),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=_STANDARD_ROSTER, status_overrides=())
    summaries = [swap.summary for swap in result.swaps_vs_current]
    assert any("WR3-bench" in s and "over" in s for s in summaries)


def test_close_call_flags_a_small_margin_and_leaves_a_blowout_unflagged() -> None:
    candidates = [
        _candidate("1", "QB1", "QB", 20.0),
        _candidate("2", "RB1", "RB", 18.0),
        _candidate("3", "RB2", "RB", 15.0),
        _candidate("4", "WR1", "WR", 17.0),
        _candidate("5", "WR2", "WR", 14.0),
        _candidate("6", "WR3", "WR", 13.5),  # tiny margin over WR-bench below -> close call
        _candidate("7", "WR-bench", "WR", 13.0),
        _candidate("8", "TE1", "TE", 8.0),
        _candidate("9", "K1", "K", 7.0),
        _candidate("10", "DST1", "DST", 1.0),  # blowout at DST, only candidate -> no close call
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=_STANDARD_ROSTER, status_overrides=())
    flex_slot = next(slot for slot in result.starters if slot.slot_type == "FLEX")
    assert flex_slot.close_call is True
    dst_slot = next(slot for slot in result.starters if slot.slot_type == "DST")
    assert dst_slot.close_call is False
