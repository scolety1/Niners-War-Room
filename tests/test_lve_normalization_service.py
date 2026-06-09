from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.lve_normalization_service import (
    FINAL_NORMALIZED_FEATURE_BUCKETS,
    MARKET_ONLY_FEATURES,
    NORMALIZED_FEATURE_HEADER,
    NORMALIZED_FEATURE_RECEIPT_HEADER,
    derive_lve_normalized_feature_receipt_rows,
    derive_lve_normalized_veteran_feature_rows,
    normalized_feature_summary_rows,
    write_lve_normalized_feature_receipt_rows,
    write_lve_normalized_veteran_feature_rows,
)
from src.services.lve_projection_import_service import PROJECTION_SOURCE_DISABLED
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

TEMPLATE_ROOT = Path("templates/real_data_inputs/nflverse_stats_upgrade")


def test_normalization_combines_scoring_role_injury_and_projection(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root)
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_injury_rows(source_root)
    _write_projection_rows(source_root)

    result = derive_lve_normalized_veteran_feature_rows(
        source_root,
        computed_at="2026-08-01T00:00:00Z",
    )
    row = result.rows[0]

    assert result.status == "ready"
    assert row["player_id"] == "p_wr"
    assert row["lve_projection_value"] > 60
    assert row["role_security"] > 80
    assert row["injury_durability"] >= 80
    assert row["private_stat_value"] > 60
    assert row["computed_at"] == "2026-08-01T00:00:00Z"

    receipt_rows = derive_lve_normalized_feature_receipt_rows(source_root).rows
    role_receipt = _receipt_row(receipt_rows, "role_security")
    assert role_receipt["player_name"] == "Receiver One"
    assert role_receipt["position"] == "WR"
    assert role_receipt["team"] == "SF"


