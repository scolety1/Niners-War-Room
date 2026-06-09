from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.lve_projection_import_service import (
    PROJECTION_FEATURE_HEADER,
    PROJECTION_SOURCE_DISABLED,
    PROJECTION_SOURCE_INDEPENDENT,
    PROJECTION_SOURCE_LOCAL_BASELINE,
    derive_lve_projection_feature_rows,
    projection_import_summary_rows,
    write_lve_projection_feature_rows,
)
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

TEMPLATE_ROOT = Path("templates/real_data_inputs/nflverse_stats_upgrade")


def test_projection_rescore_uses_lve_no_ppr_and_direct_first_downs(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_projection_rows(
        source_root,
        [
            {
                "season": "2026",
                "week": "0",
                "projection_scope": "season",
                "source_id": "ffa",
                "source_player_id": "wr1",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "projected_games": "17",
                "projected_targets": "120",
                "projected_receptions": "80",
                "projected_receiving_yards": "1000",
                "projected_receiving_tds": "8",
                "projected_receiving_first_downs": "55",
                "projected_fumbles_lost": "1",
                "source_updated_at": "2026-08-01T00:00:00Z",
                "confidence": "90",
            }
        ],
    )

    result = derive_lve_projection_feature_rows(source_root)
    row = result.rows[0]

    assert result.status == "ready"
    assert row["lve_projected_points"] == 153.0
    assert row["first_down_estimation_method"] == "direct_partial"
    assert "first_downs_estimated" not in row["warnings"]
    assert row["scoring_effect"] == "projection rescore only; no model mutation"



def test_projection_import_marks_independent_source_status(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_projection_rows(
        source_root,
        [
            {
                "season": "2026",
                "projection_scope": "season",
                "source_id": "ffa",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "projected_games": "17",
                "projected_receiving_yards": "1000",
                "projected_receiving_tds": "8",
                "projected_receiving_first_downs": "55",
            }
        ],
    )

    row = derive_lve_projection_feature_rows(source_root).rows[0]

    assert row["projection_source_status"] == PROJECTION_SOURCE_INDEPENDENT


def test_projection_import_quarantines_local_baseline_source_status(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_projection_rows(
        source_root,
        [
            {
                "season": "2026",
                "projection_scope": "local_baseline_recent_lve",
                "source_id": "local_baseline_from_imported_nflverse_stats",
                "source_scoring_format": "LVE_baseline_from_actual_recent_stats",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "projected_games": "17",
                "projected_receiving_yards": "1000",
                "projected_receiving_tds": "8",
                "projected_receiving_first_downs": "55",
            }
        ],
    )

    row = derive_lve_projection_feature_rows(source_root).rows[0]

    assert row["projection_source_status"] == PROJECTION_SOURCE_LOCAL_BASELINE


def test_projection_import_respects_disabled_source_status(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_projection_rows(
        source_root,
        [
            {
                "season": "2026",
                "projection_source_status": PROJECTION_SOURCE_DISABLED,
                "source_id": "projection_disabled",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "projected_games": "17",
                "projected_receiving_yards": "1000",
                "projected_receiving_tds": "8",
                "projected_receiving_first_downs": "55",
            }
        ],
    )

    row = derive_lve_projection_feature_rows(source_root).rows[0]

    assert row["projection_source_status"] == PROJECTION_SOURCE_DISABLED

def test_projection_rescore_estimates_missing_first_downs(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_projection_rows(
        source_root,
        [
            {
                "season": "2026",
                "projection_scope": "season",
                "source_id": "ffa",
                "player_name": "Runner One",
                "position": "RB",
                "team": "DET",
                "projected_games": "17",
                "projected_rushing_attempts": "200",
                "projected_rushing_yards": "900",
                "projected_rushing_tds": "7",
                "projected_targets": "50",
                "projected_receiving_yards": "300",
                "projected_receiving_tds": "2",
                "confidence": "88",
            }
        ],
    )

    row = derive_lve_projection_feature_rows(source_root).rows[0]

    assert row["projected_rushing_first_downs"] == 46.0
    assert row["projected_receiving_first_downs"] == 15.0
    assert row["lve_projected_points"] == 180.4
    assert row["first_down_estimation_method"] == "estimated"
    assert "first_downs_estimated" in row["warnings"]
    assert row["confidence"] < 88


def test_projection_import_blocks_bad_header(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    (source_root / "projection_raw_import.csv").write_text("bad,header\n", encoding="utf-8")

    result = derive_lve_projection_feature_rows(source_root)

    assert result.status == "blocked"
    assert result.rows == ()
    assert result.issues[0].issue == "Projection import header does not match the Phase 7 contract."


def test_projection_import_blocks_non_numeric_stat(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_projection_rows(
        source_root,
        [
            {
                "season": "2026",
                "source_id": "ffa",
                "player_name": "Bad Row",
                "position": "WR",
                "projected_receiving_yards": "a lot",
            }
        ],
    )

    result = derive_lve_projection_feature_rows(source_root)

    assert result.status == "blocked"
    assert "projected_receiving_yards must be numeric." in {
        issue.issue for issue in result.issues
    }


def test_projection_summary_and_write(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_projection_rows(
        source_root,
        [
            {
                "season": "2026",
                "source_id": "ffa",
                "player_name": "QB One",
                "position": "QB",
                "projected_games": "17",
                "projected_passing_yards": "4000",
                "projected_passing_tds": "30",
                "projected_interceptions": "10",
                "source_updated_at": "2026-08-01T00:00:00Z",
            }
        ],
    )
    result = derive_lve_projection_feature_rows(source_root)
    output_path = tmp_path / "projection" / "lve_projection_features.csv"

    write_lve_projection_feature_rows(output_path, result.rows)
    summary = projection_import_summary_rows(result.rows)

    with output_path.open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == PROJECTION_FEATURE_HEADER
    assert result.rows[0]["lve_projected_points"] == 213.33
    assert summary[0]["position"] == "QB"
    assert summary[0]["rows"] == 1


def _copy_templates(tmp_path: Path) -> Path:
    target = tmp_path / "nflverse_stats_upgrade"
    shutil.copytree(TEMPLATE_ROOT, target)
    return target


def _write_projection_rows(source_root: Path, rows: list[dict[str, str]]) -> None:
    with (source_root / "projection_raw_import.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["projection_raw_import.csv"],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

