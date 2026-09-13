from __future__ import annotations

import time

from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.redraft_trade_analysis_service import TradeEvaluation, TradeSideImpact
from src.services.trade_package_search_service import (
    MAX_PACKAGES_EVALUATED_PER_OPPONENT,
    MAX_TOTAL_PACKAGES_EVALUATED,
    TradePackageCandidate,
    _combos,
    _drop_dominated,
    _passes_utility_gates,
    _roster_size_legal,
    search_improve_position_packages,
    search_target_player_packages,
    search_win_win_packages,
)


def _row(player_id, name, position, value, rank):
    return RedraftRankingRow(
        rank, rank, player_id, name, position, "TST", value, 0, value, 0,
        "HIGH", 1, "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-09-01", False,
    )


def _profile(**overrides) -> LeagueProfile:
    kwargs = dict(
        profile_id="fixture-league", league_name="Fixture League", season=2026, team_count=10,
        roster=RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=0, dst=0, bench_size=6),
        scoring=ScoringSettings(reception=1), draft=DraftContext(rounds=15, draft_slot=5),
        practical_mode=True, provider="sleeper", provider_league_id="lg1",
    )
    kwargs.update(overrides)
    return LeagueProfile(**kwargs)


def _names_positions(ids, rows_by_id):
    return (
        {pid: rows_by_id[pid].player_name for pid in ids},
        {pid: rows_by_id[pid].position for pid in ids},
    )


# ---------------------------------------------------------------------------
# Fixture 1 (FIND_WIN_WIN / IMPROVE_POSITION): a 2-team scenario with real,
# individually-verified marginal-utility numbers (computed by running the
# real `evaluate_trade` against these exact rows before writing the
# assertions below -- not hand-guessed).
#
# K/DST are deliberately absent from every row here: `_asset_pool`
# (`shadow_numeric_authorities_service.py`) only models QB/RB/WR/TE --
# K/DST are real, disclosed "unmodeled assets" with a hard-coded 0.0 value
# in this ranking pool, same as `test_trade_finder_service.py`'s own
# fixture (which nominally configures k=1/dst=1 but never actually trades
# one either, for the same reason).
#
# My roster has two real starter holes (WR 1/2, TE 0/1: only 1 WR and 0 TE
# rostered). The opponent has genuine redundant depth at both positions
# (`opp-wr4`, `opp-te2`) -- their own starters are already filled by
# higher-value players. Both sides' weakest bench pieces (`my-rb4`/
# `my-rb5`) are true deadweight (buried behind real starters + FLEX).
# ---------------------------------------------------------------------------

