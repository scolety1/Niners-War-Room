from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.lve_normalization_service import NORMALIZED_FEATURE_HEADER
from src.services.lve_stats_first_apply_service import (
    STATS_FIRST_APPLIED_PACK_MANIFEST_FILE,
    STATS_FIRST_APPLY_CONFIRMATION,
    create_stats_first_applied_pack,
    stats_first_applied_pack_review_rows,
    stats_first_applied_pack_snapshot_rows,
)
from src.services.lve_stats_first_preview_service import create_stats_first_model_preview
from src.services.lve_stats_first_veteran_formula_service import STATS_FIRST_MODEL_VERSION

SAMPLE_PACK = Path("sample_data/2026_pre_declaration")


def test_apply_workflow_writes_new_pack_copy_only(tmp_path: Path) -> None:
    source_pack = _copy_pack(tmp_path)
    preview_root = tmp_path / "previews"
    output_root = tmp_path / "applied"
    normalized = tmp_path / "normalized.csv"
    _write_normalized_rows(normalized, [_normalized_rb_row()])
    create_stats_first_model_preview(normalized, preview_root, preview_id="preview_one")
    original_model_outputs = (source_pack / "model_outputs.csv").read_text(encoding="utf-8")

    result = create_stats_first_applied_pack(
        source_pack,
        preview_root,
        output_root,
        preview_id="preview_one",
        applied_pack_id="Stats First Apply",
        confirmation_text=STATS_FIRST_APPLY_CONFIRMATION,
        created_at="2026-08-02T00:00:00Z",
    )

    assert result.created is True
    assert result.applied_pack_id == "stats_first_apply"
    assert result.applied_row_count == 1
    assert (source_pack / "model_outputs.csv").read_text(encoding="utf-8") == original_model_outputs
    applied_rows = _read_csv(result.applied_pack_path / "model_outputs.csv")
    achane = next(row for row in applied_rows if row["player_id"] == "p_achane")
    assert achane["model_version"] == STATS_FIRST_MODEL_VERSION
    assert achane["notes"].startswith("Applied from stats-first preview copy")
    assert float(achane["keeper_score"]) > 80
    assert achane["overall_rank"] == "1"
    assert achane["position_rank"] == "1"
    assert achane["position_rank_label"] == "RB1"
    assert achane["cross_position_replacement_baseline"] != ""
    assert achane["lve_lineup_demand_adjustment"] != ""
    assert achane["market_trade_value"] != ""
    assert achane["market_edge_score"] != ""
    assert achane["market_edge_label"] != ""
    assert achane["market_score"] == achane["market_trade_value"]
    assert "sort=keeper_score_desc" in achane["rank_audit"]
    manifest = result.manifest_path.read_text(encoding="utf-8")
    assert "source pack and selected pack were not overwritten" in manifest


def test_apply_workflow_requires_confirmation(tmp_path: Path) -> None:
    source_pack = _copy_pack(tmp_path)
    preview_root = tmp_path / "previews"
    normalized = tmp_path / "normalized.csv"
    _write_normalized_rows(normalized, [_normalized_rb_row()])
    create_stats_first_model_preview(normalized, preview_root, preview_id="preview_one")

    result = create_stats_first_applied_pack(
        source_pack,
        preview_root,
        tmp_path / "applied",
        preview_id="preview_one",
        confirmation_text="yes",
    )

    assert result.created is False
    assert result.status == "blocked"
    assert not result.applied_pack_path.exists()
    assert "Confirmation text" in result.message


def test_apply_workflow_blocks_when_preview_has_no_ready_rows(tmp_path: Path) -> None:
    source_pack = _copy_pack(tmp_path)
    preview_root = tmp_path / "previews"
    normalized = tmp_path / "normalized.csv"
    _write_normalized_rows(
        normalized,
        [_normalized_rb_row(confidence="35", warnings="missing_projection_features")],
    )
    create_stats_first_model_preview(normalized, preview_root, preview_id="blocked_preview")

    result = create_stats_first_applied_pack(
        source_pack,
        preview_root,
        tmp_path / "applied",
        preview_id="blocked_preview",
        confirmation_text=STATS_FIRST_APPLY_CONFIRMATION,
    )

    assert result.created is False
    assert "No review-ready preview rows" in result.message


def test_apply_workflow_blocks_duplicate_applied_pack_id(tmp_path: Path) -> None:
    source_pack = _copy_pack(tmp_path)
    preview_root = tmp_path / "previews"
    normalized = tmp_path / "normalized.csv"
    _write_normalized_rows(normalized, [_normalized_rb_row()])
    create_stats_first_model_preview(normalized, preview_root, preview_id="preview_one")

    first = create_stats_first_applied_pack(
        source_pack,
        preview_root,
        tmp_path / "applied",
        preview_id="preview_one",
        applied_pack_id="same",
        confirmation_text=STATS_FIRST_APPLY_CONFIRMATION,
    )
    second = create_stats_first_applied_pack(
        source_pack,
        preview_root,
        tmp_path / "applied",
        preview_id="preview_one",
        applied_pack_id="same",
        confirmation_text=STATS_FIRST_APPLY_CONFIRMATION,
    )

    assert first.created is True
    assert second.created is False
    assert "already exists" in second.message


def test_applied_pack_snapshot_and_review_rows(tmp_path: Path) -> None:
    source_pack = _copy_pack(tmp_path)
    preview_root = tmp_path / "previews"
    output_root = tmp_path / "applied"
    normalized = tmp_path / "normalized.csv"
    _write_normalized_rows(normalized, [_normalized_rb_row()])
    create_stats_first_model_preview(normalized, preview_root, preview_id="preview_one")
    create_stats_first_applied_pack(
        source_pack,
        preview_root,
        output_root,
        preview_id="preview_one",
        applied_pack_id="review_me",
        confirmation_text=STATS_FIRST_APPLY_CONFIRMATION,
    )

    snapshots = stats_first_applied_pack_snapshot_rows(output_root)
    reviews = stats_first_applied_pack_review_rows(output_root)

    assert snapshots[0]["applied_pack_id"] == "review_me"
    assert snapshots[0]["applied_row_count"] == 1
    assert reviews[0]["review_status"] in {"ready", "review"}
    manifest_path = (
        Path(str(snapshots[0]["applied_pack_path"]))
        / STATS_FIRST_APPLIED_PACK_MANIFEST_FILE
    )
    assert manifest_path.exists()


def _copy_pack(tmp_path: Path) -> Path:
    target = tmp_path / "source_pack"
    shutil.copytree(SAMPLE_PACK, target)
    return target


def _normalized_rb_row(
    *,
    confidence: str = "90",
    warnings: str = "",
) -> dict[str, str]:
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
            "confidence": confidence,
            "missing_data_penalty": "0",
            "warnings": warnings,
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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
