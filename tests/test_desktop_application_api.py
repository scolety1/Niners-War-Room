from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.run_nwr_desktop_api import validate_repo_root
from src.application.contracts import contract_envelope
from src.application.desktop_facade import (
    OUTCOME_INTEGRATION_RELATIVE,
    OUTCOME_MANIFEST_RELATIVE,
    REDRAFT_SEED_SHA256,
    ROOKIE_BOARD_RELATIVE,
    DesktopBackendFacade,
    FacadeError,
)
from src.services.draft_day_app_v1_service import file_sha256
from src.services.outcome_v3_display_service import load_outcome_v3_display
from src.services.redraft_engine_v1_service import builtin_presets, projection_snapshot_path
from src.services.rookie_owner_experience_service import load_owner_rookie_board

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_public_contract_is_camel_case_json_safe_and_path_free() -> None:
    value = contract_envelope(
        "dynasty",
        data={
            "source_path": Path("C:/private/source.csv"),
            "sourcePath": "C:\\private\\source.csv",
            "some_value": float("nan"),
            "nested_items": [{"when_created": "2026-08-11", "report": "at C:\\private\\x"}],
        },
    )

    encoded = json.dumps(value, allow_nan=False)

    assert set(value) == {"contractVersion", "mode", "data", "warnings", "errors"}
    assert "sourcePath" not in value["data"]
    assert value["data"]["someValue"] is None
    assert value["data"]["nestedItems"][0]["whenCreated"] == "2026-08-11"
    assert "C:\\" not in encoded


def test_dynasty_bootstrap_fails_closed_when_rankings_are_missing(tmp_path: Path) -> None:
    facade = DesktopBackendFacade(repo_root=tmp_path, mode="dynasty")

    with pytest.raises(FacadeError) as caught:
        facade.dynasty_bootstrap()

    assert caught.value.code == "DYNASTY_RANKINGS_UNAVAILABLE"
    assert caught.value.status == 503


def test_rookie_review_facade_matches_governed_service_fixture() -> None:
    expected = load_owner_rookie_board(REPO_ROOT / ROOKIE_BOARD_RELATIVE)
    actual = DesktopBackendFacade(repo_root=REPO_ROOT, mode="dynasty").rookie_review()
    rows = actual.data["rookies"]

    assert len(rows) == len(expected) == 80
    assert [row["player"] for row in rows] == expected["Player"].tolist()
    assert [row["rank"] for row in rows] == [
        int(value) if str(value).strip().isdigit() else None
        for value in expected["Rookie Rank"].tolist()
    ]
    assert [row["authority"] for row in rows] == expected["Authority"].tolist()


def test_outcome_status_facade_matches_governed_service_fixture() -> None:
    expected = load_outcome_v3_display(
        integration_path=REPO_ROOT / OUTCOME_INTEGRATION_RELATIVE,
        manifest_path=REPO_ROOT / OUTCOME_MANIFEST_RELATIVE,
    )
    actual = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
    ).outcome_release_status()

    assert expected.loaded
    assert actual.data == {
        "loaded": True,
        "rowCount": expected.row_count,
        "playerCount": expected.player_count,
        "sourceHash": expected.source_hash,
        "releaseIdentifier": expected.release_identifier,
    }


