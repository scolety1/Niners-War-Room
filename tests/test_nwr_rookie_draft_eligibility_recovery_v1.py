from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

from src.services.rookie_draft_eligibility_service import (
    BLOCKED_ROOKIES_RELATIVE,
    BLOCKED_ROOKIES_SHA256,
    ROOKIE_BOARD_RELATIVE,
    ROOKIE_BOARD_SHA256,
    file_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/hq/product/nwr_rookie_draft_eligibility_recovery_v1_20260813"
REQUIRED = {
    "EXECUTIVE_VERDICT.md",
    "STRIBLING_INCIDENT.md",
    "EXISTING_FRAMEWORK_AUDIT.md",
    "ELIGIBILITY_VS_SCORING_CONTRACT.md",
    "LIVE_ROOKIE_OVERLAY.md",
    "FULL_DRAFT_CLASS_RECONCILIATION.csv",
    "BLOCKED_ROOKIE_REFRESH.csv",
    "DRAFT_READINESS_GATE.md",
    "OWNER_ALERT_BEHAVIOR.md",
    "STRIBLING_ACCEPTANCE.md",
    "VALIDATION_RESULTS.md",
    "AUTHORITY_PRESERVATION.md",
    "NEXT_ACTION.md",
}


def _csv(name: str) -> list[dict[str, str]]:
    with (PACKET / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_recovery_packet_is_deterministic_and_complete() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/build_nwr_rookie_draft_eligibility_recovery_v1.py"),
            "--check",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert {path.name for path in PACKET.iterdir() if path.is_file()} == REQUIRED
    assert "GREEN_NWR_ROOKIE_DRAFT_CLASS_COMPLETE_WITH_MANUAL_REVIEW_ASSETS" in (
        PACKET / "EXECUTIVE_VERDICT.md"
    ).read_text(encoding="utf-8")


def test_reconciliation_proves_all_80_assets_are_draftable_without_fake_scores() -> None:
    rows = _csv("FULL_DRAFT_CLASS_RECONCILIATION.csv")
    manual = [row for row in rows if row["model_score_eligible"] == "NO"]
    stribling = next(row for row in rows if row["player_name"] == "De'Zhaun Stribling")

    assert len(rows) == 80
    assert sum(row["model_score_eligible"] == "YES" for row in rows) == 73
    assert len(manual) == 7
    assert all(
        row["searchable"]
        == row["selectable"]
        == row["draftable"]
        == row["detail_available"]
        == row["compare_selectable"]
        == row["trade_selectable"]
        == row["draft_cockpit_selectable"]
        == "YES"
        for row in rows
    )
    assert all(row["frozen_rank"] == row["frozen_score"] == "" for row in manual)
    assert stribling["live_governed_player_id"] == "00-0041035"
    assert (stribling["team"], stribling["draft_round"], stribling["overall_pick"]) == (
        "SF",
        "2",
        "33",
    )


def test_frozen_rookie_authorities_remain_byte_identical() -> None:
    assert file_sha256(ROOT / ROOKIE_BOARD_RELATIVE) == ROOKIE_BOARD_SHA256
    assert file_sha256(ROOT / BLOCKED_ROOKIES_RELATIVE) == BLOCKED_ROOKIES_SHA256


def test_desktop_selection_gate_uses_selectable_not_score_block() -> None:
    decisions = (ROOT / "desktop/apps/dynasty/src/pages/decisions.tsx").read_text(
        encoding="utf-8"
    )
    cockpit = (ROOT / "desktop/apps/dynasty/src/pages/system.tsx").read_text(
        encoding="utf-8"
    )
    rookie_board = (ROOT / "desktop/apps/dynasty/src/pages/research.tsx").read_text(
        encoding="utf-8"
    )
    contract = (ROOT / "desktop/packages/contracts/src/index.ts").read_text(encoding="utf-8")

    assert "return asset.selectable" in decisions
    assert "filter(canSelectAsset)" in decisions
    assert "data.rookieReadiness.draftableAssetIds" in cockpit
    assert "admittedIds.has(row.assetId)" in cockpit
    assert ".filter((row) => row.rank != null && !row.blockedReason)" not in cockpit
    assert 'key: "reviewScore", label: "Review score"' in rookie_board
    for field in ("draftEligible", "modelScoreEligible", "selectable", "scoreStatus"):
        assert field in contract