def _two_team_ranking() -> RankingResult:
    rows = [
        _row("my-qb1", "My QB1", "QB", 300, 1),
        _row("my-rb1", "My RB1", "RB", 220, 2),
        _row("my-rb2", "My RB2", "RB", 180, 3),
        _row("my-rb3", "My RB3", "RB", 130, 4),  # fills FLEX
        _row("my-wr1", "My WR1", "WR", 150, 5),  # only WR rostered -- real hole at WR2
        _row("my-rb4", "My RB4", "RB", 70, 6),  # true deadweight bench
        _row("my-rb5", "My RB5", "RB", 60, 7),  # true deadweight bench (weakest)
        # NOTE: no TE at all -- a second real starter hole (TE 0/1).
        _row("opp-qb1", "Opp QB1", "QB", 280, 8),
        _row("opp-rb1", "Opp RB1", "RB", 210, 9),
        _row("opp-rb2", "Opp RB2", "RB", 170, 10),
        _row("opp-wr1", "Opp WR1", "WR", 230, 11),
        _row("opp-wr2", "Opp WR2", "WR", 190, 12),
        _row("opp-wr3", "Opp WR3", "WR", 140, 13),  # fills FLEX
        _row("opp-te1", "Opp TE1", "TE", 100, 14),
        _row("opp-te2", "Opp TE2", "TE", 15, 15),  # true deadweight backup TE
        _row("opp-wr4", "Opp WR4", "WR", 20, 16),  # true deadweight backup WR
    ]
    return RankingResult(_profile(), tuple(rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")


def _my_ids():
    return ["my-qb1", "my-rb1", "my-rb2", "my-rb3", "my-wr1", "my-rb4", "my-rb5"]


def _opp_ids():
    return [
        "opp-qb1", "opp-rb1", "opp-rb2", "opp-wr1", "opp-wr2", "opp-wr3",
        "opp-te1", "opp-te2", "opp-wr4",
    ]


def _two_team_search_kwargs():
    ranking = _two_team_ranking()
    rows_by_id = {row.player_id: row for row in ranking.rows}
    my_names, my_positions = _names_positions(_my_ids(), rows_by_id)
    opp_names, opp_positions = _names_positions(_opp_ids(), rows_by_id)
    opponents = [
        {
            "rosterId": "2", "teamName": "Rival Team",
            "canonicalIds": _opp_ids(), "names": opp_names, "positions": opp_positions,
        }
    ]
    return dict(
        my_roster_canonical_ids=_my_ids(), my_player_names=my_names, my_player_positions=my_positions,
        opponents=opponents, profile=ranking.profile, ranking=ranking, manual_assets=[],
    )


def test_find_win_win_returns_a_real_1_for_2_filling_two_starter_holes() -> None:
    result = search_win_win_packages(**_two_team_search_kwargs())
    assert result.candidates, "expected at least one real win-win candidate"
    shapes = {c.package_shape for c in result.candidates}
    one_for_two = [c for c in result.candidates if c.package_shape == "1-for-2"]
    assert one_for_two, f"expected a real 1-for-2 candidate; got shapes {shapes}"
    # At least one surviving 1-for-2 must fill BOTH real starter holes at
    # once (WR and TE) -- the exact reason this shape exists at all.
    assert any(
        "WR 1/2" in " ".join(c.why_it_helps_you) and "TE 0/1" in " ".join(c.why_it_helps_you)
        for c in one_for_two
    )
    for candidate in result.candidates:
        assert candidate.owner_evaluation.net_marginal_utility > 0.0
        assert candidate.opponent_evaluation.net_marginal_utility > 0.0


def test_find_win_win_never_returns_duplicate_packages() -> None:
    result = search_win_win_packages(**_two_team_search_kwargs())
    keys = [
        (c.opponent_roster_id, frozenset(c.you_send), frozenset(c.you_receive)) for c in result.candidates
    ]
    assert len(keys) == len(set(keys))


def test_why_explanations_are_structured_real_deltas_never_a_probability() -> None:
    result = search_win_win_packages(**_two_team_search_kwargs())
    assert result.candidates
    for candidate in result.candidates:
        assert candidate.why_it_helps_you
        assert candidate.why_it_may_fit_them
        for note in (*candidate.why_it_helps_you, *candidate.why_it_may_fit_them):
            lowered = note.lower()
            assert "probability" not in lowered
            assert "likely to accept" not in lowered
            assert "accept" not in lowered


# ---------------------------------------------------------------------------
# Mode: IMPROVE_POSITION -- receive side always includes the requested
# position, ranked by real ROS value (a different signal than the other two
# modes' "weakest bench" ordering -- see the module docstring).
# ---------------------------------------------------------------------------

def test_improve_position_always_includes_the_requested_position() -> None:
    kwargs = _two_team_search_kwargs()
    result = search_improve_position_packages(position="WR", **kwargs)
    assert result.candidates, "expected at least one real WR-improving candidate"
    for candidate in result.candidates:
        assert any(pid in ("opp-wr1", "opp-wr2", "opp-wr3", "opp-wr4") for pid in candidate.you_receive)
        assert candidate.owner_evaluation.net_marginal_utility > 0.0
        assert candidate.opponent_evaluation.net_marginal_utility >= 0.0


def test_improve_position_unknown_position_returns_no_candidates() -> None:
    kwargs = _two_team_search_kwargs()
    result = search_improve_position_packages(position="LB", **kwargs)
    assert result.candidates == ()
    assert result.opponents_searched == 0


# ---------------------------------------------------------------------------
# Fixture 2 (TARGET_PLAYER): opponent has a real, entrenched WR starter
# (`opp-star`) the owner wants, and a real hole at TE (0 TE rostered). The
# owner has a spare TE (`my-te2`) that would become a genuine starter for
# the opponent, plus one modest throwaway (`my-rb3`). Values verified by
# running `evaluate_trade` directly before writing assertions:
#   * my-rb3 alone -> opp-star: opponent net utility is NEGATIVE (a
#     mediocre throw-in cannot offset losing a real starter) -- excluded.
#   * my-te2 alone -> opp-star: opponent net utility is POSITIVE (the TE
#     fills their real hole) -- a real 1-for-1 candidate.
#   * my-rb3 + my-te2 -> opp-star: also positive, a distinct, non-dominated
#     2-for-1 candidate (higher owner utility than the 1-for-1 above).
# ---------------------------------------------------------------------------

def _target_player_ranking() -> RankingResult:
    rows = [
        _row("my-qb1", "My QB1", "QB", 300, 1),
        _row("my-rb1", "My RB1", "RB", 220, 2),
        _row("my-rb2", "My RB2", "RB", 180, 3),
        _row("my-wr1", "My WR1", "WR", 200, 4),
        _row("my-wr2", "My WR2", "WR", 160, 5),
        _row("my-te1", "My TE1", "TE", 90, 6),
        _row("my-te2", "My TE2", "TE", 140, 7),  # real spare -- would start elsewhere
        _row("my-rb3", "My RB3", "RB", 20, 8),  # modest throwaway
        _row("opp-qb1", "Opp QB1", "QB", 280, 9),
        _row("opp-rb1", "Opp RB1", "RB", 210, 10),
        _row("opp-rb2", "Opp RB2", "RB", 170, 11),
        _row("opp-wr1", "Opp WR1", "WR", 230, 12),
        _row("opp-wr2", "Opp WR2", "WR", 190, 13),
        _row("opp-wr3", "Opp WR3", "WR", 60, 14),
        _row("opp-star", "Opp Star WR", "WR", 150, 15),  # target -- a real entrenched starter
        # NOTE: opponent has NO TE at all -- a real starter hole.
    ]
    return RankingResult(_profile(), tuple(rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")


def _target_my_ids():
    return ["my-qb1", "my-rb1", "my-rb2", "my-wr1", "my-wr2", "my-te1", "my-te2", "my-rb3"]


def _target_opp_ids():
    return ["opp-qb1", "opp-rb1", "opp-rb2", "opp-wr1", "opp-wr2", "opp-wr3", "opp-star"]


def _target_player_search_kwargs():
    ranking = _target_player_ranking()
    rows_by_id = {row.player_id: row for row in ranking.rows}
    my_names, my_positions = _names_positions(_target_my_ids(), rows_by_id)
    opp_names, opp_positions = _names_positions(_target_opp_ids(), rows_by_id)
    opponents = [
        {
            "rosterId": "2", "teamName": "Rival Team",
            "canonicalIds": _target_opp_ids(), "names": opp_names, "positions": opp_positions,
        }
    ]
    return dict(
        my_roster_canonical_ids=_target_my_ids(), my_player_names=my_names, my_player_positions=my_positions,
        opponents=opponents, profile=ranking.profile, ranking=ranking, manual_assets=[],
    )


def test_target_player_excludes_a_mediocre_throw_in_only_package() -> None:
    kwargs = _target_player_search_kwargs()
    result = search_target_player_packages(target_player_id="opp-star", **kwargs)
    assert all(
        candidate.you_send != ("my-rb3",) for candidate in result.candidates
    ), "a lone mediocre throw-in leaves the opponent worse off and must be excluded"


def test_target_player_surfaces_real_1_for_1_and_2_for_1_packages() -> None:
    kwargs = _target_player_search_kwargs()
    result = search_target_player_packages(target_player_id="opp-star", **kwargs)
    assert result.candidates, "expected at least one real package that can acquire the target"
    shapes = {c.package_shape for c in result.candidates}
    assert "1-for-1" in shapes and "2-for-1" in shapes, shapes
    for candidate in result.candidates:
        assert "opp-star" in candidate.you_receive
        assert candidate.opponent_evaluation.net_marginal_utility >= 0.0
        target_impact = next(
            impact for impact in candidate.owner_evaluation.receives if impact.player_id == "opp-star"
        )
        assert target_impact.marginal_utility is not None and target_impact.marginal_utility > 0.0


def test_target_player_scoped_to_the_real_owning_roster() -> None:
    kwargs = _target_player_search_kwargs()
    # A second "opponent" that does not actually roster the target -- must
    # never be searched/returned against.
    kwargs["opponents"].append(
        {"rosterId": "3", "teamName": "Unrelated Team", "canonicalIds": ["opp-qb1"], "names": {}, "positions": {}}
    )
    result = search_target_player_packages(target_player_id="opp-star", **kwargs)
    assert all(c.opponent_roster_id == "2" for c in result.candidates)
    assert result.opponents_searched == 1


def test_target_player_missing_from_every_roster_returns_no_candidates() -> None:
    kwargs = _target_player_search_kwargs()
    result = search_target_player_packages(target_player_id="does-not-exist", **kwargs)
    assert result.candidates == ()
    assert result.opponents_searched == 0


# ---------------------------------------------------------------------------
# Legality (gate 1) -- unit test of the check itself, then a real,
# precisely-measured end-to-end proof that it is load-bearing (not a no-op).
# ---------------------------------------------------------------------------

def test_roster_size_legal_direct() -> None:
    profile = _profile(roster=RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=0, dst=0, bench_size=1))
    # total slots = 1+2+2+1+1+0+0+0+1 = 8
    roster_before = [f"p{i}" for i in range(8)]  # already at capacity
    assert _roster_size_legal(roster_before, ["p0"], ["new1"], profile)  # 1-for-1: still 8, legal
    assert not _roster_size_legal(roster_before, ["p0"], ["new1", "new2"], profile)  # 1-for-2: 9, illegal
    assert _roster_size_legal(roster_before, ["p0", "p1"], ["new1"], profile)  # 2-for-1: 7, legal


def test_end_to_end_legality_pruning_blocks_size_changing_packages_at_full_capacity() -> None:
    """Both rosters start EXACTLY at the league's configured capacity (4
    slots: QB/RB/WR + 1 bench). Any package that changes either side's
    total player count (1-for-2, 2-for-1) is therefore illegal by
    construction -- confirms the search actually prunes them rather than
    relying on `evaluate_trade` to reject them after the fact."""

    rows = [
        _row("my-qb", "My QB", "QB", 200, 1),
        _row("my-rb1", "My RB1", "RB", 150, 2),
        _row("my-wr1", "My WR1", "WR", 90, 3),
        _row("my-rb2", "My RB2", "RB", 20, 4),
        _row("opp-qb", "Opp QB", "QB", 190, 5),
        _row("opp-rb1", "Opp RB1", "RB", 140, 6),
        _row("opp-wr1", "Opp WR1", "WR", 30, 7),
        _row("opp-wr2", "Opp WR2", "WR", 25, 8),
    ]
    profile = _profile(roster=RosterSettings(qb=1, rb=1, wr=1, te=0, flex=0, k=0, dst=0, bench_size=1))
    ranking = RankingResult(profile, tuple(rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")
    rows_by_id = {row.player_id: row for row in rows}
    my_ids = ["my-qb", "my-rb1", "my-wr1", "my-rb2"]
    opp_ids = ["opp-qb", "opp-rb1", "opp-wr1", "opp-wr2"]
    my_names, my_positions = _names_positions(my_ids, rows_by_id)
    opp_names, opp_positions = _names_positions(opp_ids, rows_by_id)
    opponents = [
        {"rosterId": "2", "teamName": "Rival", "canonicalIds": opp_ids, "names": opp_names, "positions": opp_positions}
    ]
    result = search_win_win_packages(
        my_roster_canonical_ids=my_ids, my_player_names=my_names, my_player_positions=my_positions,
        opponents=opponents, profile=profile, ranking=ranking, manual_assets=[],
    )
    assert result.candidates, "expected at least one real same-size win-win candidate"
    for candidate in result.candidates:
        assert candidate.package_shape in ("1-for-1", "2-for-2")
    # Precise, load-bearing proof: with 4 players per side (candidates_per_
    # side default of 6 covers the whole roster), raw combos = 10 per side
    # (4 singles + 6 pairs); same-size cross products = 4*4 + 6*6 = 52 --
    # exactly the size-mismatched 1x2/2x1 combos (24+24=48) were pruned
    # before ever reaching `evaluate_trade`.
    assert result.packages_evaluated == 52


# ---------------------------------------------------------------------------
# Baseline-utility gate (gates 2/3) -- direct tests of the gate function.
# ---------------------------------------------------------------------------

def _fake_impact(player_id: str, marginal_utility: float | None) -> TradeSideImpact:
    return TradeSideImpact(
        player_id=player_id, player_name=player_id, position="WR", ros_replacement_value=0.0,
        marginal_utility=marginal_utility, becomes_starter=False, status_flag=None,
    )


def _fake_evaluation(*, net_marginal_utility: float | None, receives_impacts=()) -> TradeEvaluation:
    return TradeEvaluation(
        gives=(), receives=tuple(receives_impacts), ros_value_delta=0.0,
        net_marginal_utility=net_marginal_utility, starting_lineup_value_before=0.0,
        starting_lineup_value_after=0.0, starting_lineup_value_delta=0.0,
        bench_contingency_value_before=0.0, bench_contingency_value_after=0.0,
        starter_holes_before=(), starter_holes_after=(), position_redundancy_before={},
        position_redundancy_after={}, risk_flags=(),
    )


def test_win_win_gate_rejects_a_non_positive_owner_utility_package() -> None:
    owner_eval = _fake_evaluation(net_marginal_utility=0.0)  # not strictly > 0 -- must fail
    opponent_eval = _fake_evaluation(net_marginal_utility=5.0)
    assert not _passes_utility_gates(
        mode="FIND_WIN_WIN", owner_eval=owner_eval, opponent_eval=opponent_eval, target_player_id=None
    )


def test_win_win_gate_rejects_a_zero_opponent_utility_package() -> None:
    owner_eval = _fake_evaluation(net_marginal_utility=5.0)
    opponent_eval = _fake_evaluation(net_marginal_utility=0.0)  # win-win requires strictly > 0
    assert not _passes_utility_gates(
        mode="FIND_WIN_WIN", owner_eval=owner_eval, opponent_eval=opponent_eval, target_player_id=None
    )


def test_improve_position_gate_allows_zero_opponent_utility() -> None:
    owner_eval = _fake_evaluation(net_marginal_utility=5.0)
    opponent_eval = _fake_evaluation(net_marginal_utility=0.0)  # non-negative is enough here
    assert _passes_utility_gates(
        mode="IMPROVE_POSITION", owner_eval=owner_eval, opponent_eval=opponent_eval, target_player_id=None
    )


def test_target_player_gate_requires_positive_target_impact_not_owner_net() -> None:
    # Owner net utility is NEGATIVE (paying a real cost for the target) --
    # must still pass, because TARGET_PLAYER mode has no owner-net floor.
    owner_eval = _fake_evaluation(
        net_marginal_utility=-10.0, receives_impacts=[_fake_impact("target", 25.0)]
    )
    opponent_eval = _fake_evaluation(net_marginal_utility=0.0)
    assert _passes_utility_gates(
        mode="TARGET_PLAYER", owner_eval=owner_eval, opponent_eval=opponent_eval, target_player_id="target"
    )


def test_target_player_gate_rejects_a_target_with_non_positive_own_impact() -> None:
    owner_eval = _fake_evaluation(
        net_marginal_utility=50.0, receives_impacts=[_fake_impact("target", 0.0)]
    )
    opponent_eval = _fake_evaluation(net_marginal_utility=10.0)
    assert not _passes_utility_gates(
        mode="TARGET_PLAYER", owner_eval=owner_eval, opponent_eval=opponent_eval, target_player_id="target"
    )


def test_target_player_gate_rejects_negative_opponent_utility() -> None:
    owner_eval = _fake_evaluation(
        net_marginal_utility=50.0, receives_impacts=[_fake_impact("target", 25.0)]
    )
    opponent_eval = _fake_evaluation(net_marginal_utility=-0.01)
    assert not _passes_utility_gates(
        mode="TARGET_PLAYER", owner_eval=owner_eval, opponent_eval=opponent_eval, target_player_id="target"
    )


# ---------------------------------------------------------------------------
# Dominance filtering (gate 4) -- direct unit test on `_drop_dominated`.
# ---------------------------------------------------------------------------

def _fake_candidate(shape: str, send, receive, owner_utility: float, opp_utility: float) -> TradePackageCandidate:
    return TradePackageCandidate(
        opponent_roster_id="2", opponent_team_name="Rival Team", package_shape=shape,
        you_send=tuple(send), you_receive=tuple(receive), you_send_names=tuple(send),
        you_receive_names=tuple(receive),
        owner_evaluation=_fake_evaluation(net_marginal_utility=owner_utility),
        opponent_evaluation=_fake_evaluation(net_marginal_utility=opp_utility),
        why_it_helps_you=(), why_it_may_fit_them=(),
    )


def test_dominance_filter_removes_a_strictly_worse_larger_package() -> None:
    simple = _fake_candidate("1-for-1", ["a"], ["x"], owner_utility=10.0, opp_utility=5.0)
    worse_bigger = _fake_candidate("2-for-2", ["a", "b"], ["x", "y"], owner_utility=8.0, opp_utility=4.0)
    kept = _drop_dominated([simple, worse_bigger])
    assert simple in kept
    assert worse_bigger not in kept


def test_dominance_filter_keeps_a_bigger_package_that_wins_on_either_axis() -> None:
    simple = _fake_candidate("1-for-1", ["a"], ["x"], owner_utility=10.0, opp_utility=5.0)
    better_bigger = _fake_candidate("2-for-2", ["a", "b"], ["x", "y"], owner_utility=15.0, opp_utility=1.0)
    kept = _drop_dominated([simple, better_bigger])
    assert simple in kept
    assert better_bigger in kept  # higher owner utility -- not dominated on both axes


def test_dominance_filter_keeps_incomparable_same_size_packages() -> None:
    left = _fake_candidate("1-for-1", ["a"], ["x"], owner_utility=10.0, opp_utility=2.0)
    right = _fake_candidate("1-for-1", ["b"], ["y"], owner_utility=4.0, opp_utility=9.0)
    kept = _drop_dominated([left, right])
    assert left in kept
    assert right in kept


# ---------------------------------------------------------------------------
# Pruning bound + latency -- realistic 12-team league (11 opponents), each
# with a full 15-player roster.
# ---------------------------------------------------------------------------

def _build_realistic_league(num_opponents: int = 11):
    rows = []
    idx = 0

    def add(prefix, position, base_value, count):
        nonlocal idx
        ids = []
        for i in range(count):
            player_id = f"{prefix}-{position.lower()}{i}"
            value = max(5.0, base_value - i * 18.0)
            rows.append(_row(player_id, f"{prefix} {position}{i}", position, value, idx))
            ids.append(player_id)
            idx += 1
        return ids

    def build_roster(prefix):
        ids = []
        ids += add(prefix, "QB", 250, 2)
        ids += add(prefix, "RB", 220, 5)
        ids += add(prefix, "WR", 210, 5)
        ids += add(prefix, "TE", 100, 3)
        return ids

    my_ids = build_roster("my")
    opponents = []
    for opp_num in range(num_opponents):
        prefix = f"opp{opp_num}"
        opp_ids = build_roster(prefix)
        opponents.append({"rosterId": str(opp_num + 2), "teamName": f"Team {opp_num + 2}", "canonicalIds": opp_ids})

    profile = _profile(roster=RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=0, dst=0, bench_size=8))
    ranking = RankingResult(profile, tuple(rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")
    rows_by_id = {row.player_id: row for row in ranking.rows}
    my_names, my_positions = _names_positions(my_ids, rows_by_id)
    for opponent in opponents:
        names, positions = _names_positions(opponent["canonicalIds"], rows_by_id)
        opponent["names"] = names
        opponent["positions"] = positions
    return ranking, my_ids, my_names, my_positions, opponents


def test_pruning_and_latency_bounds_hold_on_a_realistic_12_team_league() -> None:
    ranking, my_ids, my_names, my_positions, opponents = _build_realistic_league(num_opponents=11)
    start = time.perf_counter()
    result = search_win_win_packages(
        my_roster_canonical_ids=my_ids, my_player_names=my_names, my_player_positions=my_positions,
        opponents=opponents, profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"FIND_WIN_WIN took {elapsed:.2f}s across 11 opponents -- exceeds the 5s target"
    assert result.packages_evaluated <= MAX_TOTAL_PACKAGES_EVALUATED
    assert result.opponents_searched <= 11
    # Bound is real per-opponent too, not just the global cap.
    assert MAX_PACKAGES_EVALUATED_PER_OPPONENT * 11 >= result.packages_evaluated


def test_combos_generates_both_size_1_and_size_2() -> None:
    combos = _combos(["a", "b", "c"])
    sizes = sorted(len(c) for c in combos)
    assert sizes == [1, 1, 1, 2, 2, 2]
    assert ("a", "b") in combos and ("a", "c") in combos and ("b", "c") in combos
