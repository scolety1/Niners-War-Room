"""NWR Post-Closure Fixes V1 (Worker F): regression test for a real,
found-but-not-yet-fixed crash in `redraft_waivers`' decision-envelope
rationale string.

Worker E (see docs/codex/post_ui_v1/NWR_POST_CLOSURE_LEDGER_V1.md)
discovered -- while building test fixtures for an unrelated latency pass --
that `desktop_facade.py`'s `redraft_waivers` rationale f-string
(`f"...{top_add.marginal_utility:.1f}"`) raises
`TypeError: unsupported format string passed to NoneType.__format__`
whenever the single BEST-RANKED add candidate is genuinely
`UNMATCHED_IDENTITY` (no governed-ranking identity match -- see
`waiver_engine_service.rank_waiver_candidates`, where an unmatched
candidate's `marginal_utility` is legitimately `None`, never fabricated).
That candidate deliberately still sorts to the top when it is the ONLY
free agent in the pool (an unmatched candidate only ever sorts BEHIND any
matched one, per `rank_waiver_candidates`' own `sort_key` -- it is never
excluded outright).

This test builds exactly that real scenario end-to-end through the public
facade method (not by calling the private rationale-building code
directly), using the same Sleeper-fixture pattern
`test_weekly_home_sleeper_fetch_caching.py` already established: a real
governed ranking bootstrapped into a fresh local store, one owner roster
player, and exactly one free agent whose name/position/team does not
identity-match any row in the real bundled ranking -- so
`sleeper_free_agent_pool` reports it `UNRANKED` (`playerId=""`) and
`rank_waiver_candidates` marks it `UNMATCHED_IDENTITY` with
`marginal_utility=None`, and it is the only (hence top) add candidate.

Before the fix, calling `redraft_waivers` in this exact fixture raised
`TypeError`. After the narrow guard added in `desktop_facade.py`
(`redraft_waivers`'s decision-envelope `rationale=`), it must instead
return a normal, non-crashing response whose rationale honestly says the
marginal utility is unavailable rather than fabricating a number.
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
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Unmatched FAAB Rationale League"
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


_ROSTERS = [
    {"owner_id": "owner-1", "players": ["me-1"], "starters": ["me-1"]},
    {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
]
_PLAYERS = {
    "me-1": {"full_name": "Roster Player One", "position": "RB", "team": "SF"},
    "rival-1": {"full_name": "Rival Player One", "position": "WR", "team": "BUF"},
    # Deliberately NOT a real identity present anywhere in the repo's
    # bundled governed ranking (Freeze V7, 12_TEAM_1QB_HALF_PPR preset) --
    # this is the one and only free agent in the pool, and it must remain
    # genuinely UNMATCHED (playerId="") for this test to exercise the real
    # bug. If this fixture ever starts colliding with a real ranking row,
    # pick a different fictitious name/team.
    "fa-unmatched-1": {
        "full_name": "Zzyzx Nonexistent Playerton",
        "position": "RB",
        "team": "ZZ",
    },
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


def test_redraft_waivers_does_not_crash_when_the_top_add_candidate_is_unmatched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    # Before the fix, this call raised TypeError: unsupported format
    # string passed to NoneType.__format__.
    result = facade.redraft_waivers(mode="REST_OF_SEASON")

    add_candidates = result.data["addCandidates"]
    assert len(add_candidates) == 1
    assert add_candidates[0]["identityStatus"] == "UNMATCHED_IDENTITY"
    assert add_candidates[0]["marginalUtility"] is None

    rationale = result.data["decisionEnvelope"]["rationale"]
    # Honest -- never fabricates a number for a candidate with no real
    # marginal utility.
    assert "unavailable" in rationale.lower()
    assert "(None)" not in rationale  # never a raw formatted Python None
    assert "identity unmatched" in rationale.lower()


def test_redraft_waivers_rationale_still_reports_a_real_number_when_matched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Equivalence guard: a genuinely MATCHED top candidate's rationale is
    completely unaffected by the fix -- still the original, real-number
    sentence."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    matched_players = dict(_PLAYERS)
    # A real identity from the bundled Freeze V7 ranking, matched by name/
    # position/team -- see the analogous fixture in
    # test_weekly_home_sleeper_fetch_caching.py.
    matched_players["fa-matched-1"] = {
        "full_name": "Christian McCaffrey", "position": "RB", "team": "SF",
    }
    del matched_players["fa-unmatched-1"]

    def _fake_get_json_matched(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return _ROSTERS
        if path == "players/nfl":
            return matched_players
        if path == "league/9999":
            return {"settings": {"waiver_type": 1, "waiver_budget": 100}}
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json_matched)

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    add_candidates = result.data["addCandidates"]
    assert len(add_candidates) == 1
    assert add_candidates[0]["identityStatus"] == "MATCHED"
    assert add_candidates[0]["marginalUtility"] is not None

    rationale = result.data["decisionEnvelope"]["rationale"]
    assert rationale.startswith("Top marginal-utility add: Christian McCaffrey (")
    assert "unavailable" not in rationale.lower()