def test_normalization_blocks_when_underlying_contract_blocks(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    (source_root / "nflverse_player_stats_weekly.csv").write_text(
        "bad,header\n",
        encoding="utf-8",
    )

    result = derive_lve_normalized_veteran_feature_rows(source_root)

    assert result.status == "blocked"
    assert result.rows == ()
    assert any("CSV header" in issue for issue in result.issues)


def test_normalization_keeps_missing_projection_visible(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root)
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_injury_rows(source_root)

    result = derive_lve_normalized_veteran_feature_rows(source_root)
    row = result.rows[0]

    assert row["missing_data_penalty"] >= 8
    assert row["projection_source_status"] == "missing_projection"
    assert "missing_projection_features" in row["warnings"]


def test_no_nfl_scoring_history_does_not_turn_empty_injury_report_into_perfect_health(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_projection_rows(source_root)

    row = derive_lve_normalized_veteran_feature_rows(source_root).rows[0]
    receipt_rows = derive_lve_normalized_feature_receipt_rows(source_root).rows
    injury = _receipt_row(receipt_rows, "injury_durability")

    assert row["weighted_recent_lve_ppg_score"] == 50.0
    assert row["injury_durability"] == 50.0
    assert injury["warning_status"] == "imputed"
    assert injury["warning_reason"] == "no_injury_report_rows_without_nfl_activity"
    assert injury["imputation_value"] == 50.0


def test_local_baseline_projection_does_not_fill_expected_points(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root)
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_injury_rows(source_root)
    _write_local_baseline_projection_rows(source_root)

    row = derive_lve_normalized_veteran_feature_rows(source_root).rows[0]
    receipt_rows = derive_lve_normalized_feature_receipt_rows(source_root).rows
    expected = _receipt_row(receipt_rows, "expected_lve_points_score")
    role = _receipt_row(receipt_rows, "role_security")

    assert row["expected_lve_points_score"] == 50.0
    assert row["projection_source_status"] == "local_baseline_projection"
    assert row["missing_data_penalty"] >= 4.0
    assert "local_baseline_projection_not_independent" in row["warnings"]
    assert expected["projection_source_status"] == "local_baseline_projection"
    assert expected["warning_status"] == "imputed"
    assert expected["warning_reason"] == "local_baseline_projection_not_independent"
    assert expected["is_missing"] == "true"
    assert role["source_status"] == "derived_real_data"
    assert role["warning_reason"] == ""


def test_local_baseline_projection_alone_cannot_create_decision_ready_confidence(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_local_baseline_projection_rows(source_root)

    row = derive_lve_normalized_veteran_feature_rows(source_root).rows[0]
    receipt_rows = derive_lve_normalized_feature_receipt_rows(source_root).rows
    expected = _receipt_row(receipt_rows, "expected_lve_points_score")
    composite = _receipt_row(receipt_rows, "lve_projection_value")

    assert row["projection_source_status"] == "local_baseline_projection"
    assert row["expected_lve_points_score"] == 50.0
    assert row["confidence"] < 65.0
    assert row["missing_data_penalty"] == 20.0
    assert "local_baseline_projection_not_independent" in row["warnings"]
    assert "missing_lve_scoring_history" in row["warnings"]
    assert expected["warning_status"] == "imputed"
    assert expected["is_missing"] == "true"
    assert composite["warning_reason"] == "local_baseline_projection_not_independent"
    assert composite["is_missing"] == "true"



def test_disabled_projection_is_visible_and_cannot_fill_expected_points(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root)
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_injury_rows(source_root)
    _write_disabled_projection_rows(source_root)

    row = derive_lve_normalized_veteran_feature_rows(source_root).rows[0]
    receipt_rows = derive_lve_normalized_feature_receipt_rows(source_root).rows
    expected = _receipt_row(receipt_rows, "expected_lve_points_score")

    assert row["expected_lve_points_score"] == 50.0
    assert row["projection_source_status"] == PROJECTION_SOURCE_DISABLED
    assert PROJECTION_SOURCE_DISABLED in row["warnings"]
    assert expected["projection_source_status"] == PROJECTION_SOURCE_DISABLED
    assert expected["warning_reason"] == PROJECTION_SOURCE_DISABLED
    assert expected["source_status"] == "neutral_imputation"

def test_normalization_metadata_uses_latest_source_period(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root)
    _write_rows(
        source_root / "nflverse_player_stats_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        [
            {
                "season": "2023",
                "week": "1",
                "player_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "targets": "4",
                "receptions": "3",
                "receiving_yards": "31",
                "receiving_first_downs": "2",
            },
            {
                "season": "2025",
                "week": "18",
                "player_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "targets": "10",
                "receptions": "8",
                "receiving_yards": "100",
                "receiving_tds": "1",
                "receiving_first_downs": "6",
            },
        ],
    )
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_injury_rows(source_root)

    row = derive_lve_normalized_veteran_feature_rows(source_root).rows[0]

    assert row["season"] == "2025"
    assert row["as_of_week"] == "18"


def test_normalization_warns_when_scoring_lags_newer_role_sources(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "nflverse_player_stats_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        [
            {
                "season": "2024",
                "week": "18",
                "player_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "targets": "10",
                "receptions": "8",
                "receiving_yards": "100",
                "receiving_tds": "1",
                "receiving_first_downs": "6",
            }
        ],
    )
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_injury_rows(source_root)
    _write_projection_rows(source_root)

    row = derive_lve_normalized_veteran_feature_rows(source_root).rows[0]

    assert "stale_lve_scoring_source" in row["warnings"]


def test_normalization_summary_and_write(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root)
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_injury_rows(source_root)
    _write_projection_rows(source_root)
    rows = derive_lve_normalized_veteran_feature_rows(source_root).rows
    output_path = tmp_path / "normalized" / "lve_normalized_veteran_features.csv"

    write_lve_normalized_veteran_feature_rows(output_path, rows)
    summary = normalized_feature_summary_rows(rows)

    with output_path.open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == NORMALIZED_FEATURE_HEADER
    assert summary[0]["position"] == "WR"
    assert summary[0]["rows"] == 1
    assert summary[0]["scoring_effect"] == "normalized feature preview only; no model mutation"


def test_normalized_feature_schema_has_final_stats_buckets() -> None:
    header = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["lve_normalized_veteran_features.csv"]
    receipt_header = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[
        "lve_normalized_feature_receipts.csv"
    ]

    assert "efficiency_score" in header
    assert tuple(receipt_header) == NORMALIZED_FEATURE_RECEIPT_HEADER
    assert FINAL_NORMALIZED_FEATURE_BUCKETS == (
        "production",
        "opportunity",
        "role",
        "efficiency",
        "first_down_td_fit",
        "age_window",
        "injury_durability",
    )


def test_feature_receipts_show_raw_normalized_source_and_warning_status(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root)
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_injury_rows(source_root)
    _write_projection_rows(source_root)

    result = derive_lve_normalized_feature_receipt_rows(
        source_root,
        computed_at="2026-08-01T00:00:00Z",
    )
    output_path = tmp_path / "normalized" / "lve_normalized_feature_receipts.csv"
    write_lve_normalized_feature_receipt_rows(output_path, result.rows)

    assert result.status == "ready"
    assert {row["feature_bucket"] for row in result.rows} == set(
        FINAL_NORMALIZED_FEATURE_BUCKETS
    )
    assert not MARKET_ONLY_FEATURES.intersection({str(row["feature_name"]) for row in result.rows})
    for row in result.rows:
        assert row["raw_value"] != ""
        assert 0 <= float(row["normalized_score"]) <= 100
        assert row["source_key"]
        assert row["warning_status"] in {"ready", "review", "imputed", "missing"}
    with output_path.open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == NORMALIZED_FEATURE_RECEIPT_HEADER


def test_missing_projection_receipts_are_imputed_not_fake_raw_stats(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root)
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_injury_rows(source_root)

    rows = derive_lve_normalized_feature_receipt_rows(source_root).rows
    expected = _receipt_row(rows, "expected_lve_points_score")
    composite = _receipt_row(rows, "lve_projection_value")

    assert expected["raw_value"] == ""
    assert expected["normalized_score"] == 50.0
    assert expected["projection_source_status"] == "missing_projection"
    assert expected["warning_status"] == "imputed"
    assert expected["warning_reason"] == "missing_projection_features"
    assert expected["is_missing"] == "true"
    assert composite["warning_status"] == "imputed"


def test_normalization_clamps_feature_boundaries(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(
        source_root,
        receiving_yards="10000",
        receiving_tds="30",
        receiving_first_downs="200",
    )
    _write_snap_rows(source_root)
    _write_participation_rows(source_root)
    _write_depth_rows(source_root)
    _write_injury_rows(source_root)
    _write_projection_rows(
        source_root,
        projected_receiving_yards="8000",
        projected_receiving_tds="40",
        projected_receiving_first_downs="250",
    )

    feature_rows = derive_lve_normalized_feature_receipt_rows(source_root).rows
    wide_row = derive_lve_normalized_veteran_feature_rows(source_root).rows[0]

    assert all(0 <= float(row["normalized_score"]) <= 100 for row in feature_rows)
    assert wide_row["weighted_recent_lve_ppg_score"] == 100.0
    assert wide_row["efficiency_score"] == 100.0


def _copy_templates(tmp_path: Path) -> Path:
    target = tmp_path / "nflverse_stats_upgrade"
    shutil.copytree(TEMPLATE_ROOT, target)
    return target


def _write_player_stats(
    source_root: Path,
    *,
    receiving_yards: str = "100",
    receiving_tds: str = "1",
    receiving_first_downs: str = "6",
) -> None:
    _write_rows(
        source_root / "nflverse_player_stats_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "player_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "targets": "10",
                "receptions": "8",
                "receiving_yards": receiving_yards,
                "receiving_tds": receiving_tds,
                "receiving_first_downs": receiving_first_downs,
            }
        ],
    )


