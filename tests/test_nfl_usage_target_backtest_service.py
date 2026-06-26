from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd

from src.services.nfl_usage_target_backtest_service import (
    FEATURE_FIELDS,
    ablation_rows,
    backtest_result_rows,
    build_joined_backtest_panel,
    leakage_report_rows,
    position_summary_rows,
    promotion_recommendation_rows,
)


def _features_fixture() -> pd.DataFrame:
    rows = []
    for idx in range(30):
        rows.append(
            {
                "season": 2023,
                "player_id": f"p{idx}",
                "player_name": f"Player {idx}",
                "position": "RB" if idx < 15 else "WR",
                "team": "SF",
                "targets": idx,
                "carries": 30 - idx,
                "receptions": idx // 2,
                "touches": 30,
                "opportunities": 30,
                "rushing_yards": 300 - idx,
                "receiving_yards": idx * 10,
                "receiving_air_yards": idx * 8,
                "receiving_yards_after_catch": idx * 5,
                "rushing_first_downs": 10,
                "receiving_first_downs": idx // 3,
                "offense_snaps": 400,
                "offense_pct": 0.5,
                "red_zone_carries": idx % 5,
                "red_zone_targets": idx % 4,
                "red_zone_touches": idx % 6,
                "inside_10_carries": idx % 3,
                "inside_10_targets": idx % 2,
                "inside_10_touches": idx % 4,
                "inside_5_carries": idx % 2,
                "inside_5_targets": idx % 2,
                "inside_5_touches": idx % 3,
            }
        )
    return pd.DataFrame(rows)


def _labels_fixture() -> pd.DataFrame:
    rows = []
    for idx in range(30):
        rows.append(
            {
                "target_season": 2024,
                "player_id": f"p{idx}",
                "player_name": f"Player {idx}",
                "position": "RB" if idx < 15 else "WR",
                "next_season_nwr_points": float(idx * 10),
                "next_season_nwr_points_per_game": float(idx),
                "next_season_games": 10,
                "next_season_position_rank": 30 - idx,
                "next_season_top_qb12": 0,
                "next_season_top_rb12": 1 if idx < 12 else 0,
                "next_season_top_rb24": 1 if idx < 15 else 0,
                "next_season_top_wr12": 1 if 15 <= idx < 27 else 0,
                "next_season_top_wr24": 1 if idx >= 15 else 0,
                "next_season_top_wr36": 1 if idx >= 15 else 0,
                "next_season_top_te12": 0,
                "next_season_starter_level_by_position": "RB1" if idx < 12 else "DEPTH",
                "next_season_flex_relevant_rb_wr_te": 1,
            }
        )
    return pd.DataFrame(rows)


def test_backtest_join_enforces_feature_season_n_to_target_n_plus_1() -> None:
    joined = build_joined_backtest_panel(_features_fixture(), _labels_fixture())

    assert not joined.empty
    assert (joined["target_season"] == joined["feature_season"] + 1).all()
    assert joined["leakage_status"].eq("PASS_FEATURE_SEASON_N_TARGET_N_PLUS_1").all()
    assert joined["model_input_allowed"].eq("no").all()
    assert joined["app_wiring_allowed"].eq("no").all()


def test_backtest_results_and_reports_have_valid_review_only_statuses() -> None:
    joined = build_joined_backtest_panel(_features_fixture(), _labels_fixture())
    results = pd.DataFrame(backtest_result_rows(joined))

    assert set(FEATURE_FIELDS) <= set(results["field_name"])
    assert results["leakage_status"].eq("PASS").all()
    assert results["model_input_allowed"].eq("no").all()

    ablation = pd.DataFrame(ablation_rows(results))
    leakage = pd.DataFrame(leakage_report_rows(joined))
    position = pd.DataFrame(position_summary_rows(joined))
    recommendations = pd.DataFrame(promotion_recommendation_rows(results))

    assert not ablation.empty
    assert leakage["status"].eq("PASS").all()
    assert not position.empty
    assert recommendations["model_input_allowed"].eq("no").all()
    assert recommendations["app_wiring_allowed"].eq("no").all()
    assert recommendations["model_candidate_status"].eq("NO_ACTIVE_MODEL_CANDIDATE").all()


def test_expanded_historical_artifacts_load_and_remain_review_only() -> None:
    historical_root = Path("docs/hq/data_sources/nfl_usage/historical_panel")
    target_root = Path("docs/hq/data_sources/nfl_usage/target_backtest")
    source_summary = pd.read_csv(
        historical_root / "historical_usage_expanded_source_summary_v0.csv"
    )
    coverage = pd.read_csv(
        historical_root / "historical_usage_expanded_field_coverage_matrix_v0.csv"
    )
    manifest = pd.read_csv(historical_root / "historical_usage_expanded_panel_manifest_v0.csv")
    target_coverage = pd.read_csv(
        target_root / "nfl_usage_expanded_target_label_coverage_summary_v0.csv"
    )
    results = pd.read_csv(target_root / "nfl_usage_expanded_target_backtest_results_v0.csv")
    leakage = pd.read_csv(target_root / "nfl_usage_expanded_target_backtest_leakage_report_v0.csv")
    final_recs = pd.read_csv(target_root / "nfl_usage_final_promotion_recommendations_v0.csv")

    assert {"player_stats", "snap_counts", "pbp"} <= set(source_summary["source_family"])
    assert not coverage.empty
    assert manifest["committed_to_git"].astype(str).str.lower().eq("no").all()
    assert manifest["raw_payload_included"].astype(str).str.lower().eq("no").all()
    assert target_coverage["leakage_safe"].eq("yes").all()
    assert results["leakage_status"].eq("PASS").all()
    assert leakage["status"].eq("PASS").all()
    assert final_recs["model_input_allowed"].eq("no").all()
    assert final_recs["app_wiring_allowed"].eq("no").all()


def test_expanded_recommendations_keep_licensed_route_gaps_blocked() -> None:
    final_recs = pd.read_csv(
        "docs/hq/data_sources/nfl_usage/target_backtest/"
        "nfl_usage_final_promotion_recommendations_v0.csv"
    )
    gaps = final_recs[final_recs["field_name"].isin(["true_routes_run", "true_tprr", "true_yprr"])]

    assert set(gaps["field_name"]) == {"true_routes_run", "true_tprr", "true_yprr"}
    assert gaps["recommended_final_status"].eq("LICENSED_DATA_GAP").all()
    assert gaps["approved_for_model_candidate_pending_manual_review"].eq("no").all()


def test_no_raw_shared_runtime_paths_are_tracked() -> None:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    blocked_fragments = [
        "NWR_SHARED_DATA",
        "NWR_LOCAL_SECRETS",
        "local_exports",
        "nfl_usage_cache",
        "runtime.json",
    ]

    assert not any(fragment in result.stdout for fragment in blocked_fragments)
