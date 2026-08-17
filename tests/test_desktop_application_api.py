from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

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
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    builtin_presets,
    create_profile,
    projection_snapshot_path,
)
from src.services.rookie_draft_eligibility_service import (
    load_rookie_draft_eligibility_overlay,
)
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
    eligibility = load_rookie_draft_eligibility_overlay(repo_root=REPO_ROOT)
    expected = load_owner_rookie_board(
        REPO_ROOT / ROOKIE_BOARD_RELATIVE,
        eligibility_rows=eligibility.rows,
    )
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
        "rookieReadiness",
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
        "manualReviewRookies",
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
        "marketMatched": 230,
        "rookieRows": 80,
        "blockedRookies": 0,
        "manualReviewRookies": 7,
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
        "evidenceBand",
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
        "marketShare",
        "athleticContext",
        "researchTier",
        "researchNeighborhood",
        "currentRole",
        "whatNwrLikes",
        "whatHoldsBack",
        "biggestUncertainty",
        "rankScoreExplanation",
        "floor",
        "expected",
        "ceiling",
        "identityStatus",
        "draftEligibility",
        "scoreStatus",
        "modelScoreEligible",
        "searchable",
        "selectable",
        "draftable",
        "refreshAvailable",
        "draftRound",
        "overallPick",
        "eligibilityReason",
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
        "selectable",
        "searchable",
        "draftEligible",
        "modelScoreEligible",
        "evidenceBlocked",
        "scoreStatus",
        "identityStatus",
        "playerId",
        "draftRound",
        "overallPick",
        "refreshAvailable",
    }
    assert set(bootstrap.data["marketFreshness"]) == {
        "sourceAsOf",
        "status",
        "message",
    }
    readiness = bootstrap.data["rookieReadiness"]
    assert readiness | {
        "reviewAssetIds": None,
        "draftableAssetIds": None,
        "validatedSurfaces": None,
    } == readiness | {
        "verdict": "GREEN_NWR_ROOKIE_DRAFT_CLASS_COMPLETE_WITH_MANUAL_REVIEW_ASSETS",
        "ready": True,
        "officialDrafted": 80,
        "positionCounts": {"QB": 10, "RB": 12, "WR": 36, "TE": 22},
        "exactIdentity": 80,
        "scored": 73,
        "manualReview": 7,
        "unresolved": 0,
        "missingFromRegistry": 0,
        "missingFromDraftablePool": 0,
        "duplicateAssetIds": 0,
        "refreshAvailable": 7,
        "reviewAssetIds": None,
        "missingAssetIds": [],
        "surfaceGapAssetIds": [],
        "nonselectableAssetIds": [],
        "draftableAssetIds": None,
        "missingBySurface": {
            surface: []
            for surface in (
                "registry",
                "detail",
                "search",
                "selectable",
                "compare",
                "trade",
                "draftable",
                "rookie_board",
                "draft_cockpit",
            )
        },
        "duplicateBySurface": {
            surface: []
            for surface in (
                "registry",
                "detail",
                "search",
                "selectable",
                "compare",
                "trade",
                "draftable",
                "rookie_board",
                "draft_cockpit",
            )
        },
        "validatedSurfaces": None,
        "alertCode": "ROOKIE_DRAFT_CLASS_COMPLETE",
        "alertTitle": "Rookie Draft Class Complete",
        "alertMessage": (
            "80 official QB/RB/WR/TE assets survived every validated workflow surface: "
            "73 scored, 7 manual review, 0 missing or duplicated."
        ),
    }
    assert len(readiness["draftableAssetIds"]) == 80
    assert set(readiness["validatedSurfaces"]) == set(readiness["missingBySurface"])
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
        "playerId",
        "identityStatus",
        "officialDraftAssetId",
        "nflDraftCapital",
        "draftRound",
        "overallPick",
        "draftEligibility",
        "modelScoreEligible",
        "scoreStatus",
        "selectable",
        "refreshAvailable",
        "rookieIntelligence",
        "immediateProduction",
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
    assert detail.data["rookieIntelligence"] is None
    assert "admitted score" in detail.data["reasons"][0].lower()
    assert all("usable_with_confidence_cap" not in reason for reason in detail.data["reasons"])
    assert any(
        reason.startswith(("Holds them back:", "Gate context:", "Watch-out:"))
        for reason in detail.data["reasons"][1:]
    )

    blocked_rows = [row for row in bootstrap.data["rookies"] if row["blockedReason"]]
    assert blocked_rows
    assert all("canonical" not in row["blockedReason"].lower() for row in blocked_rows)
    assert all("gsis" not in row["blockedReason"].lower() for row in blocked_rows)
    blocked_rookie = next(row for row in blocked_rows if row["player"] == "De'Zhaun Stribling")
    assert blocked_rookie["playerId"] == "00-0041035"
    assert blocked_rookie["team"] == "SF"
    assert blocked_rookie["draftable"] is True
    assert blocked_rookie["selectable"] is True
    assert blocked_rookie["modelScoreEligible"] is False
    assert blocked_rookie["blockedReason"].startswith(
        "The frozen Rookie Review did not admit a score."
    )
    blocked_detail = facade.dynasty_asset(blocked_rookie["assetId"])
    assert set(blocked_detail.data["rookieIntelligence"]) == {
        "nwrRookieScore",
        "reviewScore",
        "rawModelScore",
        "collegeProduction",
        "marketShare",
        "athleticContext",
        "currentRole",
        "whatNwrLikes",
        "whatHoldsBack",
        "biggestUncertainty",
        "rankScoreExplanation",
    }
    assert blocked_detail.data["reasons"][0] == (
        "Draft eligible and selectable using the governed official draft asset."
    )
    assert blocked_detail.data["playerId"] == "00-0041035"
    assert blocked_detail.data["nflDraftCapital"] == "NFL Round 2 · Pick 33"
    assert blocked_detail.data["selectable"] is True
    assert blocked_detail.data["nwrScore"] is None
    assert blocked_detail.data["rookieIntelligence"]["nwrRookieScore"] is None
    assert blocked_detail.data["age"] == 23.348871
    assert blocked_detail.data["rookieIntelligence"]["collegeProduction"] == (
        "72.6 / 100 normalized"
    )
    assert blocked_detail.data["rookieIntelligence"]["marketShare"] == ("51.4 / 100 normalized")
    assert blocked_detail.data["rookieIntelligence"]["athleticContext"] == (
        "NOT_ENOUGH_INFORMATION"
    )
    assert blocked_detail.data["rookieIntelligence"]["whatNwrLikes"][:3] == [
        "Age: 87.7/100",
        "NFL draft capital: 77.6/100",
        "College production: 72.6/100",
    ]
    assert blocked_detail.data["rookieIntelligence"]["biggestUncertainty"].startswith(
        "Owner approval of the proposed identity contract"
    )
    assert "canonical" not in " ".join(blocked_detail.data["reasons"]).lower()
    assert "gsis" not in " ".join(blocked_detail.data["reasons"]).lower()

    kc = next(row for row in bootstrap.data["rookies"] if row["player"] == "KC Concepcion")
    kc_detail = facade.dynasty_asset(kc["assetId"]).data
    assert kc_detail["nwrScore"] == kc["boardScore"] == 50.0
    assert kc_detail["rookieIntelligence"]["nwrRookieScore"] == 50.0
    assert kc_detail["rookieIntelligence"]["reviewScore"] == kc["reviewScore"]

    assert set(comparison.data) == {"leans", "ranges", "players", "warnings", "bridge"}
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
        "synthesisTrace",
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


