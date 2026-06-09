from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from src.services import model_audit_packet_service as audit_service
from src.services.model_audit_packet_service import export_model_audit_packet
from src.services.model_recalibration_service import rankings_are_review_only


def test_export_model_audit_packet_writes_manifest_and_required_files(
    monkeypatch,
    tmp_path: Path,
) -> None:
    model_root = tmp_path / "model"
    model_root.mkdir()
    _write_required_model_sources(model_root)
    monkeypatch.setattr(
        audit_service,
        "build_war_board",
        lambda _pack: SimpleNamespace(rows=[{"player": "A", "overall_rank": 1}]),
    )
    monkeypatch.setattr(
        audit_service,
        "build_team_command_board",
        lambda _pack: SimpleNamespace(roster_rows=[{"player": "B", "cut_risk": 12}]),
    )
    monkeypatch.setattr(
        audit_service,
        "build_named_player_audit",
        lambda _pack, veteran_model_dir=None: SimpleNamespace(
            player_rows=[{"player": "C", "rank": 3}],
            pair_rows=[{"pair": "A vs B", "status": "ready"}],
            receipt_rows=[{"player": "C", "feature": "role", "contribution": 4.2}],
        ),
    )

    packet = export_model_audit_packet(
        tmp_path / "pack",
        export_root=tmp_path / "exports",
        model_source_root=model_root,
        packet_id="phase_1_packet",
    )

    manifest = json.loads(packet.manifest_path.read_text())
    assert manifest["active_model_version"] == "veteran_lve_stats_first_v1_0_0"
    assert manifest["computed_at"] == "2026-05-14T06:15:22Z"
    assert manifest["review_only_status"] is True
    assert manifest["decision_ready_allowed"] is False
    assert manifest["model_recalibration_active"] is True
    assert manifest["trust_status"] == "model_recalibration"
    assert manifest["row_counts"]["full_active_rankings"] == 1
    assert manifest["row_counts"]["visible_war_board_rankings"] == 1
    assert manifest["row_counts"]["niners_roster_rankings"] == 1
    assert manifest["row_counts"]["named_player_audit_rows"] == 1

    exported_files = {entry.file_name for entry in packet.files}
    assert {
        "full_active_rankings.csv",
        "visible_war_board_rankings.csv",
        "niners_roster_rankings.csv",
        "normalized_feature_rows.csv",
        "contribution_receipts.csv",
        "source_coverage_rows.csv",
        "outlier_rows.csv",
        "named_player_audit_rows.csv",
        "named_player_pair_rows.csv",
        "named_player_receipt_rows.csv",
        "forced_release_comparison.csv",
        "confidence_audit.csv",
        "confidence_audit_summary.csv",
        "source_gap_reconciliation_summary.csv",
        "route_participation_gap_summary.csv",
        "decision_checklist.csv",
        "decision_checklist_summary.csv",
        "projection_guardrail_report.csv",
        "sprint4_changelog_from_sprint3_phase20.md",
        "neutral_auditor_prompt.md",
    } <= exported_files


def test_export_model_audit_packet_can_write_movement_reason_export(
    monkeypatch,
    tmp_path: Path,
) -> None:
    model_root = tmp_path / "model"
    model_root.mkdir()
    _write_required_model_sources(model_root)
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "full_active_rankings.csv").write_text(
        "player_id,player_name,overall_rank,keeper_score,model_version,rank_audit\n"
        "p1,Player One,20,60,veteran_lve_stats_first_v1_0_0,sort=old\n",
        encoding="utf-8",
    )
    (model_root / "stats_first_veteran_model_preview_outputs.csv").write_text(
        "player_id,player_name,overall_rank,keeper_score,model_version,computed_at,rank_audit\n"
        "p1,Player One,5,60,veteran_lve_stats_first_v1_0_0,2026-05-14T06:15:22Z,sort=new\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        audit_service,
        "build_war_board",
        lambda _pack: SimpleNamespace(rows=[{"player": "A", "overall_rank": 1}]),
    )
    monkeypatch.setattr(
        audit_service,
        "build_team_command_board",
        lambda _pack: SimpleNamespace(roster_rows=[{"player": "B", "cut_risk": 12}]),
    )
    monkeypatch.setattr(
        audit_service,
        "build_named_player_audit",
        lambda _pack, veteran_model_dir=None: SimpleNamespace(
            player_rows=[],
            pair_rows=[],
            receipt_rows=[],
        ),
    )

    packet = export_model_audit_packet(
        tmp_path / "pack",
        export_root=tmp_path / "exports",
        model_source_root=model_root,
        comparison_baseline=baseline,
        movement_export_name="movement_vs_sprint2_checkpoint.csv",
        packet_id="phase_25_packet",
    )

    manifest = json.loads(packet.manifest_path.read_text())
    movement_file = packet.export_dir / "movement_vs_sprint2_checkpoint.csv"
    movement_text = movement_file.read_text(encoding="utf-8")
    assert "movement_reason" in movement_text
    assert "movement_magnitude" in movement_text
    assert "movement_review_flag" in movement_text
    assert "ranking_surface_change" in movement_text
    assert manifest["row_counts"]["movement_vs_sprint2_checkpoint"] == 1


def test_model_rescue_freeze_keeps_rankings_review_only() -> None:
    assert rankings_are_review_only(calibration_passed=False) is True


def _write_required_model_sources(model_root: Path) -> None:
    (model_root / "stats_first_veteran_model_preview_outputs.csv").write_text(
        "player_id,player_name,model_version,computed_at\n"
        "p1,Player One,veteran_lve_stats_first_v1_0_0,2026-05-14T06:15:22Z\n",
        encoding="utf-8",
    )
    for file_name in (
        "stats_first_normalized_features.csv",
        "stats_first_feature_contributions.csv",
        "stats_first_source_coverage.csv",
        "stats_first_preview_outliers.csv",
    ):
        (model_root / file_name).write_text("player_id,value\np1,1\n", encoding="utf-8")
