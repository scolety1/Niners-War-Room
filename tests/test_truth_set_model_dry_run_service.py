from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_model_dry_run_service import (
    build_truth_set_model_dry_run,
    write_truth_set_model_dry_run,
)


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _base_feature(player_name: str, position: str = "WR") -> dict[str, object]:
    return {
        "season": "2025",
        "player_id": player_name.lower().replace(" ", "_"),
        "gsis_id": player_name.lower().replace(" ", "_"),
        "player_name": player_name,
        "position": position,
        "team": "TST",
        "weighted_recent_lve_ppg_score": 60,
        "expected_lve_points_score": 60,
        "lve_projection_value": 50,
        "projection_source_status": "local_baseline_projection",
        "role_security": 60,
        "workload_earning": 50,
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
    }


def test_dry_run_uses_recomputed_projection_without_production(tmp_path: Path) -> None:
    active = tmp_path / "active.csv"
    features = tmp_path / "features.csv"
    projections = tmp_path / "projections.csv"
    bridge = tmp_path / "bridge.csv"
    production = tmp_path / "production.csv"
    injury = tmp_path / "injury.csv"
    market = tmp_path / "market.csv"

    _write(
        active,
        [{"player_name": "Player A", "private_lve_value": "60", "confidence_score": "70"}],
    )
    _write(features, [_base_feature("Player A"), _base_feature("Player B")])
    _write(
        projections,
        [
            {
                "player_name": "Player A",
                "position": "WR",
                "nfl_team": "TST",
                "recomputed_lve_points": "200",
                "supplied_projected_points": "300",
                "first_down_projection_status": "estimated_missing",
                "projection_availability_status": "projection_stat_line_present",
            },
            {
                "player_name": "Player B",
                "position": "WR",
                "nfl_team": "TST",
                "recomputed_lve_points": "100",
                "projection_availability_status": "projection_stat_line_present",
            },
        ],
    )
    _write(bridge, [])
    _write(production, [{"player_name": "Player A", "bad_column": "bad"}])
    _write(injury, [{"player_name": "Player A", "notes": "context only"}])
    _write(market, [{"player_name": "Player A", "trade_value_number": "1000"}])

    result = build_truth_set_model_dry_run(
        active_output_path=active,
        normalized_features_path=features,
        projection_preview_path=projections,
        young_bridge_preview_path=bridge,
        production_clean_path=production,
        injury_path=injury,
        trade_liquidity_path=market,
    )
    row = result.rows[0]

    assert "recomputed_projection_lve_points" in str(row["source_fields_used"])
    assert "production_stat_columns_rejected" in str(row["source_fields_rejected"])
    assert "market_excluded_from_private_value" in str(row["source_fields_rejected"])
    assert "injury_excluded_from_private_value" in str(row["source_fields_rejected"])
    assert result.summary["projection_recompute_rows_used"] == 2
    assert result.rejected_rows[0]["source"] == "production"


def test_young_bridge_prior_only_applies_to_eligible_players(tmp_path: Path) -> None:
    active = tmp_path / "active.csv"
    features = tmp_path / "features.csv"
    projections = tmp_path / "projections.csv"
    bridge = tmp_path / "bridge.csv"
    empty = tmp_path / "empty.csv"

    _write(
        active,
        [{"player_name": "Young WR", "private_lve_value": "60", "confidence_score": "70"}],
    )
    _write(features, [_base_feature("Young WR")])
    _write(
        projections,
        [
            {
                "player_name": "Young WR",
                "position": "WR",
                "nfl_team": "TST",
                "recomputed_lve_points": "100",
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
    _write(empty, [])

    result = build_truth_set_model_dry_run(
        active_output_path=active,
        normalized_features_path=features,
        projection_preview_path=projections,
        young_bridge_preview_path=bridge,
        production_clean_path=empty,
        injury_path=empty,
        trade_liquidity_path=empty,
    )

    assert "young_bridge_draft_capital_prior" in str(result.rows[0]["source_fields_used"])


def test_writer_uses_expected_header(tmp_path: Path) -> None:
    output = tmp_path / "dry_run.csv"
    write_truth_set_model_dry_run(
        output,
        (
            {
                "player_name": "Player",
                "position": "WR",
                "nfl_team": "TST",
                "current_active_model_value": 50,
                "truth_set_preview_model_value": 51,
                "delta": 1,
                "delta_reason": "projection recompute",
                "current_confidence": 70,
                "truth_set_preview_confidence": 71,
                "confidence_impact": "unchanged",
                "source_fields_used": "recomputed_projection_lve_points",
                "source_fields_rejected": "production_stat_columns_rejected",
                "large_change_flag": "no",
                "review_flags": "",
            },
        ),
    )

    assert output.read_text(encoding="utf-8").startswith("player_name,position,nfl_team")
