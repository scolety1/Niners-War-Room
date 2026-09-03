import pytest

from src.services.draft_strategy_framework_service import (
    STRATEGY_GREEDY_NWR,
    STRATEGY_PLATFORM_ADP,
    greedy_nwr_strategy,
    platform_adp_strategy,
)
from src.services.historical_draft_replay_engine_service import (
    HistoricalDraftReplayError,
    run_historical_draft_replay,
)
from src.services.point_in_time_feature_store_service import (
    FAMILY_MARKET_ADP,
    FAMILY_NWR_COMPONENT_SCORES,
    PointInTimeFeatureStore,
    known_feature_value,
)


def _feature_store(player_ids: list[str]) -> PointInTimeFeatureStore:
    """Builds a store where ADP order and NWR rank order deliberately
    DIFFER, so tests can tell which strategy actually drove a pick."""
    values = []
    for i, player_id in enumerate(player_ids):
        # ADP ascending in player_ids order.
        values.append(
            known_feature_value(
                player_id=player_id, season=2020, as_of="2020-08-20",
                feature_name="market.overall_adp", feature_family=FAMILY_MARKET_ADP,
                value=float(i), source="s", source_as_of="2020-08-01", retrieved_at="2020-08-01",
            )
        )
        # NWR rank REVERSED relative to ADP -- distinguishing signal.
        values.append(
            known_feature_value(
                player_id=player_id, season=2020, as_of="2020-08-20",
                feature_name="nwr_component_scores.overall_rank",
                feature_family=FAMILY_NWR_COMPONENT_SCORES,
                value=float(len(player_ids) - i), source="s",
                source_as_of="2020-08-01", retrieved_at="2020-08-01",
            )
        )
    return PointInTimeFeatureStore().with_values(values)


def test_replay_is_deterministic_given_the_same_seed_and_inputs() -> None:
    player_ids = [f"P{i}" for i in range(12)]
    store = _feature_store(player_ids)
    kwargs = dict(
        season=2020, team_count=4, rounds=3, available_player_ids=player_ids,
        feature_store=store, as_of="2020-08-20", owner_slot=2,
        owner_strategy_name=STRATEGY_GREEDY_NWR, owner_strategy=greedy_nwr_strategy,
        seed=42,
    )
    receipt_a = run_historical_draft_replay(**kwargs)
    receipt_b = run_historical_draft_replay(**kwargs)
    assert receipt_a.picks == receipt_b.picks
    assert receipt_a.rosters_by_slot == receipt_b.rosters_by_slot


def test_owner_seat_uses_the_strategy_under_test_and_opponents_use_the_market_model() -> None:
    player_ids = [f"P{i}" for i in range(8)]
    store = _feature_store(player_ids)
    receipt = run_historical_draft_replay(
        season=2020, team_count=4, rounds=2, available_player_ids=player_ids,
        feature_store=store, as_of="2020-08-20", owner_slot=1,
        owner_strategy_name=STRATEGY_GREEDY_NWR, owner_strategy=greedy_nwr_strategy,
        opponent_strategy_name=STRATEGY_PLATFORM_ADP, opponent_strategy=platform_adp_strategy,
        seed=1,
    )
    owner_picks = [p for p in receipt.picks if p.team_slot == 1]
    opponent_picks = [p for p in receipt.picks if p.team_slot != 1]
    assert all(p.strategy_name == STRATEGY_GREEDY_NWR for p in owner_picks)
    assert all(p.strategy_name == STRATEGY_PLATFORM_ADP for p in opponent_picks)
    # The very first pick (team slot 1, owner) should be P7 -- lowest ADP
    # is P0, but GREEDY_NWR ranks P7 first (NWR rank is reversed vs ADP).
    assert receipt.picks[0].selected_player_id == "P7"


def test_no_player_is_ever_drafted_twice() -> None:
    player_ids = [f"P{i}" for i in range(12)]
    store = _feature_store(player_ids)
    receipt = run_historical_draft_replay(
        season=2020, team_count=4, rounds=3, available_player_ids=player_ids,
        feature_store=store, as_of="2020-08-20", owner_slot=3,
        owner_strategy_name=STRATEGY_PLATFORM_ADP, owner_strategy=platform_adp_strategy,
        seed=5,
    )
    all_selected = [p.selected_player_id for p in receipt.picks if p.selected_player_id]
    assert len(all_selected) == len(set(all_selected))


def test_snake_order_reverses_direction_each_round() -> None:
    player_ids = [f"P{i}" for i in range(16)]
    store = _feature_store(player_ids)
    receipt = run_historical_draft_replay(
        season=2020, team_count=4, rounds=2, available_player_ids=player_ids,
        feature_store=store, as_of="2020-08-20", owner_slot=1,
        owner_strategy_name=STRATEGY_PLATFORM_ADP, owner_strategy=platform_adp_strategy,
        seed=1,
    )
    round_1_slots = [p.team_slot for p in receipt.picks if p.round_number == 1]
    round_2_slots = [p.team_slot for p in receipt.picks if p.round_number == 2]
    assert round_1_slots == [1, 2, 3, 4]
    assert round_2_slots == [4, 3, 2, 1]


def test_rejects_an_owner_slot_outside_the_team_count() -> None:
    player_ids = [f"P{i}" for i in range(4)]
    store = _feature_store(player_ids)
    with pytest.raises(HistoricalDraftReplayError):
        run_historical_draft_replay(
            season=2020, team_count=4, rounds=1, available_player_ids=player_ids,
            feature_store=store, as_of="2020-08-20", owner_slot=9,
            owner_strategy_name=STRATEGY_PLATFORM_ADP, owner_strategy=platform_adp_strategy,
        )


def test_replay_stops_rather_than_loops_when_no_candidate_can_be_ranked() -> None:
    empty_store = PointInTimeFeatureStore()
    receipt = run_historical_draft_replay(
        season=2020, team_count=2, rounds=2, available_player_ids=["P0", "P1"],
        feature_store=empty_store, as_of="2020-08-20", owner_slot=1,
        owner_strategy_name=STRATEGY_PLATFORM_ADP, owner_strategy=platform_adp_strategy,
        seed=1,
    )
    assert len(receipt.picks) == 1
    assert receipt.picks[0].selected_player_id is None
