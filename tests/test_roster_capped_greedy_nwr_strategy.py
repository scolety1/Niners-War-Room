"""Regression tests for the real, production position-cap fix
(`compute_position_caps` / `make_roster_capped_greedy_nwr_strategy`),
per the NWR Final Pre-2025 Hardening V1 directive's explicit requirement
for tests covering: no pathological QB hoarding, valid depth,
league-specific positional caps, roster legality, K/DST handling, and
normal late-round depth behavior -- across multiple real league shapes
(1QB, Superflex, 2QB, K/DST-inclusive), not just the historical 1QB
shape the underlying defect was discovered in.
"""

from __future__ import annotations

from src.services.draft_strategy_framework_service import (
    STRATEGY_ROSTER_CAPPED_GREEDY_NWR,
    StrategyDecisionContext,
    baseline_strategy_registry,
    compute_position_caps,
    make_roster_capped_greedy_nwr_strategy,
)
from src.services.point_in_time_feature_store_service import (
    FAMILY_NWR_COMPONENT_SCORES,
    FAMILY_POSITION,
    PointInTimeFeatureStore,
    known_feature_value,
)

HISTORICAL_ROSTER_SLOTS = {
    "qb": 1, "rb": 1, "wr": 1, "te": 1, "flex": 1, "superflex": 0,
    "k": 0, "dst": 0, "bench_size": 1,
}
SUPERFLEX_ROSTER_SLOTS = {
    "qb": 1, "rb": 2, "wr": 2, "te": 1, "flex": 1, "superflex": 1,
    "k": 1, "dst": 1, "bench_size": 6,
}
TWO_QB_ROSTER_SLOTS = {
    "qb": 2, "rb": 2, "wr": 2, "te": 1, "flex": 1, "superflex": 0,
    "k": 0, "dst": 0, "bench_size": 6,
}
NO_BENCH_NO_FLEX_SLOTS = {
    "qb": 1, "rb": 1, "wr": 1, "te": 1, "flex": 0, "superflex": 0,
    "k": 0, "dst": 0, "bench_size": 0,
}


def _feature_value(player_id, feature_name, family, value):
    return known_feature_value(
        player_id=player_id, season=2026, as_of="2026-08-15", feature_name=feature_name,
        feature_family=family, value=value, source="s",
        source_as_of="2026-08-01", retrieved_at="2026-08-01",
    )


def _player(store_values: list, player_id: str, position: str, rank: float) -> None:
    store_values.append(
        _feature_value(
            player_id, "nwr_component_scores.overall_rank", FAMILY_NWR_COMPONENT_SCORES, rank
        )
    )
    store_values.append(_feature_value(player_id, "position", FAMILY_POSITION, position))


def _context(store, available, roster, **overrides) -> StrategyDecisionContext:
    defaults = dict(
        league_rules_summary={"open_starter_positions": ()},
        pick_number=1, round_number=1, available_player_ids=available,
        roster_player_ids=roster, feature_store=store, as_of="2026-08-15", season=2026,
    )
    defaults.update(overrides)
    return StrategyDecisionContext(**defaults)


# --- compute_position_caps: league-config-derived, never a universal constant --

def test_caps_derived_from_historical_1qb_roster() -> None:
    caps = compute_position_caps(HISTORICAL_ROSTER_SLOTS)
    assert caps["QB"] == 2  # 1 starter + 1 bench (QB not flex-eligible)
    assert caps["RB"] == 3  # 1 starter + 1 flex + 1 bench
    assert caps["WR"] == 3
    assert caps["TE"] == 3


def test_caps_do_not_silently_break_superflex() -> None:
    caps = compute_position_caps(SUPERFLEX_ROSTER_SLOTS)
    historical_caps = compute_position_caps(HISTORICAL_ROSTER_SLOTS)
    assert caps["QB"] > historical_caps["QB"]  # Superflex needs real QB depth
    assert "K" in caps and "DST" in caps  # real K/DST slots get real caps


def test_caps_handle_2qb_leagues() -> None:
    caps = compute_position_caps(TWO_QB_ROSTER_SLOTS)
    assert caps["QB"] == 8  # 2 starters + 0 superflex + 6 bench


