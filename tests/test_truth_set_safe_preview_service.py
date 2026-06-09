from __future__ import annotations

import csv
from pathlib import Path

from src.services.lve_normalization_service import NORMALIZED_FEATURE_HEADER
from src.services.truth_set_safe_preview_service import create_truth_set_safe_model_preview


def _write(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    resolved = fieldnames or sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=resolved, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _feature_row(player: str, position: str = "WR") -> dict[str, object]:
    row = {field: "" for field in NORMALIZED_FEATURE_HEADER}
    row.update(
        {
            "season": "2025",
            "player_id": player.lower().replace(" ", "_"),
            "gsis_id": player.lower().replace(" ", "_"),
            "player_name": player,
            "position": position,
            "team": "TST",
            "weighted_recent_lve_ppg_score": 60,
            "expected_lve_points_score": 60,
            "lve_projection_value": 50,
            "projection_source_status": "local_baseline_projection",
            "role_security": 60,
            "workload_earning": 55 if position == "RB" else 50,
            "target_earning_stability": 60,
            "route_role": 60,
            "efficiency_score": 60,
            "first_down_td_fit": 60,
            "age_curve": 80,
            "age_raw": 24,
            "age_bucket": "prime_window",
            "age_warning": "",
            "age_source_status": "derived_real_data",
            "age_interaction_flags": "",
            "injury_durability": 75,
            "private_stat_value": 60,
            "market_liquidity": "",
            "confidence": 70,
            "missing_data_penalty": 4,
            "warnings": "local_baseline_projection_not_independent|missing_participation_proxy",
            "source_version": "test",
            "computed_at": "2026-05-14T00:00:00Z",
            "draft_year": "",
            "draft_round": "",
            "draft_overall": "",
            "experience_bucket": "established_veteran",
            "young_nfl_bridge_prior_score": "",
            "young_nfl_bridge_source": "",
            "young_nfl_bridge_weight": "",
        }
    )
    return row


def test_safe_preview_applies_only_allowed_fields(tmp_path: Path) -> None:
    active_output = tmp_path / "active.csv"
    normalized = tmp_path / "normalized.csv"
    projections = tmp_path / "projections.csv"
    bridge = tmp_path / "bridge.csv"
    injury = tmp_path / "injury.csv"
    market = tmp_path / "market.csv"
    production = tmp_path / "production.csv"

    _write(
        active_output,
        [
            {
                "player_name": "Young WR",
                "overall_rank": "1",
                "private_lve_value": "60",
                "keeper_score": "60",
                "trade_value": "60",
                "confidence_score": "70",
            }
        ],
    )
    _write(normalized, [_feature_row("Young WR")], list(NORMALIZED_FEATURE_HEADER))
    _write(
        projections,
        [
            {
                "player_name": "Young WR",
                "position": "WR",
                "recomputed_lve_points": "120",
                "projection_availability_status": "projection_stat_line_present",
            }
        ],
    )
    _write(
        bridge,
        [
            {
                "player_name": "Young WR",
                "asset_lifecycle": "year_one_nfl_bridge",
                "draft_year": "2025",
                "nfl_draft_round": "1",
                "nfl_draft_pick": "20",
                "draft_capital_prior_score": "90",
                "draft_capital_source_status": "derived_from_round_pick",
            }
        ],
    )
    _write(injury, [{"player_name": "Young WR", "notes": "healthy context"}])
    _write(market, [{"player_name": "Young WR", "trade_value_number": "9999"}])
    _write(
        production,
        [{"player_name": "Young WR", "weighted_recent_lve_ppg_score": "999"}],
    )

    result = create_truth_set_safe_model_preview(
        active_output_path=active_output,
        active_normalized_path=normalized,
        projection_preview_path=projections,
        young_bridge_preview_path=bridge,
        injury_path=injury,
        market_path=market,
        production_path=production,
        output_root=tmp_path / "previews",
        preview_id="safe_preview_test",
        computed_at="2026-05-14T00:00:00Z",
    )

    comparison = result.comparison_rows[0]
    normalized_rows = list(csv.DictReader(result.normalized_path.open(encoding="utf-8")))

    assert "recomputed_projection_lve_points" in str(comparison["source_fields_used"])
    assert "young_bridge_draft_capital_prior" in str(comparison["source_fields_used"])
    assert "production_stat_columns_rejected" in str(comparison["source_fields_rejected"])
    assert normalized_rows[0]["weighted_recent_lve_ppg_score"] == "60"
    assert normalized_rows[0]["projection_source_status"] == "truth_set_projection_recompute"
    assert result.summary["active_outputs_overwritten"] is False


def test_rejected_rb_role_text_is_rb_only(tmp_path: Path) -> None:
    active_output = tmp_path / "active.csv"
    normalized = tmp_path / "normalized.csv"
    projections = tmp_path / "projections.csv"
    empty = tmp_path / "empty.csv"
    production = tmp_path / "production.csv"

    _write(
        active_output,
        [
            {"player_name": "RB One", "overall_rank": "1", "private_lve_value": "60"},
            {"player_name": "WR One", "overall_rank": "2", "private_lve_value": "60"},
        ],
    )
    _write(
        normalized,
        [_feature_row("RB One", "RB"), _feature_row("WR One", "WR")],
        list(NORMALIZED_FEATURE_HEADER),
    )
    _write(
        projections,
        [
            {
                "player_name": "RB One",
                "position": "RB",
                "recomputed_lve_points": "100",
                "projection_availability_status": "projection_stat_line_present",
            },
            {
                "player_name": "WR One",
                "position": "WR",
                "recomputed_lve_points": "100",
                "projection_availability_status": "projection_stat_line_present",
            },
        ],
    )
    _write(empty, [])
    _write(production, [{"player_name": "RB One"}, {"player_name": "WR One"}])

    result = create_truth_set_safe_model_preview(
        active_output_path=active_output,
        active_normalized_path=normalized,
        projection_preview_path=projections,
        young_bridge_preview_path=empty,
        injury_path=empty,
        market_path=empty,
        production_path=production,
        output_root=tmp_path / "previews",
        preview_id="rb_only_rejection",
        computed_at="2026-05-14T00:00:00Z",
    )
    by_player = {row["player_name"]: row for row in result.comparison_rows}

    assert "unsafe_rb_role_text_rejected" in by_player["RB One"]["source_fields_rejected"]
    assert "unsafe_rb_role_text_rejected" not in by_player["WR One"]["source_fields_rejected"]


def test_safe_preview_carries_projection_quality_flags(tmp_path: Path) -> None:
    active_output = tmp_path / "active.csv"
    normalized = tmp_path / "normalized.csv"
    projections = tmp_path / "projections.csv"
    empty = tmp_path / "empty.csv"
    production = tmp_path / "production.csv"

    _write(
        active_output,
        [{"player_name": "Review WR", "overall_rank": "1", "private_lve_value": "80"}],
    )
    _write(normalized, [_feature_row("Review WR")], list(NORMALIZED_FEATURE_HEADER))
    _write(
        projections,
        [
            {
                "player_name": "Review WR",
                "position": "WR",
                "projection_availability_status": "missing_offensive_projection",
                "projection_source_quality_status": "review_needed",
                "projection_source_quality_flags": (
                    "missing_projection|missing_first_down_projection|"
                    "high_active_value_missing_projection"
                ),
            }
        ],
    )
    _write(empty, [])
    _write(production, [{"player_name": "Review WR"}])

    result = create_truth_set_safe_model_preview(
        active_output_path=active_output,
        active_normalized_path=normalized,
        projection_preview_path=projections,
        young_bridge_preview_path=empty,
        injury_path=empty,
        market_path=empty,
        production_path=production,
        output_root=tmp_path / "previews",
        preview_id="projection_quality_flags",
        computed_at="2026-05-14T00:00:00Z",
    )

    comparison = result.comparison_rows[0]
    source_log = result.source_log_rows

    assert "missing_truth_set_projection" in comparison["review_flags"]
    assert "projection_quality_missing_projection" in comparison["review_flags"]
    assert (
        "projection_quality_high_active_value_missing_projection"
        in comparison["review_flags"]
    )
    assert any(
        row["source"] == "projection_quality_high_active_value_missing_projection"
        for row in source_log
    )
