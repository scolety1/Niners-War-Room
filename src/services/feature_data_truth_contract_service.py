from __future__ import annotations

from dataclasses import dataclass

SOURCE_IMPORTED_REAL_DATA = "imported_real_data"
SOURCE_DERIVED_REAL_DATA = "derived_real_data"
SOURCE_NEUTRAL_IMPUTATION = "neutral_imputation"
SOURCE_MANUAL_REVIEW = "manual_review"
SOURCE_DISABLED = "disabled"
SOURCE_UNAVAILABLE_FREE_PUBLIC = "unavailable_free_public"
SOURCE_PROXY_ONLY_SNAP_TARGET = "proxy_only_snap_target"
SOURCE_MISSING_PAID_OR_CHARTED_DATA = "missing_paid_or_charted_data"

SOURCE_STATUS_VALUES = (
    SOURCE_IMPORTED_REAL_DATA,
    SOURCE_DERIVED_REAL_DATA,
    SOURCE_NEUTRAL_IMPUTATION,
    SOURCE_MANUAL_REVIEW,
    SOURCE_DISABLED,
    SOURCE_UNAVAILABLE_FREE_PUBLIC,
    SOURCE_PROXY_ONLY_SNAP_TARGET,
    SOURCE_MISSING_PAID_OR_CHARTED_DATA,
)


@dataclass(frozen=True)
class FeatureDataContract:
    feature_name: str
    feature_bucket: str
    source_key: str
    raw_field: str
    normalized_field: str
    default_source_status: str
    model_usage: str
    default_values: tuple[float, ...]
    default_reason: str
    implementation_note: str


@dataclass(frozen=True)
class FeatureTruthStatus:
    feature_name: str
    source_status: str
    imputed_flag: bool
    neutral_default_value: object
    warning_reason: str
    model_usage: str


