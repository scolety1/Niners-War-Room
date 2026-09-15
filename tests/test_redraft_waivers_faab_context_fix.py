"""NWR Waiver Night V1 (Worker 3, Work Unit 6): regression test for a real,
previously-undocumented gap in `redraft_waivers`.

Live verification against the real Fantasy Gamers Sleeper league
(`1312983576827920384`, owner `scolety`, 2026-09-15, week 2) found that
NOTHING anywhere in this codebase -- backend or frontend -- ever read
Sleeper's own real `league.settings.waiver_type` / `waiver_budget`, or the
owner's own real `roster.settings.waiver_budget_used` / `waiver_position`.
`suggest_faab_bids` (`waiver_engine_service.py`) itself was always genuinely
contextual, never a static table, but the frontend fed it a hardcoded
$100/$100/14-week guess (`improve-team.tsx`'s initial `useState` values) --
only coincidentally correct for this real league today because nothing has
been spent yet. It would silently go stale the first week the owner
actually won a FAAB bid, and a genuinely non-FAAB (rolling waiver-priority)
league would still have shown a fabricated dollar bid range, since nothing
ever checked `waiver_type`.

Fixed by reading the real `league/{id}` settings (read-only, one more GET)
and the owner's own already-fetched roster's `settings` block, and
surfacing them as the new `faabContext` field: `isFaabLeague`,
`totalBudgetDollars`, `remainingBudgetDollars` (both `None` when not FAAB --
never fabricated), and `waiverPosition`. `suggest_faab_bids` itself is
UNCHANGED -- this is purely an additive, informational field the frontend
now uses to seed its budget fields with real data and to suppress the
dollar-bid UI entirely for a confirmed non-FAAB league.
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
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="FAAB Context League"
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
    {
        "owner_id": "owner-1",
        "players": ["bench-1"],
        "starters": [],
        "settings": {"waiver_budget_used": 35, "waiver_position": 4},
    },
    {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
]
_PLAYERS = {
    "bench-1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
    "rival-1": {"full_name": "Justin Jefferson", "position": "WR", "team": "MIN"},
    "fa-1": {"full_name": "Tyreek Hill", "position": "WR", "team": "MIA"},
}


def _make_fake_get_json(league_settings: dict[str, Any]):
    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return _ROSTERS
        if path == "players/nfl":
            return _PLAYERS
        if path == "league/9999":
            return {"settings": league_settings}
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    return _fake_get_json


def test_faab_context_reads_real_remaining_budget_for_a_real_faab_league(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 1, "waiver_budget": 100}),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    ctx = result.data["faabContext"]
    assert ctx is not None
    assert ctx["isFaabLeague"] is True
    assert ctx["totalBudgetDollars"] == 100
    # 100 total - 35 already used (real roster.settings.waiver_budget_used)
    assert ctx["remainingBudgetDollars"] == 65
    assert ctx["waiverPosition"] == 4
    assert ctx["source"] == "SLEEPER_LIVE"


def test_faab_context_never_fabricates_a_budget_for_a_non_faab_league(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """waiver_type=0 is Sleeper's own real rolling-waiver-priority mode
    (not FAAB) -- this must never report a dollar budget."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 0, "waiver_budget": 100}),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    ctx = result.data["faabContext"]
    assert ctx is not None
    assert ctx["isFaabLeague"] is False
    assert ctx["totalBudgetDollars"] is None
    assert ctx["remainingBudgetDollars"] is None
    assert ctx["waiverPosition"] == 4  # still real and useful for a non-FAAB league

    # suggest_faab_bids itself is entirely unchanged by this fix -- the
    # endpoint still computes bid ranges from whatever budget params the
    # caller passed (defaults here), it simply never claims those numbers
    # are real for a non-FAAB league. The frontend is responsible for
    # suppressing the dollar UI using `faabContext.isFaabLeague`.
    assert result.data["addCandidates"]


def test_faab_context_is_none_when_league_settings_cannot_be_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)

    def _fake_get_json_no_settings(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return _ROSTERS
        if path == "players/nfl":
            return _PLAYERS
        if path == "league/9999":
            raise OSError("simulated network failure")
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json_no_settings)

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result.data["faabContext"] is None
    # The rest of the endpoint must remain fully functional -- a
    # league-settings read failure is honestly degraded, never fatal.
    assert result.data["addCandidates"]
