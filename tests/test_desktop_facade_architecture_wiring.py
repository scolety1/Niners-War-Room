"""Facade-level wiring tests for the NWR pre-UI architecture pass
(2026-09-10, directive sections 1/3/4/5/6).

These exercise `DesktopBackendFacade`'s three new read-only endpoints
(`redraft_league_workspace_context`, `redraft_player_availability_status`,
`redraft_data_health`) plus the additive `traceId`/`leagueSnapshotId`
fields now returned by `redraft_kdst_streamer`.

Real, disclosed test-environment gap (confirmed by direct investigation,
not assumed): a freshly created local profile in this worktree has an
EMPTY governed ranking -- `redraft_bootstrap()` on a brand-new profile
returns zero rankings here (`health.status` reads "Blocked - current-
season evidence required"). This is the same pre-existing "no governed
2026 projection snapshot installed in this worktree's default store" gap
already documented in `docs/codex/overnight_v3/
NWR_PROSPECTIVE_2026_IN_SEASON_FREEZE_V2.md`'s "Known limitations" and in
this branch's own 5-failure baseline (`test_redraft_bootstrap_seeds_once_
and_matches_desktop_contract` is one of them) -- unrelated to this pass.
It means `redraft_weekly_lineup`/`redraft_waivers`/`redraft_trade_analysis`
/`redraft_trade_finder` cannot be exercised end-to-end in THIS environment
regardless of this pass's changes, so the new `traceId`/`leagueSnapshotId`
/`decisionEnvelope` fields added to those four functions are covered here
only indirectly (via the pure `league_workspace_context_service.py` /
`decision_envelope_service.py` unit tests, and via this file's direct
proof that a fresh local profile's degraded-ranking path never crashes
the new standalone endpoints) -- disclosed, not silently skipped. See
`DECISION_CONTRACTS.md`.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.fantasypros_kdst_consensus_service import ConsensusRow
from src.services.redraft_engine_v1_service import load_profile, save_profile

REPO_ROOT = Path(__file__).resolve().parents[1]


def _fresh_local_facade(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Architecture Wiring League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    return facade, profile_id


def test_league_workspace_context_requires_an_active_profile(tmp_path: Path) -> None:
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path / "redraft-store"
    )
    with pytest.raises(FacadeError) as excinfo:
        facade.redraft_league_workspace_context()
    assert excinfo.value.code == "REDRAFT_PROFILE_REQUIRED"


def test_league_workspace_context_pre_draft_local_profile(tmp_path: Path) -> None:
    facade, profile_id = _fresh_local_facade(tmp_path)
    context = facade.redraft_league_workspace_context().data
    assert context["profileId"] == profile_id
    assert context["provider"] == "local"
    assert context["lifecycle"] == "PRE_DRAFT"
    assert context["syncStatus"] == "NOT_APPLICABLE"
    assert context["rosterStateHash"] is None
    assert context["leagueSnapshotId"]  # always populated
    assert context["scoringProfileHash"]
    assert any("week is not automatically sourced" in issue for issue in context["issues"])


def test_league_workspace_context_snapshot_id_changes_with_a_real_rule_edit(tmp_path: Path) -> None:
    facade, profile_id = _fresh_local_facade(tmp_path)
    before = facade.redraft_league_workspace_context().data
    facade.update_redraft_profile(
        profile_id,
        league_name="Architecture Wiring League",
        team_count=14,  # real rule edit (was 12)
        roster={
            "qb": 1, "rb": 2, "wr": 2, "te": 1, "flex": 1, "superflex": 0,
            "k": 1, "dst": 1, "benchSize": 6,
        },
        scoring={"reception": 0.5, "passingTd": 4.0, "interception": -2.0, "tePremium": 0.0},
        draft={"rounds": 16, "draftSlot": None, "replacementMethod": "expected_available"},
    )
    after = facade.redraft_league_workspace_context().data
    assert before["scoringProfileHash"] != after["scoringProfileHash"]
    assert before["leagueSnapshotId"] != after["leagueSnapshotId"]


def test_player_availability_status_reflects_real_admitted_overrides(tmp_path: Path) -> None:
    facade, _profile_id = _fresh_local_facade(tmp_path)
    result = facade.redraft_player_availability_status().data
    assert result["authorityHealth"]["automatedFeed"] is False
    # This repo's real, committed override file -- not test-fabricated data.
    kinds = {row["overrideKind"] for row in result["statuses"]}
    assert kinds  # at least one real admitted override exists in this repo
    assert kinds <= {"SEASON_OUT", "NOT_WITH_TEAM", "ADMINISTRATIVE_EXEMPT", "TEAM_CORRECTION"}


def test_data_health_reports_all_seven_categories_for_a_local_profile(tmp_path: Path) -> None:
    facade, _profile_id = _fresh_local_facade(tmp_path)
    result = facade.redraft_data_health().data
    names = {row["category"] for row in result["categories"]}
    assert names == {
        "LEAGUE_SYNC", "WEEKLY_PROJECTIONS", "ROS_PROJECTIONS", "MARKET_ADP",
        "PLAYER_STATUS", "DECISION_ENGINE", "SNAPSHOT",
    }
    by_name = {row["category"]: row for row in result["categories"]}
    # Real, disclosed degraded state for a brand-new local profile in this
    # environment -- never silently reported as healthy.
    assert by_name["LEAGUE_SYNC"]["status"] == "NOT_APPLICABLE"
    assert by_name["WEEKLY_PROJECTIONS"]["status"] == "NOT_APPLICABLE"
    assert by_name["PLAYER_STATUS"]["status"] == "OK"
    assert by_name["SNAPSHOT"]["status"] == "OK"
    assert result["generatedAtUtc"]


def test_data_health_with_no_active_profile_reports_every_category_unavailable(
    tmp_path: Path,
) -> None:
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path / "redraft-store"
    )
    result = facade.redraft_data_health().data
    assert len(result["categories"]) == 7
    assert all(row["status"] == "UNAVAILABLE" for row in result["categories"])


def test_kdst_streamer_response_carries_trace_ids_and_league_snapshot_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="KDST Snapshot League"
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

    monkeypatch.setattr(
        desktop_facade_module,
        "fantasypros_provider_status",
        lambda: SimpleNamespace(
            configured=True, authority="EXTERNAL CONSENSUS — FANTASYPROS", message="ok"
        ),
    )

    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return [
                {"owner_id": "owner-1", "players": ["k-1"], "starters": ["k-1"]},
                {"owner_id": "owner-2", "players": ["d-1"], "starters": []},
            ]
        if path == "players/nfl":
            return {
                "k-1": {"full_name": "Kicker One", "position": "K", "team": "SF"},
                "d-1": {"full_name": "Seahawks", "position": "DEF", "team": "SEA"},
            }
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    def _fake_consensus_rankings(
        self: Any, *, season: int, position: str, week: int, scoring: str
    ) -> tuple[ConsensusRow, ...]:
        if position == "K":
            return (ConsensusRow("fp-k-1", "Kicker One", "K", "SF", 1, 1, week, season),)
        return (
            ConsensusRow("fp-d-1", "Seahawks", "DST", "SEA", 3, 1, week, season),
            ConsensusRow("fp-d-2", "Free Defense", "DST", "GB", 4, 1, week, season),
        )

    monkeypatch.setattr(
        desktop_facade_module.FantasyProsConsensusClient,
        "consensus_rankings",
        _fake_consensus_rankings,
    )

    result = facade.redraft_kdst_streamer(week=1).data
    assert result["leagueSnapshotId"]
    assert isinstance(result["traceIds"], list)
    assert result["traceIds"]  # at least one real trace was recorded
    for row in result["traceIds"]:
        assert row["position"] in ("K", "DST")
        assert row["traceId"]
