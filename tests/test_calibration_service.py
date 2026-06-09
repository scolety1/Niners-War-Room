from __future__ import annotations

from src.services.calibration_service import (
    build_calibration_report,
    calibration_readiness_rows,
    calibration_verdict_summary_rows,
)
from src.services.historical_draft_service import (
    compare_historical_rookie_replay,
    load_historical_rookie_model_replay,
    load_offline_rookie_notes,
)

OFFLINE_NOTES_FIXTURE = (
    "sample_data/historical_rookie_notes/offline_notes_four_seasons.csv"
)
MODEL_REPLAY_FIXTURE = "sample_data/historical_rookie_notes/model_replay_sample.csv"


def test_calibration_scenarios_cover_lve_decision_traps() -> None:
    report = build_calibration_report()
    scenarios = {row["scenario_id"]: row for row in report.scenario_rows}

    assert {
        "obvious_keep",
        "obvious_cut",
        "forced_release_star",
        "veteran_vs_rookie",
        "pick_vs_player",
        "qb_1qb_suppression",
        "te_no_premium_suppression",
    }.issubset(scenarios)
    assert all(row["passed"] for row in report.scenario_rows)


def test_calibration_sensitivity_is_not_highly_volatile() -> None:
    report = build_calibration_report()

    assert report.sensitivity_rows
    assert all(row["volatility"] in {"low", "medium"} for row in report.sensitivity_rows)
    assert max(float(row["absolute_change"]) for row in report.sensitivity_rows) < 6


def test_calibration_uses_historical_rookie_records() -> None:
    report = build_calibration_report()

    assert len(report.historical_rows) == 20
    assert {row["season"] for row in report.historical_rows} == {2022, 2023, 2024, 2025}
    assert {row["needs_review"] for row in report.historical_rows} == {True}


def test_calibration_report_summarizes_loaded_replay_verdicts() -> None:
    actual = load_offline_rookie_notes(OFFLINE_NOTES_FIXTURE)
    replay = load_historical_rookie_model_replay(MODEL_REPLAY_FIXTURE)
    comparison = compare_historical_rookie_replay(actual, replay)

    verdict_rows = calibration_verdict_summary_rows(comparison)

    verdicts = {row["replay_verdict"]: row for row in verdict_rows}
    assert verdicts["missing_model_replay"]["count"] == 5
    assert "as-of model row" in verdicts["missing_model_replay"]["calibration_meaning"]
    assert sum(row["count"] for row in verdict_rows) == len(comparison.rows)


def test_calibration_readiness_marks_missing_model_rows_as_review() -> None:
    report = build_calibration_report()
    actual = load_offline_rookie_notes(OFFLINE_NOTES_FIXTURE)
    replay = load_historical_rookie_model_replay(MODEL_REPLAY_FIXTURE)
    comparison = compare_historical_rookie_replay(actual, replay)

    readiness = {row["area"]: row for row in calibration_readiness_rows(report, comparison)}

    assert readiness["scenario_fixtures"]["status"] == "ready"
    assert readiness["sensitivity"]["status"] == "ready"
    assert readiness["historical_model_rows"]["status"] == "review"
    assert readiness["current_score_safety"]["value"] == "isolated"