ACTIVE_FEATURE_CONTRACTS: dict[str, FeatureDataContract] = {
    "weighted_recent_lve_ppg_score": FeatureDataContract(
        "weighted_recent_lve_ppg_score",
        "production",
        "nflverse_player_stats_weekly",
        "lve_points",
        "weighted_recent_lve_ppg_score",
        SOURCE_DERIVED_REAL_DATA,
        "private_stat_feature",
        (50.0,),
        "No LVE weekly scoring history; neutral midpoint is used.",
        "Derived from imported nflverse weekly stats when rows exist.",
    ),
    "expected_lve_points_score": FeatureDataContract(
        "expected_lve_points_score",
        "projection",
        "projection_raw_import",
        "lve_projected_ppg",
        "expected_lve_points_score",
        SOURCE_IMPORTED_REAL_DATA,
        "private_stat_feature",
        (50.0,),
        "Missing or local-baseline-only projection; independent projection credit is neutralized.",
        "Only independent projection rows count as imported real data.",
    ),
    "lve_projection_value": FeatureDataContract(
        "lve_projection_value",
        "projection",
        "normalization_policy",
        "expected_recent_confidence_composite",
        "lve_projection_value",
        SOURCE_DERIVED_REAL_DATA,
        "private_stat_feature",
        (50.0,),
        (
            "Composite uses neutral projection/confidence pieces when independent "
            "projections are absent."
        ),
        "Derived from expected points, recent LVE scoring, and projection confidence.",
    ),
    "role_security": FeatureDataContract(
        "role_security",
        "role_usage",
        "nflverse_snap_participation_depth",
        "role_security",
        "role_security",
        SOURCE_DERIVED_REAL_DATA,
        "private_stat_feature",
        (50.0,),
        "Missing role source; neutral midpoint is used.",
        "Derived from snap, participation, and depth-chart evidence.",
    ),
    "workload_earning": FeatureDataContract(
        "workload_earning",
        "role_usage",
        "nflverse_player_stats_weekly",
        "workload_earning_score",
        "workload_earning",
        SOURCE_DERIVED_REAL_DATA,
        "private_stat_feature",
        (50.0,),
        "Missing workload source; neutral midpoint is used.",
        "Derived from rushing attempts, targets, and touch profile.",
    ),
    "target_earning_stability": FeatureDataContract(
        "target_earning_stability",
        "role_usage",
        "nflverse_participation_player_weekly",
        "target_earning_stability_score",
        "target_earning_stability",
        SOURCE_DERIVED_REAL_DATA,
        "private_stat_feature",
        (50.0,),
        (
            "Missing target/participation source; neutral midpoint is used or proxy "
            "review is required."
        ),
        "Derived from targets, route proxy, and participation when available.",
    ),
    "route_role": FeatureDataContract(
        "route_role",
        "role_usage",
        "route_unavailable_free_public",
        "routes_run_or_route_participation",
        "route_role",
        SOURCE_UNAVAILABLE_FREE_PUBLIC,
        "private_stat_feature",
        (50.0,),
        (
            "True routes run, route participation, TPRR, and YPRR are not available "
            "from the current free/public structured source stack."
        ),
        (
            "Any current route_role value is a proxy/default unless a future legal "
            "structured route source is imported."
        ),
    ),
    "efficiency_score": FeatureDataContract(
        "efficiency_score",
        "efficiency",
        "nflverse_player_stats_weekly",
        "lve_points_per_opportunity",
        "efficiency_score",
        SOURCE_DERIVED_REAL_DATA,
        "private_stat_feature",
        (50.0,),
        "Missing weekly production/opportunity rows; neutral midpoint is used.",
        "Derived from LVE points per rush/target/attempt proxy.",
    ),
    "first_down_td_fit": FeatureDataContract(
        "first_down_td_fit",
        "first_down_td_fit",
        "nflverse_player_stats_weekly",
        "rush_rec_first_downs_and_touchdown_points",
        "first_down_td_fit",
        SOURCE_DERIVED_REAL_DATA,
        "private_stat_feature",
        (50.0,),
        "Missing first-down/TD source stats; neutral midpoint is used.",
        "Derived from rushing/receiving first downs and TD scoring fit.",
    ),
    "age_curve": FeatureDataContract(
        "age_curve",
        "age_bio",
        "normalization_policy",
        "age_or_birth_date",
        "age_curve",
        SOURCE_NEUTRAL_IMPUTATION,
        "private_stat_feature",
        (50.0,),
        "Age source is not imported into the active normalization path yet.",
        "Must not be treated as imported age evidence until age/bio source rows exist.",
    ),
    "injury_durability": FeatureDataContract(
        "injury_durability",
        "injury",
        "nflverse_injuries_weekly",
        "injury_durability_score",
        "injury_durability",
        SOURCE_DERIVED_REAL_DATA,
        "private_stat_feature",
        (50.0, 75.0, 76.0, 78.0),
        "Missing injury rows use neutral/default durability depending on the formula boundary.",
        "Derived from injury rows when available; missing injury data remains visible.",
    ),
    "private_stat_value": FeatureDataContract(
        "private_stat_value",
        "derived_score",
        "stats_first_formula",
        "component_features",
        "private_stat_value",
        SOURCE_DERIVED_REAL_DATA,
        "private_value_output",
        (),
        "No direct raw source; this is a formula output.",
        "Derived from stats-first feature buckets and excludes market data.",
    ),
    "confidence": FeatureDataContract(
        "confidence",
        "confidence",
        "stats_first_formula",
        "coverage_and_source_reliability",
        "confidence",
        SOURCE_DERIVED_REAL_DATA,
        "confidence_output",
        (50.0, 70.0),
        "Missing source pieces use confidence defaults before penalties are applied.",
        "Confidence should expose source gaps rather than hide them.",
    ),
    "confidence_score": FeatureDataContract(
        "confidence_score",
        "confidence",
        "stats_first_formula",
        "coverage_and_source_reliability",
        "confidence_score",
        SOURCE_DERIVED_REAL_DATA,
        "confidence_output",
        (50.0, 70.0),
        "Missing source pieces use confidence defaults before penalties are applied.",
        "Formula-derived active output confidence.",
    ),
    "market_liquidity": FeatureDataContract(
        "market_liquidity",
        "market_liquidity",
        "market_export",
        "market_liquidity",
        "market_liquidity",
        SOURCE_IMPORTED_REAL_DATA,
        "trade_liquidity_only",
        (50.0,),
        "Missing market value uses neutral liquidity and must not affect private value.",
        "Market is only for trade/liquidity surfaces, not private football value.",
    ),
    "market_trade_value": FeatureDataContract(
        "market_trade_value",
        "market_liquidity",
        "market_export",
        "market_trade_value",
        "market_trade_value",
        SOURCE_IMPORTED_REAL_DATA,
        "trade_liquidity_only",
        (50.0,),
        "Missing trade market value uses neutral liquidity and must not affect private value.",
        "Output-layer trade market value.",
    ),
    "young_nfl_bridge_prior": FeatureDataContract(
        "young_nfl_bridge_prior",
        "young_player_bridge",
        "draft_capital_or_rookie_grade",
        "draft_overall_or_rookie_prior",
        "young_nfl_bridge_prior_score",
        SOURCE_DERIVED_REAL_DATA,
        "young_player_bridge_only",
        (),
        "Disabled for established veterans and players without active young-player bridge weight.",
        "Bridge prior is separate from NFL production and decays with experience.",
    ),
    "young_nfl_bridge_prior_score": FeatureDataContract(
        "young_nfl_bridge_prior_score",
        "young_player_bridge",
        "draft_capital_or_rookie_grade",
        "draft_overall_or_rookie_prior",
        "young_nfl_bridge_prior_score",
        SOURCE_DERIVED_REAL_DATA,
        "young_player_bridge_only",
        (),
        "Disabled for established veterans and players without active young-player bridge weight.",
        "Wide-row form of the young NFL bridge prior.",
    ),
}

