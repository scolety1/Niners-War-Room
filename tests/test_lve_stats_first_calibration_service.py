from __future__ import annotations

import csv
from pathlib import Path

from src.services.lve_normalization_service import NORMALIZED_FEATURE_HEADER
from src.services.lve_stats_first_calibration_service import (
    build_stats_first_calibration_report,
    stats_first_calibration_readiness_rows,
    stats_first_preview_replay_rows,
)
from src.services.lve_stats_first_preview_service import create_stats_first_model_preview


def test_stats_first_calibration_scenarios_cover_key_traps() -> None:
    report = build_stats_first_calibration_report("missing_preview_root")
    scenarios = {row["scenario_id"]: row for row in report.scenario_rows}

    assert {
        "obvious_keep",
        "obvious_cut",
        "solid_wr_over_speculative_rb",
        "qb_1qb_suppression",
        "te_no_premium_suppression",
        "market_not_private_value",
        "brian_thomas_jr_over_luther_burden",
        "chase_brown_over_luther_burden",
        "kaleb_johnson_over_older_fragile_rb",
        "jayden_higgins_over_low_upside_veteran_wr",
        "high_cap_limited_wr_review_needed",
        "low_cap_limited_wr_not_boosted",
        "young_rb_uncertain_role_review_needed",
        "established_strong_veteran_over_young_limited",
    }.issubset(scenarios)
    assert all(row["passed"] for row in report.scenario_rows)


def test_young_bridge_sanity_fixtures_require_receipt_justification() -> None:
    report = build_stats_first_calibration_report("missing_preview_root")
    scenarios = {row["scenario_id"]: row for row in report.scenario_rows}
    young_bridge_ids = {
        "brian_thomas_jr_over_luther_burden",
        "chase_brown_over_luther_burden",
        "kaleb_johnson_over_older_fragile_rb",
        "jayden_higgins_over_low_upside_veteran_wr",
        "high_cap_limited_wr_review_needed",
        "young_rb_uncertain_role_review_needed",
    }

    for scenario_id in young_bridge_ids:
        assert "receipt_features=" in str(scenarios[scenario_id]["notes"])
        assert "draft_capital_prior_score" in str(scenarios[scenario_id]["notes"])
        assert "young_nfl_bridge_prior" in str(scenarios[scenario_id]["notes"])

    assert "Strong real NFL evidence" in str(
        scenarios["established_strong_veteran_over_young_limited"]["notes"]
    )


def test_stats_first_calibration_sensitivity_is_not_high_volatility() -> None:
    report = build_stats_first_calibration_report("missing_preview_root")

    assert report.sensitivity_rows
    assert all(row["volatility"] in {"low", "medium"} for row in report.sensitivity_rows)
    market_private = next(
        row
        for row in report.sensitivity_rows
        if row["scenario_id"] == "market_private_value_guardrail"
    )
    assert market_private["absolute_change"] == 0


def test_stats_first_preview_replay_rows_show_needed_without_preview() -> None:
    rows = stats_first_preview_replay_rows("missing_preview_root")

    assert rows[0]["preview_review_status"] == "needed"
    assert rows[0]["calibration_note"] == "Create a stats-first preview before replay review."


def test_stats_first_preview_replay_rows_summarize_preview_root(tmp_path: Path) -> None:
    normalized = tmp_path / "normalized.csv"
    preview_root = tmp_path / "previews"
    _write_normalized_rows(
        normalized,
        [_normalized_row("wr_ready"), _normalized_row("wr_review", confidence="62")],
    )
    create_stats_first_model_preview(normalized, preview_root, preview_id="preview_one")

    rows = stats_first_preview_replay_rows(str(preview_root))

    assert rows[0]["preview_id"] == "preview_one"
    assert rows[0]["row_count"] == 2
    assert rows[0]["ready_rows"] == 1
    assert rows[0]["review_rows"] == 1


def test_stats_first_calibration_readiness_rows_are_isolated(tmp_path: Path) -> None:
    report = build_stats_first_calibration_report(str(tmp_path / "previews"))
    readiness = {
        row["area"]: row for row in stats_first_calibration_readiness_rows(report)
    }

    assert readiness["stats_first_scenarios"]["status"] == "ready"
    assert readiness["stats_first_sensitivity"]["status"] == "ready"
    assert readiness["current_score_safety"]["value"] == "isolated"


def _normalized_row(player_id: str, *, confidence: str = "88") -> dict[str, str]:
    row = {column: "" for column in NORMALIZED_FEATURE_HEADER}
    row.update(
        {
            "season": "2026",
            "as_of_week": "18",
            "player_id": player_id,
            "gsis_id": player_id,
            "player_name": player_id.replace("_", " ").title(),
            "position": "WR",
            "team": "SF",
            "weighted_recent_lve_ppg_score": "82",
            "expected_lve_points_score": "83",
            "lve_projection_value": "82",
            "role_security": "84",
            "workload_earning": "55",
            "target_earning_stability": "82",
            "route_role": "84",
            "first_down_td_fit": "80",
            "age_curve": "80",
            "injury_durability": "80",
            "private_stat_value": "82",
            "confidence": confidence,
            "missing_data_penalty": "0",
            "warnings": "",
            "source_version": "fixture",
            "computed_at": "2026-08-01T00:00:00Z",
        }
    )
    return row


def _write_normalized_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NORMALIZED_FEATURE_HEADER)
        writer.writeheader()
        writer.writerows(rows)
