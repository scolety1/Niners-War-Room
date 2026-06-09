from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.player_feature_receipts_service import (
    PlayerFeatureReceiptsReport,
    build_player_feature_receipts,
    compact_receipt_preview_for_player,
    component_summary_rows_for_players,
    receipt_rows_for_players,
)


def test_player_feature_receipts_show_component_reconciliation() -> None:
    report = build_player_feature_receipts(
        "sample_data/2026_pre_declaration",
        veteran_model_dir="sample_data/veteran_model_v1",
    )

    assert not report.issues
    assert report.rows

    lamar_base = [
        row
        for row in report.component_summary_rows
        if row["player"] == "Lamar Jackson" and row["component"] == "veteran_base_value"
    ][0]
    lamar_horizon = [
        row
        for row in report.component_summary_rows
        if row["player"] == "Lamar Jackson" and row["component"] == "horizon_retention_score"
    ][0]

    assert lamar_base["reconciliation_status"] == "matched"
    assert abs(float(lamar_base["component_score"]) - float(lamar_base["contribution_sum"])) <= 0.05
    assert lamar_horizon["reconciliation_status"] == "matched"
    assert abs(
        float(lamar_horizon["component_score"]) - float(lamar_horizon["contribution_sum"])
    ) <= 0.05

    receipt = [
        row
        for row in report.rows
        if row["player"] == "Lamar Jackson"
        and row["formula_feature_name"] == "passing_td_yardage_output"
    ][0]
    assert receipt["raw_feature_value"] == 89.0
    assert receipt["normalized_score"] == 89.0
    assert receipt["feature_weight"] == 20
    assert receipt["source_file"]
    assert receipt["source_date"] == "2026-05-05"
    assert receipt["imputed_flag"] is False

    visible_rows = [{"player": "Lamar Jackson", "position": "QB"}]
    sorted_rows = receipt_rows_for_players(report, visible_rows)
    contributions = [
        abs(float(row["contribution"]))
        for row in sorted_rows
        if row["player"] == "Lamar Jackson"
    ]

    assert contributions == sorted(contributions, reverse=True)

    summary_rows = component_summary_rows_for_players(report, visible_rows)
    assert any(row["component"] == "veteran_base_value" for row in summary_rows)