FEATURE_ALIASES = {
    "stats_first_production": "weighted_recent_lve_ppg_score",
    "young_nfl_bridge_production_prior": "young_nfl_bridge_prior",
    "stats_first_role_usage": "role_security",
    "market_trade_value": "market_trade_value",
}

MISSING_WARNING_MARKERS = {
    "missing_lve_scoring_history",
    "no_nfl_scoring_history",
    "missing_projection_features",
    "disabled_projection",
    "missing_projection_component",
    "missing_recent_production_component",
    "missing_projection_and_production_sources",
    "missing_role_usage_features",
    "missing_efficiency_source_stats",
    "missing_first_down_td_source_stats",
    "missing_injury_features",
    "no_injury_report_rows_without_nfl_activity",
}
REVIEW_WARNING_MARKERS = {
    "local_baseline_projection_not_independent",
    "missing_participation_proxy",
    "missing_snap_counts",
    "stale_lve_scoring_source",
    "age_curve_source_not_imported_yet",
    "route_data_unavailable_free_public",
    "route_data_proxy_only_snap_target",
}


def feature_data_contract_rows() -> list[dict[str, object]]:
    return [
        {
            "feature_name": contract.feature_name,
            "feature_bucket": contract.feature_bucket,
            "source_key": contract.source_key,
            "raw_field": contract.raw_field,
            "normalized_field": contract.normalized_field,
            "default_source_status": contract.default_source_status,
            "model_usage": contract.model_usage,
            "default_values": "|".join(str(value) for value in contract.default_values),
            "default_reason": contract.default_reason,
            "implementation_note": contract.implementation_note,
        }
        for contract in sorted(ACTIVE_FEATURE_CONTRACTS.values(), key=lambda row: row.feature_name)
    ]


def default_value_audit_rows() -> list[dict[str, object]]:
    return [
        {
            "default_value": 50,
            "scope": "neutral midpoint",
            "where_used": (
                "missing production, projection, role, efficiency, first-down/TD, "
                "age curve, replacement fallback, and market-neutral fallback"
            ),
            "source_status": SOURCE_NEUTRAL_IMPUTATION,
            "review_note": "Must never be counted as imported real data.",
        },
        {
            "default_value": 75,
            "scope": "normalization injury fallback",
            "where_used": "missing injury_durability source in normalization receipts",
            "source_status": SOURCE_NEUTRAL_IMPUTATION,
            "review_note": (
                "Temporary durability placeholder; confidence/warnings must stay visible."
            ),
        },
        {
            "default_value": 76,
            "scope": "formula injury and QB replacement fallback",
            "where_used": (
                "stats-first formula default injury_durability and QB replacement baseline"
            ),
            "source_status": SOURCE_NEUTRAL_IMPUTATION,
            "review_note": "Formula safety fallback, not player-specific evidence.",
        },
        {
            "default_value": 78,
            "scope": "formula injury fallback",
            "where_used": "stats-first RB/WR/TE subformula injury_durability defaults",
            "source_status": SOURCE_NEUTRAL_IMPUTATION,
            "review_note": "Formula safety fallback, not player-specific evidence.",
        },
    ]


