from src.services.draft_strategy_framework_service import (
    STRATEGY_CURRENT_NWR_DRAFT_HEURISTIC,
    STRATEGY_GREEDY_NWR,
    STRATEGY_PLATFORM_ADP,
    STRATEGY_STANDARD_VBD,
    STRATEGY_TEAM_SCORE_OPTIMIZER,
    StrategyDecisionContext,
    baseline_strategy_registry,
    current_nwr_draft_heuristic_strategy,
    greedy_nwr_strategy,
    make_optimizer_strategy,
    platform_adp_strategy,
    standard_vbd_strategy,
)
from src.services.point_in_time_feature_store_service import (
    FAMILY_MARKET_ADP,
    FAMILY_NWR_COMPONENT_SCORES,
    FAMILY_POSITION,
    FAMILY_REPLACEMENT_LEVEL,
    PointInTimeFeatureStore,
    known_feature_value,
)


def _store_with(*values):
    return PointInTimeFeatureStore().with_values(values)


def _context(
    store: PointInTimeFeatureStore, player_ids: tuple[str, ...], **overrides
) -> StrategyDecisionContext:
    defaults = dict(
        league_rules_summary={"open_starter_positions": ()},
        pick_number=1,
        round_number=1,
        available_player_ids=player_ids,
        roster_player_ids=(),
        feature_store=store,
        as_of="2026-08-15",
        season=2026,
    )
    defaults.update(overrides)
    return StrategyDecisionContext(**defaults)


def test_platform_adp_strategy_picks_the_lowest_adp() -> None:
    store = _store_with(
        known_feature_value(
            player_id="A", season=2026, as_of="2026-08-15", feature_name="market.overall_adp",
            feature_family=FAMILY_MARKET_ADP, value=45.0, source="s", source_as_of="2026-08-01",
            retrieved_at="2026-08-01",
        ),
        known_feature_value(
            player_id="B", season=2026, as_of="2026-08-15", feature_name="market.overall_adp",
            feature_family=FAMILY_MARKET_ADP, value=12.0, source="s", source_as_of="2026-08-01",
            retrieved_at="2026-08-01",
        ),
    )
    decision = platform_adp_strategy(_context(store, ("A", "B")))
    assert decision.selected_player_id == "B"
    assert decision.candidate_ranking == ("B", "A")
    assert decision.strategy_name == STRATEGY_PLATFORM_ADP


def test_standard_vbd_strategy_picks_the_highest_vor() -> None:
    store = _store_with(
        known_feature_value(
            player_id="A", season=2026, as_of="2026-08-15",
            feature_name="replacement_level.value_over_replacement",
            feature_family=FAMILY_REPLACEMENT_LEVEL, value=30.0, source="s",
            source_as_of="2026-08-01", retrieved_at="2026-08-01",
        ),
        known_feature_value(
            player_id="B", season=2026, as_of="2026-08-15",
            feature_name="replacement_level.value_over_replacement",
            feature_family=FAMILY_REPLACEMENT_LEVEL, value=80.0, source="s",
            source_as_of="2026-08-01", retrieved_at="2026-08-01",
        ),
    )
    decision = standard_vbd_strategy(_context(store, ("A", "B")))
    assert decision.selected_player_id == "B"
    assert decision.strategy_name == STRATEGY_STANDARD_VBD


def test_greedy_nwr_strategy_picks_the_best_overall_rank() -> None:
    store = _store_with(
        known_feature_value(
            player_id="A", season=2026, as_of="2026-08-15",
            feature_name="nwr_component_scores.overall_rank",
            feature_family=FAMILY_NWR_COMPONENT_SCORES, value=5.0, source="s",
            source_as_of="2026-08-01", retrieved_at="2026-08-01",
        ),
        known_feature_value(
            player_id="B", season=2026, as_of="2026-08-15",
            feature_name="nwr_component_scores.overall_rank",
            feature_family=FAMILY_NWR_COMPONENT_SCORES, value=1.0, source="s",
            source_as_of="2026-08-01", retrieved_at="2026-08-01",
        ),
    )
    decision = greedy_nwr_strategy(_context(store, ("A", "B")))
    assert decision.selected_player_id == "B"  # rank 1 beats rank 5
    assert decision.strategy_name == STRATEGY_GREEDY_NWR


