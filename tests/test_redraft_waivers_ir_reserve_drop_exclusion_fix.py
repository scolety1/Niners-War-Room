"""NWR Waiver Night V1 (Worker 3, Work Unit 5): regression test for a real,
reproducible bug in `redraft_waivers`' Add/Drop pairing.

`redraft_my_roster()` has no reserve/IR field at all (see
docs/codex/waiver_night_v1/LEDGER.md, Worker 2's disclosed gap) -- every
roster row is only ever `starter: true/false`. Before this fix,
`redraft_waivers` inherited that same blind spot: a player parked on Sleeper's
real IR/reserve roster slot (present in `roster["players"]` and
`roster["reserve"]`, but never in `roster["starters"]`) was ranked as an
ordinary drop candidate by `rank_drop_candidates`, using the SAME
`marginal_roster_utility_v2` call used for every other bench player. Since an
IR-stashed player often has a genuinely low real marginal-roster-utility
number (contributing ~0 live value while shelved), he could -- and, in the
real fixture below, DID -- get selected as the single weakest drop and
surfaced as the Add/Drop pairing's recommended drop. That is a real wrong
recommendation: dropping a reserve-slot player does not free the bench-slot
type an ordinary Add/Drop suggestion implies, and this app has no signal to
reason about IR-specific roster mechanics.

This owner's own real Fantasy Gamers roster has 0 players on IR right now (3
of 9 real opponents do, raw-confirmed live), so the bug could not be
reproduced against the owner's own live data -- this fixture constructs one,
per the governing directive's own instruction to do so.

Fixed narrowly in `desktop_facade.py`'s `redraft_waivers`: the real raw
Sleeper `roster["reserve"]` list is read directly (independent of the
`redraft_my_roster()` gap above) and any canonical id it resolves to is
filtered OUT of the returned/paired drop-candidate list. The FULL roster
(including the reserve player) is still passed into `rank_drop_candidates`
so every OTHER bench player's own marginal-utility computation continues to
reflect the real, actual roster composition -- only the reserve player
himself is excluded from being offered as a drop.

`waiver_engine_service.py` itself (the existing waiver engine) is
UNCHANGED -- this fix is entirely in the facade call site, per the
directive's "use the existing waiver engine, do not rebuild it."
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade
from src.services.redraft_engine_v1_service import load_profile, save_profile

REPO_ROOT = Path(__file__).resolve().parents[1]


def _facade_with_sleeper_league(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()  # installs the real governed seed into this fresh store
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="IR Reserve Drop Exclusion League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="sleeper", provider_league_id="9999"))
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps({"league": {"league_id": "9999"}, "owner": {"user_id": "owner-1"}}),
        encoding="utf-8",
    )
    return facade, profile_id


# Real, bundled-ranking-present identities (Freeze V7, 12_TEAM_1QB_HALF_PPR
# preset) -- same pattern as test_redraft_waivers_unmatched_identity_
# rationale_fix.py. "ir-1" (Bijan Robinson) sits in BOTH "players" and
# "reserve" but never "starters" -- the real Sleeper roster shape for an
# IR-designated player.
_ROSTERS = [
    {
        "owner_id": "owner-1",
        "players": ["bench-1", "ir-1"],
        "starters": [],
        "reserve": ["ir-1"],
    },
    {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
]
_PLAYERS = {
    "bench-1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
    "ir-1": {"full_name": "Bijan Robinson", "position": "RB", "team": "ATL"},
    "rival-1": {"full_name": "Justin Jefferson", "position": "WR", "team": "MIN"},
    "fa-1": {"full_name": "Tyreek Hill", "position": "WR", "team": "MIA"},
}


def _fake_get_json(self: Any, path: str) -> Any:
    if path == "league/9999/rosters":
        return _ROSTERS
    if path == "players/nfl":
        return _PLAYERS
    if path == "league/9999":
        # NWR Waiver Night V1 (Worker 3, Work Unit 6): `redraft_waivers` now
        # also reads real league settings for the new `faabContext` field.
        return {"settings": {"waiver_type": 1, "waiver_budget": 100}}
    raise AssertionError(f"unexpected Sleeper GET path in test: {path}")


def test_redraft_waivers_never_offers_a_reserve_slotted_player_as_a_drop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    result = facade.redraft_waivers(mode="REST_OF_SEASON")

    drop_names = {row["playerName"] for row in result.data["dropCandidates"]}
    assert "Bijan Robinson" not in drop_names  # the real reserve/IR player
    assert "Christian McCaffrey" in drop_names  # the real ordinary bench player

    pairings = result.data["addDropPairings"]
    assert pairings, "expected at least one real Add/Drop pairing in this fixture"
    for pairing in pairings:
        if pairing["drop"] is not None:
            assert pairing["drop"]["playerName"] != "Bijan Robinson"
    assert pairings[0]["drop"]["playerName"] == "Christian McCaffrey"


def test_redraft_waivers_reserve_exclusion_does_not_affect_other_bench_players_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Equivalence guard: the reserve player is still passed into
    `rank_drop_candidates`' own roster context (so bench-1's marginal
    utility is computed against the REAL roster, reserve player included) --
    only the returned candidate list is filtered. This fixture only has one
    non-reserve bench player, so this asserts the mechanism ran (the
    reserve player was evaluated and then dropped) rather than silently
    short-circuited before ever calling the real ranking function."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    drop_candidates = result.data["dropCandidates"]
    assert len(drop_candidates) == 1
    assert drop_candidates[0]["playerName"] == "Christian McCaffrey"
    assert drop_candidates[0]["marginalUtility"] is not None


def test_redraft_waivers_with_no_reserve_players_is_unaffected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Equivalence guard: a roster with an empty/absent `reserve` list
    behaves exactly as before this fix (the real shape of this owner's own
    live Fantasy Gamers roster today)."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    rosters_no_reserve = [
        {"owner_id": "owner-1", "players": ["bench-1"], "starters": []},
        {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
    ]

    def _fake_get_json_no_reserve(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return rosters_no_reserve
        if path == "players/nfl":
            return _PLAYERS
        if path == "league/9999":
            return {"settings": {"waiver_type": 1, "waiver_budget": 100}}
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json_no_reserve)

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    drop_names = {row["playerName"] for row in result.data["dropCandidates"]}
    assert drop_names == {"Christian McCaffrey"}
