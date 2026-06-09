from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from src.utils.scoring import clamp_score

MODEL_VERSION = "veteran_lve_v1_3_0"


class VeteranPosition(StrEnum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"


SOURCE_CONFIDENCE_SCORE = {
    "verified": 100.0,
    "derived": 88.0,
    "manual": 76.0,
    "estimated": 48.0,
    "unknown": 45.0,
}

PRIVATE_CONFIDENCE_EXCLUDED_FEATURES = frozenset({"market_liquidity"})


HORIZON_WEIGHTS = {
    "age_window": 35,
    "role_security": 25,
    "health_stability": 20,
    "skill_portability": 10,
    "team_commitment": 10,
}


@dataclass(frozen=True)
class VeteranInput:
    player_id: str
    player_name: str
    position: VeteranPosition
    age: float
    league_rank: int | None
    is_league_rank_top5: bool
    features: Mapping[str, float | None]
    missing_penalties: Mapping[str, float]
    source_reliability: Mapping[str, float]
    source_freshness: Mapping[str, float]
    source_confidence: Mapping[str, str]
    user_overrides: Mapping[str, bool]


@dataclass(frozen=True)
class VeteranFeatureContribution:
    player_id: str
    component: str
    feature_name: str
    normalized_score: float
    feature_weight: float
    component_contribution: float


@dataclass(frozen=True)
class VeteranScore:
    player_id: str
    player_name: str
    position: VeteranPosition
    model_version: str
    veteran_base_value: float
    horizon_retention_score: float
    keeper_score: float
    drop_candidate_score: float
    trade_value: float
    confidence_score: float
    lve_format_fit: float
    league_rank_signal: float
    top_five_release_pressure: float
    age_curve_adjustment: float
    role_adjustment: float
    injury_adjustment: float
    structural_adjustment: float
    league_rank_adjustment: float
    missing_data_penalty: float
    warning_status: str
    warning_reasons: tuple[str, ...]
    risk_flags: tuple[str, ...]
    upside_flags: tuple[str, ...]
    floor_flags: tuple[str, ...]
    contributions: tuple[VeteranFeatureContribution, ...]


def score_veteran(veteran: VeteranInput) -> VeteranScore:
    missing_penalty = missing_data_penalty(veteran)
    confidence = confidence_score(veteran, missing_penalty)
    base, base_contributions = _base_value(veteran)
    horizon, horizon_contributions = _horizon_retention_score(veteran)
    lve_fit, lve_contributions = _lve_format_fit(veteran)
    structural_adjustment = _structural_adjustment(veteran, base)
    keeper = keeper_score(base, horizon, confidence, lve_fit, structural_adjustment)
    league_rank_signal = league_rank_signal_score(veteran.league_rank)
    top_five_pressure = top_five_release_pressure(veteran.is_league_rank_top5, base)
    trade, trade_contributions = trade_value(
        veteran,
        base,
        keeper,
        confidence,
    )
    league_adjustment = league_rank_release_adjustment(veteran.is_league_rank_top5, keeper)
    drop = drop_candidate_score(
        veteran,
        base,
        keeper,
        trade,
        top_five_pressure,
        league_adjustment,
    )

    all_contributions = (
        *base_contributions,
        *horizon_contributions,
        *lve_contributions,
        *trade_contributions,
    )
    risk = risk_flags(veteran, base, keeper, drop, confidence)
    warnings = warning_reasons(veteran, missing_penalty, confidence, risk)
    return VeteranScore(
        player_id=veteran.player_id,
        player_name=veteran.player_name,
        position=veteran.position,
        model_version=MODEL_VERSION,
        veteran_base_value=round(base, 2),
        horizon_retention_score=round(horizon, 2),
        keeper_score=round(keeper, 2),
        drop_candidate_score=round(drop, 2),
        trade_value=round(trade, 2),
        confidence_score=round(confidence, 2),
        lve_format_fit=round(lve_fit, 2),
        league_rank_signal=round(league_rank_signal, 2),
        top_five_release_pressure=round(top_five_pressure, 2),
        age_curve_adjustment=0.0,
        role_adjustment=0.0,
        injury_adjustment=0.0,
        structural_adjustment=round(structural_adjustment, 2),
        league_rank_adjustment=round(league_adjustment, 2),
        missing_data_penalty=round(missing_penalty, 2),
        warning_status=warning_status(confidence, missing_penalty, risk, warnings),
        warning_reasons=warnings,
        risk_flags=risk,
        upside_flags=upside_flags(veteran, base, trade),
        floor_flags=floor_flags(veteran, keeper),
        contributions=all_contributions,
    )


def feature_score(value: float | None) -> float:
    if value is None:
        return 50.0
    return clamp_score(float(value))


def league_rank_signal_score(league_rank: int | None) -> float:
    if league_rank is None:
        return 50.0
    rank = clamp_score(float(league_rank), 1.0, 400.0)
    return round(clamp_score(100.0 - ((rank - 1.0) * 75.0 / 399.0), 20.0, 100.0), 2)


def top_five_release_pressure(is_top_five: bool, base_value: float) -> float:
    if not is_top_five:
        return 0.0
    return round(clamp_score((100.0 - base_value) * 0.25, 0.0, 12.0), 2)


def league_rank_release_adjustment(is_top_five: bool, keeper_value: float) -> float:
    # League-rank top-five status is rule pressure, not player quality.
    # Preserve the output field for audit/schema compatibility, but never feed
    # it into keeper/drop scoring.
    _ = is_top_five, keeper_value
    return 0.0


def keeper_score(
    base_value: float,
    horizon_retention: float,
    confidence: float,
    lve_format_fit: float,
    structural_adjustment: float,
) -> float:
    return clamp_score(
        (0.62 * base_value)
        + (0.23 * horizon_retention)
        + (0.10 * confidence)
        + (0.05 * lve_format_fit)
        + structural_adjustment
    )


def trade_value(
    veteran: VeteranInput,
    base_value: float,
    keeper_value: float,
    confidence: float,
) -> tuple[float, tuple[VeteranFeatureContribution, ...]]:
    market_value = _market_value(veteran, base_value)
    liquidity_adjustment = {
        VeteranPosition.QB: -6.0 if base_value < 92 else -1.0,
        VeteranPosition.RB: 0.0,
        VeteranPosition.WR: 3.0,
        VeteranPosition.TE: -7.0 if base_value < 88 else -1.0,
    }[veteran.position]
    trade = clamp_score(
        (0.50 * market_value)
        + (0.35 * keeper_value)
        + (0.15 * confidence)
        + liquidity_adjustment
    )
    contributions = (
        VeteranFeatureContribution(
            veteran.player_id,
            "trade_value",
            "market_liquidity_proxy",
            round(market_value, 2),
            50,
            round(market_value * 0.50, 4),
        ),
        VeteranFeatureContribution(
            veteran.player_id,
            "trade_value",
            "keeper_score",
            round(keeper_value, 2),
            35,
            round(keeper_value * 0.35, 4),
        ),
        VeteranFeatureContribution(
            veteran.player_id,
            "trade_value",
            "confidence_score",
            round(confidence, 2),
            15,
            round(confidence * 0.15, 4),
        ),
    )
    return trade, contributions


def missing_data_penalty(veteran: VeteranInput) -> float:
    penalty = sum(
        veteran.missing_penalties.get(feature_name, 0.0)
        for feature_name, value in veteran.features.items()
        if value is None and feature_name not in PRIVATE_CONFIDENCE_EXCLUDED_FEATURES
    )
    cap = 10.0 if veteran.position in {VeteranPosition.QB, VeteranPosition.TE} else 8.0
    return round(clamp_score(penalty * 0.35, 0.0, cap), 2)


def confidence_score(veteran: VeteranInput, missing_penalty: float) -> float:
    feature_names = _private_feature_names(veteran)
    if not feature_names:
        return 0.0
    present_features = [name for name in feature_names if veteran.features.get(name) is not None]
    coverage = 100.0 * len(present_features) / len(feature_names)
    source_reliability = _average(
        veteran.source_reliability.get(name, 50.0) for name in present_features
    )
    source_freshness = _average(
        veteran.source_freshness.get(name, 50.0) for name in present_features
    )
    source_confidence = _average(
        SOURCE_CONFIDENCE_SCORE.get(veteran.source_confidence.get(name, "unknown"), 45.0)
        for name in present_features
    )
    observed_scores = [feature_score(veteran.features.get(name)) for name in present_features]
    agreement = 100.0 - (_spread(observed_scores) * 0.55)
    override_penalty = sum(3.0 for value in veteran.user_overrides.values() if value)
    combined_source_reliability = (0.65 * source_reliability) + (0.35 * source_confidence)
    confidence = (
        (0.40 * coverage)
        + (0.25 * combined_source_reliability)
        + (0.20 * source_freshness)
        + (0.15 * agreement)
        - missing_penalty
        - _estimated_private_feature_penalty(veteran)
        - override_penalty
    )
    return clamp_score(confidence)


def warning_status(
    confidence: float,
    missing_penalty: float,
    risk_flags_value: tuple[str, ...],
    warning_reasons_value: tuple[str, ...],
) -> str:
    if confidence < 40:
        return "blocking"
    if confidence < 65 or missing_penalty >= 6 or "low_confidence" in risk_flags_value:
        return "review_needed"
    if any(reason.startswith("review_needed") for reason in warning_reasons_value):
        return "review_needed"
    if any(reason.startswith("model_") for reason in warning_reasons_value):
        return "model_warning"
    if any(reason.startswith("data_") for reason in warning_reasons_value):
        return "data_warning"
    return "ready"


def warning_reasons(
    veteran: VeteranInput,
    missing_penalty: float,
    confidence: float,
    risk_flags_value: tuple[str, ...],
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if confidence < 40:
        reasons.add("blocking_low_confidence")
    elif confidence < 65:
        reasons.add("review_needed_low_confidence")
    elif confidence < 75:
        reasons.add("data_warning_confidence_below_target")
    if missing_penalty >= 6:
        reasons.add("review_needed_missing_core_inputs")
    elif missing_penalty > 0:
        reasons.add("data_warning_missing_inputs")
    if any(veteran.user_overrides.values()):
        reasons.add("review_needed_manual_override")
    if _average(veteran.source_freshness.values()) < 60:
        reasons.add("data_warning_stale_sources")
    if "role_fragility" in risk_flags_value or "keeper_bubble" in risk_flags_value:
        reasons.add("model_warning_role_or_keeper_fragility")
    estimated_private_features = _estimated_private_feature_names(veteran)
    if len(estimated_private_features) >= 3:
        reasons.add("review_needed_estimated_private_features")
    elif len(estimated_private_features) >= 2:
        reasons.add("data_warning_estimated_private_features")
    if (
        veteran.position in {VeteranPosition.QB, VeteranPosition.TE}
        and any("replaceable" in flag for flag in risk_flags_value)
    ):
        reasons.add("model_warning_lve_replacement_drag")
    return tuple(sorted(reasons))


def _private_feature_names(veteran: VeteranInput) -> tuple[str, ...]:
    return tuple(
        name
        for name in veteran.features
        if name not in PRIVATE_CONFIDENCE_EXCLUDED_FEATURES
    )


def _estimated_private_feature_names(veteran: VeteranInput) -> tuple[str, ...]:
    return tuple(
        name
        for name in _private_feature_names(veteran)
        if veteran.features.get(name) is not None
        and veteran.source_confidence.get(name, "unknown") == "estimated"
    )


def _estimated_private_feature_penalty(veteran: VeteranInput) -> float:
    return min(8.0, len(_estimated_private_feature_names(veteran)) * 2.0)


def _base_value(
    veteran: VeteranInput,
) -> tuple[float, tuple[VeteranFeatureContribution, ...]]:
    if veteran.position == VeteranPosition.QB:
        items = (
            _item(veteran, "start_security", 28, "role_security"),
            _item(veteran, "passing_td_yardage_output", 20, "lve_projection_value"),
            _item(veteran, "rushing_value", 15, "position_replaceability"),
            _item(veteran, "passing_efficiency_epa", 12, "lve_projection_value"),
            _item(veteran, "sack_avoidance", 10, "role_security"),
            _item(veteran, "age_curve_archetype", 8, "age_curve"),
            _item(veteran, "current_injury_durability", 7, "injury_durability", default=76),
        )
    elif veteran.position == VeteranPosition.RB:
        items = (
            _item(veteran, "touch_share", 22, "role_security"),
            _item(veteran, "high_value_touches", 18, "first_down_td_fit"),
            _item(veteran, "goal_line_short_yardage_role", 14, "first_down_td_fit"),
            _item(veteran, "receiving_role_no_ppr_adjusted", 12, "lve_projection_value"),
            _item(veteran, "rush_efficiency_creation", 10, "lve_projection_value"),
            _item(veteran, "first_down_conversion_profile", 8, "first_down_td_fit"),
            _item(veteran, "offense_environment_line", 6, "lve_projection_value"),
            _item(veteran, "age_curve", 10),
            _item(veteran, "injury_durability", 10),
        )
    elif veteran.position == VeteranPosition.WR:
        items = (
            _item(veteran, "target_share", 16, "target_earning_stability"),
            _item(veteran, "route_participation", 14, "role_security"),
            _item(veteran, "targets_per_route_run", 14, "target_earning_stability"),
            _item(veteran, "yards_per_route_run", 13, "lve_projection_value"),
            _item(veteran, "first_downs_per_route", 8, "target_earning_stability"),
            _item(veteran, "get_open_role_robustness", 10, "role_security"),
            _item(veteran, "td_area_air_yards_role", 7, "lve_projection_value"),
            _item(veteran, "offense_environment", 6, "lve_projection_value"),
            _item(veteran, "age_curve", 7),
            _item(veteran, "injury_durability", 5, default=78),
        )
    else:
        items = (
            _item(veteran, "route_participation", 20, "route_share_stability"),
            _item(veteran, "target_earning", 18, "lve_projection_value"),
            _item(veteran, "yards_per_route_run", 16, "lve_projection_value"),
            _item(veteran, "blocking_suppression_inverse", 12, "position_replaceability"),
            _item(veteran, "td_area_adot_role", 8, "lve_projection_value"),
            _item(veteran, "first_down_profile", 6, "route_share_stability"),
            _item(veteran, "age_curve", 8),
            _item(veteran, "injury_durability", 6, default=76),
            _item(veteran, "offense_environment", 6, "lve_projection_value"),
        )
    return _weighted_items(veteran.player_id, "veteran_base_value", items)


def _horizon_retention_score(
    veteran: VeteranInput,
) -> tuple[float, tuple[VeteranFeatureContribution, ...]]:
    skill_portability = {
        VeteranPosition.QB: _feature(
            veteran,
            "passing_efficiency_epa",
            "sack_avoidance",
            "lve_projection_value",
        ),
        VeteranPosition.RB: _feature(veteran, "receiving_role_no_ppr_adjusted", "role_security"),
        VeteranPosition.WR: _feature(veteran, "target_share", "target_earning_stability"),
        VeteranPosition.TE: _feature(veteran, "target_earning", "route_share_stability"),
    }[veteran.position]
    items = (
        ("age_window", _feature(veteran, "age_curve"), HORIZON_WEIGHTS["age_window"]),
        (
            "role_security",
            _feature(veteran, "start_security", "role_security", "route_share_stability"),
            HORIZON_WEIGHTS["role_security"],
        ),
        (
            "health_stability",
            _feature(veteran, "injury_durability", "current_injury_durability", default=78),
            HORIZON_WEIGHTS["health_stability"],
        ),
        ("skill_portability", skill_portability, HORIZON_WEIGHTS["skill_portability"]),
        (
            "team_commitment",
            _feature(veteran, "team_commitment_contract", "role_security", default=60),
            HORIZON_WEIGHTS["team_commitment"],
        ),
    )
    return _weighted_items(veteran.player_id, "horizon_retention_score", items)


def _lve_format_fit(
    veteran: VeteranInput,
) -> tuple[float, tuple[VeteranFeatureContribution, ...]]:
    if veteran.position == VeteranPosition.QB:
        items = (
            _item(veteran, "rushing_value", 45, "position_replaceability"),
            _item(veteran, "passing_td_yardage_output", 25, "lve_projection_value"),
            _item(veteran, "start_security", 20, "role_security"),
            _item(veteran, "position_replaceability", 10),
        )
    elif veteran.position == VeteranPosition.RB:
        items = (
            _item(veteran, "first_down_conversion_profile", 30, "first_down_td_fit"),
            _item(veteran, "goal_line_short_yardage_role", 30, "first_down_td_fit"),
            _item(veteran, "touch_share", 25, "role_security"),
            _item(veteran, "receiving_role_no_ppr_adjusted", 15, "lve_projection_value"),
        )
    elif veteran.position == VeteranPosition.WR:
        items = (
            _item(veteran, "route_participation", 30, "role_security"),
            _item(veteran, "target_share", 25, "target_earning_stability"),
            _item(veteran, "first_downs_per_route", 20, "target_earning_stability"),
            _item(veteran, "yards_per_route_run", 15, "lve_projection_value"),
            _item(veteran, "lve_projection_value", 10),
        )
    else:
        items = (
            _item(veteran, "route_participation", 35, "route_share_stability"),
            _item(veteran, "target_earning", 25, "lve_projection_value"),
            _item(veteran, "yards_per_route_run", 20, "lve_projection_value"),
            _item(veteran, "position_replaceability", 20),
        )
    return _weighted_items(veteran.player_id, "lve_format_fit", items)


def _structural_adjustment(veteran: VeteranInput, base_value: float) -> float:
    if veteran.position == VeteranPosition.QB:
        rushing = _feature(veteran, "rushing_value", "position_replaceability")
        elite = base_value >= 88 and rushing >= 85
        return -3.0 if elite else -10.0
    if veteran.position == VeteranPosition.TE:
        route_role = _feature(veteran, "route_participation", "route_share_stability")
        target_earning = _feature(veteran, "target_earning", "lve_projection_value")
        elite = base_value >= 88 and route_role >= 85 and target_earning >= 85
        return -2.0 if elite else -8.0
    if veteran.position == VeteranPosition.RB:
        role = _feature(veteran, "touch_share", "role_security")
        high_value = _feature(veteran, "high_value_touches", "first_down_td_fit")
        goal_line = _feature(veteran, "goal_line_short_yardage_role", "first_down_td_fit")
        durability = _feature(veteran, "injury_durability", default=76)
        elite_lve_role = (
            base_value >= 88
            and role >= 84
            and high_value >= 84
            and goal_line >= 82
            and durability >= 70
        )
        strong_lve_role = (
            base_value >= 84
            and role >= 80
            and high_value >= 80
            and goal_line >= 76
            and durability >= 68
        )
        if elite_lve_role:
            return 2.5
        if strong_lve_role:
            return 1.25
        return 0.0
    if veteran.position == VeteranPosition.WR:
        target_earning = _feature(veteran, "target_share", "target_earning_stability")
        role = _feature(veteran, "route_participation", "role_security")
        if target_earning >= 82 and role >= 82:
            return 2.0
        return 1.0
    return 0.0


def drop_candidate_score(
    veteran: VeteranInput,
    base_value: float,
    keeper_value: float,
    trade_value_score: float,
    top_five_pressure: float,
    league_adjustment: float,
) -> float:
    # Football cut risk only. Market salvage and forced-release rule pressure
    # belong in shop/action strategy layers, not in the player score.
    _ = trade_value_score, top_five_pressure, league_adjustment
    replaceability_drag = _replaceability_drag(veteran)
    age_role_risk = _age_role_risk(veteran)
    role_collapse_penalty = clamp_score((100.0 - _role_score(veteran)) * 0.20, 0.0, 12.0)
    health_uncertainty_penalty = clamp_score(
        (100.0 - _feature(veteran, "injury_durability", default=78)) * 0.12,
        0.0,
        8.0,
    )
    score = (
        (0.42 * (100.0 - keeper_value))
        + (0.16 * (100.0 - base_value))
        + (0.10 * replaceability_drag)
        + (0.10 * age_role_risk)
        + role_collapse_penalty
        + health_uncertainty_penalty
    )
    return clamp_score(score)


def risk_flags(
    veteran: VeteranInput,
    base_value: float,
    keeper_value: float,
    drop_value: float,
    confidence: float,
) -> tuple[str, ...]:
    flags: set[str] = set()
    if confidence < 65:
        flags.add("low_confidence")
    if veteran.is_league_rank_top5 and drop_value >= 55:
        flags.add("top_five_release_pressure")
    if _role_score(veteran) < 60:
        flags.add("role_fragility")
    if (
        veteran.position == VeteranPosition.RB
        and feature_score(veteran.features.get("age_curve")) < 50
    ):
        flags.add("aging_rb")
    if (
        veteran.position == VeteranPosition.TE
        and feature_score(veteran.features.get("age_curve")) < 45
    ):
        flags.add("aging_te")
    if (
        "injury_durability" in veteran.features
        and feature_score(veteran.features.get("injury_durability")) < 60
    ):
        flags.add("injury_risk")
    if veteran.position == VeteranPosition.RB:
        if _feature(veteran, "touch_share", "role_security") < 60:
            flags.add("committee_risk")
        if _feature(veteran, "goal_line_short_yardage_role", "first_down_td_fit") < 45:
            flags.add("goal_line_fragility")
        if (
            _feature(veteran, "receiving_role_no_ppr_adjusted", "lve_projection_value") >= 80
            and _feature(veteran, "goal_line_short_yardage_role", "first_down_td_fit") < 50
        ):
            flags.add("no_ppr_satellite")
    if veteran.position == VeteranPosition.WR:
        if _feature(veteran, "target_share", "target_earning_stability") < 50:
            flags.add("weak_target_earning")
        if _feature(veteran, "route_participation", "role_security") < 60:
            flags.add("route_role_fragility")
    if (
        veteran.position == VeteranPosition.TE
        and _feature(veteran, "route_participation", "route_share_stability") < 65
    ):
        flags.add("blocking_dependency_risk")
    if (
        veteran.position == VeteranPosition.QB
        and feature_score(veteran.features.get("position_replaceability")) < 75
    ):
        flags.add("replaceable_1qb_profile")
    if (
        veteran.position == VeteranPosition.TE
        and feature_score(veteran.features.get("position_replaceability")) < 75
    ):
        flags.add("replaceable_no_premium_te")
    if base_value < 62 or keeper_value < 62:
        flags.add("keeper_bubble")
    return tuple(sorted(flags))


def upside_flags(veteran: VeteranInput, base_value: float, trade_value: float) -> tuple[str, ...]:
    flags: set[str] = set()
    if base_value >= 88:
        flags.add("elite_lve_value")
    if trade_value >= 85:
        flags.add("strong_trade_liquidity")
    if (
        veteran.position == VeteranPosition.RB
        and _feature(veteran, "first_down_conversion_profile", "first_down_td_fit") >= 85
    ):
        flags.add("first_down_td_engine")
    if (
        veteran.position == VeteranPosition.WR
        and _feature(veteran, "target_share", "target_earning_stability") >= 85
    ):
        flags.add("stable_target_earner")
    if (
        veteran.position == VeteranPosition.TE
        and _feature(veteran, "route_participation", "route_share_stability") >= 85
    ):
        flags.add("difference_making_te_routes")
    if (
        veteran.position == VeteranPosition.QB
        and feature_score(veteran.features.get("position_replaceability")) >= 85
    ):
        flags.add("elite_qb_edge")
    return tuple(sorted(flags))


def floor_flags(veteran: VeteranInput, keeper_value: float) -> tuple[str, ...]:
    flags: set[str] = set()
    if keeper_value >= 80:
        flags.add("strong_keeper")
    if _role_score(veteran) >= 80:
        flags.add("secure_role")
    if (
        "injury_durability" in veteran.features
        and feature_score(veteran.features.get("injury_durability")) >= 75
    ):
        flags.add("clean_durability")
    if (
        veteran.position in {VeteranPosition.WR, VeteranPosition.RB}
        and feature_score(veteran.features.get("lve_projection_value")) >= 85
    ):
        flags.add("flex_demand_edge")
    return tuple(sorted(flags))


def _item(
    veteran: VeteranInput,
    feature_name: str,
    weight: float,
    *fallbacks: str,
    default: float = 50.0,
) -> tuple[str, float, float]:
    return (feature_name, _feature(veteran, feature_name, *fallbacks, default=default), weight)


def _feature(
    veteran: VeteranInput,
    feature_name: str,
    *fallbacks: str,
    default: float = 50.0,
) -> float:
    for candidate in (feature_name, *fallbacks):
        if candidate in veteran.features and veteran.features[candidate] is not None:
            return feature_score(veteran.features[candidate])
    return clamp_score(default)


def _role_score(veteran: VeteranInput) -> float:
    if veteran.position == VeteranPosition.TE:
        return _feature(veteran, "route_participation", "route_share_stability", "role_security")
    if veteran.position == VeteranPosition.WR:
        return _feature(veteran, "route_participation", "role_security")
    if veteran.position == VeteranPosition.RB:
        return _feature(veteran, "touch_share", "role_security")
    return _feature(veteran, "start_security", "role_security")


def _market_value(veteran: VeteranInput, base_value: float) -> float:
    if "market_liquidity" in veteran.features:
        return _feature(veteran, "market_liquidity")
    if veteran.position == VeteranPosition.QB:
        return clamp_score((0.70 * base_value) + (0.30 * _feature(veteran, "role_security")))
    if veteran.position == VeteranPosition.TE:
        return clamp_score(
            (0.65 * base_value) + (0.35 * _feature(veteran, "route_share_stability"))
        )
    return base_value


def _weighted_items(
    player_id: str,
    component: str,
    items: tuple[tuple[str, float, float], ...],
) -> tuple[float, tuple[VeteranFeatureContribution, ...]]:
    denominator = sum(weight for _, _, weight in items)
    if denominator <= 0:
        return 50.0, ()
    total = 0.0
    contributions: list[VeteranFeatureContribution] = []
    for feature_name, score, weight in items:
        contribution = score * weight / denominator
        total += contribution
        contributions.append(
            VeteranFeatureContribution(
                player_id=player_id,
                component=component,
                feature_name=feature_name,
                normalized_score=round(score, 2),
                feature_weight=weight,
                component_contribution=round(contribution, 4),
            )
        )
    return round(clamp_score(total), 2), tuple(contributions)


def _weighted_component(
    player_id: str,
    component: str,
    features: Mapping[str, float | None],
    weights: Mapping[str, float],
) -> tuple[float, tuple[VeteranFeatureContribution, ...]]:
    denominator = sum(weights.values())
    if denominator <= 0:
        return 50.0, ()
    contributions: list[VeteranFeatureContribution] = []
    total = 0.0
    for feature_name, weight in weights.items():
        score = feature_score(features.get(feature_name))
        contribution = score * weight / denominator
        total += contribution
        contributions.append(
            VeteranFeatureContribution(
                player_id=player_id,
                component=component,
                feature_name=feature_name,
                normalized_score=round(score, 2),
                feature_weight=weight,
                component_contribution=round(contribution, 4),
            )
        )
    return round(clamp_score(total), 2), tuple(contributions)


def _position_adjusted_base(
    position: VeteranPosition,
    raw_base: float,
    features: Mapping[str, float | None],
) -> float:
    adjusted = raw_base
    if (
        position == VeteranPosition.QB
        and feature_score(features.get("position_replaceability")) < 75
        and feature_score(features.get("lve_projection_value")) < 90
    ):
        adjusted -= 4.0
    if (
        position == VeteranPosition.TE
        and feature_score(features.get("position_replaceability")) < 75
        and feature_score(features.get("lve_projection_value")) < 88
    ):
        adjusted -= 5.0
    return clamp_score(adjusted)


def _position_adjusted_trade(
    position: VeteranPosition,
    raw_trade: float,
    features: Mapping[str, float | None],
) -> float:
    adjusted = raw_trade
    if position == VeteranPosition.QB and feature_score(features.get("lve_projection_value")) < 88:
        adjusted -= 5.0
    if (
        position == VeteranPosition.TE
        and feature_score(features.get("position_replaceability")) < 75
    ):
        adjusted -= 6.0
    if position == VeteranPosition.RB and feature_score(features.get("age_curve")) < 50:
        adjusted -= 5.0
    return clamp_score(adjusted)


def _age_curve_adjustment(veteran: VeteranInput) -> float:
    age_curve = feature_score(veteran.features.get("age_curve"))
    multiplier = 0.09 if veteran.position == VeteranPosition.RB else 0.07
    return clamp_score((age_curve - 50.0) * multiplier, -5.0, 5.0)


def _role_adjustment(veteran: VeteranInput) -> float:
    role_security = feature_score(veteran.features.get("role_security"))
    return clamp_score((role_security - 50.0) * 0.05, -3.0, 3.0)


def _injury_adjustment(veteran: VeteranInput) -> float:
    if "injury_durability" not in veteran.features:
        return 0.0
    injury = feature_score(veteran.features.get("injury_durability"))
    return clamp_score((injury - 50.0) * 0.06, -4.0, 4.0)


def _replaceability_drag(veteran: VeteranInput) -> float:
    if "position_replaceability" in veteran.features:
        return 100.0 - feature_score(veteran.features.get("position_replaceability"))
    return 100.0 - feature_score(veteran.features.get("role_security"))


def _age_role_risk(veteran: VeteranInput) -> float:
    age_risk = 100.0 - feature_score(veteran.features.get("age_curve"))
    role_risk = 100.0 - feature_score(veteran.features.get("role_security"))
    injury_risk = 100.0 - feature_score(veteran.features.get("injury_durability"))
    return clamp_score((0.45 * age_risk) + (0.35 * role_risk) + (0.20 * injury_risk))


def _average(values) -> float:
    value_list = list(values)
    if not value_list:
        return 50.0
    return sum(value_list) / len(value_list)


def _spread(values: list[float]) -> float:
    if not values:
        return 0.0
    return max(values) - min(values)