def test_dynasty_facade_composes_real_governed_workflows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NWR_DYNASTY_RANKINGS_ROOT", raising=False)
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="dynasty")

    bootstrap = facade.dynasty_bootstrap()
    current_ids = [
        row["assetId"]
        for row in bootstrap.data["assetOptions"]
        if row["assetType"] == "Current Player"
    ][:2]
    detail = facade.dynasty_asset(current_ids[0])
    comparison = facade.compare_dynasty_assets(current_ids)
    trade = facade.evaluate_dynasty_trade(
        give=[current_ids[0]],
        receive=[current_ids[1]],
        team_window="Balanced",
    )

    assert set(bootstrap.data) == {
        "product",
        "status",
        "summary",
        "rankings",
        "rookies",
        "assetOptions",
        "marketFreshness",
        "planning",
        "notices",
    }
    assert set(bootstrap.data["product"]) == {
        "title",
        "contextLabel",
        "leagueLabel",
        "authority",
    }
    assert set(bootstrap.data["status"]) == {
        "ready",
        "tone",
        "authority",
        "sourceAsOf",
        "freshness",
        "summary",
        "scheduledRefresh",
        "errors",
        "warnings",
        "sourceHashes",
    }
    assert set(bootstrap.data["summary"]) == {
        "rankedPlayers",
        "marketMatched",
        "rookieRows",
        "blockedRookies",
        "outcomeRows",
        "workspace",
    }
    assert set(bootstrap.data["summary"]["workspace"]) == {
        "watchlist",
        "targets",
        "avoid",
        "openDecisions",
        "savedScenarios",
    }
    assert bootstrap.data["summary"] | {"workspace": None} == {
        "rankedPlayers": 240,
        "marketMatched": 232,
        "rookieRows": 80,
        "blockedRookies": 7,
        "outcomeRows": 17280,
        "workspace": None,
    }
    assert set(bootstrap.data["rankings"][0]) == {
        "rank",
        "player",
        "position",
        "team",
        "age",
        "positionRank",
        "tier",
        "nwrScore",
        "nwrView",
        "range",
        "marketBand",
        "marketRank",
        "marketGap",
        "marketValue",
        "marketDate",
        "confidence",
        "risk",
        "assetId",
    }
    assert set(bootstrap.data["rookies"][0]) == {
        "rank",
        "assetId",
        "playerId",
        "player",
        "position",
        "team",
        "rookieTier",
        "draftRange",
        "nflDraftCapital",
        "boardScore",
        "reviewScore",
        "authority",
        "blockedReason",
        "warnings",
        "confidence",
        "age",
        "collegeProduction",
        "athleticContext",
        "researchTier",
        "floor",
        "expected",
        "ceiling",
    }
    assert set(bootstrap.data["assetOptions"][0]) == {
        "assetId",
        "name",
        "assetType",
        "position",
        "team",
        "rank",
        "authority",
        "blocked",
    }
    assert set(bootstrap.data["marketFreshness"]) == {
        "sourceAsOf",
        "status",
        "message",
    }
    assert set(bootstrap.data["planning"]) == {
        "storeStatus",
        "updatedAtUtc",
        "message",
        "modules",
    }
    assert [row["moduleId"] for row in bootstrap.data["planning"]["modules"]] == [
        "roster",
        "picks",
        "keeper",
        "drop",
        "trade",
        "draft",
    ]
    assert all(
        set(row) == {"moduleId", "checks", "notes", "saved", "updatedAtUtc"}
        for row in bootstrap.data["planning"]["modules"]
    )
    assert all(set(notice) == {"tone", "title", "message"} for notice in bootstrap.data["notices"])
    assert bootstrap.data["status"]["sourceHashes"]["dynasty_finished_v1"] == (
        "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
    )

    assert set(detail.data) == {
        "assetId",
        "name",
        "assetType",
        "position",
        "team",
        "rank",
        "positionRank",
        "nwrScore",
        "age",
        "confidence",
        "authority",
        "range",
        "market",
        "risk",
        "reasons",
        "outcomes",
        "research",
        "caveats",
    }
    assert detail.data["assetId"] == current_ids[0]
    assert set(detail.data["range"]) == {"floor", "expected", "ceiling", "method", "authority"}
    assert set(detail.data["market"]) == {
        "band",
        "gap",
        "rank",
        "value",
        "sourceAsOf",
        "status",
    }

    assert set(comparison.data) == {"leans", "ranges", "players", "warnings"}
    assert [row["assetId"] for row in comparison.data["players"]] == current_ids
    assert [row["assetId"] for row in comparison.data["ranges"]] == current_ids
    assert all(
        set(row) == {"horizon", "preferred", "reason", "authority"}
        for row in comparison.data["leans"]
    )
    assert all(
        set(row) == {"assetId", "player", "dimensions", "advantages", "risks"}
        for row in comparison.data["players"]
    )
    assert all(
        set(row)
        == {
            "assetId",
            "player",
            "floor",
            "expected",
            "ceiling",
            "ageWindow",
            "risk",
            "authority",
            "method",
        }
        for row in comparison.data["ranges"]
    )

    assert set(trade.data) == {
        "authority",
        "recommendation",
        "preferredSide",
        "confidence",
        "teamWindow",
        "summary",
        "reasons",
        "mainUncertainty",
        "whatWouldChange",
        "dimensions",
        "counterStatus",
        "counterMessage",
    }
    assert trade.data["counterStatus"] == "blocked"
    assert "verified" in trade.data["counterMessage"].lower()
    assert all(
        set(row) == {"code", "label", "outcome", "confidence", "evidence", "explanation"}
        for row in trade.data["dimensions"]
    )

    for payload in (bootstrap, detail, comparison, trade):
        json.dumps(
            contract_envelope("dynasty", data=payload.data, warnings=payload.warnings),
            allow_nan=False,
        )


