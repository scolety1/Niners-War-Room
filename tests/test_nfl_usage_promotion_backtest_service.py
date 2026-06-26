from __future__ import annotations

import pandas as pd

from src.services.nfl_usage_promotion_backtest_service import (
    APP_WIRING_ALLOWED,
    MODEL_INPUT_ALLOWED,
    backtest_result_rows,
    decision_matrix_rows,
    feature_window_rows,
    field_classification_rows,
    run_promotion_gate,
    validate_feature_windows,
)


def test_promotion_gate_dry_run_default_writes_nothing(tmp_path) -> None:
    result = run_promotion_gate(output_root=tmp_path)

    assert result.files_written == ()
    assert result.predictive_backtest_status == "BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE"
    assert not list(tmp_path.iterdir())


def test_missing_or_skipped_predictive_request_blocks_predictive_backtest(tmp_path) -> None:
    result = run_promotion_gate(
        output_root=tmp_path,
        write=True,
        predictive_requested=False,
    )

    rows = pd.read_csv(tmp_path / "nfl_usage_backtest_results_v0.csv", keep_default_na=False)
    assert result.predictive_backtest_status == "BACKTEST_BLOCKED_INSUFFICIENT_LABELS"
    assert rows.loc[0, "predictive_backtest_run"] == "no"
    assert rows.loc[0, "model_input_allowed"] == MODEL_INPUT_ALLOWED
    assert rows.loc[0, "app_wiring_allowed"] == APP_WIRING_ALLOWED


def test_leakage_policy_rejects_same_season_final_window_if_allowed() -> None:
    rows = feature_window_rows()
    rows[2] = {**rows[2], "allowed": "yes"}

    try:
        validate_feature_windows(rows)
    except ValueError as exc:
        assert "illegal leakage window" in str(exc)
    else:
        raise AssertionError("expected leakage window validation to fail")


def test_decision_matrix_keeps_model_and_app_flags_off() -> None:
    classification = field_classification_rows()
    backtest_status = backtest_result_rows("BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE")[0]["status"]
    decision_rows = decision_matrix_rows(classification, backtest_status)

    assert decision_rows
    assert {row["model_input_allowed"] for row in decision_rows} == {"no"}
    assert {row["app_wiring_allowed"] for row in decision_rows} == {"no"}
    assert all(row["approved_for_model_candidate"] == "no" for row in decision_rows)


def test_route_and_market_fields_fail_closed() -> None:
    rows = {row["field_name"]: row for row in field_classification_rows()}

    assert rows["true_routes_run"]["promotion_candidate_status"] == "BLOCKED_LICENSED_DATA_GAP"
    assert rows["true_tprr"]["promotion_candidate_status"] == "BLOCKED_LICENSED_DATA_GAP"
    assert rows["true_yprr"]["promotion_candidate_status"] == "BLOCKED_LICENSED_DATA_GAP"
    assert rows["route_participation_proxy"]["promotion_candidate_status"] == "RESEARCH_ONLY"
    assert (
        rows["ranks_projections_adp_market_vendor_values"]["promotion_candidate_status"]
        == "BLOCKED_UNSAFE"
    )