def classify_feature_truth(
    feature_name: str,
    normalized_row: dict[str, object] | None = None,
    *,
    raw_value: object = "",
    warning_reason: object = "",
    is_formula_derived: bool = False,
    component: object = "",
) -> FeatureTruthStatus:
    normalized = normalized_row or {}
    canonical_feature = FEATURE_ALIASES.get(feature_name, feature_name)
    contract = ACTIVE_FEATURE_CONTRACTS.get(canonical_feature)
    if contract is None and is_formula_derived:
        return FeatureTruthStatus(
            feature_name=feature_name,
            source_status=SOURCE_DERIVED_REAL_DATA,
            imputed_flag=False,
            neutral_default_value="",
            warning_reason="formula derived from displayed component features",
            model_usage="formula_derived",
        )
    if contract is None:
        return FeatureTruthStatus(
            feature_name=feature_name,
            source_status=SOURCE_MANUAL_REVIEW,
            imputed_flag=False,
            neutral_default_value="",
            warning_reason="feature missing from data truth contract",
            model_usage="manual_review",
        )

    warnings = _warning_set(normalized.get("warnings"), warning_reason)
    feature_value = _feature_value(canonical_feature, normalized, raw_value)

    if canonical_feature in {"market_liquidity", "market_trade_value"}:
        if (
            _is_blank(feature_value)
            or _is_default(feature_value, 50.0)
            or "missing_market_trade_value" in warnings
        ):
            return _truth(
                contract,
                SOURCE_NEUTRAL_IMPUTATION,
                True,
                50.0,
                "missing_market_trade_value",
            )
        return _truth(contract, SOURCE_IMPORTED_REAL_DATA, False, "", "")

    if canonical_feature in {"young_nfl_bridge_prior", "young_nfl_bridge_prior_score"}:
        bridge_weight = _float(normalized.get("young_nfl_bridge_weight"), 0.0)
        if bridge_weight <= 0 or _is_blank(feature_value):
            return _truth(contract, SOURCE_DISABLED, False, "", "young bridge prior inactive")
        return _truth(contract, SOURCE_DERIVED_REAL_DATA, False, "", "")

    if canonical_feature == "age_curve":
        if normalized.get("age_source_status") == SOURCE_DERIVED_REAL_DATA:
            return _truth(
                contract,
                SOURCE_DERIVED_REAL_DATA,
                False,
                "",
                str(normalized.get("age_warning") or ""),
            )
        return _truth(
            contract,
            SOURCE_NEUTRAL_IMPUTATION,
            True,
            50.0,
            "age_curve_source_not_imported_yet",
        )

    if canonical_feature == "route_role":
        route_warnings = warnings | _warning_set(warning_reason)
        if _is_blank(feature_value) or _is_default(feature_value, 50.0):
            if "missing_role_usage_features" in route_warnings:
                return _truth(
                    contract,
                    SOURCE_MISSING_PAID_OR_CHARTED_DATA,
                    True,
                    50.0,
                    "missing_paid_or_charted_route_data",
                )
            if route_warnings & {
                "missing_participation_proxy",
                "missing_snap_counts",
                "route_data_unavailable_free_public",
            }:
                return _truth(
                    contract,
                    SOURCE_UNAVAILABLE_FREE_PUBLIC,
                    True,
                    50.0,
                    "route_data_unavailable_free_public",
                )
            return _truth(
                contract,
                SOURCE_UNAVAILABLE_FREE_PUBLIC,
                True,
                50.0,
                "route_default_not_real_evidence",
            )
        return _truth(
            contract,
            SOURCE_PROXY_ONLY_SNAP_TARGET,
            False,
            "",
            "route_data_proxy_only_snap_target",
        )

    if canonical_feature in {
        "role_security",
        "workload_earning",
        "target_earning_stability",
    }:
        role_warnings = _warning_set(warning_reason)
        missing_reason = _first_present(role_warnings, tuple(sorted(MISSING_WARNING_MARKERS)))
        if missing_reason and (_is_blank(feature_value) or _is_default(feature_value, 50.0)):
            return _truth(contract, SOURCE_NEUTRAL_IMPUTATION, True, 50.0, missing_reason)
        review_reason = _first_present(role_warnings, tuple(sorted(REVIEW_WARNING_MARKERS)))
        if review_reason:
            return _truth(contract, SOURCE_MANUAL_REVIEW, False, "", review_reason)
        if "te_route_role_gate" in role_warnings:
            return _truth(contract, SOURCE_MANUAL_REVIEW, False, "", "te_route_role_gate")
        return _truth(contract, contract.default_source_status, False, "", "")

    if is_formula_derived or canonical_feature in {
        "private_stat_value",
        "confidence",
        "confidence_score",
    }:
        return _truth(contract, SOURCE_DERIVED_REAL_DATA, False, "", "")

    if canonical_feature == "expected_lve_points_score" and (
        "missing_projection_features" in warnings
        or "local_baseline_projection_not_independent" in warnings
        or "disabled_projection" in warnings
    ):
        reason = _first_present(
            warnings,
            (
                "missing_projection_features",
                "local_baseline_projection_not_independent",
                "disabled_projection",
            ),
        )
        return _truth(contract, SOURCE_NEUTRAL_IMPUTATION, True, 50.0, reason)

    if canonical_feature == "lve_projection_value" and (
        "missing_projection_features" in warnings
        or "local_baseline_projection_not_independent" in warnings
        or "disabled_projection" in warnings
    ):
        reason = _first_present(
            warnings,
            (
                "missing_projection_features",
                "local_baseline_projection_not_independent",
                "disabled_projection",
            ),
        )
        return _truth(contract, SOURCE_MANUAL_REVIEW, True, 50.0, reason)

    missing_reason = _first_present(warnings, tuple(sorted(MISSING_WARNING_MARKERS)))
    if missing_reason and (
        _is_blank(feature_value)
        or _is_default(feature_value, 50.0)
        or (canonical_feature == "injury_durability" and _is_default(feature_value, 75.0))
    ):
        default_value = 75.0 if canonical_feature == "injury_durability" else 50.0
        if "no_injury_report_rows_without_nfl_activity" in warnings:
            default_value = 50.0
        return _truth(contract, SOURCE_NEUTRAL_IMPUTATION, True, default_value, missing_reason)

    review_reason = _first_present(warnings, tuple(sorted(REVIEW_WARNING_MARKERS)))
    if review_reason:
        return _truth(contract, SOURCE_MANUAL_REVIEW, False, "", review_reason)

    return _truth(contract, contract.default_source_status, False, "", "")