def test_strategy_never_ranks_a_player_with_no_resolvable_feature_value() -> None:
    store = _store_with(
        known_feature_value(
            player_id="A", season=2026, as_of="2026-08-15", feature_name="market.overall_adp",
            feature_family=FAMILY_MARKET_ADP, value=45.0, source="s", source_as_of="2026-08-01",
            retrieved_at="2026-08-01",
        ),
    )
    decision = platform_adp_strategy(_context(store, ("A", "ghost")))
    assert decision.candidate_ranking == ("A",)
    assert decision.decision_metadata["unresolved_player_ids"] == ("ghost",)


def test_current_nwr_draft_heuristic_prefers_a_roster_need_on_a_tie() -> None:
    store = _store_with(
        known_feature_value(
            player_id="A", season=2026, as_of="2026-08-15",
            feature_name="nwr_component_scores.overall_rank",
            feature_family=FAMILY_NWR_COMPONENT_SCORES, value=10.0, source="s",
            source_as_of="2026-08-01", retrieved_at="2026-08-01",
        ),
        known_feature_value(
            player_id="A", season=2026, as_of="2026-08-15", feature_name="position",
            feature_family=FAMILY_POSITION, value="RB", source="s",
            source_as_of="2026-08-01", retrieved_at="2026-08-01",
        ),
        known_feature_value(
            player_id="B", season=2026, as_of="2026-08-15",
            feature_name="nwr_component_scores.overall_rank",
            feature_family=FAMILY_NWR_COMPONENT_SCORES, value=10.0, source="s",
            source_as_of="2026-08-01", retrieved_at="2026-08-01",
        ),
        known_feature_value(
            player_id="B", season=2026, as_of="2026-08-15", feature_name="position",
            feature_family=FAMILY_POSITION, value="QB", source="s",
            source_as_of="2026-08-01", retrieved_at="2026-08-01",
        ),
    )
    context = _context(
        store, ("A", "B"),
        league_rules_summary={"open_starter_positions": ("RB",)},
    )
    decision = current_nwr_draft_heuristic_strategy(context)
    assert decision.selected_player_id == "A"
    assert decision.strategy_name == STRATEGY_CURRENT_NWR_DRAFT_HEURISTIC


def test_optimizer_strategy_wraps_a_real_caller_supplied_evaluator() -> None:
    calls: list[str] = []

    def evaluator(player_id: str, context: StrategyDecisionContext) -> float | None:
        calls.append(player_id)
        return {"A": 55.0, "B": 91.0}.get(player_id)

    strategy = make_optimizer_strategy(STRATEGY_TEAM_SCORE_OPTIMIZER, evaluator, version="v1")
    decision = strategy(_context(_store_with(), ("A", "B")))
    assert decision.selected_player_id == "B"
    assert set(calls) == {"A", "B"}
    assert decision.decision_metadata["evaluator"] == "caller_supplied"


def test_baseline_strategy_registry_omits_unsupplied_optimizer_slots() -> None:
    registry = baseline_strategy_registry()
    assert STRATEGY_PLATFORM_ADP in registry
    assert STRATEGY_TEAM_SCORE_OPTIMIZER not in registry

    registry_with_team_score = baseline_strategy_registry(
        team_score_evaluator=lambda player_id, context: 1.0
    )
    assert STRATEGY_TEAM_SCORE_OPTIMIZER in registry_with_team_score


def test_every_strategy_reports_a_nonzero_or_zero_but_real_runtime() -> None:
    store = _store_with(
        known_feature_value(
            player_id="A", season=2026, as_of="2026-08-15", feature_name="market.overall_adp",
            feature_family=FAMILY_MARKET_ADP, value=45.0, source="s", source_as_of="2026-08-01",
            retrieved_at="2026-08-01",
        ),
    )
    decision = platform_adp_strategy(_context(store, ("A",)))
    assert decision.runtime_seconds >= 0.0
    assert decision.strategy_version == "v1"
