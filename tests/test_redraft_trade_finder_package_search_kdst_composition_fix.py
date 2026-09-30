"""K/DST trade-hole bug, closed -- Trade Finder / Trade Package Search
(`docs/codex/dogfood_rebuild_20260929/LEDGER.md`, "K/DST Trade Finder
composition gap").

Root cause (already fixed once, for Trade Analysis / counter search, by a
prior worker this cycle): `resolve_roster_canonical_ids`'s own
`ranking_by_identity` lookup is sourced only from NWR's own governed
ranking, which structurally never contains K/DST rows ("K/DST are always
manual, NWR has no model for them"). So a real, catalog-resolvable K/DST
roster occupant always lands in `unmatched_sleeper_player_ids` and is
silently dropped from `canonical_player_ids` -- correct for WAIVER ranking
(K/DST have no ranked value to waiver-rank), but wrong whenever that same
resolved roster is used to represent "what's actually on this roster" for
composition/legality purposes. That fix (`resolve_full_roster_with_
unranked_occupants`, `src/services/waiver_engine_service.py`) was wired
into `redraft_trade_analysis` and `search_counter_offer_packages`, but NOT
into `redraft_trade_finder` or `redraft_trade_package_search` -- this file
proves those two call sites are now fixed too, using the exact same
already-tested function, reused as-is.

Uses the SAME real-facade Sleeper-mocking pattern as
`test_redraft_identity_boundary_opponent_and_trade_finder.py` (the real
bundled Freeze V7 governed ranking, real player rows, a fake
`SleeperHttpClient.get_json`) -- not a synthetic ranking double.
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
from src.services.trade_package_search_service import TradePackageSearchResult

REPO_ROOT = Path(__file__).resolve().parents[1]

# Real rows from the bundled Freeze V7 governed seed (GOVERNED_COMBINED_564_
# PROJECTION_SNAPSHOT.csv) -- real canonical ids, names, positions, teams.
_RODGERS_CANONICAL_ID = "00-0023459"
_FLACCO_CANONICAL_ID = "00-0026158"


def _facade_with_sleeper_league(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()  # installs the real governed Freeze V7 seed into this fresh store
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="KDST Composition League"
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
                "league": {"league_id": "9999", "name": "KDST Composition League"},
                "owner": {"user_id": "owner-1"},
            }
        ),
        encoding="utf-8",
    )
    return facade, profile_id


# A real kicker + a real team defense per side (Worker 5's own established
# fixture recipe from `tests/test_redraft_trade_analysis_service.py`), plus
# one real skill player per side already in the bundled Freeze V7 ranking.
_PLAYERS_CATALOG = {
    "sleeper-rodgers": {"full_name": "Aaron Rodgers", "position": "QB", "team": "PIT"},
    "sleeper-flacco": {"full_name": "Joe Flacco", "position": "QB", "team": "CIN"},
    "my-kicker": {"full_name": "Ka'imi Fairbairn", "position": "K", "team": "HOU"},
    "NE": {"position": "DEF", "team": "NE"},
    "opp-kicker": {"full_name": "Jason Sanders", "position": "K", "team": "MIA"},
    "SEA": {"position": "DEF", "team": "SEA"},
}


def _mock_sleeper(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return [
                {
                    "owner_id": "owner-1", "roster_id": "1",
                    "players": ["sleeper-rodgers", "my-kicker", "NE"], "starters": [],
                },
                {
                    "owner_id": "owner-2", "roster_id": "2",
                    "players": ["sleeper-flacco", "opp-kicker", "SEA"], "starters": [],
                },
            ]
        if path == "league/9999/users":
            return [
                {"user_id": "owner-1", "display_name": "Me"},
                {"user_id": "owner-2", "display_name": "Rival"},
            ]
        if path == "players/nfl":
            return _PLAYERS_CATALOG
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)


# ---------------------------------------------------------------------------
# 1. Trade Finder
# ---------------------------------------------------------------------------


def test_trade_finder_feeds_the_real_kdst_occupants_into_find_win_win_trades(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch)

    captured: dict[str, Any] = {}

    def _fake_find_win_win_trades(**kwargs: Any) -> list[Any]:
        captured.update(kwargs)
        return []

    monkeypatch.setattr(desktop_facade_module, "find_win_win_trades", _fake_find_win_win_trades)

    result = facade.redraft_trade_finder().data
    assert result["candidates"] == []

    # Owner's own roster: Rodgers + K + DST -- all 3 real occupants must be
    # present, not just the 1 skill player the OLD (unfixed) code produced.
    my_ids = captured["my_roster_canonical_ids"]
    assert len(my_ids) == 3
    assert _RODGERS_CANONICAL_ID in my_ids
    my_kdst_ids = [value for value in my_ids if value != _RODGERS_CANONICAL_ID]
    assert len(my_kdst_ids) == 2

    # The synthetic K/DST ids must have REAL display names wired in, not a
    # raw synthetic id string -- `rank_drop_candidates` has no "value known"
    # filter the way `search_counter_offer_packages` does, so a real K/DST
    # occupant can legitimately surface as a real drop candidate here. The
    # facade's own `_canonical_player_catalog` already names a bare team
    # defense by its team abbreviation (e.g. "NE", matching the real,
    # already-live `/api/v1/redraft/my-roster` shape for the owner's real
    # CHI defense), so that -- not a synthesized "TEAM D/ST" suffix -- is
    # the correct real-pipeline value here.
    my_names = captured["my_player_names"]
    assert set(my_names[pid] for pid in my_kdst_ids) == {"Ka'imi Fairbairn", "NE"}

    # The opponent roster (Flacco + K + DST) gets the identical fix.
    opponent = captured["opponents"][0]
    opp_ids = opponent["canonicalIds"]
    assert len(opp_ids) == 3
    assert _FLACCO_CANONICAL_ID in opp_ids
    opp_kdst_ids = [value for value in opp_ids if value != _FLACCO_CANONICAL_ID]
    assert len(opp_kdst_ids) == 2
    opp_names = opponent["names"]
    assert set(opp_names[pid] for pid in opp_kdst_ids) == {"Jason Sanders", "SEA"}

    # `manual_assets` must carry a synthetic "NOT MODELED" row for every one
    # of the 4 real K/DST occupants across BOTH rosters (owner + opponent),
    # never duplicated, and never missing one side.
    manual_assets = captured["manual_assets"]
    manual_ids = {str(asset.get("player_id")) for asset in manual_assets}
    assert manual_ids == set(my_kdst_ids) | set(opp_kdst_ids)
    assert len(manual_assets) == 4  # no duplicates


def test_trade_finder_kdst_ids_never_collide_with_a_real_canonical_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sanity check on the synthetic id shape itself -- `resolve_full_
    roster_with_unranked_occupants`'s own `unranked_roster_occupant:<raw
    sleeper id>` ids must never collide with a real GSIS-style canonical id
    from the governed ranking."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch)

    captured: dict[str, Any] = {}

    def _fake_find_win_win_trades(**kwargs: Any) -> list[Any]:
        captured.update(kwargs)
        return []

    monkeypatch.setattr(desktop_facade_module, "find_win_win_trades", _fake_find_win_win_trades)
    facade.redraft_trade_finder()

    for value in captured["my_roster_canonical_ids"]:
        assert not value.startswith("00-") or value == _RODGERS_CANONICAL_ID


# ---------------------------------------------------------------------------
# 2. Trade Package Search
# ---------------------------------------------------------------------------


def _fake_search_result() -> TradePackageSearchResult:
    return TradePackageSearchResult(
        mode="FIND_WIN_WIN", candidates=(), packages_evaluated=0,
        opponents_searched=0, truncated=False,
    )


def test_trade_package_search_find_win_win_feeds_the_real_kdst_occupants(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch)

    captured: dict[str, Any] = {}

    def _fake_search_win_win_packages(**kwargs: Any) -> TradePackageSearchResult:
        captured.update(kwargs)
        return _fake_search_result()

    monkeypatch.setattr(
        desktop_facade_module, "search_win_win_packages", _fake_search_win_win_packages
    )

    result = facade.redraft_trade_package_search(mode="FIND_WIN_WIN").data
    assert result["candidates"] == []

    my_ids = captured["my_roster_canonical_ids"]
    assert len(my_ids) == 3
    assert _RODGERS_CANONICAL_ID in my_ids

    opponent = captured["opponents"][0]
    assert len(opponent["canonicalIds"]) == 3
    assert _FLACCO_CANONICAL_ID in opponent["canonicalIds"]

    manual_assets = captured["manual_assets"]
    manual_ids = {str(asset.get("player_id")) for asset in manual_assets}
    assert len(manual_ids) == 4  # my K, my DST, opp K, opp DST -- no duplicates


def test_trade_package_search_target_player_resolves_a_real_opponent_kdst_instead_of_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Before this fix, `target_resolved.canonical_player_ids` was ALWAYS
    empty for a real K/DST target (the plain resolver structurally never
    matches them), so TARGET_PLAYER mode unconditionally raised
    `TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED` for a real,
    catalog-resolvable opponent-owned kicker or defense -- even though the
    owner can see that player is real and rostered. This proves the fixed
    path resolves it instead of failing."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch)

    captured: dict[str, Any] = {}

    def _fake_search_target_player_packages(**kwargs: Any) -> TradePackageSearchResult:
        captured.update(kwargs)
        return _fake_search_result()

    monkeypatch.setattr(
        desktop_facade_module, "search_target_player_packages", _fake_search_target_player_packages
    )

    result = facade.redraft_trade_package_search(
        mode="TARGET_PLAYER", target_player_sleeper_id="opp-kicker",
    ).data
    assert result["candidates"] == []
    assert captured["target_player_id"] in captured["opponents"][0]["canonicalIds"]
    # The resolved target must carry the real name, not a raw synthetic id.
    opponent = captured["opponents"][0]
    assert opponent["names"][captured["target_player_id"]] == "Jason Sanders"


def test_trade_package_search_target_player_still_fails_honestly_for_a_genuinely_unknown_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fix must not weaken the existing honest-failure behavior for a
    target id that is genuinely not in the Sleeper catalog at all -- only a
    real, catalog-resolvable K/DST occupant is recovered."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch)

    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_trade_package_search(
            mode="TARGET_PLAYER", target_player_sleeper_id="nobody-unmatched-at-all",
        )
    assert exc_info.value.code == "TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED"