def _truth(
    contract: FeatureDataContract,
    source_status: str,
    imputed_flag: bool,
    neutral_default_value: object,
    warning_reason: str,
) -> FeatureTruthStatus:
    return FeatureTruthStatus(
        feature_name=contract.feature_name,
        source_status=source_status,
        imputed_flag=imputed_flag,
        neutral_default_value=neutral_default_value,
        warning_reason=warning_reason,
        model_usage=contract.model_usage,
    )


def _feature_value(
    feature_name: str,
    normalized: dict[str, object],
    raw_value: object,
) -> object:
    if not _is_blank(raw_value):
        return raw_value
    if feature_name == "young_nfl_bridge_prior":
        return normalized.get("young_nfl_bridge_prior_score", "")
    if feature_name == "market_trade_value":
        return normalized.get("market_trade_value") or normalized.get("market_liquidity", "")
    return normalized.get(feature_name, "")


def _warning_set(*values: object) -> set[str]:
    warnings: set[str] = set()
    for value in values:
        for item in str(value or "").split("|"):
            clean = item.strip()
            if clean:
                warnings.add(clean)
    return warnings


def _first_present(warnings: set[str], candidates: tuple[str, ...]) -> str:
    for candidate in candidates:
        if candidate in warnings:
            return candidate
    return ""


def _is_blank(value: object) -> bool:
    return str(value or "").strip() == ""


def _is_default(value: object, default: float) -> bool:
    try:
        return abs(float(str(value).strip()) - default) <= 0.001
    except (TypeError, ValueError):
        return False


def _float(value: object, default: float) -> float:
    try:
        text = str(value or "").strip()
        if not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default