def test_dynasty_planning_modules_save_and_reload_through_personal_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NWR_DYNASTY_RANKINGS_ROOT", raising=False)
    workspace = tmp_path / "personal-workspace"
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
        workspace_root=workspace,
    )

    before = facade.dynasty_bootstrap().data["planning"]
    saved = facade.save_dynasty_planning_module(
        module_id="draft",
        checks=[True, False, True, True],
        notes="Need an early running back; verify the owner-entered pick ledger first.",
    ).data
    reloaded = (
        DesktopBackendFacade(
            repo_root=REPO_ROOT,
            mode="dynasty",
            workspace_root=workspace,
        )
        .dynasty_bootstrap()
        .data["planning"]
    )

    assert before["storeStatus"] == "empty"
    assert saved["storeStatus"] == "loaded"
    draft = next(row for row in reloaded["modules"] if row["moduleId"] == "draft")
    assert draft["checks"] == [True, False, True, True]
    assert draft["notes"].startswith("Need an early running back")
    assert draft["saved"] is True
    assert draft["updatedAtUtc"]
    assert (workspace / "stores" / "saved_scenarios.json").is_file()

    with pytest.raises(FacadeError, match="exactly 4"):
        facade.save_dynasty_planning_module(module_id="draft", checks=[True], notes="invalid")
    with pytest.raises(FacadeError) as caught:
        facade.save_dynasty_planning_module(
            module_id="unknown", checks=[False] * 4, notes="invalid"
        )
    assert caught.value.code == "PLANNING_MODULE_NOT_FOUND"


def test_dynasty_trade_scenarios_save_reopen_update_and_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NWR_DYNASTY_RANKINGS_ROOT", raising=False)
    workspace = tmp_path / "personal-workspace"
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
        workspace_root=workspace,
    )
    options = facade.dynasty_bootstrap().data["assetOptions"]
    current_ids = [
        row["assetId"]
        for row in options
        if row["assetType"] == "Current Player" and not row["blocked"]
    ][:2]

    empty = facade.list_dynasty_trades().data
    saved = facade.save_dynasty_trade(
        scenario_id=None,
        title="Contender window",
        give=[current_ids[0]],
        receive=[current_ids[1]],
        team_window="Contending",
        notes="Review the exact governed sides and team window.",
    ).data
    scenario_id = saved["scenarioId"]
    updated = facade.save_dynasty_trade(
        scenario_id=scenario_id,
        title="Contender window - revised notes",
        give=[current_ids[0]],
        receive=[current_ids[1]],
        team_window="Contending",
        notes="The asset sides remain exact.",
    ).data
    reloaded = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
        workspace_root=workspace,
    ).list_dynasty_trades().data
    exported = facade.export_dynasty_trade(
        title="Contender window brief",
        give=[current_ids[0]],
        receive=[current_ids[1]],
        team_window="Contending",
        notes="The asset sides remain exact.",
    ).data

    assert empty == {
        "storeStatus": "empty",
        "updatedAtUtc": "",
        "message": "No saved trades yet.",
        "scenarios": [],
    }
    assert scenario_id.startswith("desktop-trade:")
    assert updated["scenarioId"] == scenario_id
    assert len(updated["workspace"]["scenarios"]) == 1
    assert reloaded["scenarios"] == updated["workspace"]["scenarios"]
    reopened = reloaded["scenarios"][0]
    assert reopened["scenarioId"] == scenario_id
    assert reopened["give"] == [current_ids[0]]
    assert reopened["receive"] == [current_ids[1]]
    assert reopened["teamWindow"] == "Contending"
    assert reopened["notes"] == "The asset sides remain exact."
    assert reopened["sourceStatus"] == "CURRENT"
    assert exported["fileName"] == "nwr-trade-brief.md"
    assert "## You give" in exported["markdown"]
    assert "## You receive" in exported["markdown"]
    assert exported["missingData"] == []