def test_player_feature_receipts_flag_missing_and_imputed_features(tmp_path: Path) -> None:
    source = Path("sample_data/veteran_model_v1")
    model_dir = tmp_path / "veteran_model_v1"
    shutil.copytree(source, model_dir)
    feature_path = model_dir / "veteran_feature_scores.csv"
    rows = _read_rows(feature_path)
    for row in rows:
        if (
            row["player_id"] == "lamar_jackson"
            and row["feature_name"] == "current_injury_durability"
        ):
            row["normalized_score"] = ""
            row["is_missing"] = "true"
            row["missing_reason"] = "injury_source_missing_for_test"
    _write_rows(feature_path, rows)

    report = build_player_feature_receipts(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    injury_receipt = [
        row
        for row in report.rows
        if row["player"] == "Lamar Jackson"
        and row["formula_feature_name"] == "current_injury_durability"
    ][0]
    assert injury_receipt["imputed_flag"] is True
    assert injury_receipt["warning_reason"] == "injury source missing for test"
    assert injury_receipt["raw_feature_value"] == ""

    visible_rows = [{"player": "Lamar Jackson", "position": "QB"}]
    page_rows = receipt_rows_for_players(report, visible_rows)
    warning_rows = [
        row for row in page_rows if row["formula_feature_name"] == "current_injury_durability"
    ]

    assert warning_rows[0]["imputed_flag"] is True
    assert warning_rows[0]["warning_reason"] == "injury source missing for test"


def test_receipt_rows_for_players_adds_fallback_for_draft_pool_rows() -> None:
    report = build_player_feature_receipts(
        "sample_data/2026_pre_declaration",
        veteran_model_dir="sample_data/veteran_model_v1",
    )
    rows = receipt_rows_for_players(
        report,
        [
            {
                "player": "Unmodeled Rookie",
                "position": "WR",
                "stats_model_value": 88.5,
                "market_edge": 4.2,
                "confidence": 71.0,
                "warning": "Review-only: calibration blocked",
                "source": "fact_rookie_draftables.csv",
            }
        ],
        page_source="Rankings",
    )

    assert rows[0]["player"] == "Unmodeled Rookie"
    assert rows[0]["formula_feature_name"] == "visible_stats_value"
    assert rows[0]["raw_feature_value"] == 88.5
    assert rows[0]["normalized_score"] == 88.5
    assert rows[0]["feature_weight"] == 100
    assert rows[0]["contribution"] == 88.5
    assert rows[0]["source_file"] == "fact_rookie_draftables.csv"
    assert rows[0]["warning_reason"] == "Review-only: calibration blocked"


def test_stats_first_receipts_show_lifecycle_sections_and_bridge_prior(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "stats_first"
    source_root.mkdir()
    _write_rows(
        source_root / "stats_first_normalized_features.csv",
        [
            {
                "player_id": "p_luther_burden",
                "player_name": "Luther Burden",
                "position": "WR",
                "team": "CHI",
                "weighted_recent_lve_ppg_score": "70",
                "role_security": "60",
                "first_down_td_fit": "55",
                "age_curve": "90",
                "lve_projection_value": "50",
                "market_liquidity": "80",
                "experience_bucket": "year_one_nfl_player",
                "young_nfl_bridge_prior_score": "82",
                "young_nfl_bridge_source": "draft_capital_prior",
                "young_nfl_bridge_weight": "0.35",
                "source_file": "stats_first_normalized_features.csv",
                "source_date": "2026-05-10",
                "warnings": "young_nfl_bridge_prior_active",
            }
        ],
    )
    _write_rows(
        source_root / "stats_first_feature_contributions.csv",
        [
            _contribution_row("weighted_recent_lve_ppg_score", "private_lve_value", 70, 20, 14),
            _contribution_row("role_security", "private_lve_value", 60, 20, 12),
            _contribution_row("first_down_td_fit", "private_lve_value", 55, 14.5455, 8),
            _contribution_row("age_curve", "private_lve_value", 90, 8.8889, 8),
            _contribution_row("lve_projection_value", "private_lve_value", 50, 10, 5),
            _contribution_row("young_nfl_bridge_prior", "private_lve_value", 82, 42.6829, 35),
            _contribution_row("market_liquidity", "trade_value", 80, 0, 0),
        ],
    )

    report = build_player_feature_receipts(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=source_root,
    )

    luther_rows = [row for row in report.rows if row["player"] == "Luther Burden"]
    section_labels = {row["receipt_section_label"] for row in luther_rows}
    assert {
        "NFL Production",
        "Role/Usage",
        "First-Down/TD Fit",
        "Age/Injury",
        "Projection",
        "Young-Player Bridge Prior",
        "Market/Liquidity",
    }.issubset(section_labels)
    bridge_row = [
        row for row in luther_rows if row["formula_feature_name"] == "young_nfl_bridge_prior"
    ][0]
    assert bridge_row["asset_lifecycle_label"] == "Year-One NFL Bridge"
    assert "young NFL bridge asset" in str(bridge_row["lifecycle_explanation"])
    assert "35%" in str(bridge_row["lifecycle_explanation"])
    assert bridge_row["young_nfl_bridge_prior_score"] == "82"

    summary = [
        row
        for row in report.component_summary_rows
        if row["player"] == "Luther Burden" and row["component"] == "private_lve_value"
    ][0]
    assert summary["reconciliation_status"] == "matched"
    assert abs(float(summary["component_score"]) - float(summary["contribution_sum"])) <= 0.05


def test_compact_receipt_preview_for_selected_war_board_player() -> None:
    report = build_player_feature_receipts(
        "sample_data/2026_pre_declaration",
        veteran_model_dir="sample_data/veteran_model_v1",
    )

    preview = compact_receipt_preview_for_player(
        report,
        {
            "overall_rank": 2,
            "position_rank_label": "QB1",
            "player": "Lamar Jackson",
            "pos": "QB",
            "asset_lifecycle_label": "Established Veteran",
            "stats_value": 89.0,
            "confidence": 88.0,
            "warning_reason": "No active warning.",
        },
    )

    assert preview["summary"]["player"] == "Lamar Jackson"
    assert preview["summary"]["rank"] == 2
    assert preview["summary"]["position_rank"] == "QB1"
    assert preview["summary"]["model_value"] == 89.0
    assert preview["positive_drivers"]
    assert len(preview["positive_drivers"]) <= 5
    assert "Driver" in preview["positive_drivers"][0]
    assert "Lifecycle" not in preview["positive_drivers"][0]
    assert preview["lifecycle_explanation"]
    assert preview["advanced_receipt_rows"]


def test_compact_receipt_preview_prioritizes_private_model_drivers() -> None:
    report = PlayerFeatureReceiptsReport(
        rows=[
            _receipt_row(
                "Market WR",
                "WR",
                "trade_value",
                "market_liquidity",
                21.0,
                section="Market/Liquidity",
            ),
            _receipt_row(
                "Market WR",
                "WR",
                "private_lve_value",
                "role_security",
                12.0,
                section="Role/Usage",
            ),
        ],
        component_summary_rows=[],
        players=["Market WR"],
        components=["private_lve_value", "trade_value"],
        issues=[],
        source_root="test",
    )

    preview = compact_receipt_preview_for_player(
        report,
        {
            "overall_rank": 1,
            "position_rank_label": "WR1",
            "player": "Market WR",
            "pos": "WR",
            "asset_lifecycle_label": "Established Veteran",
            "stats_value": 88.0,
            "confidence": 85.0,
        },
    )

    assert preview["positive_drivers"][0]["Driver"] == "Role security"
    assert all(
        row["Driver"] != "Trade market liquidity"
        for row in preview["positive_drivers"]
    )
    assert preview["market_context"][0]["Driver"] == "Trade market liquidity"
    assert any(
        row["formula_feature_name"] == "market_liquidity"
        for row in preview["advanced_receipt_rows"]
    )


def test_compact_receipt_preview_uses_underlying_stat_drivers_before_wrappers() -> None:
    report = PlayerFeatureReceiptsReport(
        rows=[
            _receipt_row(
                "Young RB",
                "RB",
                "private_lve_value",
                "dynasty_hold_value",
                50.0,
                section="NFL Production",
            ),
            _receipt_row(
                "Young RB",
                "RB",
                "dynasty_hold_value",
                "workload_earning",
                16.0,
                section="Role/Usage",
            ),
            _receipt_row(
                "Young RB",
                "RB",
                "dynasty_hold_value",
                "age_curve",
                12.0,
                section="Age/Injury",
            ),
            _receipt_row(
                "Young RB",
                "RB",
                "private_lve_value",
                "young_nfl_bridge_prior",
                4.0,
                section="Young-Player Bridge Prior",
            ),
        ],
        component_summary_rows=[],
        players=["Young RB"],
        components=["private_lve_value", "dynasty_hold_value"],
        issues=[],
        source_root="test",
    )

    preview = compact_receipt_preview_for_player(
        report,
        {
            "overall_rank": 1,
            "position_rank_label": "RB1",
            "player": "Young RB",
            "pos": "RB",
            "asset_lifecycle_label": "Young NFL Bridge",
            "stats_value": 88.0,
            "confidence": 85.0,
        },
    )

    assert preview["positive_drivers"][0]["Driver"] == "Workload earning"
    assert all(row["Driver"] != "Dynasty Hold Value" for row in preview["positive_drivers"])
    assert preview["bridge_drivers"][0]["Driver"] == "Young-player bridge contribution"


def test_war_board_page_uses_selected_player_compact_receipts() -> None:
    page_text = Path("app/pages/03_war_board.py").read_text(encoding="utf-8")

    assert 'selection_mode="single-row"' in page_text
    assert 'key="war_board_main_table"' in page_text
    assert "compact_receipt_preview_for_player(" in page_text
    assert "Select one player row above" in page_text
    assert "Advanced: full receipt rows" in page_text


def _receipt_row(
    player: str,
    position: str,
    component: str,
    feature: str,
    contribution: float,
    *,
    section: str,
) -> dict[str, object]:
    return {
        "player": player,
        "position": position,
        "component": component,
        "receipt_section_label": section,
        "formula_feature_name": feature,
        "normalized_score": 80.0,
        "feature_weight": 20.0,
        "contribution": contribution,
        "warning_reason": "",
        "imputed_flag": False,
    }


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _contribution_row(
    feature_name: str,
    component: str,
    normalized_score: float,
    feature_weight: float,
    contribution: float,
) -> dict[str, object]:
    return {
        "player_id": "p_luther_burden",
        "player_name": "Luther Burden",
        "position": "WR",
        "component": component,
        "feature_name": feature_name,
        "normalized_score": normalized_score,
        "feature_weight": feature_weight,
        "component_contribution": contribution,
        "model_version": "test_stats_first_v1",
    }