def test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NWR_DYNASTY_RANKINGS_ROOT", raising=False)
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="dynasty")
    bootstrap = facade.dynasty_bootstrap().data
    ids = {row["name"]: row["assetId"] for row in bootstrap["assetOptions"]}

    comparison = facade.compare_dynasty_assets([ids["Jeremiyah Love"], ids["Jahmyr Gibbs"]]).data
    bridge = comparison["bridge"]

    assert bridge["mode"] == "ROOKIE_VETERAN"
    assert len(bridge["decisions"]) == 7
    by_key = {row["key"]: row for row in bridge["decisions"]}
    assert by_key["win_now"]["preferred"] == "Jahmyr Gibbs"
    assert by_key["win_now"]["badge"] == "PRODUCTION"
    assert by_key["three_year"]["badge"] == "RESEARCH ONLY"
    assert by_key["long_term"]["badge"] == "RESEARCH ONLY"
    assert by_key["safety"]["preferred"] == "Jahmyr Gibbs"
    assert by_key["uncertainty"]["preferred"] == "Jeremiyah Love"
    assert all(row["projectedPoints"] is not None for row in bridge["immediateProduction"])
    assert "nwrScore" not in json.dumps(bridge)

    detail = facade.dynasty_asset(ids["Jeremiyah Love"]).data
    assert detail["immediateProduction"]["available"] is True
    assert detail["immediateProduction"]["authority"] == "Redraft 2026"

    trade = facade.evaluate_dynasty_trade(
        give=[ids["Jahmyr Gibbs"]],
        receive=[ids["Jeremiyah Love"]],
        team_window="Balanced",
    ).data
    dimensions = {row["code"]: row for row in trade["dimensions"]}
    assert dimensions["D11"]["label"] == "Immediate production context"
    assert dimensions["D12"]["label"] == "Medium-term research outlook"
    assert dimensions["D12"]["confidence"] == "LOW"

    rookie_pair = facade.compare_dynasty_assets([ids["Jeremiyah Love"], ids["Carnell Tate"]]).data
    veteran_pair = facade.compare_dynasty_assets([ids["Jahmyr Gibbs"], ids["CeeDee Lamb"]]).data
    assert rookie_pair["bridge"] is None
    assert veteran_pair["bridge"] is None

    manual = facade.compare_dynasty_assets([ids["De'Zhaun Stribling"], ids["Luke McCaffrey"]]).data[
        "bridge"
    ]
    manual_by_key = {row["key"]: row for row in manual["decisions"]}
    assert manual_by_key["win_now"]["badge"] == "PRODUCTION"
    assert manual_by_key["three_year"]["preferred"] == "INSUFFICIENT EVIDENCE"
    assert manual_by_key["uncertainty"]["preferred"] == "De'Zhaun Stribling"


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


