from __future__ import annotations

from src.services.nfl_usage_data_loader_service import (
    APP_WIRING_ALLOWED,
    MODEL_INPUT_ALLOWED,
    blocked_fields,
    build_core_coverage_summary_rows,
    build_core_field_inventory_rows,
    build_core_validation_report_rows,
    load_core_source,
)


def test_core_loader_fails_closed_without_live_pull() -> None:
    result = load_core_source("player_stats", skip_live=True)

    assert result.status == "DRY_RUN_BLOCKED_NO_LIVE_PULL"
    assert result.rows == ()
    assert result.raw_cache_root.drive == "C:"


def test_blocked_fields_reject_rank_market_projection_value_language() -> None:
    fields = [
        "targets",
        "receiving_yards",
        "adp",
        "market_value",
        "analyst_blurb",
        "fantasy_points_ppr",
    ]

    assert blocked_fields(fields) == [
        "adp",
        "analyst_blurb",
        "fantasy_points_ppr",
        "market_value",
    ]


def test_core_inventory_labels_flags_as_no() -> None:
    rows = build_core_field_inventory_rows(
        {
            "player_stats": ["season", "targets", "market_value"],
            "snap_counts": ["offense_snaps", "offense_pct"],
        }
    )

    assert all(row["model_input_allowed"] == MODEL_INPUT_ALLOWED for row in rows)
    assert all(row["app_wiring_allowed"] == APP_WIRING_ALLOWED for row in rows)
    assert next(row for row in rows if row["field_name"] == "market_value")[
        "field_status"
    ] == "BLOCKED"
    assert next(row for row in rows if row["field_name"] == "targets")[
        "field_type"
    ] == "TRUE_FACTUAL_FIELD"


def test_core_summary_and_validation_reports_loadable_rows() -> None:
    results = [
        load_core_source("snap_counts", skip_live=True),
        load_core_source("player_stats", skip_live=True),
        load_core_source("pbp", skip_live=True),
    ]

    coverage = build_core_coverage_summary_rows(results)
    validation = build_core_validation_report_rows(results)

    assert len(coverage) == 3
    assert len(validation) == 3
    assert {row["raw_data_tracked"] for row in coverage} == {"no"}
    assert {row["validation_status"] for row in validation} == {"YELLOW"}
