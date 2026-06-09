from __future__ import annotations

from src.services.feature_data_truth_contract_service import (
    ACTIVE_FEATURE_CONTRACTS,
    SOURCE_DERIVED_REAL_DATA,
    SOURCE_DISABLED,
    SOURCE_IMPORTED_REAL_DATA,
    SOURCE_NEUTRAL_IMPUTATION,
    SOURCE_PROXY_ONLY_SNAP_TARGET,
    SOURCE_UNAVAILABLE_FREE_PUBLIC,
    classify_feature_truth,
    default_value_audit_rows,
    feature_data_contract_rows,
)


def test_data_truth_contract_covers_active_model_features() -> None:
    required = {
        "weighted_recent_lve_ppg_score",
        "expected_lve_points_score",
        "lve_projection_value",
        "role_security",
        "workload_earning",
        "target_earning_stability",
        "route_role",
        "efficiency_score",
        "first_down_td_fit",
        "age_curve",
        "injury_durability",
        "private_stat_value",
        "confidence",
        "market_liquidity",
        "market_trade_value",
        "young_nfl_bridge_prior",
    }

    assert required <= set(ACTIVE_FEATURE_CONTRACTS)
    rows = feature_data_contract_rows()
    assert {row["feature_name"] for row in rows} >= required


def test_neutral_defaults_are_not_imported_real_data() -> None:
    row = {
        "weighted_recent_lve_ppg_score": "50.0",
        "warnings": "missing_lve_scoring_history",
    }

    truth = classify_feature_truth("weighted_recent_lve_ppg_score", row)

    assert truth.source_status == SOURCE_NEUTRAL_IMPUTATION
    assert truth.imputed_flag is True
    assert truth.neutral_default_value == 50.0


def test_market_default_is_trade_only_neutral_not_private_evidence() -> None:
    truth = classify_feature_truth(
        "market_liquidity",
        {"market_liquidity": "50.0", "warnings": "missing_market_trade_value"},
    )

    assert truth.source_status == SOURCE_NEUTRAL_IMPUTATION
    assert truth.model_usage == "trade_liquidity_only"


def test_young_bridge_prior_is_disabled_when_weight_is_zero() -> None:
    truth = classify_feature_truth(
        "young_nfl_bridge_prior",
        {
            "young_nfl_bridge_prior_score": "90.0",
            "young_nfl_bridge_weight": "0.0",
        },
    )

    assert truth.source_status == SOURCE_DISABLED


def test_age_curve_with_imported_bio_is_derived_real_data() -> None:
    truth = classify_feature_truth(
        "age_curve",
        {
            "age_curve": "82",
            "age_raw": "28",
            "age_bucket": "mild_decline",
            "age_source_status": "derived_real_data",
            "age_warning": "age_mild_decline_window",
        },
    )

    assert truth.source_status == SOURCE_DERIVED_REAL_DATA
    assert truth.imputed_flag is False
    assert truth.warning_reason == "age_mild_decline_window"


def test_real_and_formula_derived_statuses_are_distinct() -> None:
    imported = classify_feature_truth(
        "expected_lve_points_score",
        {"expected_lve_points_score": "74.0", "warnings": ""},
    )
    derived = classify_feature_truth(
        "private_lve_value",
        {"private_lve_value": "80.0"},
        is_formula_derived=True,
    )

    assert imported.source_status == SOURCE_IMPORTED_REAL_DATA
    assert derived.source_status == SOURCE_DERIVED_REAL_DATA


def test_route_default_is_unavailable_not_imported_evidence() -> None:
    truth = classify_feature_truth(
        "route_role",
        {
            "route_role": "50.0",
            "warnings": "missing_participation_proxy",
        },
    )

    assert truth.source_status == SOURCE_UNAVAILABLE_FREE_PUBLIC
    assert truth.imputed_flag is True
    assert truth.neutral_default_value == 50.0
    assert truth.warning_reason == "route_data_unavailable_free_public"


def test_non_default_route_role_is_proxy_not_real_route_data() -> None:
    truth = classify_feature_truth(
        "route_role",
        {
            "route_role": "74.0",
            "warnings": "",
        },
    )

    assert truth.source_status == SOURCE_PROXY_ONLY_SNAP_TARGET
    assert truth.imputed_flag is False
    assert truth.warning_reason == "route_data_proxy_only_snap_target"


def test_default_value_audit_rows_include_project_gold_defaults() -> None:
    defaults = {row["default_value"]: row for row in default_value_audit_rows()}

    assert {50, 75, 76, 78} <= set(defaults)
    assert all(
        row["source_status"] == SOURCE_NEUTRAL_IMPUTATION for row in defaults.values()
    )
