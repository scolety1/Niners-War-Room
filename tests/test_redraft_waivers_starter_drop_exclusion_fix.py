from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade
from src.services.redraft_engine_v1_service import load_profile, save_profile
from src.services.waiver_engine_service import DropCandidate, filter_legal_drop_candidates

REPO_ROOT = Path(__file__).resolve().parents[1]


def _facade(tmp_path: Path) -> DesktopBackendFacade:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Starter Drop Exclusion League"
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
                "league": {"league_id": "9999", "name": "Starter Drop Exclusion League"},
                "owner": {"user_id": "owner-1"},
            }
        ),
        encoding="utf-8",
    )
    return facade


PLAYERS = {
    "starter-1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
    "bench-1": {"full_name": "Bijan Robinson", "position": "RB", "team": "ATL"},
    "rival-1": {"full_name": "Justin Jefferson", "position": "WR", "team": "MIN"},
    "fa-1": {"full_name": "Tyreek Hill", "position": "WR", "team": "MIA"},
}


def test_locked_bench_player_is_excluded_from_legal_drop_candidates() -> None:
    candidates = (
        DropCandidate("p-starter", "Starter", "RB", 1.0, "fixture"),
        DropCandidate("p-locked", "Locked Bench", "WR", 0.1, "fixture"),
        DropCandidate("p-bench", "Open Bench", "TE", 0.2, "fixture"),
    )

    legal = filter_legal_drop_candidates(
        candidates=candidates,
        canonical_id_by_sleeper_id={
            "s-starter": "p-starter",
            "s-locked": "p-locked",
            "s-bench": "p-bench",
        },
        starter_sleeper_player_ids=("s-starter",),
        locked_sleeper_player_ids=("s-locked",),
    )

    assert [candidate.player_name for candidate in legal] == ["Open Bench"]


def _get_json(rosters: list[dict[str, Any]]):
    def fake(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return rosters
        if path == "players/nfl":
            return PLAYERS
        if path == "league/9999":
            return {
                "settings": {
                    "waiver_type": 2,
                    "waiver_budget": 100,
                    "playoff_week_start": 15,
                },
                "roster_positions": ["RB", "BN"],
            }
        if path == "state/nfl":
            return {"week": 3}
        raise AssertionError(path)

    return fake


def test_current_starter_is_never_returned_or_paired_as_a_drop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade = _facade(tmp_path)
    rosters = [
        {
            "owner_id": "owner-1",
            "players": ["starter-1", "bench-1"],
            "starters": ["starter-1"],
            "settings": {"waiver_budget_used": 25},
        },
        {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
    ]
    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _get_json(rosters))

    result = facade.redraft_waivers(mode="REST_OF_SEASON").data

    assert [row["playerName"] for row in result["dropCandidates"]] == ["Bijan Robinson"]
    assert all(
        pairing["drop"]["playerName"] == "Bijan Robinson"
        for pairing in result["addDropPairings"]
    )
    assert result["dropEligibilityContext"]["excludedStarterCount"] == 1
    assert result["dropEligibilityContext"]["legalDropCandidateCount"] == 1
    assert result["rosterPositionCounts"]["RB"] == 2
    assert result["freeAgentPoolContext"]["source"] == "SLEEPER_LIVE"
    assert result["freeAgentPoolContext"]["retrievedAtUtc"]
    assert result["acquisitionContext"]["waiverStatusAvailable"] is False


def test_full_roster_with_only_a_starter_degrades_to_no_legal_drop_and_zero_bid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade = _facade(tmp_path)
    rosters = [
        {
            "owner_id": "owner-1",
            "players": ["starter-1"],
            "starters": ["starter-1"],
            "settings": {"waiver_budget_used": 25},
        },
        {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
    ]

    def fake(self: Any, path: str) -> Any:
        value = _get_json(rosters)(self, path)
        if path == "league/9999":
            value["roster_positions"] = ["RB"]
        return value

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", fake)

    result = facade.redraft_waivers(mode="REST_OF_SEASON").data

    assert result["rosterSlotContext"]["openSlotAvailable"] is False
    assert result["dropCandidates"] == []
    assert result["addDropPairings"]
    assert all(pairing["dropRequired"] is True for pairing in result["addDropPairings"])
    assert all(pairing["drop"] is None for pairing in result["addDropPairings"])
    assert all(
        pairing["contextLabel"] == "NO_DROP_CANDIDATE_AVAILABLE"
        for pairing in result["addDropPairings"]
    )
    assert all(row["faabBidLowDollars"] == 0 for row in result["addCandidates"])
    assert all(row["faabBidHighDollars"] == 0 for row in result["addCandidates"])
