"""Waiver Night V1, Section 4 (Add/Drop context repair): facade-level
regression tests, end to end through the real public `redraft_waivers`
method (not by calling `waiver_engine_service.pair_add_drop` directly --
that is already covered in `tests/test_waiver_engine_service.py`).

Covers, per the governing directive:
  * the corrected same-context `netMarginalUtility` arithmetic is exposed
    on the real API response, alongside the new
    `addUtilityVsOriginalRoster`/`addUtilityVsPostDropRoster`/
    `dropUtilityVsPostDropRoster`/`dropRequired`/`contextLabel` fields;
  * open-slot handling uses the league's real, raw `roster_positions`
    array (never the count of roster ids that happened to resolve to a
    canonical identity) to legally add without a forced drop;
  * the conservative fallback (still force a drop) when `roster_positions`
    could not be read this request;
  * IR/reserve protection (Worker 3's earlier fix) still holds in
    combination with the same-context recompute -- a reserve-slotted
    player is never offered as a drop, AND never silently counted as an
    "occupied" non-reserve roster slot for the open-slot check either.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade
from src.services.redraft_engine_v1_service import load_profile, save_profile

REPO_ROOT = Path(__file__).resolve().parents[1]


def _facade_with_sleeper_league(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()  # installs the real governed seed into this fresh store
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Open Slot / Same Context League"
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
                "league": {"league_id": "9999", "name": "Open Slot / Same Context League"},
                "owner": {"user_id": "owner-1"},
            }
        ),
        encoding="utf-8",
    )
    return facade, profile_id


# Real, bundled-ranking-present identities (Freeze V7, 12_TEAM_1QB_HALF_PPR
# preset) -- same real players the IR/reserve exclusion fixture already
# uses, so this reuses an already-verified-real identity join rather than
# inventing a new one.
_PLAYERS = {
    "bench-1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
    "bench-2": {"full_name": "Justin Jefferson", "position": "WR", "team": "MIN"},
    "ir-1": {"full_name": "Bijan Robinson", "position": "RB", "team": "ATL"},
    "rival-1": {"full_name": "Saquon Barkley", "position": "RB", "team": "PHI"},
    "fa-1": {"full_name": "Tyreek Hill", "position": "WR", "team": "MIA"},
}

def _league_response(*, roster_positions: list[str] | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"settings": {"waiver_type": 1, "waiver_budget": 100}}
    if roster_positions is not None:
        payload["roster_positions"] = roster_positions
    return payload


def _make_fake_get_json(rosters: list[dict[str, Any]], roster_positions: list[str] | None):
    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return rosters
        if path == "players/nfl":
            return _PLAYERS
        if path == "league/9999":
            return _league_response(roster_positions=roster_positions)
        if path == "state/nfl":
            return {"week": 2}
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    return _fake_get_json


def test_addDropPairings_exposes_same_context_fields_and_corrected_net(
    tmp_path: Path, monkeypatch: Any,
) -> None:
    """The real API response now carries the same-context breakdown, not
    just the corrected `netMarginalUtility` number -- and never claims to
    be an authoritative total-roster/completed-transaction value."""
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    rosters = [
        {"owner_id": "owner-1", "players": ["bench-1", "bench-2"], "starters": []},
        {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
    ]
    # A full roster (2 real `roster_positions` slots, 2 occupied) -- a real
    # drop is genuinely required, so this exercises the same-context fields
    # rather than the open-slot path.
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient, "get_json",
        _make_fake_get_json(rosters, roster_positions=["RB", "WR"]),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    pairings = result.data["addDropPairings"]
    assert pairings, "expected at least one real Add/Drop pairing in this fixture"
    real_pairing = next(p for p in pairings if p["drop"] is not None)
    assert real_pairing["contextLabel"] == "SAME_CONTEXT_MARGINAL_COMPARISON"
    assert real_pairing["dropRequired"] is True
    assert real_pairing["addUtilityVsOriginalRoster"] == real_pairing["add"]["marginalUtility"]
    assert real_pairing["dropUtilityVsPostDropRoster"] == real_pairing["drop"]["marginalUtility"]
    # The corrected net is the SAME-CONTEXT difference, not the old
    # mismatched-context one.
    if real_pairing["addUtilityVsPostDropRoster"] is not None:
        expected = round(
            real_pairing["addUtilityVsPostDropRoster"] - real_pairing["dropUtilityVsPostDropRoster"], 2
        )
        assert real_pairing["netMarginalUtility"] == expected


def test_open_roster_slot_produces_add_only_pairings_using_real_roster_positions(
    tmp_path: Path, monkeypatch: Any,
) -> None:
    """A real open non-reserve roster slot (2 occupied of 4 real
    `roster_positions` slots) means no drop is forced."""
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    rosters = [
        {"owner_id": "owner-1", "players": ["bench-1"], "starters": []},
        {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
    ]
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient, "get_json",
        _make_fake_get_json(rosters, roster_positions=["RB", "WR", "BN", "BN"]),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result.data["rosterSlotContext"] == {
        "openSlotAvailable": True,
        "status": "OPEN_SLOT_AVAILABLE",
        "rosterSlotsTotal": 4,
        "rosterSlotsOccupied": 1,
    }
    pairings = result.data["addDropPairings"]
    assert pairings, "expected at least one real Add/Drop pairing in this fixture"
    for pairing in pairings:
        assert pairing["drop"] is None
        assert pairing["dropRequired"] is False
        assert pairing["contextLabel"] == "OPEN_ROSTER_SLOT_ADD_ONLY"
        assert pairing["netMarginalUtility"] == pairing["add"]["marginalUtility"]


def test_full_roster_no_open_slot_still_forces_the_real_weakest_drop(
    tmp_path: Path, monkeypatch: Any,
) -> None:
    """A real, verified full roster (no open slot) keeps the existing,
    unchanged drop-selection policy -- the weakest real bench player is
    still the recommended drop."""
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    rosters = [
        {"owner_id": "owner-1", "players": ["bench-1", "bench-2"], "starters": []},
        {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
    ]
    # A real `roster_positions` array the same length as the real occupied
    # non-reserve count (2) -- a genuinely full roster, no open slot.
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient, "get_json",
        _make_fake_get_json(rosters, roster_positions=["RB", "WR"]),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result.data["rosterSlotContext"]["openSlotAvailable"] is False
    assert result.data["rosterSlotContext"]["status"] == "NO_OPEN_SLOT"
    pairings = result.data["addDropPairings"]
    assert pairings
    for pairing in pairings:
        assert pairing["dropRequired"] is True
        assert pairing["contextLabel"] == "SAME_CONTEXT_MARGINAL_COMPARISON"


def test_unverifiable_roster_positions_keeps_the_conservative_forced_drop(
    tmp_path: Path, monkeypatch: Any,
) -> None:
    """When the league response has no real `roster_positions` (could not
    be verified this request), NWR never silently assumes an open slot
    exists -- it keeps showing the real weakest drop, the same
    conservative behavior as before this fix."""
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    rosters = [
        {"owner_id": "owner-1", "players": ["bench-1"], "starters": []},
        {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
    ]
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient, "get_json",
        _make_fake_get_json(rosters, roster_positions=None),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result.data["rosterSlotContext"] == {
        "openSlotAvailable": None,
        "status": "UNVERIFIED_ROSTER_SLOTS",
        "rosterSlotsTotal": None,
        "rosterSlotsOccupied": None,
    }
    pairings = result.data["addDropPairings"]
    assert pairings
    for pairing in pairings:
        assert pairing["dropRequired"] is True
        assert pairing["contextLabel"] == "SAME_CONTEXT_MARGINAL_COMPARISON"


def test_reserve_player_never_counted_as_an_occupied_open_slot_and_never_offered_as_a_drop(
    tmp_path: Path, monkeypatch: Any,
) -> None:
    """Combination check (Section 4's own explicit IR/reserve requirement):
    a reserve/IR-slotted player is (a) excluded from the real, raw
    non-reserve occupied-slot count the open-slot check uses, and (b)
    still never offered as a drop, holding Worker 3's earlier fix under
    this pass's changes."""
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    rosters = [
        {
            "owner_id": "owner-1",
            "players": ["bench-1", "ir-1"],
            "starters": [],
            "reserve": ["ir-1"],
        },
        {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
    ]
    # 2 real non-reserve slots total; only 1 (bench-1) is actually
    # occupied once the reserve player is correctly excluded -- a real
    # open slot, even though `len(players)` (2) alone would say "full".
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient, "get_json",
        _make_fake_get_json(rosters, roster_positions=["RB", "BN"]),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result.data["rosterSlotContext"] == {
        "openSlotAvailable": True,
        "status": "OPEN_SLOT_AVAILABLE",
        "rosterSlotsTotal": 2,
        "rosterSlotsOccupied": 1,
    }
    drop_names = {row["playerName"] for row in result.data["dropCandidates"]}
    assert "Bijan Robinson" not in drop_names  # the real reserve/IR player, still excluded
    pairings = result.data["addDropPairings"]
    assert pairings
    for pairing in pairings:
        assert pairing["drop"] is None
        assert pairing["dropRequired"] is False
        assert pairing["contextLabel"] == "OPEN_ROSTER_SLOT_ADD_ONLY"
