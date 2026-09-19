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


def _candidate(
    sleeper_id, name, position, points, starting=False, canonical=None, identity="MATCHED",
    reserve=False, taxi=False, locked=False,
):
    return RosterCandidate(
        sleeper_player_id=sleeper_id, canonical_player_id=canonical or f"nwr-{sleeper_id}",
        player_name=name, position=position, team="AAA", projected_points=points,
        identity_match=identity, currently_starting=starting,
        is_reserve=reserve, is_taxi=taxi, is_locked=locked,
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


# ---------------------------------------------------------------------------
# NWR Sunday Readiness overnight cycle, Worker 2 -- the 5 concrete
# regression fixtures from the governing brief (section "2. Fix W1-W4"),
# each written as a real failing-before/passing-after case against the
# EXACT numbers the brief specifies. "Failing-before" is documented in each
# test's own comment (traced against the pre-fix source, not re-run against
# reverted code) rather than re-run live, since the fix already replaced
# that code in this same file.
# ---------------------------------------------------------------------------


def test_regression_fixture_1_duplicate_sits_produces_one_correct_swap_set() -> None:
    """Two RB slots; current A=10, B=9; bench C=20, D=19. Correct optimal
    set is C/D, total gain 20 (39 - 19). BEFORE this pass's fix, the old
    per-slot-type `_swap_reasons` independently searched the whole bench
    for "the currently-starting RB" for EACH newly-started RB slot and
    always picked the single highest-points one (A) both times -- emitting
    "START C over A" (+10) and "START D over A" (+9), sitting A twice and
    summing to a wrong displayed total of 19, never mentioning B at all.
    AFTER: exactly one swap per real newly-benched player, each used once,
    and the summed displayed deltas equal the real total gain.
    """

    roster = RosterSettings(qb=0, rb=2, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=10)
    candidates = [
        _candidate("a", "A", "RB", 10.0, starting=True),
        _candidate("b", "B", "RB", 9.0, starting=True),
        _candidate("c", "C", "RB", 20.0, starting=False),
        _candidate("d", "D", "RB", 19.0, starting=False),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    started_names = {slot.player.player_name for slot in result.starters if slot.player}
    assert started_names == {"C", "D"}
    assert result.projected_total == 39.0

    sat_players = [swap.bench_player for swap in result.swaps_vs_current]
    # The real bug: A named twice, B never named.
    assert sorted(sat_players) == ["A", "B"], "each real displaced incumbent must be named exactly once"
    assert len(result.swaps_vs_current) == 2
    total_displayed_gain = sum(swap.projected_delta for swap in result.swaps_vs_current)
    assert total_displayed_gain == 20.0, "displayed swap deltas must sum to the real total gain (39 - 19), not 19"


def test_regression_fixture_2_flex_rearrangement_no_longer_disappears() -> None:
    """RB=1, WR=1, FLEX=1; current RB=10 (RB slot), WR=20 (WR slot), FLEX
    WR=5 (FLEX slot); bench RB=15. Correct new set is WR20/RB15/RB10(FLEX).
    BEFORE this pass's fix: the old code's `slot.player.currently_starting`
    guard skipped the FLEX slot's new occupant (RB10, who is still
    `currently_starting` via his OLD slot) entirely, and the RB slot's new
    occupant (RB15) found no same-slot-type (RB-eligible) benched
    incumbent (the real displaced player, WR5, is a WR) -- so ZERO swaps
    were emitted and the UI's no-swaps branch claimed "Already optimal"
    despite the starting SET having actually changed. AFTER: the real
    before/after ID diff finds WR5 genuinely benched and RB15 genuinely
    new, and emits the real swap regardless of slot-type mismatch.
    """

    roster = RosterSettings(qb=0, rb=1, wr=1, te=0, flex=1, superflex=0, k=0, dst=0, bench_size=10)
    candidates = [
        _candidate("rb10", "RB10", "RB", 10.0, starting=True),
        _candidate("wr20", "WR20", "WR", 20.0, starting=True),
        _candidate("wr5", "WR5", "WR", 5.0, starting=True),
        _candidate("rb15", "RB15", "RB", 15.0, starting=False),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    started_names = {slot.player.player_name for slot in result.starters if slot.player}
    assert started_names == {"WR20", "RB15", "RB10"}
    assert result.projected_total == 45.0
    # The real bug: this was empty (falsely "Already optimal").
    assert len(result.swaps_vs_current) >= 1
    assert any(swap.start_player == "RB15" and swap.bench_player == "WR5" for swap in result.swaps_vs_current)


def test_regression_fixture_3_missing_starter_counts_as_unprojected_not_silently_dropped() -> None:
    """A real roster/starter id with NO row at all in
    `weekly_projection_service`'s output. BEFORE this pass's fix:
    `build_roster_candidates` silently `continue`d past it -- the
    candidate list, the EMPTY slot's own accounting, and
    `unprojected_starter_count` all showed zero real effect, letting a
    caller's LIVE-feed confidence gate stay falsely NOMINAL. AFTER: the
    player is kept (for coverage/explanation) and a real empty starting
    slot increments `unprojected_starter_count`.
    """

    roster = RosterSettings(qb=1, rb=0, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=0)
    candidates = build_roster_candidates(
        roster_sleeper_player_ids=["missing-1"],
        starter_sleeper_player_ids=["missing-1"],
        projection_rows=(),  # no row anywhere for this id -- the real gap
        status_overrides=(),
    )
    # The real bug: this used to be an empty tuple (the player vanished).
    assert len(candidates) == 1
    assert candidates[0].identity_match == "UNMATCHED_NO_PROJECTION_ROW"
    assert candidates[0].projected_points is None

    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    qb_slot = result.starters[0]
    assert qb_slot.status == "EMPTY"
    # The real bug: this was 0 before the fix (an empty slot was invisible
    # to the confidence gate).
    assert result.unprojected_starter_count == 1
    assert len(result.swaps_vs_current) == 0  # no real replacement was available to name


def test_regression_fixture_3b_missing_starter_resolves_name_and_position_from_catalog() -> None:
    """Same real gap as fixture 3, but the caller supplies the real Sleeper
    player catalog (as the facade does) -- the missing player is now
    resolved to a real name/position instead of an opaque id, still
    honestly unprojected."""

    candidates = build_roster_candidates(
        roster_sleeper_player_ids=["9001"],
        starter_sleeper_player_ids=["9001"],
        projection_rows=(),
        status_overrides=(),
        player_catalog={"9001": {"position": "RB", "team": "sf", "full_name": "Real Player"}},
    )
    assert len(candidates) == 1
    assert candidates[0].player_name == "Real Player"
    assert candidates[0].position == "RB"
    assert candidates[0].team == "SF"
    assert candidates[0].projected_points is None
    assert candidates[0].identity_match == "UNMATCHED_NO_PROJECTION_ROW"


def test_regression_fixture_4_unmatched_identity_not_promoted_to_ok() -> None:
    """An unmatched RB with 10 projected points, the only candidate for a
    single RB slot. BEFORE this pass's fix: the final `LineupSlot.status`
    was derived purely from `projected_points is None`, so a real,
    provider-scored-but-identity-UNMATCHED player rendered as plain "OK" --
    indistinguishable from a confirmed-identity starter. AFTER: identity
    confirmation is checked FIRST; an unmatched starter is always
    UNRESOLVED_IDENTITY, never OK, regardless of whether points exist.
    """

    roster = RosterSettings(qb=0, rb=1, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=0)
    candidates = [
        _candidate("u1", "Unknown RB", "RB", 10.0, starting=False, identity="UNMATCHED"),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    rb_slot = result.starters[0]
    assert rb_slot.player is not None
    assert rb_slot.player.player_name == "Unknown RB"
    # The real bug: this was "OK" before the fix.
    assert rb_slot.status == "UNRESOLVED_IDENTITY"
    assert rb_slot.status != "OK"
    assert result.unresolved_identity_starter_count == 1
    # Points are still real/usable (Sleeper did project 10) -- only the
    # STATUS label changes, never a silent zeroing of a real number.
    assert result.projected_total == 10.0


def test_kdst_unmatched_identity_is_not_flagged_unresolved_by_design() -> None:
    """Real, live-reproduced follow-up finding (verified against Fantasy
    Gamers' real Week 2 roster this pass): NWR's governed ranking has ZERO
    K/DST rows BY DESIGN (the same established distinction
    `waiver_engine_service.py`'s own `_OUT_OF_RANKED_MODEL_SCOPE_POSITIONS`
    draws), so every real K/DST candidate is structurally
    `identity_match != "MATCHED"` in every league, every week -- never a
    genuine identity failure. Without this carve-out, fixture 4's fix would
    make any league that starts a K or DST show permanently LOW confidence
    for a real, expected scope boundary, not an actual data problem.
    """

    roster = RosterSettings(qb=0, rb=0, wr=0, te=0, flex=0, superflex=0, k=1, dst=1, bench_size=0)
    candidates = [
        _candidate("k1", "Some Kicker", "K", 8.0, identity="UNMATCHED"),
        _candidate("d1", "NE D/ST", "DST", 6.0, identity="UNMATCHED"),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    statuses = {slot.slot_type: slot.status for slot in result.starters}
    assert statuses["K"] == "OK"
    assert statuses["DST"] == "OK"
    assert result.unresolved_identity_starter_count == 0


def test_regression_fixture_5a_reserve_excluded_from_normal_candidate_selection() -> None:
    """Without a matching hard-exclusion override, a 20-point reserve
    candidate must NOT beat the active 10-point starter. BEFORE this
    pass's fix, reserve/taxi membership was not carried into this
    optimizer at all, so a reserve player retaining a real projection
    could win the greedy selection outright. AFTER: reserve/taxi are
    hard-excluded from the normal eligible pool before any point
    comparison happens.
    """

    roster = RosterSettings(qb=0, rb=1, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=10)
    candidates = [
        _candidate("active", "Active Starter", "RB", 10.0, starting=True),
        _candidate("reserve", "Reserve Player", "RB", 20.0, starting=False, reserve=True),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    rb_slot = result.starters[0]
    assert rb_slot.player is not None
    # The real bug: this would have been "Reserve Player" (20 > 10) before the fix.
    assert rb_slot.player.player_name == "Active Starter"
    assert any(c.player_name == "Reserve Player" for c in result.reserve)
    assert not any(c.player_name == "Reserve Player" for c in result.bench)


def test_regression_fixture_5b_locked_starter_is_pinned_not_swapped_out() -> None:
    """A 10-point ALREADY-LOCKED starter must not be swapped for a
    20-point bench candidate -- his real game already kicked off, so NWR
    cannot legally recommend benching him. BEFORE this pass's fix, lock
    state was not carried into this optimizer at all, so pure point
    comparison would have swapped him out. AFTER: a locked current
    starter is pinned in phase 1, before the normal greedy comparison
    ever runs.
    """

    roster = RosterSettings(qb=0, rb=1, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=10)
    candidates = [
        _candidate("locked", "Locked Starter", "RB", 10.0, starting=True, locked=True),
        _candidate("bench", "Bench Upgrade", "RB", 20.0, starting=False, locked=False),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    rb_slot = result.starters[0]
    assert rb_slot.player is not None
    # The real bug: this would have been "Bench Upgrade" (20 > 10) before the fix.
    assert rb_slot.player.player_name == "Locked Starter"
    assert any(c.player_name == "Bench Upgrade" for c in result.bench)
    assert len(result.swaps_vs_current) == 0


def test_regression_fixture_5c_locked_bench_player_excluded_from_new_starts() -> None:
    """A bench player whose own game already kicked off (locked) and who
    was NOT already starting must never be newly started this week, even
    when he is the only real candidate for an open slot -- inserting him
    now would be illegal on the real platform. The slot must stay real and
    visibly EMPTY, not silently filled by an illegal move."""

    roster = RosterSettings(qb=0, rb=1, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=10)
    candidates = [
        _candidate("locked_bench", "Locked Bench Player", "RB", 25.0, starting=False, locked=True),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    rb_slot = result.starters[0]
    assert rb_slot.player is None
    assert rb_slot.status == "EMPTY"
    assert any(c.player_name == "Locked Bench Player" for c in result.locked_unavailable)


# ---------------------------------------------------------------------------
# NWR connection/update pass, Worker 2 (2026-09-19) -- owner-reported bug
# fix: `_swap_reasons` used to compute `bumped.projected_points or 0.0`,
# silently treating a genuinely MISSING weekly projection on the displaced
# player as a real, known 0.0. This fabricated a delta equal to the new
# starter's own raw points (real-world case: Zay Flowers had no projection
# row this week; both "start Pittman over Flowers, +11.7" and "start Coker
# over [bench], +7.6" were built on this exact silent-zero substitution).
# These fixtures prove the fix DISTINGUISHES a genuinely missing projection
# from a real, known 0.0 -- an explicit owner requirement, not merely "no
# crash".
# ---------------------------------------------------------------------------


def test_swap_with_real_known_zero_bumped_projection_produces_a_real_numeric_delta() -> None:
    """A real, KNOWN 0.0 projection (e.g. a kicker projected for exactly
    zero points in a specific bad-weather week) is a genuine, computable
    value -- the resulting delta must be a real number equal to the new
    starter's own points minus that real 0.0, with `delta_basis == "KNOWN"`,
    never treated the same as a missing projection."""

    roster = RosterSettings(qb=0, rb=0, wr=0, te=0, flex=0, superflex=0, k=1, dst=0, bench_size=10)
    candidates = [
        _candidate("k_bad_weather", "Bad Weather Kicker", "K", 0.0, starting=True),
        _candidate("k_bench", "Bench Kicker", "K", 9.0, starting=False),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    assert len(result.swaps_vs_current) == 1
    swap = result.swaps_vs_current[0]
    assert swap.start_player == "Bench Kicker"
    assert swap.bench_player == "Bad Weather Kicker"
    assert swap.delta_basis == "KNOWN"
    assert swap.projected_delta == 9.0  # 9.0 - a REAL, known 0.0 -- not fabricated, not dropped
    assert "9.0" in swap.summary


def test_swap_with_missing_bumped_projection_is_honestly_unknown_not_fabricated_zero() -> None:
    """The displaced player has NO real weekly-projection row at all
    (`projected_points=None`) -- a genuinely missing value, not a real
    zero. The fix must represent this delta as honestly UNKNOWN
    (`projected_delta is None`, `delta_basis ==
    "UNKNOWN_MISSING_BENCH_PROJECTION"`), never as a fabricated number
    equal to the new starter's own raw points (the exact pre-fix bug)."""

    roster = RosterSettings(qb=0, rb=0, wr=1, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=10)
    candidates = [
        _candidate("wr_no_projection", "No-Projection Incumbent", "WR", None, starting=True),
        _candidate("wr_bench", "New Starter", "WR", 12.0, starting=False),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    assert len(result.swaps_vs_current) == 1
    swap = result.swaps_vs_current[0]
    assert swap.start_player == "New Starter"
    assert swap.bench_player == "No-Projection Incumbent"
    assert swap.delta_basis == "UNKNOWN_MISSING_BENCH_PROJECTION"
    assert swap.projected_delta is None
    # The pre-fix bug would have fabricated exactly 12.0 (12.0 - 0.0).
    assert "12.0" not in swap.summary
    assert "unknown" in swap.summary.lower()
    assert "missing" in swap.summary.lower()


def test_owner_reported_zay_flowers_shaped_case_reproduced_and_fixed() -> None:
    """The exact real-world shape from the owner's bug report: a real
    starter promotion (Michael Pittman over Zay Flowers) where the
    displaced player (Zay Flowers) has no projection row this week at all.
    Confirms the fix produces the honest unknown state, not a fabricated
    "+11.7"-style number."""

    roster = RosterSettings(qb=0, rb=0, wr=1, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=10)
    candidates = [
        _candidate("zay_flowers", "Zay Flowers", "WR", None, starting=True),
        _candidate("michael_pittman", "Michael Pittman", "WR", 11.7, starting=False),
    ]
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    assert len(result.swaps_vs_current) == 1
    swap = result.swaps_vs_current[0]
    assert swap.start_player == "Michael Pittman"
    assert swap.bench_player == "Zay Flowers"
    assert swap.projected_delta is None, "must NOT be the fabricated 11.7 (Pittman's own raw points minus an assumed zero)"
    assert swap.delta_basis == "UNKNOWN_MISSING_BENCH_PROJECTION"
    assert "+11.7" not in swap.summary
    assert "Zay Flowers" in swap.summary and "missing" in swap.summary.lower()