def test_redraft_bootstrap_seeds_once_and_matches_desktop_contract(
    tmp_path: Path,
) -> None:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="redraft",
        redraft_root=store,
    )

    first = facade.redraft_bootstrap()
    target = projection_snapshot_path(store, 2026)
    first_bytes = target.read_bytes()
    first_mtime = target.stat().st_mtime_ns
    second = facade.redraft_bootstrap()

    assert target.is_file()
    assert file_sha256(target) == REDRAFT_SEED_SHA256
    assert target.read_bytes() == first_bytes
    assert target.stat().st_mtime_ns == first_mtime
    assert set(first.data) == {
        "product",
        "status",
        "profiles",
        "presets",
        "activeProfileId",
        "activeProfile",
        "rankings",
        "replacementLevels",
        "draftBoard",
        "health",
        "notices",
    }
    assert set(first.data["product"]) == {"title", "contextLabel", "authority"}
    assert set(first.data["status"]) == {
        "ready",
        "tone",
        "authority",
        "sourceAsOf",
        "freshness",
        "summary",
        "scheduledRefresh",
        "errors",
        "warnings",
        "sourceHashes",
    }
    assert first.data["profiles"] == []
    assert first.data["activeProfileId"] is None
    assert first.data["activeProfile"] is None
    assert [row["profileId"] for row in first.data["presets"]] == [
        profile.profile_id for profile in builtin_presets()
    ]
    assert all(
        set(row)
        == {
            "profileId",
            "leagueName",
            "season",
            "teamCount",
            "roster",
            "scoring",
            "draft",
            "presetKey",
            "archived",
            "createdAtUtc",
            "updatedAtUtc",
        }
        for row in first.data["presets"]
    )
    assert first.data["health"]["blockedPlayers"] == 2
    assert all(set(row) == {"tone", "title", "message"} for row in first.data["notices"])
    blocked_notice = " ".join(row["message"] for row in first.data["notices"])
    assert "Max Bredeson" in blocked_notice
    assert "Riley Nowakowski" in blocked_notice
    assert second.data["health"]["blockedPlayers"] == 2

    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR",
        league_name="Contract Test League",
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    active = facade.redraft_bootstrap()

    assert active.data["activeProfileId"] == profile_id
    assert active.data["activeProfile"]["profileId"] == profile_id
    assert active.data["status"]["ready"] is True
    assert len(active.data["rankings"]) == 608
    assert active.data["health"]["blockedPlayers"] == 2
    assert set(active.data["rankings"][0]) == {
        "overallRank",
        "positionRank",
        "playerId",
        "playerName",
        "position",
        "team",
        "projectedPoints",
        "replacementPoints",
        "replacementAdjustedValue",
        "starterGap",
        "confidence",
        "tier",
        "sourceAsOf",
        "rookie",
        "drafted",
        "draftedBy",
        "pickNumber",
    }
    assert set(active.data["replacementLevels"][0]) == {
        "position",
        "starterCount",
        "rosteredCount",
        "starterCutoffPoints",
        "replacementPoints",
    }
    assert set(active.data["health"]) == {
        "status",
        "playerUniverseAvailable",
        "currentSeasonForecastAvailable",
        "scoringProfileValid",
        "replacementCalculationValid",
        "rankedPlayers",
        "blockedPlayers",
        "lastGeneratedTimestamp",
        "messages",
    }
    if active.data["draftBoard"] is not None:
        assert set(active.data["draftBoard"]).issubset(
            {
                "schemaVersion",
                "profileId",
                "drafted",
                "updatedAtUtc",
                "recoveredFromBackup",
            }
        )
    json.dumps(
        contract_envelope("redraft", data=active.data, warnings=active.warnings),
        allow_nan=False,
    )