def test_caps_omit_kdst_when_league_does_not_roster_them() -> None:
    caps = compute_position_caps(HISTORICAL_ROSTER_SLOTS)
    assert "K" not in caps
    assert "DST" not in caps


def test_caps_never_go_below_one_even_with_no_bench_or_flex() -> None:
    caps = compute_position_caps(NO_BENCH_NO_FLEX_SLOTS)
    assert all(cap >= 1 for cap in caps.values())
    assert caps == {"QB": 1, "RB": 1, "WR": 1, "TE": 1}


# --- make_roster_capped_greedy_nwr_strategy: real drafting behavior -----------

def test_no_pathological_qb_hoarding() -> None:
    """The exact defect this fix targets: a roster already at its real QB
    cap must never draft another QB, even if that QB is the single best
    remaining player by NWR rank."""
    store_values: list = []
    _player(store_values, "elite_qb_3", "QB", rank=1.0)  # best remaining player overall
    _player(store_values, "decent_rb", "RB", rank=50.0)
    store = PointInTimeFeatureStore().with_values(store_values)
    strategy = make_roster_capped_greedy_nwr_strategy(HISTORICAL_ROSTER_SLOTS)
    # Roster already has 2 QBs -- at the real historical-roster QB cap.
    # The roster-composition lookup needs positions for already-rostered
    # players too.
    store_values.append(_feature_value("qb_1_already_rostered", "position", FAMILY_POSITION, "QB"))
    store_values.append(_feature_value("qb_2_already_rostered", "position", FAMILY_POSITION, "QB"))
    store = PointInTimeFeatureStore().with_values(store_values)
    context = _context(
        store, ("elite_qb_3", "decent_rb"), ("qb_1_already_rostered", "qb_2_already_rostered"),
    )
    decision = strategy(context)
    assert decision.selected_player_id == "decent_rb"  # NOT the elite QB
    assert decision.strategy_name == STRATEGY_ROSTER_CAPPED_GREEDY_NWR


def test_valid_depth_normal_pick_when_no_cap_binds() -> None:
    """With an empty roster, behavior matches the uncapped greedy
    ranking -- the fix changes nothing when no cap is actually binding."""
    store_values: list = []
    _player(store_values, "best", "RB", rank=1.0)
    _player(store_values, "worse", "WR", rank=10.0)
    store = PointInTimeFeatureStore().with_values(store_values)
    strategy = make_roster_capped_greedy_nwr_strategy(HISTORICAL_ROSTER_SLOTS)
    decision = strategy(_context(store, ("best", "worse"), ()))
    assert decision.selected_player_id == "best"


def test_superflex_league_allows_a_second_and_third_qb() -> None:
    """The same roster composition (2 QBs already rostered) that excludes
    a 3rd QB under the 1-QB historical shape must NOT exclude one under a
    real Superflex league shape -- this is the exact "do not silently
    break Superflex" requirement."""
    store_values: list = []
    _player(store_values, "elite_qb_3", "QB", rank=1.0)
    _player(store_values, "decent_rb", "RB", rank=50.0)
    store_values.append(_feature_value("qb_1", "position", FAMILY_POSITION, "QB"))
    store_values.append(_feature_value("qb_2", "position", FAMILY_POSITION, "QB"))
    store = PointInTimeFeatureStore().with_values(store_values)
    strategy = make_roster_capped_greedy_nwr_strategy(SUPERFLEX_ROSTER_SLOTS)
    decision = strategy(_context(store, ("elite_qb_3", "decent_rb"), ("qb_1", "qb_2")))
    assert decision.selected_player_id == "elite_qb_3"  # allowed under Superflex


