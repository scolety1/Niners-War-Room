from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import pytest

from src.services.draft_freeze_service import freeze_draft_pack
from src.services.lve_normalization_service import NORMALIZED_FEATURE_HEADER
from src.services.lve_stats_first_apply_service import (
    STATS_FIRST_APPLY_CONFIRMATION,
    create_stats_first_applied_pack,
)
from src.services.lve_stats_first_preview_service import create_stats_first_model_preview


def test_freeze_draft_pack_exports_boards_and_backups(tmp_path: Path) -> None:
    result = freeze_draft_pack(
        "sample_data/2026_pre_declaration",
        output_root=tmp_path,
        freeze_id="draft_day_fixture",
        allow_review_snapshot=True,
    )

    assert result.freeze_dir.exists()
    assert result.data_pack_backup_dir.exists()
    assert (result.freeze_dir / "FREEZE_LOCK.txt").exists()
    assert (result.data_pack_backup_dir / "fact_rosters.csv").exists()
    assert (result.freeze_dir / "model_output_backup" / "model_outputs.csv").exists()
    assert result.metadata_path.exists()
    assert result.checklist_path.exists()
    assert result.summary_path.exists()
    assert {"war_board", "draft_picks", "decision_readiness_checklist"}.issubset(
        result.export_files
    )
    assert {
        "pack_health_checks",
        "pack_coverage_report",
        "trust_status",
        "final_calibration_gate",
    }.issubset(result.export_files)
    assert "admission_reasons" in result.export_files
    assert "money_decision_certificate" in result.export_files
    assert _read_csv(result.export_files["war_board"])
    assert _read_csv(result.checklist_path)
    certificate = _read_csv(result.export_files["money_decision_certificate"])[0]
    assert certificate["money_decision_status"] == "review_only"
    assert certificate["can_use_for_money_decisions"] == "False"
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "LVE Draft-Day Freeze" in summary
    assert "Artifact type: REVIEW SNAPSHOT - NOT A FINAL BOARD" in summary
    assert "Admission decision: ready" in summary


