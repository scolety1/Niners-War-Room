from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.model_v4_preview_engine_service import (
    V4_PREVIEW_OUTPUT_HEADER,
    V4_RECEIPT_HEADER,
)
from src.services.model_v4_wr_normalization_audit_service import (
    WR_NORMALIZATION_AUDIT_HEADER,
    run_model_v4_wr_normalization_audit,
)


def test_wr_normalization_audit_reconciles_raw_and_normalized_rows(
    tmp_path: Path,
) -> None:
    preview_path = tmp_path / "preview.csv"
    receipts_path = tmp_path / "receipts.csv"
    source_root = tmp_path / "source_reports"
    _write(
        preview_path,
        V4_PREVIEW_OUTPUT_HEADER,
        [
            _preview_row(
                "Puka Nacua",
                47.5,
                warnings=(
                    "route_participation_unavailable|estimated_from_history|"
                    "projection_first_downs_estimated_from_history"
                ),
            ),
            _preview_row("Bijan Robinson", 76.5, position="RB"),
            _preview_row("Jahmyr Gibbs", 75.0, position="RB"),
        ],
    )
    _write(
        receipts_path,
        V4_RECEIPT_HEADER,
        [
            _receipt_row(
                "Puka Nacua",
                "production",
                40.0,
                10.4,
                raw={"lve_points_no_first_downs": 120.0},
            ),
            _receipt_row(
                "Puka Nacua",
                "first_down_scoring_fit",
                50.0,
                6.0,
                raw={"first_downs": 50, "first_down_points": 20.0},
            ),
            _receipt_row(
                "Puka Nacua",
                "usage_opportunity",
                30.0,
                7.2,
                raw={
                    "target_share": 0.25,
                    "weighted_opportunities": 122.5,
                    "red_zone_carries": 0,
                    "red_zone_targets": 12,
                    "goal_line_carries": 0,
                    "goal_line_targets": 3,
                    "sub_scores": {
                        "target_share": 25.0,
                        "weighted_opportunities": 35.0,
                    },
                },
            ),
            _receipt_row(
                "Puka Nacua",
                "snap_proxy_role",
                80.0,
                4.8,
                raw={"snap_share": 0.8},
                warning="snap_share_proxy_only_not_route_participation",
            ),
            _receipt_row(
                "Puka Nacua",
                "projection",
                75.0,
                7.5,
                raw={
                    "recomputed_lve_points": 225.0,
                    "recomputed_lve_points_no_first_downs": 205.0,
                    "first_down_projection_status": "estimated_from_history",
                },
            ),
            _receipt_row(
                "Puka Nacua",
                "age_dropoff",
                94.0,
                11.28,
                raw={"age": 24, "age_bucket": "prime_window"},
            ),
            _receipt_row("Puka Nacua", "young_player_prior", 0.0, 0.0),
            _receipt_row("Bijan Robinson", "usage_opportunity", 70.0, 16.8),
            _receipt_row("Bijan Robinson", "projection", 90.0, 9.0),
            _receipt_row("Jahmyr Gibbs", "usage_opportunity", 68.0, 16.32),
            _receipt_row("Jahmyr Gibbs", "projection", 88.0, 8.8),
        ],
    )
    _write_source_rows(source_root)

    result = run_model_v4_wr_normalization_audit(
        players=("Puka Nacua",),
        preview_outputs_path=preview_path,
        receipts_path=receipts_path,
        source_report_root=source_root,
        output_csv_path=tmp_path / "wr.csv",
        output_md_path=tmp_path / "wr.md",
    )

    assert _header(result.csv_path) == WR_NORMALIZATION_AUDIT_HEADER
    row = result.rows[0]
    assert row["latest_production_season"] == "2024"
    assert row["production_lve_points_no_first_downs"] == "120.00"
    assert row["production_normalized_score"] == "40.00"
    assert "math consistent but low" in row["production_normalization_assessment"]
    assert "route data unavailable" in row["route_data_effect"]
    assert "estimated from history" in row["first_down_projection_effect"]
    assert result.summary["confirmed_normalization_bug_rows"] == 0
    assert "Phase 5G WR Production" in result.markdown_path.read_text(
        encoding="utf-8"
    )


def test_wr_normalization_audit_flags_confirmed_mismatch(tmp_path: Path) -> None:
    preview_path = tmp_path / "preview.csv"
    receipts_path = tmp_path / "receipts.csv"
    source_root = tmp_path / "source_reports"
    _write(
        preview_path,
        V4_PREVIEW_OUTPUT_HEADER,
        [_preview_row("CeeDee Lamb", 55.0)],
    )
    _write(
        receipts_path,
        V4_RECEIPT_HEADER,
        [
            _receipt_row(
                "CeeDee Lamb",
                "production",
                80.0,
                20.8,
                raw={"lve_points_no_first_downs": 120.0},
            ),
            _receipt_row("CeeDee Lamb", "usage_opportunity", 70.0, 16.8),
        ],
    )
    _write_source_rows(source_root)

    result = run_model_v4_wr_normalization_audit(
        players=("CeeDee Lamb",),
        preview_outputs_path=preview_path,
        receipts_path=receipts_path,
        source_report_root=source_root,
        output_csv_path=tmp_path / "wr.csv",
        output_md_path=tmp_path / "wr.md",
    )

    assert "confirmed normalization mismatch" in result.rows[0][
        "production_normalization_assessment"
    ]
    assert result.summary["confirmed_normalization_bug_rows"] == 1


def _preview_row(
    player: str,
    value: float,
    *,
    position: str = "WR",
    warnings: str = "",
) -> dict[str, object]:
    return {
        "player": player,
        "position": position,
        "nfl_team": "TST",
        "lifecycle": "established_veteran",
        "truth_set_group": "fixture",
        "source_priority": "critical",
        "dynasty_asset_value": value,
        "confidence": 80,
        "confidence_label": "usable",
        "component_scores": "{}",
        "component_contributions": "{}",
        "review_warnings": warnings,
        "unavailable_sections": "",
        "review_status": "review_only",
        "formula_version": "test",
        "preview_engine_version": "test",
    }


def _receipt_row(
    player: str,
    component: str,
    normalized_score: float,
    contribution: float,
    *,
    raw: dict[str, object] | None = None,
    warning: str = "",
    source_status: str = "imported_real_data",
) -> dict[str, object]:
    return {
        "player": player,
        "position": "WR",
        "component": component,
        "raw_fields_used": "fixture",
        "raw_values": json.dumps(raw or {}),
        "normalized_score": normalized_score,
        "source_status": source_status,
        "contribution": contribution,
        "weight": 1,
        "warning": warning,
        "unavailable_reason": "",
        "review_only": True,
    }


def _write(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_source_rows(source_root: Path) -> None:
    fieldnames = (
        "truth_set_player_name",
        "player_name",
        "position",
        "season",
        "source_status",
    )
    for filename in (
        "truth_set_v3_production_player_season.csv",
        "truth_set_v3_usage_player_season.csv",
        "truth_set_v3_snap_share_player_season.csv",
    ):
        _write(
            source_root / filename,
            fieldnames,
            [
                {
                    "truth_set_player_name": "Puka Nacua",
                    "player_name": "Puka Nacua",
                    "position": "WR",
                    "season": 2024,
                    "source_status": "imported_real_data",
                },
                {
                    "truth_set_player_name": "CeeDee Lamb",
                    "player_name": "CeeDee Lamb",
                    "position": "WR",
                    "season": 2024,
                    "source_status": "imported_real_data",
                },
            ],
        )


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
