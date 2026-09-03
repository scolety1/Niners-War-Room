from src.services.draft_strategy_framework_service import (
    STRATEGY_GREEDY_NWR,
    STRATEGY_PLATFORM_ADP,
    greedy_nwr_strategy,
    platform_adp_strategy,
)
from src.services.historical_decision_state_service import build_historical_decision_state
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
from src.services.strategy_tournament_service import (
    build_pick_counterfactual,
    run_strategy_tournament,
)


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


def test_tournament_runs_every_supplied_strategy_and_reports_a_final_roster() -> None:
    bridge = _bridge_result()
    strategies = {
        STRATEGY_PLATFORM_ADP: platform_adp_strategy,
        STRATEGY_GREEDY_NWR: greedy_nwr_strategy,
    }
    results = run_strategy_tournament(
        season=2019, league_format_label="4T_1QB", team_count=4, rounds=4, owner_slot=1,
        available_player_ids=bridge.included_player_ids, feature_store=bridge.feature_store,
        as_of="2019-08-25", seed=42, strategies=strategies,
    )
    assert len(results) == 2
    names = {r.strategy_name for r in results}
    assert names == {STRATEGY_PLATFORM_ADP, STRATEGY_GREEDY_NWR}
    for result in results:
        assert len(result.final_roster) == 4  # 4 rounds
        assert result.seed == 42


def test_tournament_uses_the_identical_seed_for_every_strategy() -> None:
    bridge = _bridge_result()
    strategies = {
        STRATEGY_PLATFORM_ADP: platform_adp_strategy, STRATEGY_GREEDY_NWR: greedy_nwr_strategy,
    }
    results = run_strategy_tournament(
        season=2019, league_format_label="4T_1QB", team_count=4, rounds=4, owner_slot=1,
        available_player_ids=bridge.included_player_ids, feature_store=bridge.feature_store,
        as_of="2019-08-25", seed=99, strategies=strategies,
    )
    assert all(r.seed == 99 for r in results)


def test_tournament_never_silently_omits_a_strategy_that_ran() -> None:
    bridge = _bridge_result()
    strategies = {
        STRATEGY_PLATFORM_ADP: platform_adp_strategy, STRATEGY_GREEDY_NWR: greedy_nwr_strategy,
    }
    results = run_strategy_tournament(
        season=2019, league_format_label="4T_1QB", team_count=4, rounds=2, owner_slot=2,
        available_player_ids=bridge.included_player_ids, feature_store=bridge.feature_store,
        as_of="2019-08-25", seed=1, strategies=strategies,
    )
    assert len(results) == len(strategies)


def test_pick_counterfactual_compares_selected_against_real_top_adp_and_nwr() -> None:
    bridge = _bridge_result()
    state = build_historical_decision_state(
        bridge, season=2019, as_of="2019-08-25", pick_number=1, round_number=1,
        owner_slot=1, rosters_by_slot={1: ()}, strategy_version=STRATEGY_GREEDY_NWR,
    )
    leagues = simulate_comparable_leagues(
        state.profile, state.ranking, state.manual_assets, state.adp, trials=2, base_seed=3,
    )
    counterfactual = build_pick_counterfactual(
        state, selected_player_id="WR-3", comparable_leagues=leagues, provenance=_provenance(),
    )
    assert counterfactual.selected_player_id == "WR-3"
    assert counterfactual.top_adp_alternative_id is not None
    assert counterfactual.top_nwr_alternative_id is not None
    evaluated_ids = {c.player_id for c in counterfactual.pre_freeze_evaluation.candidates}
    assert "WR-3" in evaluated_ids


def test_pick_counterfactual_attaches_realized_metrics_only_when_supplied() -> None:
    bridge = _bridge_result()
    state = build_historical_decision_state(
        bridge, season=2019, as_of="2019-08-25", pick_number=1, round_number=1,
        owner_slot=1, rosters_by_slot={1: ()}, strategy_version=STRATEGY_GREEDY_NWR,
    )
    leagues = simulate_comparable_leagues(
        state.profile, state.ranking, state.manual_assets, state.adp, trials=2, base_seed=5,
    )
    without_outcomes = build_pick_counterfactual(
        state, selected_player_id="WR-3", comparable_leagues=leagues, provenance=_provenance(),
    )
    assert without_outcomes.realized_metrics is None

    realized = {pid: 100.0 - i for i, pid in enumerate(state.available_player_ids)}
    with_outcomes = build_pick_counterfactual(
        state, selected_player_id="WR-3", comparable_leagues=leagues, provenance=_provenance(),
        realized_production_by_player=realized,
    )
    assert with_outcomes.realized_metrics is not None
    assert with_outcomes.realized_metrics.selected_player_id == "WR-3"