def test_freeze_metadata_records_model_run_and_no_mutation_policy(tmp_path: Path) -> None:
    result = freeze_draft_pack(
        "sample_data/2026_pre_declaration",
        output_root=tmp_path,
        freeze_id="metadata_fixture",
        allow_review_snapshot=True,
        stats_first_preview_root=tmp_path / "empty_previews",
        stats_first_applied_pack_root=tmp_path / "empty_applied_packs",
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert metadata["freeze_id"] == "metadata_fixture"
    assert metadata["source_data_pack"].endswith("sample_data\\2026_pre_declaration")
    assert metadata["no_live_mutation"] is True
    assert metadata["refresh_after_freeze_allowed"] is False
    assert metadata["roster_count"] == 24
    assert metadata["model_versions"] == []
    assert metadata["trust_status"] == "model_recalibration"
    assert metadata["admission_decision"] == "ready"
    assert metadata["model_recalibration_active"] is True
    assert metadata["model_calibration_passed"] is False
    assert metadata["model_calibration_status"] == "blocked"
    assert metadata["model_calibration_badge"] == "Model Calibration Blocked"
    assert metadata["final_decision_badge"] == "Needs Data"
    assert metadata["final_decision_badge"] != "Decision Ready"
    assert metadata["decision_ready"] is False
    assert metadata["review_snapshot"] is True
    assert "pack_coverage_report" in metadata["exported_boards"]
    assert "admission_reasons" in metadata["exported_boards"]
    assert "money_decision_certificate" in metadata["exported_boards"]
    assert "final_calibration_gate" in metadata["exported_boards"]
    assert metadata["stats_first_backup"]["preview_count"] == 0
    assert metadata["stats_first_backup"]["applied_pack_count"] == 0


def test_freeze_backs_up_stats_first_preview_and_applied_pack_artifacts(
    tmp_path: Path,
) -> None:
    source_pack = tmp_path / "source_pack"
    shutil.copytree("sample_data/2026_pre_declaration", source_pack)
    normalized = tmp_path / "normalized.csv"
    preview_root = tmp_path / "previews"
    applied_root = tmp_path / "applied_packs"
    _write_normalized_rows(normalized, [_normalized_rb_row()])
    create_stats_first_model_preview(normalized, preview_root, preview_id="preview_one")
    create_stats_first_applied_pack(
        source_pack,
        preview_root,
        applied_root,
        preview_id="preview_one",
        applied_pack_id="applied_one",
        confirmation_text=STATS_FIRST_APPLY_CONFIRMATION,
    )

    result = freeze_draft_pack(
        source_pack,
        output_root=tmp_path / "freezes",
        freeze_id="with_stats_first",
        allow_review_snapshot=True,
        stats_first_preview_root=preview_root,
        stats_first_applied_pack_root=applied_root,
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert metadata["stats_first_backup"]["preview_count"] == 1
    assert metadata["stats_first_backup"]["applied_pack_count"] == 1
    assert (
        result.freeze_dir
        / "stats_first_backup"
        / "previews"
        / "preview_one"
        / "stats_first_preview_manifest.json"
    ).exists()
    assert (
        result.freeze_dir
        / "stats_first_backup"
        / "applied_packs"
        / "applied_one"
        / "stats_first_applied_pack_manifest.json"
    ).exists()
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "stats_first_backup" in summary


def test_freeze_refuses_to_overwrite_existing_freeze(tmp_path: Path) -> None:
    freeze_draft_pack(
        "sample_data/2026_pre_declaration",
        output_root=tmp_path,
        freeze_id="same_id",
        allow_review_snapshot=True,
    )

    with pytest.raises(FileExistsError):
        freeze_draft_pack(
            "sample_data/2026_pre_declaration",
            output_root=tmp_path,
            freeze_id="same_id",
            allow_review_snapshot=True,
        )


def test_freeze_blocks_money_decision_freeze_during_model_recalibration(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="review snapshot"):
        freeze_draft_pack(
            "sample_data/2026_pre_declaration",
            output_root=tmp_path,
            freeze_id="blocked_by_recalibration",
        )


def test_freeze_blocks_unadmitted_generated_applied_pack(tmp_path: Path) -> None:
    pack = tmp_path / "zero_applied_pack"
    shutil.copytree("sample_data/2026_pre_declaration", pack)
    _write_applied_pack_manifest(pack, applied_row_count=0)

    with pytest.raises(ValueError, match="not admitted"):
        freeze_draft_pack(pack, output_root=tmp_path / "freezes", freeze_id="blocked")


def test_freeze_allows_review_snapshot_with_explicit_override(tmp_path: Path) -> None:
    pack = tmp_path / "zero_applied_pack"
    shutil.copytree("sample_data/2026_pre_declaration", pack)
    _write_applied_pack_manifest(pack, applied_row_count=0)

    result = freeze_draft_pack(
        pack,
        output_root=tmp_path / "freezes",
        freeze_id="review_snapshot",
        allow_review_snapshot=True,
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert metadata["decision_ready"] is False
    assert metadata["review_snapshot"] is True
    assert metadata["admission_decision"] == "blocked"
    certificate = _read_csv(result.export_files["money_decision_certificate"])[0]
    assert certificate["money_decision_status"] == "review_only"
    assert certificate["can_use_for_money_decisions"] == "False"
    assert certificate["model_calibration_passed"] == "False"
    assert certificate["model_calibration_badge"] == "Model Calibration Blocked"
    assert certificate["final_decision_badge"] == "Needs Data"
    assert "freeze again" in certificate["next_action"]
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "REVIEW SNAPSHOT - NOT A FINAL BOARD" in summary
    assert "Do not use it as the draft-day board" in summary
    assert "Admission decision: blocked" in summary


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_applied_pack_manifest(path: Path, *, applied_row_count: int) -> None:
    (path / "model_applied_pack_manifest.json").write_text(
        json.dumps(
            {
                "applied_pack_id": path.name,
                "applied_row_count": applied_row_count,
                "promotion_candidate_count": applied_row_count,
                "scoring_effect": "generated applied pack copy",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _normalized_rb_row() -> dict[str, str]:
    row = {column: "" for column in NORMALIZED_FEATURE_HEADER}
    row.update(
        {
            "season": "2026",
            "as_of_week": "18",
            "player_id": "p_achane",
            "gsis_id": "p_achane",
            "player_name": "De'Von Achane",
            "position": "RB",
            "team": "MIA",
            "weighted_recent_lve_ppg_score": "90",
            "expected_lve_points_score": "92",
            "lve_projection_value": "91",
            "role_security": "84",
            "workload_earning": "86",
            "target_earning_stability": "70",
            "route_role": "68",
            "first_down_td_fit": "88",
            "age_curve": "86",
            "injury_durability": "78",
            "private_stat_value": "90",
            "confidence": "90",
            "missing_data_penalty": "0",
            "warnings": "",
            "source_version": "fixture",
            "computed_at": "2026-08-01T00:00:00Z",
        }
    )
    return row


def _write_normalized_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NORMALIZED_FEATURE_HEADER)
        writer.writeheader()
        writer.writerows(rows)
