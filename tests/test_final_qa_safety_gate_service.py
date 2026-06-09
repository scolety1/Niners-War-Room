from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from src.services.draft_freeze_service import freeze_draft_pack
from src.services.final_qa_safety_gate_service import (
    build_final_qa_safety_gate_audit,
    safety_gate_audit_rows,
    safety_gate_audit_summary_row,
)
from src.services.lve_normalization_service import NORMALIZED_FEATURE_HEADER
from src.services.lve_stats_first_apply_service import (
    STATS_FIRST_APPLY_CONFIRMATION,
    create_stats_first_applied_pack,
)
from src.services.lve_stats_first_preview_service import create_stats_first_model_preview


def test_final_qa_audit_marks_critical_calibration_gaps_as_blocked(
    tmp_path: Path,
) -> None:
    report = build_final_qa_safety_gate_audit(
        "sample_data/2026_pre_declaration",
        stats_first_preview_root=tmp_path / "missing_previews",
        stats_first_applied_pack_root=tmp_path / "missing_applied",
        draft_freeze_root=tmp_path / "missing_freezes",
    )
    summary = safety_gate_audit_summary_row(report)
    rows = safety_gate_audit_rows(report)

    assert report.status == "blocked"
    assert summary["money_decision_gate"] == "hold"
    assert summary["calibration_badge"] == "Model Calibration Blocked"
    assert summary["final_decision_badge"] == "Needs Data"
    assert summary["final_decision_badge"] != "Decision Ready"
    assert summary["model_calibration_passed"] is False
    assert {row["gate"] for row in rows} == {
        "final_model_calibration",
        "selected_pack_decision_readiness",
        "stats_first_preview_boundary",
        "stats_first_apply_boundary",
        "draft_freeze_gate",
        "no_silent_mutation_policy",
    }
    assert next(row for row in rows if row["gate"] == "selected_pack_decision_readiness")[
        "status"
    ] == "review"
    assert next(row for row in rows if row["gate"] == "final_model_calibration")[
        "status"
    ] == "blocked"


def test_final_qa_audit_remains_review_only_during_recalibration(
    tmp_path: Path,
) -> None:
    source_pack = _copy_pack(tmp_path)
    preview_root = tmp_path / "previews"
    applied_root = tmp_path / "applied"
    freeze_root = tmp_path / "freezes"
    normalized = tmp_path / "normalized.csv"
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
    freeze_draft_pack(
        source_pack,
        output_root=freeze_root,
        freeze_id="final_freeze",
        allow_review_snapshot=True,
        stats_first_preview_root=preview_root,
        stats_first_applied_pack_root=applied_root,
    )

    report = build_final_qa_safety_gate_audit(
        source_pack,
        stats_first_preview_root=preview_root,
        stats_first_applied_pack_root=applied_root,
        draft_freeze_root=freeze_root,
    )

    assert report.status == "blocked"
    assert safety_gate_audit_summary_row(report)["money_decision_gate"] == "hold"
    assert safety_gate_audit_summary_row(report)["model_calibration_passed"] is False
    assert safety_gate_audit_summary_row(report)["final_decision_badge"] != "Decision Ready"
    rows = safety_gate_audit_rows(report)
    assert next(row for row in rows if row["gate"] == "final_model_calibration")[
        "status"
    ] == "blocked"
    assert next(row for row in rows if row["gate"] == "stats_first_preview_boundary")[
        "status"
    ] == "ready"
    assert next(row for row in rows if row["gate"] == "stats_first_apply_boundary")[
        "status"
    ] == "ready"
    assert next(row for row in rows if row["gate"] == "selected_pack_decision_readiness")[
        "status"
    ] == "review"


def test_final_qa_audit_blocks_malformed_preview_boundary(tmp_path: Path) -> None:
    preview_root = tmp_path / "previews"
    preview_dir = preview_root / "bad_preview"
    preview_dir.mkdir(parents=True)
    (preview_dir / "stats_first_preview_manifest.json").write_text(
        json.dumps(
            {
                "preview_id": "bad_preview",
                "output_file": "stats_first_veteran_model_preview_outputs.csv",
                "apply_boundary": "can overwrite live outputs",
            }
        ),
        encoding="utf-8",
    )
    (preview_dir / "stats_first_veteran_model_preview_outputs.csv").write_text(
        "player_id,player_name,position,confidence_score,warning_status,risk_flags\n",
        encoding="utf-8",
    )

    report = build_final_qa_safety_gate_audit(
        "sample_data/2026_pre_declaration",
        stats_first_preview_root=preview_root,
        stats_first_applied_pack_root=tmp_path / "missing_applied",
        draft_freeze_root=tmp_path / "missing_freezes",
    )
    rows = safety_gate_audit_rows(report)

    assert report.status == "blocked"
    preview_gate = next(row for row in rows if row["gate"] == "stats_first_preview_boundary")
    assert preview_gate["status"] == "blocked"
    assert "preview-only boundary" in preview_gate["detail"]


def test_final_qa_audit_blocks_freeze_without_lock_evidence(tmp_path: Path) -> None:
    freeze_dir = tmp_path / "freezes" / "bad_freeze"
    freeze_dir.mkdir(parents=True)
    (freeze_dir / "model_run_metadata.json").write_text(
        json.dumps(
            {
                "decision_ready": True,
                "review_snapshot": False,
                "no_live_mutation": False,
                "refresh_after_freeze_allowed": False,
            }
        ),
        encoding="utf-8",
    )

    report = build_final_qa_safety_gate_audit(
        "sample_data/2026_pre_declaration",
        stats_first_preview_root=tmp_path / "missing_previews",
        stats_first_applied_pack_root=tmp_path / "missing_applied",
        draft_freeze_root=tmp_path / "freezes",
    )
    rows = safety_gate_audit_rows(report)

    assert report.status == "blocked"
    freeze_gate = next(row for row in rows if row["gate"] == "draft_freeze_gate")
    assert freeze_gate["status"] == "blocked"
    assert "lock/no-mutation/certificate" in freeze_gate["detail"]


def _copy_pack(tmp_path: Path) -> Path:
    target = tmp_path / "source_pack"
    shutil.copytree("sample_data/2026_pre_declaration", target)
    return target


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
