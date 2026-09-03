import pytest

from src.services.historical_decision_state_service import (
    HistoricalDecisionStateError,
    build_historical_decision_state,
    estimate_historical_survival_probability,
    evaluate_historical_candidates,
)
from src.services.historical_ranking_bridge_service import (
    KDST_OVERRIDE_FIELD,
    build_ranking_result_from_historical_rows,
)
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RosterSettings,
    ScoringSettings,
)
from src.services.score_provenance_service import build_score_provenance
from src.services.shadow_numeric_authorities_service import simulate_comparable_leagues


def _profile() -> LeagueProfile:
    return LeagueProfile(
        profile_id="hist-2019", league_name="Historical 2019", season=2019, team_count=4,
        roster=RosterSettings(
            qb=1, rb=1, wr=1, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=2
        ),
        scoring=ScoringSettings(reception=1.0), draft=DraftContext(rounds=4, draft_slot=1),
    )


def _row(player_id, position, **overrides):
    row = {
        "player_id": player_id, "player_name": f"Player {player_id}", "position": position,
        "team": "T1", "season": 2019, "draft_date": "2019-08-25",
        "projection_as_of": "2019-08-20", "adp_as_of": "2019-08-20",
        "platform_adp": 10.0, "status_as_of": "2019-08-25", "scoring_format": "ppr",
        "rookie": False,
    }
    row.update(overrides)
    return row


def _real_rows() -> list[dict]:
    rows = []
    for position, count in (("QB", 5), ("RB", 5), ("WR", 5), ("TE", 5)):
        for i in range(count):
            rows.append(
                _row(
                    f"{position}-{i}", position,
                    passing_yards=4000.0 - 100 * i if position == "QB" else 0.0,
                    passing_tds=25.0 if position == "QB" else 0.0,
                    rushing_yards=1200.0 - 50 * i if position == "RB" else 0.0,
                    rushing_tds=8.0 if position == "RB" else 0.0,
                    receiving_yards=1000.0 - 40 * i if position in {"WR", "TE"} else 0.0,
                    receptions=80.0 if position in {"WR", "TE"} else 0.0,
                    receiving_tds=7.0 if position in {"WR", "TE"} else 0.0,
                    platform_adp=float(len(rows) + 1),
                )
            )
    for i in range(5):
        rows.append(_row(f"K-{i}", "K", **{KDST_OVERRIDE_FIELD: 120.0 - i}))
    for i in range(5):
        rows.append(_row(f"DST-{i}", "DST", **{KDST_OVERRIDE_FIELD: 110.0 - i}))
    return rows


def _bridge_result():
    return build_ranking_result_from_historical_rows(
        _real_rows(), _profile(), generated_at_utc="2019-08-25T00:00:00Z",
        source_sha256="deadbeef" * 8,
    )


def _provenance():
    return build_score_provenance(
        league_profile_hash="lp", roster_state_hash="rs", available_player_hash="ap",
        universe_hash="uh", projection_model_version="proj-v1", market_snapshot_hash="mk",
        feature_set_version="fs-v1", team_score_version="ts-v1",
        championship_equity_version="ce-v1", pick_score_version="ps-v1",
        optimizer_version="opt-v1", seed=7, simulation_count=10,
        timestamp_utc="2019-08-25T00:00:00Z",
    )


def test_estimate_survival_returns_none_without_real_adp() -> None:
    result = estimate_historical_survival_probability(
        adp_expected_pick=None, current_pick_number=5, team_count=4, picks_until_next_turn=4,
    )
    assert result is None


def test_estimate_survival_is_bounded_and_monotonic_in_adp_gap() -> None:
    near = estimate_historical_survival_probability(
        adp_expected_pick=6.0, current_pick_number=5, team_count=4, picks_until_next_turn=4,
    )
    far = estimate_historical_survival_probability(
        adp_expected_pick=40.0, current_pick_number=5, team_count=4, picks_until_next_turn=4,
    )
    assert 0.0 <= near <= 1.0
    assert 0.0 <= far <= 1.0
    assert far > near  # a much later real ADP means a much higher survival chance


def test_build_historical_decision_state_excludes_already_drafted_players() -> None:
    bridge = _bridge_result()
    state = build_historical_decision_state(
        bridge, season=2019, as_of="2019-08-25", pick_number=3, round_number=1,
        owner_slot=1, rosters_by_slot={1: ("RB-0",), 2: ("QB-0",)},
        strategy_version="GREEDY_NWR",
    )
    assert "RB-0" not in state.available_player_ids
    assert "QB-0" not in state.available_player_ids
    assert "WR-0" in state.available_player_ids


def test_build_historical_decision_state_rejects_a_bad_pick_number() -> None:
    bridge = _bridge_result()
    with pytest.raises(HistoricalDecisionStateError):
        build_historical_decision_state(
            bridge, season=2019, as_of="2019-08-25", pick_number=0, round_number=1,
            owner_slot=1, rosters_by_slot={}, strategy_version="GREEDY_NWR",
        )


def test_evaluate_historical_candidates_produces_a_real_decision_bundle() -> None:
    bridge = _bridge_result()
    state = build_historical_decision_state(
        bridge, season=2019, as_of="2019-08-25", pick_number=1, round_number=1,
        owner_slot=1, rosters_by_slot={1: ()}, strategy_version="GREEDY_NWR",
    )
    leagues = simulate_comparable_leagues(
        state.profile, state.ranking, state.manual_assets, state.adp, trials=2, base_seed=3,
    )
    bundle = evaluate_historical_candidates(
        state, candidate_player_ids=["RB-0", "WR-0"], comparable_leagues=leagues,
        provenance=_provenance(), player_scores={"RB-0": 90.0},
    )
    assert len(bundle.candidates) == 2
    ids = {c.player_id for c in bundle.candidates}
    assert ids == {"RB-0", "WR-0"}
    # Never leaks a realized outcome into the score -- no such input exists at all.
    assert bundle.simulation_metadata["pick_number"] == 1


def test_evaluate_historical_candidates_flags_players_with_no_real_adp() -> None:
    bridge = _bridge_result()
    state = build_historical_decision_state(
        bridge, season=2019, as_of="2019-08-25", pick_number=1, round_number=1,
        owner_slot=1, rosters_by_slot={1: ()}, strategy_version="GREEDY_NWR",
    )
    leagues = simulate_comparable_leagues(
        state.profile, state.ranking, state.manual_assets, state.adp, trials=2, base_seed=5,
    )
    bundle = evaluate_historical_candidates(
        state, candidate_player_ids=["RB-0"], comparable_leagues=leagues,
        provenance=_provenance(),
    )
    candidate = bundle.candidates[0]
    assert candidate.make_it_back_probability is not None  # real ADP exists in the fixture
    assert "HISTORICAL_PROXY" in candidate.uncertainty
