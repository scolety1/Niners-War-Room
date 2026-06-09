from __future__ import annotations

from src.services.hidden_default_audit_service import hidden_default_audit_rows_from_receipts


def test_neutral_default_is_bucketed_as_safe_imputation() -> None:
    rows = hidden_default_audit_rows_from_receipts(
        [
            {
                "player": "Missing Projection Player",
                "component": "win_now_value",
                "formula_feature_name": "expected_lve_points_score",
                "source_feature_name": "expected_lve_points_score",
                "normalized_score": 50.0,
                "source_status": "neutral_imputation",
                "neutral_default_value": 50.0,
                "imputed_flag": True,
                "data_truth_warning": "missing_projection_features",
                "model_usage": "private_stat_feature",
            }
        ]
    )

    assert rows[0]["default_bucket"] == "safe_neutral_imputation"
    assert rows[0]["affects_private_value"] is True
    assert rows[0]["patch_required"] is False


def test_default_marked_as_real_evidence_with_missing_warning_is_unsafe() -> None:
    rows = hidden_default_audit_rows_from_receipts(
        [
            {
                "player": "Bad Default Player",
                "component": "win_now_value",
                "formula_feature_name": "expected_lve_points_score",
                "source_feature_name": "expected_lve_points_score",
                "normalized_score": 50.0,
                "source_status": "imported_real_data",
                "neutral_default_value": "",
                "imputed_flag": False,
                "warning_reason": "missing_projection_features",
                "model_usage": "private_stat_feature",
            }
        ]
    )

    assert rows[0]["default_bucket"] == "unsafe_hidden_evidence"
    assert rows[0]["patch_required"] is True


def test_formula_default_is_not_treated_as_source_evidence() -> None:
    rows = hidden_default_audit_rows_from_receipts(
        [
            {
                "player": "Formula Player",
                "component": "private_lve_value",
                "formula_feature_name": "win_now_value",
                "source_feature_name": "formula_derived",
                "normalized_score": 76.0,
                "source_status": "derived_real_data",
                "imputed_flag": False,
                "warning_reason": "formula derived from displayed component features",
                "model_usage": "formula_derived",
            }
        ]
    )

    assert rows[0]["default_bucket"] == "formula_fallback"
    assert rows[0]["patch_required"] is False


def test_market_default_is_trade_or_review_not_private_evidence() -> None:
    rows = hidden_default_audit_rows_from_receipts(
        [
            {
                "player": "No Market Player",
                "component": "trade_value",
                "formula_feature_name": "market_liquidity",
                "source_feature_name": "market_liquidity",
                "normalized_score": 50.0,
                "source_status": "neutral_imputation",
                "neutral_default_value": 50.0,
                "imputed_flag": True,
                "warning_reason": "missing_market_trade_value",
                "model_usage": "trade_liquidity_only",
            }
        ]
    )

    assert rows[0]["default_bucket"] == "safe_neutral_imputation"
    assert rows[0]["affects_private_value"] is False
    assert rows[0]["affects_keeper_drop_trade_value"] is True
