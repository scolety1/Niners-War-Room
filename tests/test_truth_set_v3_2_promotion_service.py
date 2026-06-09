from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_v3_2_promotion_service import (
    CONTEXT_ONLY,
    PROMOTE_TO_ACTIVE,
    REJECTED,
    UNAVAILABLE,
    build_promoted_source_coverage_rows,
    build_truth_set_v3_2_safe_promotion,
    promotion_matrix_rows,
)


def test_promotion_matrix_keeps_restricted_and_context_sources_out_of_private_value() -> None:
    rows = promotion_matrix_rows()
    by_group = {str(row["source_field_group"]): row for row in rows}

    assert by_group["native nflverse production"]["promotion_status"] == PROMOTE_TO_ACTIVE
    assert by_group["derived target share"]["source_status"] == "derived_real_data"
    assert by_group["true route metrics"]["promotion_status"] == UNAVAILABLE
    assert by_group["true route metrics"]["model_usage_status"] == "not_used"
    assert "PFR" in str(by_group["true route metrics"]["restriction"])
    assert by_group["market/liquidity"]["promotion_status"] == CONTEXT_ONLY
    assert by_group["market/liquidity"]["model_usage_status"] == "trade_surface_only"
    assert by_group["manual agent-collected player-stat tables"]["promotion_status"] == REJECTED


def test_promoted_source_coverage_preserves_safe_source_statuses() -> None:
    rows = build_promoted_source_coverage_rows(
        active_coverage_rows=[
            {
                "player_id": "p1",
                "player_name": "Safe Player",
                "position": "WR",
                "team": "TST",
                "production": "review_missing",
                "role_usage": "review_missing",
                "projection": "review_missing",
                "projection_source_status": "missing_projection",
                "injury": "review_missing",
                "age_bio": "ready",
                "market_liquidity": "review_missing",
                "confidence": "50",
            }
        ],
        v3_coverage_rows=[
            _v3_row("Safe Player", "WR", "production", "imported_real_data", "covered"),
            _v3_row("Safe Player", "WR", "role_usage", "derived_real_data", "covered"),
            _v3_row("Safe Player", "WR", "snap_share", "imported_real_data", "covered"),
            _v3_row("Safe Player", "WR", "projection", "derived_real_data", "covered"),
            _v3_row(
                "Safe Player",
                "WR",
                "route_participation",
                "unavailable_free_public",
                "review",
            ),
            _v3_row(
                "Safe Player",
                "WR",
                "injury",
                "unsourced_or_healthy_context",
                "review",
            ),
            _v3_row("Safe Player", "WR", "market_liquidity", "missing_market", "missing"),
        ],
        normalized_rows=[
            {
                "player_name": "Safe Player",
                "position": "WR",
                "projection_source_status": "truth_set_v3_projection_recompute",
                "warnings": (
                    "projection_first_downs_estimated_from_history|"
                    "route_data_unavailable_free_public"
                ),
            }
        ],
    )

    row = rows[0]
    assert row["production"] == "ready"
    assert row["role_usage"] == "ready"
    assert row["projection"] == "ready"
    assert row["projection_source_status"] == "truth_set_v3_projection_recompute"
    assert row["route_metrics_source_status"] == "unavailable_free_public"
    assert row["route_metrics_model_usage"] == "not_used"
    assert row["estimated_first_down_projection_status"] == "estimated_from_history"
    assert row["injury"] == "review"
    assert row["injury_context_policy"] == "does_not_boost_confidence"
    assert row["market_liquidity"] == "review_missing"
    assert row["market_context_policy"] == "trade_context_only_zero_private_value"


def test_promotion_builds_review_only_root_without_using_manual_sources(tmp_path: Path) -> None:
    active_root = tmp_path / "active"
    preview_root = tmp_path / "preview"
    active_root.mkdir()
    preview_root.mkdir()
    _write(
        active_root / "stats_first_source_coverage.csv",
        [
            {
                "player_id": "p1",
                "player_name": "Safe Player",
                "position": "RB",
                "team": "TST",
                "production": "review_missing",
                "role_usage": "review_missing",
                "projection": "review_missing",
                "projection_source_status": "missing_projection",
                "injury": "review_missing",
                "age_bio": "ready",
                "market_liquidity": "review_missing",
                "confidence": "50",
            }
        ],
    )
    _write(active_root / "veteran_player_inputs.csv", [{"player_id": "p1"}])
    _write(
        preview_root / "truth_set_v3_source_coverage.csv",
        [_v3_row("Safe Player", "RB", "production", "imported_real_data", "covered")],
    )
    for filename in (
        "stats_first_normalized_features.csv",
        "stats_first_feature_contributions.csv",
        "stats_first_veteran_model_preview_outputs.csv",
    ):
        _write(
            preview_root / filename,
            [{"player_id": "p1", "player_name": "Safe Player", "position": "RB"}],
        )
    _write(
        preview_root / "truth_set_v3_rejected_field_log.csv",
        [
            {
                "player_name": "Safe Player",
                "position": "RB",
                "field_group": "rejected_agent_production_csv",
                "rejection_reason": "manual table rejected",
            }
        ],
    )

    result = build_truth_set_v3_2_safe_promotion(
        active_model_root=active_root,
        v3_preview_path=preview_root,
        output_root=tmp_path / "out",
        promotion_id="promotion_test",
        computed_at="2026-05-15T00:00:00Z",
    )

    assert result.summary["review_status"] == "review_only"
    assert result.summary["active_rankings_overwritten"] is False
    assert "manual_agent_player_stat_tables" in result.summary["rejected_sources"]
    promoted_rows = _read(result.source_coverage_path)
    assert promoted_rows[0]["production"] == "ready"
    matrix_rows = _read(result.promotion_matrix_path)
    assert any(
        row["source_field_group"] == "manual agent-collected player-stat tables"
        and row["promotion_status"] == REJECTED
        for row in matrix_rows
    )


def _v3_row(
    player: str,
    position: str,
    bucket: str,
    source_status: str,
    coverage_status: str,
) -> dict[str, str]:
    return {
        "player_name": player,
        "position": position,
        "bucket": bucket,
        "source_status": source_status,
        "model_usage": "model_preview_only",
        "coverage_status": coverage_status,
        "fields": "",
        "notes": "",
    }


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = tuple(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
