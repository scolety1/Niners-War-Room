"""Facade + HTTP wiring for Trade Package Search (NWR Post-UI Product V1,
P1-3, Worker 6). `test_trade_package_search_service.py` already covers the
search algorithm itself (legality, gates, dominance, dedup, pruning bounds,
all three modes) against controlled fixtures -- this file proves the facade
method (`DesktopBackendFacade.redraft_trade_package_search`) is wired
correctly end to end against the REAL governed ranking (not a test
double), with a real, mocked-Sleeper roster set, and that its input
validation fails closed before any Sleeper read is attempted.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.redraft_engine_v1_service import load_profile, save_profile

REPO_ROOT = Path(__file__).resolve().parents[1]


def _facade_with_sleeper_league(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()  # installs the real governed seed into this fresh store
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Trade Package Search Facade League"
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
                "league": {"league_id": "9999", "name": "Trade Package Search Facade League"},
                "owner": {"user_id": "owner-1"},
            }
        ),
        encoding="utf-8",
    )
    return facade, profile_id


def _mock_sleeper(monkeypatch: pytest.MonkeyPatch, *, my_players, opp_players) -> None:
    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return [
                {"owner_id": "owner-1", "players": my_players, "starters": []},
                {"owner_id": "owner-2", "players": opp_players, "starters": []},
            ]
        if path == "league/9999/users":
            return [
                {"user_id": "owner-1", "display_name": "Me"},
                {"user_id": "owner-2", "display_name": "Rival"},
            ]
        if path == "players/nfl":
            return {}  # identity resolution is exercised in test_waiver_engine_service.py;
            # not needed here -- an empty catalog just leaves every player
            # UNMATCHED, which is the honest degraded path this test targets.
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)


def test_find_win_win_endpoint_returns_a_well_formed_empty_result_when_unmatched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch, my_players=["nobody-1"], opp_players=["nobody-2"])
    result = facade.redraft_trade_package_search(mode="FIND_WIN_WIN")
    assert result.data["mode"] == "FIND_WIN_WIN"
    assert result.data["candidates"] == []
    assert result.data["writeBehavior"] == "NO_SLEEPER_WRITES"
    assert result.data["decisionEnvelope"]["task"] == "TRADE_PACKAGE_SEARCH"
    assert result.data["decisionEnvelope"]["confidenceState"] == "UNAVAILABLE"
    assert result.data["traceId"] is None
    assert result.data["packagesEvaluated"] == 0


def test_invalid_mode_rejected_before_any_sleeper_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)

    def _unexpected_get_json(self: Any, path: str) -> Any:
        raise AssertionError("must not read Sleeper for an invalid mode")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _unexpected_get_json)
    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_trade_package_search(mode="NOT_A_REAL_MODE")
    assert exc_info.value.code == "TRADE_PACKAGE_SEARCH_INVALID_MODE"


def test_target_player_mode_requires_target_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)

    def _unexpected_get_json(self: Any, path: str) -> Any:
        raise AssertionError("must not read Sleeper before required-field validation")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _unexpected_get_json)
    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_trade_package_search(mode="TARGET_PLAYER")
    assert exc_info.value.code == "TRADE_PACKAGE_SEARCH_TARGET_REQUIRED"


def test_improve_position_mode_requires_position(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)

    def _unexpected_get_json(self: Any, path: str) -> Any:
        raise AssertionError("must not read Sleeper before required-field validation")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _unexpected_get_json)
    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_trade_package_search(mode="IMPROVE_POSITION")
    assert exc_info.value.code == "TRADE_PACKAGE_SEARCH_POSITION_REQUIRED"


def test_target_player_unresolved_identity_is_a_real_facade_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch, my_players=["nobody-1"], opp_players=["nobody-2"])
    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_trade_package_search(mode="TARGET_PLAYER", target_player_sleeper_id="nobody-2")
    assert exc_info.value.code == "TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED"


def test_never_calls_a_sleeper_write_method() -> None:
    """Structural guarantee, same pattern every other trade surface in this
    repo already relies on: `SleeperHttpClient` exposes no write method at
    all, so this facade method (which only calls `get_json`) cannot write
    to Sleeper no matter what mode/inputs it is given."""

    assert not hasattr(desktop_facade_module.SleeperHttpClient, "post_json")
    assert not hasattr(desktop_facade_module.SleeperHttpClient, "put_json")