def test_stribling_is_searchable_selectable_comparable_tradeable_and_scenario_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NWR_DYNASTY_RANKINGS_ROOT", raising=False)
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
        workspace_root=tmp_path / "workspace",
    )
    bootstrap = facade.dynasty_bootstrap().data
    stribling = next(
        row for row in bootstrap["assetOptions"] if row["name"] == "De'Zhaun Stribling"
    )
    anchor = next(row for row in bootstrap["assetOptions"] if row["assetType"] == "Current Player")

    assert (
        stribling
        | {
            "assetId": "blocked-rookie:dezhaun-stribling",
            "playerId": "00-0041035",
            "team": "SF",
            "position": "WR",
            "draftRound": 2,
            "overallPick": 33,
            "rank": None,
            "selectable": True,
            "draftEligible": True,
            "modelScoreEligible": False,
            "evidenceBlocked": True,
            "blocked": False,
        }
        == stribling
    )
    assert "stribling" in stribling["name"].casefold()
    assert "dezhaun" in "".join(
        character for character in stribling["name"].casefold() if character.isalnum()
    )

    detail = facade.dynasty_asset(stribling["assetId"]).data
    comparison = facade.compare_dynasty_assets([stribling["assetId"], anchor["assetId"]]).data
    trade = facade.evaluate_dynasty_trade(
        give=[stribling["assetId"]],
        receive=[anchor["assetId"]],
        team_window="Balanced",
    ).data
    saved = facade.save_dynasty_trade(
        scenario_id=None,
        title="Stribling manual-review scenario",
        give=[stribling["assetId"]],
        receive=[anchor["assetId"]],
        team_window="Balanced",
        notes="Missing Rookie Review score remains unknown.",
    ).data

    assert detail["playerId"] == "00-0041035"
    assert detail["nflDraftCapital"] == "NFL Round 2 · Pick 33"
    assert detail["nwrScore"] is None and detail["rank"] is None
    assert detail["modelScoreEligible"] is False and detail["selectable"] is True
    assert all("No admitted" in row["preferred"] for row in comparison["leans"])
    assert any("No admitted Rookie Review score" in warning for warning in comparison["warnings"])
    assert trade["recommendation"] == "INSUFFICIENT_EVIDENCE"
    assert trade["preferredSide"] == "No side"
    assert trade["confidence"] == "LOW"
    assert "UNKNOWN, not zero" in trade["mainUncertainty"]
    assert saved["workspace"]["scenarios"][0]["give"] == [stribling["assetId"]]
    assert bootstrap["rookieReadiness"]["missingFromDraftablePool"] == 0