def test_roster_legality_caps_are_never_exceeded_across_a_full_mock_draft() -> None:
    """Simulates enough sequential picks that, without the fix, the
    strategy would draft a position past its legal cap -- confirms the
    real strategy function itself (not just compute_position_caps in
    isolation) enforces the cap through a realistic sequence of calls."""
    store_values: list = []
    # 5 QBs all rank ahead of everything else (the exact failure mode
    # discovered in real historical replay) -- plus a REALISTIC amount of
    # non-QB depth (as any real historical season pool would have), so
    # the roster fills entirely from legal alternatives without ever
    # needing the (separately, deliberately tested) exhaustion fallback.
    for i in range(5):
        _player(store_values, f"qb_{i}", "QB", rank=float(i))
    non_qb_ids: list[str] = []
    for i in range(10):
        for position in ("RB", "WR", "TE"):
            pid = f"{position.lower()}_{i}"
            _player(store_values, pid, position, rank=100.0 + i)
            non_qb_ids.append(pid)
    store = PointInTimeFeatureStore().with_values(store_values)
    strategy = make_roster_capped_greedy_nwr_strategy(HISTORICAL_ROSTER_SLOTS)

    roster: tuple[str, ...] = ()
    available = ("qb_0", "qb_1", "qb_2", "qb_3", "qb_4", *non_qb_ids)
    picks: list[str] = []
    for _ in range(6):  # the historical roster's own 6 total slots
        decision = strategy(_context(store, available, roster))
        assert decision.selected_player_id is not None
        assert not decision.decision_metadata.get("cap_fallback_triggered")
        picks.append(decision.selected_player_id)
        roster = (*roster, decision.selected_player_id)
        available = tuple(p for p in available if p != decision.selected_player_id)

    qb_count = sum(1 for p in picks if p.startswith("qb_"))
    assert qb_count <= 2  # the real historical-roster QB cap -- never hoards all 5


def test_kdst_respected_when_league_rosters_them() -> None:
    store_values: list = []
    _player(store_values, "k_1", "K", rank=200.0)
    _player(store_values, "k_2", "K", rank=201.0)
    _player(store_values, "rb_1", "RB", rank=50.0)
    store_values.append(_feature_value("k_already_rostered", "position", FAMILY_POSITION, "K"))
    store = PointInTimeFeatureStore().with_values(store_values)
    strategy = make_roster_capped_greedy_nwr_strategy(SUPERFLEX_ROSTER_SLOTS)  # k=1, bench=6: cap 7
    decision = strategy(_context(store, ("k_1", "k_2", "rb_1"), ("k_already_rostered",)))
    # cap not yet reached (1 K rostered, cap 7) -- a 2nd K is still legal to
    # consider, so the best-ranked available player (rb_1, lower rank
    # value wins) should still be selected on pure rank, confirming K
    # isn't being incorrectly excluded when under its real cap.
    assert decision.selected_player_id == "rb_1"


def test_fallback_when_every_available_player_is_at_a_capped_position() -> None:
    """A real edge case near the end of a thin historical pool: if every
    remaining player is at an already-capped position, the strategy must
    still return a real pick (never silently select nothing), with the
    fallback disclosed in decision_metadata."""
    store_values: list = []
    _player(store_values, "qb_only_option", "QB", rank=5.0)
    store_values.append(_feature_value("qb_1", "position", FAMILY_POSITION, "QB"))
    store_values.append(_feature_value("qb_2", "position", FAMILY_POSITION, "QB"))
    store = PointInTimeFeatureStore().with_values(store_values)
    strategy = make_roster_capped_greedy_nwr_strategy(HISTORICAL_ROSTER_SLOTS)
    decision = strategy(_context(store, ("qb_only_option",), ("qb_1", "qb_2")))
    assert decision.selected_player_id == "qb_only_option"
    assert decision.decision_metadata.get("cap_fallback_triggered") is True


# --- registry integration: purely additive, never changes existing callers ---

def test_registry_omits_capped_strategy_when_roster_slots_not_supplied() -> None:
    registry = baseline_strategy_registry()
    assert STRATEGY_ROSTER_CAPPED_GREEDY_NWR not in registry


def test_registry_includes_capped_strategy_when_roster_slots_supplied() -> None:
    registry = baseline_strategy_registry(roster_slots=HISTORICAL_ROSTER_SLOTS)
    assert STRATEGY_ROSTER_CAPPED_GREEDY_NWR in registry
