from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.lve_normalization_service import NORMALIZED_FEATURE_HEADER
from src.services.lve_stats_first_preview_service import (
    STATS_FIRST_PREVIEW_CONTRIBUTIONS_FILE,
    STATS_FIRST_PREVIEW_OUTPUT_FILE,
    create_stats_first_model_preview,
    stats_first_preview_review_rows,
    stats_first_preview_review_summary_rows,
    stats_first_preview_snapshot_rows,
)
from src.services.lve_stats_first_veteran_formula_service import STATS_FIRST_MODEL_VERSION


def test_create_stats_first_preview_writes_isolated_outputs(tmp_path: Path) -> None:
    normalized = tmp_path / "lve_normalized_veteran_features.csv"
    output_root = tmp_path / "previews"
    _write_normalized_rows(normalized, [_normalized_row()])

    result = create_stats_first_model_preview(
        normalized,
        output_root,
        preview_id="preview_one",
        computed_at="2026-08-01T00:00:00Z",
    )

    assert result.created is True
    assert result.row_count == 1
    assert result.output_path.name == STATS_FIRST_PREVIEW_OUTPUT_FILE
    assert result.contribution_path.name == STATS_FIRST_PREVIEW_CONTRIBUTIONS_FILE
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["model_version"] == STATS_FIRST_MODEL_VERSION
    assert manifest["apply_boundary"].startswith("preview_only")

    output_rows = _read_csv(result.output_path)
    contribution_rows = _read_csv(result.contribution_path)
    assert output_rows[0]["player_id"] == "wr_one"
    assert output_rows[0]["model_version"] == STATS_FIRST_MODEL_VERSION
    assert any(row["component"] == "private_lve_value" for row in contribution_rows)


def test_preview_creation_does_not_touch_live_model_outputs(tmp_path: Path) -> None:
    normalized = tmp_path / "lve_normalized_veteran_features.csv"
    live_model_outputs = tmp_path / "model_outputs.csv"
    output_root = tmp_path / "previews"
    live_model_outputs.write_text("player_id,keeper_score\nlive,1\n", encoding="utf-8")
    _write_normalized_rows(normalized, [_normalized_row()])

    create_stats_first_model_preview(normalized, output_root, preview_id="preview_one")

    assert live_model_outputs.read_text(encoding="utf-8") == "player_id,keeper_score\nlive,1\n"
    assert not (tmp_path / STATS_FIRST_PREVIEW_OUTPUT_FILE).exists()


def test_preview_creation_blocks_bad_normalized_header(tmp_path: Path) -> None:
    normalized = tmp_path / "bad.csv"
    normalized.write_text("player_id,player_name\nx,Y\n", encoding="utf-8")

    result = create_stats_first_model_preview(normalized, tmp_path / "previews")

    assert result.created is False
    assert "missing required columns" in result.message
    assert not result.preview_path.exists()


def test_preview_snapshot_and_review_rows(tmp_path: Path) -> None:
    normalized = tmp_path / "lve_normalized_veteran_features.csv"
    output_root = tmp_path / "previews"
    _write_normalized_rows(
        normalized,
        [
            _normalized_row(player_id="wr_ready", confidence="90"),
            _normalized_row(
                player_id="wr_review",
                confidence="63",
                warnings="missing_projection_features",
            ),
        ],
    )
    create_stats_first_model_preview(normalized, output_root, preview_id="preview_one")

    snapshots = stats_first_preview_snapshot_rows(output_root)
    review_rows = stats_first_preview_review_rows(output_root)
    summary = stats_first_preview_review_summary_rows(review_rows)

    assert snapshots[0]["preview_id"] == "preview_one"
    assert snapshots[0]["review_status"] == "review"
    assert {row["review_status"] for row in review_rows} == {"ready", "review"}
    assert next(row for row in summary if row["review_status"] == "ready")["rows"] == 1
    assert next(row for row in summary if row["review_status"] == "review")["rows"] == 1


def test_preview_duplicate_id_is_rejected(tmp_path: Path) -> None:
    normalized = tmp_path / "lve_normalized_veteran_features.csv"
    output_root = tmp_path / "previews"
    _write_normalized_rows(normalized, [_normalized_row()])

    first = create_stats_first_model_preview(normalized, output_root, preview_id="preview_one")
    second = create_stats_first_model_preview(normalized, output_root, preview_id="preview_one")

    assert first.created is True
    assert second.created is False
    assert "already exists" in second.message


def test_empty_preview_summary_requests_preview() -> None:
    summary = stats_first_preview_review_summary_rows([])

    assert summary == [
        {
            "review_status": "needed",
            "rows": 0,
            "next_action": "Create a stats-first preview from normalized veteran features.",
        }
    ]


def _normalized_row(
    *,
    player_id: str = "wr_one",
    confidence: str = "88",
    warnings: str = "",
) -> dict[str, str]:
    values = {column: "" for column in NORMALIZED_FEATURE_HEADER}
    values.update(
        {
            "season": "2026",
            "as_of_week": "18",
            "player_id": player_id,
            "gsis_id": player_id,
            "player_name": "Receiver One",
            "position": "WR",
            "team": "SF",
            "weighted_recent_lve_ppg_score": "82",
            "expected_lve_points_score": "83",
            "lve_projection_value": "82",
            "role_security": "84",
            "workload_earning": "55",
            "target_earning_stability": "82",
            "route_role": "84",
            "first_down_td_fit": "80",
            "age_curve": "80",
            "injury_durability": "80",
            "private_stat_value": "82",
            "confidence": confidence,
            "missing_data_penalty": "0",
            "warnings": warnings,
            "source_version": "fixture",
            "computed_at": "2026-08-01T00:00:00Z",
        }
    )
    return values


def _write_normalized_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NORMALIZED_FEATURE_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
