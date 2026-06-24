from __future__ import annotations

import pandas as pd

from src.services.model_evaluation_harness_service import (
    CAUTION_BACKTEST,
    MARKET_DIAGNOSTIC,
    SENSITIVITY_TEST,
    TRUTH_BACKTEST,
    build_model_evaluation_harness,
    validate_evaluation_outputs,
    write_model_evaluation_outputs,
)


def _dynasty() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": "puka",
                "player_name": "Puka Nacua",
                "position": "WR",
                "age": "25.0",
                "nwr_rank": "1",
                "dp_value_1qb": "9000",
                "market_gap": "-2",
            },
            {
                "player_id": "",
                "player_name": "Missing ID Star",
                "position": "RB",
                "age": "",
                "nwr_rank": "2",
                "dp_value_1qb": "",
                "market_gap": "",
            },
        ]
    )


def _frozen() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": "rookie1",
                "player": "Rookie One",
                "position": "RB",
                "age": "21.1",
                "final_board_rank": "1",
            }
        ]
    )


def _expanded() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": "",
                "player": "High Rank Missing Data",
                "position": "WR",
                "age": "",
                "final_board_rank": "1",
                "confidence_band": "High",
                "outcome_applicable_summary": "Not enough information",
            },
            {
                "player_id": "ok",
                "player": "Covered Player",
                "position": "RB",
                "age": "23.0",
                "final_board_rank": "2",
                "confidence_band": "Medium",
                "outcome_applicable_summary": "RB T24=40%",
            },
        ]
    )


def _historical() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"player_name": "Actual", "source_class": "ACTUAL_DROP", "confidence": "HIGH"},
            {"player_name": "Inferred", "source_class": "INFERRED_DROP", "confidence": "MEDIUM"},
            {"player_name": "Proxy", "source_class": "PROXY_DROP", "confidence": "PROXY_ONLY"},
            {"player_name": "Low", "source_class": "ACTUAL_DROP", "confidence": "LOW"},
        ]
    )


def _eligibility() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_class": "ACTUAL_DROP",
                "confidence": "HIGH",
                "allowed_for_training": "no",
                "allowed_for_truth_backtest": "yes",
                "allowed_for_caution_backtest": "yes",
                "allowed_for_sensitivity": "yes",
                "notes": "truth eligible",
            },
            {
                "source_class": "INFERRED_DROP",
                "confidence": "MEDIUM",
                "allowed_for_training": "no",
                "allowed_for_truth_backtest": "no",
                "allowed_for_caution_backtest": "yes",
                "allowed_for_sensitivity": "yes",
                "notes": "caution only",
            },
            {
                "source_class": "PROXY_DROP",
                "confidence": "PROXY_ONLY",
                "allowed_for_training": "no",
                "allowed_for_truth_backtest": "no",
                "allowed_for_caution_backtest": "no",
                "allowed_for_sensitivity": "yes",
                "notes": "sensitivity only",
            },
            {
                "source_class": "ACTUAL_DROP",
                "confidence": "LOW",
                "allowed_for_training": "no",
                "allowed_for_truth_backtest": "no",
                "allowed_for_caution_backtest": "no",
                "allowed_for_sensitivity": "yes",
                "notes": "low sensitivity only",
            },
        ]
    )


def _outcome() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"player": "Covered Player", "prop_match_status": "matched_exact"},
            {"player": "High Rank Missing Data", "prop_match_status": "unmatched_no_outcome_row"},
        ]
    )


def test_evaluation_harness_separates_truth_caution_and_sensitivity() -> None:
    result = build_model_evaluation_harness(
        dynasty_frame=_dynasty(),
        frozen_frame=_frozen(),
        expanded_pool_frame=_expanded(),
        historical_drop_frame=_historical(),
        eligibility_rules_frame=_eligibility(),
        outcome_coverage_frame=_outcome(),
        market_enriched_frame=_dynasty(),
    )

    buckets = result.by_bucket
    assert TRUTH_BACKTEST in set(buckets["bucket"])
    assert CAUTION_BACKTEST in set(buckets["bucket"])
    assert SENSITIVITY_TEST in set(buckets["bucket"])
    assert MARKET_DIAGNOSTIC in set(buckets["bucket"])

    proxy = buckets.loc[buckets["source_class"].eq("PROXY_DROP")].iloc[0]
    assert proxy["eligible_for_truth_backtest"] == "no"
    assert proxy["eligible_for_training"] == "no"
    assert proxy["eligible_for_sensitivity"] == "yes"


def test_evaluation_harness_does_not_claim_predictive_accuracy() -> None:
    result = build_model_evaluation_harness(
        dynasty_frame=_dynasty(),
        frozen_frame=_frozen(),
        expanded_pool_frame=_expanded(),
        historical_drop_frame=_historical(),
        eligibility_rules_frame=_eligibility(),
        outcome_coverage_frame=_outcome(),
        market_enriched_frame=_dynasty(),
    )

    row = result.summary.loc[result.summary["metric"].eq("predictive_accuracy_claim")].iloc[0]
    assert row["value"] == "Not enough information"


def test_evaluation_harness_counts_unmatched_outcomes_as_missing() -> None:
    result = build_model_evaluation_harness(
        dynasty_frame=_dynasty(),
        frozen_frame=_frozen(),
        expanded_pool_frame=_expanded(),
        historical_drop_frame=_historical(),
        eligibility_rules_frame=_eligibility(),
        outcome_coverage_frame=_outcome(),
        market_enriched_frame=_dynasty(),
    )

    matched = result.summary.loc[result.summary["metric"].eq("matched_outcome_rows")].iloc[0]
    missing = result.summary.loc[
        result.summary["metric"].eq("unsupported_or_missing_rows")
    ].iloc[0]
    assert matched["value"] == "1"
    assert missing["value"] == "1"


def test_evaluation_harness_flags_high_rank_missing_data() -> None:
    result = build_model_evaluation_harness(
        dynasty_frame=_dynasty(),
        frozen_frame=_frozen(),
        expanded_pool_frame=_expanded(),
        historical_drop_frame=_historical(),
        eligibility_rules_frame=_eligibility(),
        outcome_coverage_frame=_outcome(),
        market_enriched_frame=_dynasty(),
    )

    warnings = result.warnings["warning"].tolist()
    assert any("High-rank player missing" in warning for warning in warnings)


def test_evaluation_outputs_validate(tmp_path) -> None:
    result = build_model_evaluation_harness(
        dynasty_frame=_dynasty(),
        frozen_frame=_frozen(),
        expanded_pool_frame=_expanded(),
        historical_drop_frame=_historical(),
        eligibility_rules_frame=_eligibility(),
        outcome_coverage_frame=_outcome(),
        market_enriched_frame=_dynasty(),
    )

    write_model_evaluation_outputs(result, output_root=tmp_path)

    assert validate_evaluation_outputs(tmp_path) == []
