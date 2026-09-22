"""Sleeper-shaped regression coverage for the five Worker 4 conversions.

The fixture uses real governed-ranking identities (Aaron Rodgers and Joe
Flacco) and the exact raw Sleeper response shapes the pre-conversion callers
consumed.  Every test asserts the established public payload and, critically,
that the additive ESPN provenance field is absent for Sleeper responses.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.fantasypros_kdst_consensus_service import sleeper_free_agent_pool
from src.services.redraft_engine_v1_service import load_profile, save_profile
from src.services.redraft_trade_analysis_service import TradeEvaluation, TradeSideImpact
from src.services.trade_package_search_service import TradePackageSearchResult
from src.services.weekly_projection_provider_service import WeeklyProjectionHealth
from src.services.weekly_projection_service import build_weekly_projection_rows

REPO_ROOT = Path(__file__).resolve().parents[1]

RODGERS_ID = "00-0023459"
FLACCO_ID = "00-0026158"
ROSTERS = [
    {
        "owner_id": "owner-1",
        "roster_id": "1",
        "players": ["sleeper-rodgers"],
        "starters": ["sleeper-rodgers"],
    },
    {
        "owner_id": "owner-2",
        "roster_id": "2",
        "players": ["sleeper-flacco"],
        "starters": ["sleeper-flacco"],
    },
]
USERS = [
    {"user_id": "owner-1", "display_name": "My Team"},
    {"user_id": "owner-2", "display_name": "Rival Team"},
]
PLAYERS = {
    "sleeper-rodgers": {
        "full_name": "Aaron Rodgers",
        "position": "QB",
        "team": "PIT",
        "active": True,
    },
    "sleeper-flacco": {
        "full_name": "Joe Flacco",
        "position": "QB",
        "team": "CIN",
        "active": True,
    },
    "sleeper-free": {
        "full_name": "Synthetic Available Player",
        "position": "WR",
        "team": "SYN",
        "active": True,
    },
}


def _facade(tmp_path: Path) -> DesktopBackendFacade:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Canonical Caller Regression League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="sleeper", provider_league_id="9999"))
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": "9999", "name": "Canonical Caller Regression League"},
                "owner": {"user_id": "owner-1"},
            }
        ),
        encoding="utf-8",
    )
    return facade


def _mock_sleeper(monkeypatch: pytest.MonkeyPatch) -> None:
    def _get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return ROSTERS
        if path == "league/9999/users":
            return USERS
        if path == "players/nfl":
            return PLAYERS
        raise AssertionError(f"unexpected Sleeper GET path: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _get_json)


def test_free_agents_sleeper_payload_matches_legacy_transform(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade = _facade(tmp_path)
    _mock_sleeper(monkeypatch)
    selected = load_profile(facade.redraft_root, facade.redraft_bootstrap().data["activeProfileId"])
    ranking = facade._redraft_ranking_for_profile(selected.profile_id)
    ranking_rows = facade._redraft_ranking_payloads(ranking, None)
    expected_rows = list(
        sleeper_free_agent_pool(rosters=ROSTERS, players=PLAYERS, rankings=ranking_rows)
    )

    result = facade.redraft_free_agents().data
    assert result == {
        "leagueId": "9999",
        "freeAgents": expected_rows,
        "rankingWarning": "",
        "writeBehavior": "NO_SLEEPER_WRITES",
    }


def test_weekly_projections_sleeper_payload_matches_legacy_transform(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade = _facade(tmp_path)
    _mock_sleeper(monkeypatch)
    raw = {"sleeper-rodgers": {"pass_yd": 250.0, "pass_td": 2.0, "pass_int": 1.0, "gp": 1}}
    health = WeeklyProjectionHealth(
        schema_version=1,
        provider="SLEEPER_WEEKLY_PROJECTIONS_TEMPORARY_STOPGAP",
        source_endpoint="synthetic://weekly",
        integration_status="TEMPORARY_STOPGAP",
        season=2026,
        week=3,
        season_type="regular",
        league_id="9999",
        retrieved_at="2026-09-22T06:30:00Z",
        schema_fingerprint="fixture",
        payload_hash="fixture-hash",
        total_rows=1,
        nonzero_projection_rows=1,
        status="OK",
        freshness="LIVE",
    )
    monkeypatch.setattr(
        desktop_facade_module,
        "get_weekly_projections",
        lambda **kwargs: (raw, health),
    )
    selected = load_profile(facade.redraft_root, facade.redraft_bootstrap().data["activeProfileId"])
    ranking = facade._redraft_ranking_for_profile(selected.profile_id)
    ranking_rows = facade._redraft_ranking_payloads(ranking, None)
    legacy = build_weekly_projection_rows(
        raw_projections=raw,
        players=PLAYERS,
        ranking_rows=ranking_rows,
        scoring=selected.scoring,
        season=selected.season,
        week=3,
        season_type="regular",
        league_id="9999",
        fetched_at=health.retrieved_at,
    )

    result = facade.redraft_weekly_projections(week=3).data
    assert result["leagueId"] == legacy.league_id
    assert result["providerHealth"] == health.to_dict()
    assert result["rows"] == [
        {
            "canonicalPlayerId": row.canonical_player_id,
            "sleeperPlayerId": row.sleeper_player_id,
            "playerName": row.player_name,
            "position": row.position,
            "team": row.team,
            "projectedPoints": row.projected_points,
            "scoringContext": row.scoring_context,
            "identityMatch": row.identity_match,
            "gp": row.gp,
            "sourceAsOf": row.source_as_of,
        }
        for row in legacy.rows
    ]
    assert "leagueStateProvenance" not in result


def _evaluation() -> TradeEvaluation:
    give = TradeSideImpact(
        player_id=RODGERS_ID,
        player_name="Aaron Rodgers",
        position="QB",
        ros_replacement_value=1.0,
        marginal_utility=0.5,
        becomes_starter=False,
        status_flag=None,
    )
    receive = TradeSideImpact(
        player_id=FLACCO_ID,
        player_name="Joe Flacco",
        position="QB",
        ros_replacement_value=2.0,
        marginal_utility=1.5,
        becomes_starter=True,
        status_flag=None,
    )
    return TradeEvaluation(
        gives=(give,),
        receives=(receive,),
        ros_value_delta=1.0,
        net_marginal_utility=1.0,
        starting_lineup_value_before=10.0,
        starting_lineup_value_after=11.0,
        starting_lineup_value_delta=1.0,
        bench_contingency_value_before=2.0,
        bench_contingency_value_after=2.5,
        starter_holes_before=(),
        starter_holes_after=(),
        position_redundancy_before={"QB": 1},
        position_redundancy_after={"QB": 1},
        risk_flags=(),
    )


def test_trade_analysis_sleeper_shape_and_values_are_unregressed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade = _facade(tmp_path)
    _mock_sleeper(monkeypatch)
    monkeypatch.setattr(desktop_facade_module, "evaluate_trade", lambda **kwargs: _evaluation())
    monkeypatch.setattr(facade, "_record_decision_trace_safe", lambda **kwargs: "trace-fixture")
    result = facade.redraft_trade_analysis(
        gives_sleeper_player_ids=["sleeper-rodgers"],
        receives_sleeper_player_ids=["sleeper-flacco"],
    ).data

    assert result["leagueId"] == "9999"
    assert result["traceId"] == "trace-fixture"
    assert result["gives"][0]["playerId"] == RODGERS_ID
    assert result["receives"][0]["playerId"] == FLACCO_ID
    assert result["netMarginalUtility"] == 1.0
    assert result["writeBehavior"] == "NO_SLEEPER_WRITES"
    assert "leagueStateProvenance" not in result


def test_trade_finder_sleeper_empty_result_shape_is_unregressed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade = _facade(tmp_path)
    _mock_sleeper(monkeypatch)
    monkeypatch.setattr(desktop_facade_module, "find_win_win_trades", lambda **kwargs: [])
    result = facade.redraft_trade_finder().data

    assert result["leagueId"] == "9999"
    assert result["traceId"] is None
    assert result["candidates"] == []
    assert result["decisionEnvelope"]["confidenceState"] == "UNAVAILABLE"
    assert result["writeBehavior"] == "NO_SLEEPER_WRITES"
    assert "leagueStateProvenance" not in result


def test_trade_package_search_sleeper_empty_result_shape_is_unregressed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade = _facade(tmp_path)
    _mock_sleeper(monkeypatch)
    monkeypatch.setattr(
        desktop_facade_module,
        "search_win_win_packages",
        lambda **kwargs: TradePackageSearchResult(
            mode="FIND_WIN_WIN",
            candidates=(),
            packages_evaluated=0,
            opponents_searched=1,
            truncated=False,
        ),
    )
    result = facade.redraft_trade_package_search(mode="FIND_WIN_WIN").data

    assert result == {
        "leagueId": "9999",
        "mode": "FIND_WIN_WIN",
        "traceId": None,
        "leagueSnapshotId": result["leagueSnapshotId"],
        "decisionEnvelope": result["decisionEnvelope"],
        "candidates": [],
        "packagesEvaluated": 0,
        "opponentsSearched": 1,
        "truncated": False,
        "writeBehavior": "NO_SLEEPER_WRITES",
    }
    assert result["decisionEnvelope"]["confidenceState"] == "UNAVAILABLE"


def test_espn_free_agents_surface_stale_snapshot_warning(tmp_path: Path) -> None:
    store = tmp_path / "espn-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(
        preset_key="10_TEAM_1QB_STANDARD", league_name="Synthetic Test ESPN League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="espn"))
    snapshot_dir = store / "espn_flaim_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "profile_id": profile_id,
                "provider_league_id": "SYNTHETIC-ESPN-1",
                "league_name": "Synthetic Test ESPN League",
                "season": 2026,
                "team_count": 10,
                "owner_team_id": "synthetic-team-1",
                "owner_team_name": "Synthetic Owner Team",
                "roster": [
                    {
                        "provider_player_id": "espn-roster-1",
                        "player_name": "Synthetic Roster Player",
                        "position": "RB",
                        "team": "SYN",
                        "slot": "STARTER",
                    }
                ],
                "scoring_settings": [],
                "scoring_completeness": "UNKNOWN",
                "available_player_pool": [
                    {
                        "provider_player_id": "espn-free-1",
                        "player_name": "Synthetic Available Player",
                        "position": "WR",
                        "team": "SYN",
                    }
                ],
                "available_player_pool_coverage": "BOUNDED",
                "available_player_pool_bound_description": "Synthetic one-row bound",
                "retrieved_at_utc": "2026-01-01T00:00:00Z",
                "provider_as_of_utc": None,
            }
        ),
        encoding="utf-8",
    )

    result = facade.redraft_free_agents().data
    assert result["leagueId"] == "SYNTHETIC-ESPN-1"
    assert result["freeAgents"][0]["sleeperPlayerId"] == "espn-free-1"
    assert result["leagueStateProvenance"]["stale"] is True
    assert "ESPN SNAPSHOT STALE" in result["leagueStateProvenance"]["warning"]


def test_espn_trade_searches_honestly_block_without_opponent_rosters(tmp_path: Path) -> None:
    store = tmp_path / "espn-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(
        preset_key="10_TEAM_1QB_STANDARD", league_name="Synthetic Test ESPN League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="espn"))
    snapshot_dir = store / "espn_flaim_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "profile_id": profile_id,
        "provider_league_id": "SYNTHETIC-ESPN-1",
        "league_name": "Synthetic Test ESPN League",
        "season": 2026,
        "team_count": 10,
        "owner_team_id": "synthetic-team-1",
        "owner_team_name": "Synthetic Owner Team",
        "roster": [
            {
                "provider_player_id": "espn-roster-1",
                "player_name": "Synthetic Roster Player",
                "position": "RB",
                "team": "SYN",
                "slot": "STARTER",
            }
        ],
        "scoring_settings": [],
        "scoring_completeness": "UNKNOWN",
        "available_player_pool": [],
        "available_player_pool_coverage": "NONE",
        "available_player_pool_bound_description": None,
        "retrieved_at_utc": "2026-09-22T00:00:00Z",
        "provider_as_of_utc": None,
    }
    (snapshot_dir / f"{profile_id}.json").write_text(json.dumps(snapshot), encoding="utf-8")

    with pytest.raises(FacadeError) as finder_error:
        facade.redraft_trade_finder()
    assert finder_error.value.code == "TRADE_FINDER_OPPONENT_ROSTERS_UNAVAILABLE"
    assert finder_error.value.status == 409
    with pytest.raises(FacadeError) as package_error:
        facade.redraft_trade_package_search(mode="FIND_WIN_WIN")
    assert package_error.value.code == "TRADE_PACKAGE_SEARCH_OPPONENT_ROSTERS_UNAVAILABLE"
    assert package_error.value.status == 409
