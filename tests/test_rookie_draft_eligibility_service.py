from __future__ import annotations

import csv
from copy import deepcopy
from pathlib import Path

import pytest

from src.services.rookie_draft_eligibility_service import (
    BLOCKED_ROOKIES_RELATIVE,
    BLOCKED_ROOKIES_SHA256,
    GREEN_COMPLETE_MANUAL,
    LIVE_IDENTITY_RELATIVE,
    RED_UNSAFE,
    ROOKIE_BOARD_RELATIVE,
    ROOKIE_BOARD_SHA256,
    YELLOW_IDENTITY_GAPS,
    build_rookie_draft_eligibility_overlay,
    file_sha256,
    load_rookie_draft_eligibility_overlay,
    reconcile_rookie_draft_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
SURFACES = (
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


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_full_official_class_is_complete_and_keeps_score_eligibility_separate() -> None:
    overlay = load_rookie_draft_eligibility_overlay(repo_root=ROOT)

    assert overlay.errors == ()
    assert overlay.summary == overlay.summary | {
        "verdict": GREEN_COMPLETE_MANUAL,
        "ready": True,
        "official_drafted": 80,
        "position_counts": {"QB": 10, "RB": 12, "WR": 36, "TE": 22},
        "exact_identity": 80,
        "scored": 73,
        "manual_review": 7,
        "unresolved": 0,
        "missing_from_registry": 0,
        "missing_from_draftable_pool": 0,
        "duplicate_asset_ids": 0,
        "refresh_available": 7,
    }
    assert len(overlay.rows) == 80
    assert all(row["asset_exists"] and row["searchable"] for row in overlay.rows)
    assert all(row["selectable"] and row["draftable"] for row in overlay.rows)


def test_stribling_is_exact_draftable_and_unscored_without_fake_values() -> None:
    overlay = load_rookie_draft_eligibility_overlay(repo_root=ROOT)
    row = next(row for row in overlay.rows if row["player_name"] == "De'Zhaun Stribling")

    assert row["asset_id"] == "blocked-rookie:dezhaun-stribling"
    assert row["live_governed_player_id"] == "00-0041035"
    assert row["live_player_id_namespace"] == "GSIS"
    assert (row["team"], row["position"], row["draft_round"], row["overall_pick"]) == (
        "SF",
        "WR",
        2,
        33,
    )
    assert row["authority_status"] == "UNSCORED_MANUAL_REVIEW"
    assert row["draft_eligible"] and row["selectable"] and row["draftable"]
    assert not row["model_score_eligible"]
    assert row["frozen_rank"] is None
    assert row["frozen_score"] is None
    assert row["refresh_available"]


def test_exact_identity_update_never_mutates_frozen_rookie_authority() -> None:
    before_board = file_sha256(ROOT / ROOKIE_BOARD_RELATIVE)
    before_blockers = file_sha256(ROOT / BLOCKED_ROOKIES_RELATIVE)

    load_rookie_draft_eligibility_overlay(repo_root=ROOT)

    assert before_board == file_sha256(ROOT / ROOKIE_BOARD_RELATIVE) == ROOKIE_BOARD_SHA256
    assert (
        before_blockers
        == file_sha256(ROOT / BLOCKED_ROOKIES_RELATIVE)
        == BLOCKED_ROOKIES_SHA256
    )


def test_unique_draft_asset_remains_selectable_when_exact_player_identity_is_unresolved() -> None:
    rookie = _rows(ROOT / ROOKIE_BOARD_RELATIVE)
    live = _rows(ROOT / LIVE_IDENTITY_RELATIVE)
    blockers = _rows(ROOT / BLOCKED_ROOKIES_RELATIVE)
    target = next(row for row in live if row["draft_name"] == "De'Zhaun Stribling")
    target["player_id"] = ""

    overlay = build_rookie_draft_eligibility_overlay(rookie, live, blockers)
    row = next(row for row in overlay.rows if row["player_name"] == "De'Zhaun Stribling")

    assert overlay.errors == ()
    assert overlay.summary["verdict"] == YELLOW_IDENTITY_GAPS
    assert overlay.summary["unresolved"] == 1
    assert row["authority_status"] == "BLOCKED_IDENTITY"
    assert row["draft_eligibility_basis"] == "UNIQUE_GOVERNED_OFFICIAL_DRAFT_ASSET"
    assert row["draftable"] and row["selectable"]
    assert row["frozen_score"] is None


def test_runtime_reconciliation_uses_official_pick_and_rejects_name_only_mismatch() -> None:
    rookie = _rows(ROOT / ROOKIE_BOARD_RELATIVE)
    live = deepcopy(_rows(ROOT / LIVE_IDENTITY_RELATIVE))
    blockers = _rows(ROOT / BLOCKED_ROOKIES_RELATIVE)
    pick_33 = next(row for row in live if row["draft_pick"] == "33")
    pick_33["draft_name"] = "Different Player"

    overlay = build_rookie_draft_eligibility_overlay(rookie, live, blockers)

    assert any("Official pick 33 identity receipt mismatch" in error for error in overlay.errors)
    assert overlay.summary["ready"] is False


@pytest.mark.parametrize("missing_surface", SURFACES)
def test_post_composition_gate_fails_when_stribling_is_missing_from_one_surface(
    missing_surface: str,
) -> None:
    overlay = load_rookie_draft_eligibility_overlay(repo_root=ROOT)
    stribling_id = "blocked-rookie:dezhaun-stribling"
    official_ids = [str(row["asset_id"]) for row in overlay.rows]
    surfaces = {surface: list(official_ids) for surface in SURFACES}
    surfaces[missing_surface].remove(stribling_id)

    readiness = reconcile_rookie_draft_readiness(
        overlay.rows,
        surface_asset_ids=surfaces,
        source_errors=overlay.errors,
    )

    assert readiness["verdict"] == RED_UNSAFE
    assert readiness["ready"] is False
    assert readiness["missing_by_surface"][missing_surface] == [stribling_id]
    assert readiness["surface_gap_asset_ids"] == [stribling_id]
    assert all(
        not missing
        for surface, missing in readiness["missing_by_surface"].items()
        if surface != missing_surface
    )


def test_post_composition_gate_rejects_a_duplicate_hidden_by_set_membership() -> None:
    overlay = load_rookie_draft_eligibility_overlay(repo_root=ROOT)
    stribling_id = "blocked-rookie:dezhaun-stribling"
    official_ids = [str(row["asset_id"]) for row in overlay.rows]
    surfaces = {surface: list(official_ids) for surface in SURFACES}
    surfaces["draft_cockpit"].append(stribling_id)

    readiness = reconcile_rookie_draft_readiness(
        overlay.rows,
        surface_asset_ids=surfaces,
    )

    assert readiness["verdict"] == RED_UNSAFE
    assert readiness["duplicate_by_surface"]["draft_cockpit"] == [stribling_id]
    assert readiness["surface_gap_asset_ids"] == [stribling_id]