def test_final_readiness_turns_red_when_draft_cockpit_adapter_drops_stribling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NWR_DYNASTY_RANKINGS_ROOT", raising=False)
    original = DesktopBackendFacade._rookie_records

    def without_stribling(frame: Any) -> list[dict[str, Any]]:
        return [
            row for row in original(frame) if row["assetId"] != "blocked-rookie:dezhaun-stribling"
        ]

    monkeypatch.setattr(DesktopBackendFacade, "_rookie_records", staticmethod(without_stribling))
    readiness = (
        DesktopBackendFacade(
            repo_root=REPO_ROOT,
            mode="dynasty",
        )
        .dynasty_bootstrap()
        .data["rookieReadiness"]
    )

    assert readiness["verdict"] == "RED_NWR_ROOKIE_DRAFT_SAFETY_STILL_UNACCEPTABLE"
    assert readiness["ready"] is False
    assert readiness["missingBySurface"]["draft_cockpit"] == ["blocked-rookie:dezhaun-stribling"]
    assert readiness["surfaceGapAssetIds"] == ["blocked-rookie:dezhaun-stribling"]


def test_final_readiness_turns_red_when_search_and_selection_drop_stribling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NWR_DYNASTY_RANKINGS_ROOT", raising=False)
    original = DesktopBackendFacade._asset_option

    def disable_stribling(row: Any) -> dict[str, Any]:
        option = original(row)
        if option["assetId"] == "blocked-rookie:dezhaun-stribling":
            option = {**option, "searchable": False, "selectable": False, "blocked": True}
        return option

    monkeypatch.setattr(DesktopBackendFacade, "_asset_option", staticmethod(disable_stribling))
    readiness = (
        DesktopBackendFacade(
            repo_root=REPO_ROOT,
            mode="dynasty",
        )
        .dynasty_bootstrap()
        .data["rookieReadiness"]
    )

    assert readiness["ready"] is False
    assert readiness["missingBySurface"]["search"] == ["blocked-rookie:dezhaun-stribling"]
    assert readiness["missingBySurface"]["selectable"] == ["blocked-rookie:dezhaun-stribling"]
    assert readiness["missingBySurface"]["draft_cockpit"] == []
    assert readiness["missingFromDraftablePool"] == 0


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
    reloaded = (
        DesktopBackendFacade(
            repo_root=REPO_ROOT,
            mode="dynasty",
            workspace_root=workspace,
        )
        .list_dynasty_trades()
        .data
    )
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
        "manualAssets",
        "externalConsensus",
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
    assert first.data["manualAssets"] == []
    assert first.data["externalConsensus"] == {
        "authority": "EXTERNAL CONSENSUS — FANTASYPROS",
        "configured": False,
        "manualFallback": "NOT_ADMITTED",
        "message": (
            "FantasyPros API key is not configured. No provider request was attempted; "
            "the existing K/DST manual-draft fallback is not yet admitted."
        ),
    }
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
            "practicalMode",
            "provider",
            "providerLeagueId",
        }
        for row in first.data["presets"]
    )
    assert first.data["health"]["blockedPlayers"] == 2
    assert all(set(row) == {"tone", "title", "message"} for row in first.data["notices"])
    blocked_notice = " ".join(row["message"] for row in first.data["notices"])
    assert "Max Bredeson" in blocked_notice
    assert "Riley Nowakowski" in blocked_notice
    assert "does not infer target or touch shares" in blocked_notice
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
    assert active.data["health"]["status"] == "Ready · 2 blocked players visible"
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
        "positionTier",
        "overallTierLabel",
        "positionTierLabel",
        "sourceAsOf",
        "rookie",
        "overallAdp",
        "expectedPick",
        "expectedRound",
        "nwrAdpGap",
        "valueLabel",
        "timingLabel",
        "makeItBack",
        "adpSource",
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
        assert {
            "schemaVersion",
            "profileId",
            "configured",
            "drafted",
            "boardCells",
            "teams",
            "adp",
            "recommendations",
            "beatAdpPool",
            "fallbackDisclosure",
        }.issubset(active.data["draftBoard"])
        assert len(active.data["draftBoard"]["boardCells"]) == 192
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
    asset = next(row for row in before.data["assetOptions"] if row["assetType"] == "Current Player")

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