def test_dynasty_personal_workspace_persists_and_verifies_backup(tmp_path: Path) -> None:
    workspace_root = tmp_path / "personal-workspace"
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
        workspace_root=workspace_root,
    )
    before = facade.dynasty_bootstrap()
    asset = next(
        row for row in before.data["assetOptions"] if row["assetType"] == "Current Player"
    )

    board = facade.save_dynasty_personal_entry(
        asset_id=asset["assetId"],
        watchlist=True,
        target=True,
        avoid=False,
        tags=[" contender ", "buy window", "contender"],
        notes="Revisit after camp usage stabilizes.",
        team_window="Custom/Unspecified",
    )
    decision = facade.create_dynasty_decision(
        title="Camp value checkpoint",
        decision_type="player evaluation",
        asset_ids=[asset["assetId"]],
        rationale="Compare role security with the current roster window.",
    )
    backup = facade.backup_dynasty_workspace()
    checked = facade.check_dynasty_workspace_restore()
    restarted = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
        workspace_root=workspace_root,
    ).dynasty_workspace()
    after = facade.dynasty_bootstrap()

    assert board.data["personalBoard"][0]["assetId"] == asset["assetId"]
    assert board.data["personalBoard"][0]["teamWindow"] == "Custom/Unspecified"
    assert board.data["personalBoard"][0]["tags"] == ["contender", "buy window"]
    assert decision.data["decisions"][0]["title"] == "Camp value checkpoint"
    assert decision.data["decisions"][0]["assetNames"] == [asset["name"]]
    assert backup.data["backup"]["status"] == "ready"
    assert checked.data["backup"]["status"] == "ready"
    assert checked.data["backup"]["fileCount"] == 2
    assert restarted.data["personalBoard"] == checked.data["personalBoard"]
    assert restarted.data["decisions"] == checked.data["decisions"]
    assert [row["assetId"] for row in before.data["rankings"]] == [
        row["assetId"] for row in after.data["rankings"]
    ]
    assert before.data["status"]["sourceHashes"] == after.data["status"]["sourceHashes"]


def test_dynasty_legacy_workspace_adoption_is_create_only(tmp_path: Path) -> None:
    legacy_root = tmp_path / "legacy-workspace"
    desktop_root = tmp_path / "desktop-workspace"
    source_facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
        workspace_root=legacy_root,
    )
    asset = next(
        row
        for row in source_facade.dynasty_bootstrap().data["assetOptions"]
        if row["assetType"] == "Current Player"
    )
    source_facade.save_dynasty_personal_entry(
        asset_id=asset["assetId"],
        watchlist=True,
        target=False,
        avoid=False,
        tags=["legacy"],
        notes="Established Streamlit context.",
        team_window="Custom/Unspecified",
    )
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
        workspace_root=desktop_root,
        legacy_workspace_root=legacy_root,
    )

    adopted = facade.adopt_legacy_dynasty_workspace(confirmed=True)

    assert adopted.data["personalBoard"][0]["assetId"] == asset["assetId"]
    assert "without changing the source" in adopted.data["message"]
    assert json.loads((legacy_root / "stores" / "personal_board.json").read_text())
    with pytest.raises(FacadeError, match="nothing was overwritten"):
        facade.adopt_legacy_dynasty_workspace(confirmed=True)


def test_redraft_first_run_never_overwrites_existing_snapshot(tmp_path: Path) -> None:
    store = tmp_path / "existing-store"
    target = projection_snapshot_path(store, 2026)
    target.parent.mkdir(parents=True)
    sentinel = b"owner-installed-projection-snapshot"
    target.write_bytes(sentinel)
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="redraft",
        redraft_root=store,
    )

    result = facade.redraft_bootstrap()

    assert target.read_bytes() == sentinel
    assert result.data["status"]["ready"] is False
    assert result.data["health"]["blockedPlayers"] == 0


def test_redraft_missing_bundled_seed_warns_and_fails_closed(tmp_path: Path) -> None:
    repo_root = tmp_path / "empty-repo"
    repo_root.mkdir()
    store = tmp_path / "missing-seed-store"
    facade = DesktopBackendFacade(
        repo_root=repo_root,
        mode="redraft",
        redraft_root=store,
    )

    result = facade.redraft_bootstrap()

    assert not projection_snapshot_path(store, 2026).exists()
    assert result.data["status"]["ready"] is False
    assert result.data["status"]["tone"] == "blocked"
    assert any("seed is unavailable" in warning for warning in result.warnings)


