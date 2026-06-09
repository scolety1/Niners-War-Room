from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.player_comparison_service import build_player_compare_options, compare_players


def test_compare_kyren_vs_elite_rb_fixture_highlights_gap(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _append_player(
        model_dir,
        "kyren_fixture",
        "Kyren Williams",
        "RB",
        age=26.0,
        league_rank=18,
    )
    _append_player(
        model_dir,
        "elite_rb_fixture",
        "Elite RB Fixture",
        "RB",
        age=23.0,
        league_rank=6,
    )
    _append_features(
        model_dir,
        "kyren_fixture",
        "RB",
        {
            "lve_projection_value": 94,
            "role_security": 86,
            "age_curve": 64,
            "first_down_td_fit": 96,
            "injury_durability": 72,
            "touch_share": 88,
            "high_value_touches": 94,
            "goal_line_short_yardage_role": 96,
            "receiving_role_no_ppr_adjusted": 68,
            "rush_efficiency_creation": 86,
            "first_down_conversion_profile": 94,
        },
    )
    _append_features(
        model_dir,
        "elite_rb_fixture",
        "RB",
        {
            "lve_projection_value": 96,
            "role_security": 94,
            "age_curve": 92,
            "first_down_td_fit": 92,
            "injury_durability": 86,
            "touch_share": 95,
            "high_value_touches": 92,
            "goal_line_short_yardage_role": 91,
            "receiving_role_no_ppr_adjusted": 84,
            "rush_efficiency_creation": 90,
            "first_down_conversion_profile": 90,
        },
    )

    report = compare_players(
        "sample_data/2026_pre_declaration",
        "kyren_fixture",
        "elite_rb_fixture",
        veteran_model_dir=model_dir,
    )

    assert not report.issues
    keeper_row = _score_row(report.score_rows, "Keeper")
    assert keeper_row["leader"] == "Elite RB Fixture"
    assert any(
        row["formula_feature_name"] in {"age_curve", "touch_share", "injury_durability"}
        for row in report.gap_driver_rows
    )


def test_compare_jsn_vs_tee_fixture_separates_market_from_stats(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _append_player(
        model_dir,
        "jsn_fixture",
        "Jaxon Smith-Njigba",
        "WR",
        age=24.0,
        league_rank=5,
    )
    _append_player(
        model_dir,
        "tee_fixture",
        "Tee Higgins",
        "WR",
        age=27.0,
        league_rank=28,
    )
    _append_features(
        model_dir,
        "jsn_fixture",
        "WR",
        {
            "lve_projection_value": 88,
            "role_security": 90,
            "age_curve": 93,
            "market_liquidity": 99,
            "target_earning_stability": 88,
            "target_share": 88,
            "route_participation": 91,
            "targets_per_route_run": 89,
            "yards_per_route_run": 88,
            "first_downs_per_route": 88,
            "injury_durability": 84,
        },
    )
    _append_features(
        model_dir,
        "tee_fixture",
        "WR",
        {
            "lve_projection_value": 94,
            "role_security": 86,
            "age_curve": 80,
            "market_liquidity": 86,
            "target_earning_stability": 92,
            "target_share": 92,
            "route_participation": 86,
            "targets_per_route_run": 92,
            "yards_per_route_run": 94,
            "first_downs_per_route": 91,
            "injury_durability": 78,
        },
    )

    report = compare_players(
        "sample_data/2026_pre_declaration",
        "jsn_fixture",
        "tee_fixture",
        veteran_model_dir=model_dir,
    )

    assert not report.issues
    trade_row = _score_row(report.score_rows, "Trade Liquidity")
    private_row = _score_row(report.score_rows, "Private LVE")
    assert trade_row["leader"] == "Jaxon Smith-Njigba"
    assert private_row["leader"] == "Tee Higgins"
    assert (
        _market_edge(report.market_edge_rows, "Jaxon Smith-Njigba")
        == "strong_negative_edge_market_higher"
    )
    assert any(
        row["formula_feature_name"] == "market_liquidity_proxy"
        and row["gap_leader"] == "Jaxon Smith-Njigba"
        for row in report.gap_driver_rows
    )
    assert any(
        row["formula_feature_name"] == "yards_per_route_run"
        and row["gap_leader"] == "Tee Higgins"
        for row in report.gap_driver_rows
    )


def test_compare_prefers_active_stats_first_data_pack_outputs(tmp_path: Path) -> None:
    pack_dir = tmp_path / "active_pack"
    shutil.copytree(Path("sample_data/2026_pre_declaration"), pack_dir)
    _write_rows(
        pack_dir / "model_outputs.csv",
        [
            {
                "snapshot_date": "2026-pre-draft",
                "player_id": "active_a",
                "player_name": "Active Stats A",
                "position": "WR",
                "private_score": "88",
                "market_score": "76",
                "war_score": "86",
                "keeper_score": "87",
                "drop_candidate_score": "18",
                "veteran_base_value": "88",
                "win_now_value": "90",
                "dynasty_hold_value": "86",
                "horizon_retention_score": "86",
                "trade_value": "80",
                "market_trade_value": "76",
                "market_edge_score": "12",
                "lve_format_fit": "88",
                "confidence_score": "84",
                "warning_status": "ready",
                "warning_reasons": "",
                "risk_flags": "",
                "upside_flags": "stable_target_earner",
                "floor_flags": "secure_role",
                "model_version": "veteran_lve_stats_first_test",
            },
            {
                "snapshot_date": "2026-pre-draft",
                "player_id": "active_b",
                "player_name": "Active Stats B",
                "position": "WR",
                "private_score": "82",
                "market_score": "90",
                "war_score": "83",
                "keeper_score": "81",
                "drop_candidate_score": "30",
                "veteran_base_value": "82",
                "win_now_value": "80",
                "dynasty_hold_value": "84",
                "horizon_retention_score": "84",
                "trade_value": "88",
                "market_trade_value": "90",
                "market_edge_score": "-8",
                "lve_format_fit": "82",
                "confidence_score": "80",
                "warning_status": "model_warning",
                "warning_reasons": "wr_unstable_role",
                "risk_flags": "wr_unstable_role",
                "upside_flags": "",
                "floor_flags": "",
                "model_version": "veteran_lve_stats_first_test",
            },
        ],
    )
    source_root = tmp_path / "stats_first_sources"
    source_root.mkdir()
    _write_rows(
        source_root / "stats_first_feature_contributions.csv",
        [
            {
                "player_id": "active_a",
                "player_name": "Active Stats A",
                "position": "WR",
                "component": "win_now_value",
                "feature_name": "role_security",
                "normalized_score": "90",
                "feature_weight": "50",
                "component_contribution": "45",
                "model_version": "veteran_lve_stats_first_test",
            },
            {
                "player_id": "active_a",
                "player_name": "Active Stats A",
                "position": "WR",
                "component": "win_now_value",
                "feature_name": "target_earning_stability",
                "normalized_score": "85",
                "feature_weight": "5",
                "component_contribution": "4.25",
                "model_version": "veteran_lve_stats_first_test",
            },
            {
                "player_id": "active_b",
                "player_name": "Active Stats B",
                "position": "WR",
                "component": "win_now_value",
                "feature_name": "role_security",
                "normalized_score": "70",
                "feature_weight": "50",
                "component_contribution": "35",
                "model_version": "veteran_lve_stats_first_test",
            },
        ],
    )
    _write_rows(
        source_root / "stats_first_normalized_features.csv",
        [
            _stats_first_normalized_row("active_a", "Active Stats A", role_security="90"),
            _stats_first_normalized_row("active_b", "Active Stats B", role_security="70"),
        ],
    )

    options = build_player_compare_options(pack_dir, veteran_model_dir=source_root)
    report = compare_players(pack_dir, "active_a", "active_b", veteran_model_dir=source_root)

    assert [row["player"] for row in options] == ["Active Stats A", "Active Stats B"]
    keeper_row = _score_row(report.score_rows, "Keeper")
    trade_row = _score_row(report.score_rows, "Trade Liquidity")
    assert keeper_row["leader"] == "Active Stats A"
    assert trade_row["leader"] == "Active Stats B"
    assert report.gap_driver_rows[0]["formula_feature_name"] == "role_security"
    assert report.warning_rows[1]["risk_notes"] == "unstable WR role"
    target_gap = [
        row
        for row in report.feature_rows
        if row["formula_feature_name"] == "target_earning_stability"
    ][0]
    assert target_gap["b_imputed"] is True
    assert "not present" in str(target_gap["warning_reason_b"])


def _fixture_model_dir(tmp_path: Path) -> Path:
    model_dir = tmp_path / "veteran_model_v1"
    shutil.copytree(Path("sample_data/veteran_model_v1"), model_dir)
    return model_dir


def _append_player(
    model_dir: Path,
    player_id: str,
    player_name: str,
    position: str,
    *,
    age: float,
    league_rank: int,
) -> None:
    path = model_dir / "veteran_player_inputs.csv"
    rows = _read_rows(path)
    rows.append(
        {
            "season": "2026",
            "snapshot_date": "2026-05-05",
            "player_id": player_id,
            "player_name": player_name,
            "position": position,
            "nfl_team": "FA",
            "age": str(age),
            "team_id": "fixture",
            "team_name": "Fixture Team",
            "league_rank": str(league_rank),
            "is_league_rank_top5": "false",
            "source_snapshot_id": "compare_fixture",
            "source_name": "compare_fixture",
            "source_date": "2026-05-05",
            "data_quality_tier": "verified",
        }
    )
    _write_rows(path, rows)


def _append_features(
    model_dir: Path,
    player_id: str,
    position: str,
    features: dict[str, float],
) -> None:
    path = model_dir / "veteran_feature_scores.csv"
    rows = _read_rows(path)
    for feature_name, score in features.items():
        rows.append(
            {
                "season": "2026",
                "snapshot_date": "2026-05-05",
                "player_id": player_id,
                "position": position,
                "feature_name": feature_name,
                "normalized_score": str(score),
                "source_key": _source_key(feature_name),
                "source_confidence": "derived",
                "is_missing": "false",
                "missing_reason": "",
                "is_user_override": "false",
                "override_reason": "",
            }
        )
    _write_rows(path, rows)


def _source_key(feature_name: str) -> str:
    if "injury" in feature_name:
        return "injury_fixture_2026"
    if feature_name == "market_liquidity":
        return "market_rank_fixture_2026"
    if feature_name in {"age_curve", "position_replaceability"}:
        return "manual_fixture_2026"
    return "projection_fixture_2026"


def _stats_first_normalized_row(
    player_id: str,
    player_name: str,
    *,
    role_security: str,
) -> dict[str, str]:
    return {
        "season": "2026",
        "snapshot_date": "2026-pre-draft",
        "player_id": player_id,
        "player_name": player_name,
        "position": "WR",
        "team": "TST",
        "weighted_recent_lve_ppg_score": "80",
        "expected_lve_points_score": "80",
        "lve_projection_value": "80",
        "role_security": role_security,
        "workload_earning": "",
        "target_earning_stability": "80",
        "route_role": role_security,
        "qb_rushing_profile": "",
        "first_down_td_fit": "80",
        "efficiency_score": "80",
        "age_curve": "80",
        "injury_durability": "80",
        "market_liquidity": "80",
        "qb_replacement_level_baseline": "76",
        "rb_replacement_level_baseline": "72",
        "wr_replacement_level_baseline": "72",
        "te_replacement_level_baseline": "69",
        "confidence": "80",
        "missing_data_penalty": "0",
        "warnings": "",
        "source_key": "stats_first_test",
        "source_date": "2026-01-15",
        "source_file": "test",
    }


def _score_row(rows: list[dict[str, object]], metric: str) -> dict[str, object]:
    return [row for row in rows if row["metric"] == metric][0]


def _market_edge(rows: list[dict[str, object]], player: str) -> str:
    return str([row for row in rows if row["player"] == player][0]["market_edge_label"])


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
