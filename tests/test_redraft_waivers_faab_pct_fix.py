"""Waiver-night hardening cycle, Worker 3 (2026-09-22): regression test for
the FAAB percent-of-remaining-budget fix.

Worker 2's real, live-verified finding: `waiver_engine_service.py`'s
`suggest_faab_bids` already computes `bid_low_pct`/`bid_high_pct` (the bid
range as a literal percent of `remaining_budget_dollars`) on every
`FaabBidSuggestion`, but those two fields never reached
`desktop_facade.py`'s serialization or the API response -- only the dollar
fields did. This test locks in the fix: `faabBidLowPct`/`faabBidHighPct`
now appear on every add-candidate row, consistent with (and derivable from)
the existing dollar fields, and honestly `None` under the exact same
conditions the dollar fields are `None`.
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
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="FAAB Pct League"
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
                "league": {"league_id": "9999", "name": "FAAB Pct League"},
                "owner": {"user_id": "owner-1"},
            }
        ),
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


def _make_fake_get_json(league_settings: dict[str, Any], *, current_week: Any = 2):
    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return _ROSTERS
        if path == "players/nfl":
            return _PLAYERS
        if path == "league/9999":
            return {"settings": league_settings}
        if path == "state/nfl":
            return {"week": current_week}
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    return _fake_get_json


def test_faab_bid_pct_fields_are_surfaced_and_consistent_with_dollar_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 2, "waiver_budget": 100, "playoff_week_start": 15}),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    add_candidates = result.data["addCandidates"]
    priced_rows = [row for row in add_candidates if row["faabBidLowDollars"] is not None]
    assert priced_rows, "expected at least one real priced candidate in this fixture"
    for row in priced_rows:
        assert row["faabBidLowPct"] is not None
        assert row["faabBidHighPct"] is not None
        assert 0.0 <= row["faabBidLowPct"] <= 1.0
        assert 0.0 <= row["faabBidHighPct"] <= 1.0
        assert row["faabBidLowPct"] <= row["faabBidHighPct"]
        # Consistent with the real remaining budget used to price this
        # request (100 total - 35 used = 65) -- the pct figure is not an
        # independent/disconnected computation.
        remaining_budget = 65
        assert row["faabBidLowDollars"] == round(remaining_budget * row["faabBidLowPct"])
        assert row["faabBidHighDollars"] == round(remaining_budget * row["faabBidHighPct"])


def test_faab_bid_pct_fields_are_none_exactly_when_dollar_fields_are_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """waiver_type=0 is a non-FAAB (rolling waivers) league -- no bid of
    any kind, dollar or pct, should ever be fabricated."""
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 0, "waiver_budget": 100}),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    add_candidates = result.data["addCandidates"]
    assert add_candidates
    for row in add_candidates:
        assert row["faabBidLowDollars"] is None
        assert row["faabBidHighDollars"] is None
        assert row["faabBidLowPct"] is None
        assert row["faabBidHighPct"] is None