def test_redraft_mutations_are_scoped_to_explicit_temp_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="redraft",
        redraft_root=store,
    )
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR",
        league_name="Local Test League",
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    ranking = SimpleNamespace(rows=(SimpleNamespace(player_id="fixture-player"),))
    monkeypatch.setattr(facade, "_redraft_ranking_for_profile", lambda _profile_id: ranking)

    marked = facade.mark_redraft_player(
        profile_id=profile_id,
        player_id="fixture-player",
        drafted=True,
    )
    undone = facade.undo_redraft_pick(profile_id=profile_id)

    assert marked.data["draftBoard"]["drafted"] == ["fixture-player"]
    assert undone.data["draftBoard"]["drafted"] == []
    files = [path for path in store.rglob("*") if path.is_file()]
    assert files
    assert all(path.is_relative_to(store) for path in files)
    assert not (REPO_ROOT / "fixture-player").exists()


def test_redraft_profile_edit_duplicate_and_restart_persist(tmp_path: Path) -> None:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="redraft",
        redraft_root=store,
    )
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR",
        league_name="Restart League",
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    initial = facade.redraft_bootstrap()
    drafted = [row["playerId"] for row in initial.data["rankings"][:2]]
    for player_id in drafted:
        facade.mark_redraft_player(
            profile_id=profile_id,
            player_id=player_id,
            drafted=True,
        )

    edited = facade.update_redraft_profile(
        profile_id,
        league_name="Restart League Updated",
        team_count=10,
        roster={
            "qb": 1,
            "rb": 2,
            "wr": 3,
            "te": 1,
            "flex": 1,
            "superflex": 0,
            "k": 0,
            "dst": 0,
            "benchSize": 7,
        },
        scoring={
            "reception": 1.0,
            "passingTd": 4.0,
            "interception": -2.0,
            "tePremium": 0.5,
        },
        draft={
            "rounds": 16,
            "draftSlot": 4,
            "replacementMethod": "expected_available",
        },
    )
    duplicate = facade.duplicate_redraft_profile(profile_id)
    duplicate_id = duplicate.data["profile"]["profileId"]
    duplicated_bootstrap = facade.redraft_bootstrap()

    assert edited.data["profile"]["leagueName"] == "Restart League Updated"
    assert edited.data["profile"]["teamCount"] == 10
    assert edited.data["profile"]["scoring"]["reception"] == 1.0
    assert duplicate_id != profile_id
    assert duplicated_bootstrap.data["activeProfileId"] == duplicate_id
    assert duplicated_bootstrap.data["draftBoard"]["drafted"] == []

    facade.activate_redraft_profile(profile_id)
    restarted = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="redraft",
        redraft_root=store,
    ).redraft_bootstrap()
    assert restarted.data["activeProfileId"] == profile_id
    assert restarted.data["activeProfile"]["leagueName"] == "Restart League Updated"
    assert restarted.data["activeProfile"]["draft"]["draftSlot"] == 4
    assert restarted.data["draftBoard"]["drafted"] == drafted

    with pytest.raises(FacadeError, match="Roster settings must use integers"):
        facade.update_redraft_profile(
            profile_id,
            league_name="Invalid",
            team_count=10,
            roster={
                "qb": True,
                "rb": 2,
                "wr": 3,
                "te": 1,
                "flex": 1,
                "superflex": 0,
                "k": 0,
                "dst": 0,
                "benchSize": 7,
            },
            scoring={
                "reception": 1.0,
                "passingTd": 4.0,
                "interception": -2.0,
                "tePremium": 0.5,
            },
            draft={
                "rounds": 16,
                "draftSlot": 4,
                "replacementMethod": "expected_available",
            },
        )


def test_launcher_repo_root_validation_is_frozen_aware(tmp_path: Path) -> None:
    resource_root = tmp_path / "installed-resources"
    (resource_root / "docs").mkdir(parents=True)
    checkout_root = tmp_path / "checkout"
    (checkout_root / "src" / "services").mkdir(parents=True)
    empty_root = tmp_path / "empty"
    empty_root.mkdir()

    assert validate_repo_root(resource_root, frozen=True) == resource_root.resolve()
    assert validate_repo_root(checkout_root, frozen=False) == checkout_root.resolve()
    with pytest.raises(ValueError, match="repository checkout"):
        validate_repo_root(resource_root, frozen=False)
    with pytest.raises(ValueError, match="bundled NWR resources"):
        validate_repo_root(empty_root, frozen=True)


def test_facade_has_no_streamlit_or_app_component_dependency() -> None:
    source = (REPO_ROOT / "src" / "application" / "desktop_facade.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert all(not name.startswith("streamlit") for name in imports)
    assert all(not name.startswith("app") for name in imports)