def test_redraft_league_switching_isolates_draft_state_and_persists_active_profile(
    tmp_path: Path,
) -> None:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    niners = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Niners"
    ).data["profile"]
    ppr_preset = builtin_presets()[2]
    fantasy = create_profile(
        store,
        LeagueProfile(
            profile_id="fantasy-gamers-template",
            league_name="Fantasy Gamers",
            season=2026,
            team_count=10,
            roster=ppr_preset.roster,
            scoring=ppr_preset.scoring,
            draft=DraftContext(rounds=15, draft_slot=5),
            provider="sleeper",
            provider_league_id="1312983576827920384",
        ),
        league_name="Fantasy Gamers",
    )
    facade.activate_redraft_profile(fantasy.profile_id)
    fantasy_board = facade.redraft_bootstrap()
    drafted_id = fantasy_board.data["rankings"][0]["playerId"]
    facade.mark_redraft_player(profile_id=fantasy.profile_id, player_id=drafted_id, drafted=True)

    facade.activate_redraft_profile(niners["profileId"])
    niners_board = facade.redraft_bootstrap()
    assert niners_board.data["activeProfile"]["leagueName"] == "Niners"
    assert niners_board.data["activeProfile"]["scoring"]["reception"] == 0.5
    assert niners_board.data["draftBoard"]["drafted"] == []
    assert niners_board.data["activeProfile"]["providerLeagueId"] is None

    restarted = DesktopBackendFacade(
        repo_root=REPO_ROOT, mode="redraft", redraft_root=store
    ).redraft_bootstrap()
    assert restarted.data["activeProfileId"] == niners["profileId"]

    facade.activate_redraft_profile(fantasy.profile_id)
    restored = facade.redraft_bootstrap()
    assert restored.data["activeProfile"]["leagueName"] == "Fantasy Gamers"
    assert restored.data["activeProfile"]["teamCount"] == 10
    assert restored.data["activeProfile"]["scoring"]["reception"] == 1.0
    assert restored.data["activeProfile"]["provider"] == "sleeper"
    assert restored.data["activeProfile"]["providerLeagueId"] == "1312983576827920384"
    assert restored.data["draftBoard"]["drafted"] == [drafted_id]


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