def _write_snap_rows(source_root: Path) -> None:
    _write_rows(
        source_root / "nflverse_snap_counts_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_snap_counts_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "game_id": "2025_01_SF_ARI",
                "gsis_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "offense_snaps": "60",
                "offense_pct": "88",
            }
        ],
    )


def _write_participation_rows(source_root: Path) -> None:
    _write_rows(
        source_root / "nflverse_participation_player_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_participation_player_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "team": "SF",
                "gsis_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "route_participation_proxy": "82",
                "targets": "10",
                "targets_per_dropback_snap_proxy": "0.22",
                "confidence": "90",
            }
        ],
    )


def _write_depth_rows(source_root: Path) -> None:
    _write_rows(
        source_root / "nflverse_depth_chart_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_depth_chart_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "team": "SF",
                "gsis_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "pos_rank": "1",
            }
        ],
    )


def _write_injury_rows(source_root: Path) -> None:
    _write_rows(
        source_root / "nflverse_injuries_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_injuries_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "team": "SF",
                "gsis_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "source_confidence": "90",
            }
        ],
    )


def _write_projection_rows(
    source_root: Path,
    *,
    projected_receiving_yards: str = "1000",
    projected_receiving_tds: str = "8",
    projected_receiving_first_downs: str = "55",
) -> None:
    _write_rows(
        source_root / "projection_raw_import.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["projection_raw_import.csv"],
        [
            {
                "season": "2026",
                "source_id": "ffa",
                "gsis_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "projected_games": "17",
                "projected_receiving_yards": projected_receiving_yards,
                "projected_receiving_tds": projected_receiving_tds,
                "projected_receiving_first_downs": projected_receiving_first_downs,
                "source_updated_at": "2026-08-01T00:00:00Z",
                "confidence": "88",
            }
        ],
    )


def _write_local_baseline_projection_rows(source_root: Path) -> None:
    _write_rows(
        source_root / "projection_raw_import.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["projection_raw_import.csv"],
        [
            {
                "season": "2025",
                "week": "0",
                "projection_scope": "local_baseline_recent_lve",
                "source_id": "local_baseline_from_imported_nflverse_stats",
                "gsis_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "projected_games": "17",
                "projected_receiving_yards": "1700",
                "projected_receiving_tds": "14",
                "projected_receiving_first_downs": "90",
                "source_scoring_format": "LVE_baseline_from_actual_recent_stats",
                "source_updated_at": "2026-08-01T00:00:00Z",
                "confidence": "62",
            }
        ],
    )



def _write_disabled_projection_rows(source_root: Path) -> None:
    _write_rows(
        source_root / "projection_raw_import.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["projection_raw_import.csv"],
        [
            {
                "season": "2026",
                "week": "0",
                "projection_source_status": PROJECTION_SOURCE_DISABLED,
                "source_id": "projection_disabled",
                "gsis_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "projected_games": "17",
                "projected_receiving_yards": "1700",
                "projected_receiving_tds": "14",
                "projected_receiving_first_downs": "90",
                "source_updated_at": "2026-08-01T00:00:00Z",
                "confidence": "90",
            }
        ],
    )

def _write_rows(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _receipt_row(
    rows: tuple[dict[str, object], ...],
    feature_name: str,
) -> dict[str, object]:
    matches = [row for row in rows if row["feature_name"] == feature_name]
    assert matches
    return matches[0]


