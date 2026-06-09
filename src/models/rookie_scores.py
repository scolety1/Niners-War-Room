from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from src.utils.scoring import clamp_score

MODEL_VERSION = "rookie_lve_v1_0_0"


class Position(StrEnum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"


class ModelMode(StrEnum):
    PRE_DRAFT = "pre_draft"
    POST_DRAFT = "post_draft"


POSITIONS = {position.value for position in Position}

FINAL_WEIGHTS = {
    "main_prospect_score": 0.62,
    "league_fit_score": 0.12,
    "rookie_opportunity_score": 0.10,
    "long_term_dynasty_score": 0.10,
    "trade_insulation_score": 0.06,
}

FEATURES_BY_POSITION = {
    Position.QB: (
        "draft_capital",
        "rushing_profile",
        "passing_efficiency",
        "sack_avoidance",
        "age_trajectory",
    ),
    Position.RB: (
        "draft_capital",
        "workload_earning",
        "rush_efficiency",
        "receiving_impact",
        "goal_line_power",
        "age_trajectory",
    ),
    Position.WR: (
        "draft_capital",
        "target_earning",
        "efficiency_dominance",
        "age_trajectory",
        "chain_moving",
    ),
    Position.TE: (
        "draft_capital",
        "receiving_efficiency",
        "route_role",
        "production_volume",
        "athletic_size",
        "age_trajectory",
    ),
}

MAIN_WEIGHTS = {
    Position.QB: {
        "draft_capital": 28,
        "rushing_profile": 26,
        "passing_efficiency": 20,
        "sack_avoidance": 16,
        "age_trajectory": 10,
    },
    Position.RB: {
        "draft_capital": 26,
        "workload_earning": 22,
        "rush_efficiency": 16,
        "receiving_impact": 14,
        "goal_line_power": 12,
        "age_trajectory": 10,
    },
    Position.WR: {
        "draft_capital": 24,
        "target_earning": 24,
        "efficiency_dominance": 24,
        "age_trajectory": 16,
        "chain_moving": 12,
    },
    Position.TE: {
        "draft_capital": 30,
        "receiving_efficiency": 22,
        "route_role": 18,
        "production_volume": 14,
        "athletic_size": 8,
        "age_trajectory": 8,
    },
}

VETERAN_CAPS = {
    Position.QB: (-14.0, 3.0),
    Position.RB: (-10.0, 5.0),
    Position.WR: (-10.0, 5.0),
    Position.TE: (-12.0, 3.0),
}

MISSING_CAPS = {
    Position.QB: 12.0,
    Position.RB: 10.0,
    Position.WR: 10.0,
    Position.TE: 12.0,
}

POSITION_FLOORS = {
    Position.QB: 11,
    Position.RB: 1,
    Position.WR: 1,
    Position.TE: 16,
}


@dataclass(frozen=True)
class RookieInput:
    player_id: str
    player_name: str
    position: Position
    class_year: int
    model_mode: ModelMode
    source_snapshot_id: str
    source_name: str
    source_date: str
    features: Mapping[str, float | None]
    feature_sources: Mapping[str, str] | None = None
    rookie_opportunity_score: float | None = None
    veteran_benchmark_score: float | None = None


@dataclass(frozen=True)
class RookieScore:
    player_id: str
    player_name: str
    position: Position
    model_version: str
    main_prospect_score: float
    league_fit_score: float
    rookie_opportunity_score: float
    long_term_dynasty_score: float
    trade_insulation_score: float
    internal_score: float
    confidence_score: float
    veteran_benchmark_score: float
    veteran_delta: float
    veteran_opportunity_adjustment: float
    gate_applied: str
    gate_reason: str
    gate_adjustment: float
    exceptional_profile_flag: bool
    missing_data_penalty: float
    final_decision_score: float
    recommended_pick_min: int
    recommended_pick_max: int
    recommended_range_label: str
    do_not_draft_before_pick: int
    risk_flags: tuple[str, ...]
    upside_flags: tuple[str, ...]
    floor_flags: tuple[str, ...]


def weighted_average(items: Mapping[str, float | None], weights: Mapping[str, float]) -> float:
    numerator = 0.0
    denominator = 0.0
    for feature, weight in weights.items():
        numerator += feature_score(items.get(feature)) * weight
        denominator += weight
    if denominator <= 0:
        return 50.0
    return round(clamp_score(numerator / denominator), 2)


def feature_score(value: float | None) -> float:
    if value is None:
        return 50.0
    return clamp_score(float(value))


def score_rookie(rookie: RookieInput) -> RookieScore:
    features = rookie.features
    main = weighted_average(features, MAIN_WEIGHTS[rookie.position])
    league_fit = _league_fit(rookie.position, features)
    opportunity = _rookie_opportunity(rookie)
    long_term = _long_term_dynasty(rookie.position, features)
    trade = _trade_insulation(rookie.position, features)
    internal = _internal_score(main, league_fit, opportunity, long_term, trade)

    missing_penalty = missing_data_penalty(rookie.position, features)
    confidence = confidence_score(rookie.position, features, missing_penalty)
    exceptional = exceptional_profile(rookie.position, features)
    gate_adjustment, gate_applied, gate_reason = gate_for(rookie.position, features, exceptional)

    benchmark = feature_score(rookie.veteran_benchmark_score)
    veteran_delta = round(internal - benchmark, 2)
    veteran_adj = veteran_opportunity_adjustment(rookie.position, internal, benchmark)
    pre_range_score = clamp_score(internal + veteran_adj + gate_adjustment - missing_penalty)
    final = _apply_confidence_cap(pre_range_score, confidence, features, rookie.position)
    min_pick = do_not_draft_before_pick(
        rookie.position,
        final,
        confidence,
        veteran_adj,
        gate_applied,
        features,
    )
    max_pick = min(50, min_pick + (2 if confidence >= 85 else 4 if confidence >= 70 else 6))

    components = {
        "rookie_opportunity_score": opportunity,
        "trade_insulation_score": trade,
        "veteran_opportunity_adjustment": veteran_adj,
        "gate_adjustment": gate_adjustment,
    }
    risk = risk_flags(rookie.position, features, components, confidence)
    upside = upside_flags(rookie.position, features, components, exceptional)
    floor = floor_flags(features, components)
    return RookieScore(
        player_id=rookie.player_id,
        player_name=rookie.player_name,
        position=rookie.position,
        model_version=MODEL_VERSION,
        main_prospect_score=main,
        league_fit_score=league_fit,
        rookie_opportunity_score=opportunity,
        long_term_dynasty_score=long_term,
        trade_insulation_score=trade,
        internal_score=internal,
        confidence_score=confidence,
        veteran_benchmark_score=benchmark,
        veteran_delta=veteran_delta,
        veteran_opportunity_adjustment=veteran_adj,
        gate_applied=gate_applied,
        gate_reason=gate_reason,
        gate_adjustment=gate_adjustment,
        exceptional_profile_flag=exceptional,
        missing_data_penalty=missing_penalty,
        final_decision_score=round(final, 2),
        recommended_pick_min=min_pick,
        recommended_pick_max=max_pick,
        recommended_range_label=f"{pick_label(min_pick)}-{pick_label(max_pick)}",
        do_not_draft_before_pick=min_pick,
        risk_flags=risk,
        upside_flags=upside,
        floor_flags=floor,
    )


def missing_data_penalty(position: Position, features: Mapping[str, float | None]) -> float:
    missing = sum(1 for feature in FEATURES_BY_POSITION[position] if features.get(feature) is None)
    raw = missing * 3.5
    return round(clamp_score(raw, 0.0, MISSING_CAPS[position]), 2)


def confidence_score(
    position: Position,
    features: Mapping[str, float | None],
    missing_penalty: float,
) -> float:
    total = len(FEATURES_BY_POSITION[position])
    present = total - sum(
        1 for feature in FEATURES_BY_POSITION[position] if features.get(feature) is None
    )
    coverage = 100.0 * present / total
    core_values = [
        feature_score(features.get(feature)) for feature in FEATURES_BY_POSITION[position]
    ]
    agreement = max(0.0, 100.0 - (_spread(core_values) * 1.15))
    score = (coverage * 0.65) + (agreement * 0.20) + 15.0 - (missing_penalty * 1.25)
    return round(clamp_score(score), 2)


def veteran_opportunity_adjustment(
    position: Position,
    internal_score: float,
    benchmark_score: float,
) -> float:
    low, high = VETERAN_CAPS[position]
    return round(clamp_score((internal_score - benchmark_score) * 0.35, low, high), 2)


def exceptional_profile(position: Position, features: Mapping[str, float | None]) -> bool:
    if position == Position.QB:
        return feature_score(features.get("draft_capital")) >= 85 and (
            feature_score(features.get("rushing_profile")) >= 85
            or (
                feature_score(features.get("passing_efficiency")) >= 92
                and feature_score(features.get("sack_avoidance")) >= 75
            )
        )
    if position == Position.TE:
        return (
            feature_score(features.get("draft_capital")) >= 85
            and feature_score(features.get("receiving_efficiency")) >= 85
            and feature_score(features.get("route_role")) >= 80
            and feature_score(features.get("athletic_size")) >= 70
        )
    return False


def gate_for(
    position: Position,
    features: Mapping[str, float | None],
    exceptional: bool,
) -> tuple[float, str, str]:
    if position == Position.QB:
        if exceptional:
            return 0.0, "qb_elite_exempt", "Premium QB profile clears 1QB suppression."
        if feature_score(features.get("draft_capital")) < 55:
            return -14.0, "qb_low_capital_penalty", "Low-capital QB in a 10-team 1QB league."
        return -8.0, "qb_structural_penalty", "Non-exceptional QB held down by 1QB format."
    if position == Position.TE:
        if exceptional:
            return 0.0, "te_elite_exempt", "Premium TE clears no-premium suppression."
        if feature_score(features.get("draft_capital")) < 50:
            return -18.0, "te_day3_penalty", "Low-capital TE suppressed in no-premium format."
        return -12.0, "te_structural_penalty", "Non-exceptional TE held down by no-premium format."
    return 0.0, "none", ""


def do_not_draft_before_pick(
    position: Position,
    final_score: float,
    confidence: float,
    veteran_adjustment: float,
    gate_applied: str,
    features: Mapping[str, float | None],
) -> int:
    base_pick = score_to_pick(final_score)
    floor = POSITION_FLOORS[position]
    if gate_applied in {"qb_elite_exempt", "te_elite_exempt"}:
        floor = 4 if position == Position.QB else 11
    if position == Position.QB and feature_score(features.get("draft_capital")) < 55:
        floor = 21
    if position == Position.TE and feature_score(features.get("draft_capital")) < 50:
        floor = 31
    if veteran_adjustment <= -6:
        base_pick += 4
    elif veteran_adjustment <= -3:
        base_pick += 2
    if confidence < 60:
        base_pick += 3
    elif confidence < 75:
        base_pick += 1
    return int(clamp_score(max(base_pick, floor), 1, 50))


def score_to_pick(score: float) -> int:
    if score >= 90:
        return 1
    if score >= 86:
        return 2
    if score >= 82:
        return 4
    if score >= 78:
        return 6
    if score >= 74:
        return 8
    if score >= 70:
        return 11
    if score >= 66:
        return 14
    if score >= 62:
        return 18
    if score >= 58:
        return 22
    if score >= 54:
        return 27
    if score >= 50:
        return 31
    if score >= 46:
        return 36
    if score >= 42:
        return 41
    return 46


def pick_label(pick: int) -> str:
    round_number = ((pick - 1) // 10) + 1
    round_pick = ((pick - 1) % 10) + 1
    return f"{round_number}.{round_pick:02d}"


def risk_flags(
    position: Position,
    features: Mapping[str, float | None],
    scores: Mapping[str, float],
    confidence: float,
) -> tuple[str, ...]:
    flags: set[str] = set()
    if confidence < 60:
        flags.add("low_confidence")
    if scores["veteran_opportunity_adjustment"] <= -6:
        flags.add("loses_to_veteran_market")
    elif scores["veteran_opportunity_adjustment"] <= -3:
        flags.add("veteran_opportunity_drag")
    if scores["gate_adjustment"] < 0:
        flags.add(f"{position.value.lower()}_suppression")
    if position == Position.QB and feature_score(features.get("rushing_profile")) < 45:
        flags.add("pocket_qb_only")
    if position == Position.RB:
        if feature_score(features.get("workload_earning")) < 55:
            flags.add("committee_risk")
        if (
            feature_score(features.get("receiving_impact")) >= 70
            and feature_score(features.get("goal_line_power")) < 45
        ):
            flags.add("no_ppr_satellite")
    if position == Position.WR:
        if feature_score(features.get("target_earning")) < 45:
            flags.add("weak_target_earning")
        if feature_score(features.get("age_trajectory")) < 40:
            flags.add("old_for_class")
    if position == Position.TE and feature_score(features.get("route_role")) < 55:
        flags.add("blocking_dependency_risk")
    return tuple(sorted(flags))


def upside_flags(
    position: Position,
    features: Mapping[str, float | None],
    scores: Mapping[str, float],
    exceptional: bool,
) -> tuple[str, ...]:
    flags: set[str] = set()
    if scores["veteran_opportunity_adjustment"] >= 3:
        flags.add("beats_veteran_market")
    if position == Position.QB and feature_score(features.get("rushing_profile")) >= 85:
        flags.add("weekly_ceiling")
        if exceptional:
            flags.add("elite_dual_threat_qb")
    if position == Position.RB:
        if (
            feature_score(features.get("workload_earning")) >= 80
            and feature_score(features.get("goal_line_power")) >= 75
        ):
            flags.add("three_down_goal_line_rb")
    if position == Position.WR:
        if (
            feature_score(features.get("target_earning")) >= 85
            and feature_score(features.get("efficiency_dominance")) >= 80
        ):
            flags.add("alpha_target_earner")
    if position == Position.TE:
        if exceptional:
            flags.add("exceptional_te_gate")
        if feature_score(features.get("receiving_efficiency")) >= 85:
            flags.add("difference_making_receiver")
    return tuple(sorted(flags))


def floor_flags(
    features: Mapping[str, float | None],
    scores: Mapping[str, float],
) -> tuple[str, ...]:
    flags: set[str] = set()
    if feature_score(features.get("draft_capital")) >= 70:
        flags.add("day1_or_day2_capital")
    if scores["rookie_opportunity_score"] >= 75:
        flags.add("immediate_role_path")
    if scores["trade_insulation_score"] >= 75:
        flags.add("trade_insulation")
    return tuple(sorted(flags))


def _league_fit(position: Position, features: Mapping[str, float | None]) -> float:
    if position == Position.QB:
        return weighted_average(
            features,
            {"rushing_profile": 55, "sack_avoidance": 25, "passing_efficiency": 20},
        )
    if position == Position.RB:
        return weighted_average(
            features,
            {
                "goal_line_power": 40,
                "workload_earning": 30,
                "rush_efficiency": 20,
                "receiving_impact": 10,
            },
        )
    if position == Position.WR:
        return weighted_average(
            features,
            {"chain_moving": 40, "target_earning": 30, "efficiency_dominance": 30},
        )
    return weighted_average(
        features,
        {"route_role": 45, "receiving_efficiency": 35, "production_volume": 20},
    )


def _rookie_opportunity(rookie: RookieInput) -> float:
    if rookie.model_mode == ModelMode.PRE_DRAFT:
        return 50.0
    return feature_score(rookie.rookie_opportunity_score)


def _long_term_dynasty(position: Position, features: Mapping[str, float | None]) -> float:
    if position == Position.QB:
        return weighted_average(
            features,
            {
                "age_trajectory": 35,
                "passing_efficiency": 30,
                "rushing_profile": 20,
                "sack_avoidance": 15,
            },
        )
    if position == Position.RB:
        return weighted_average(
            features,
            {
                "age_trajectory": 35,
                "workload_earning": 25,
                "receiving_impact": 25,
                "rush_efficiency": 15,
            },
        )
    if position == Position.WR:
        return weighted_average(
            features,
            {
                "age_trajectory": 35,
                "target_earning": 30,
                "efficiency_dominance": 25,
                "chain_moving": 10,
            },
        )
    return weighted_average(
        features,
        {"age_trajectory": 30, "receiving_efficiency": 30, "route_role": 25, "athletic_size": 15},
    )


def _trade_insulation(position: Position, features: Mapping[str, float | None]) -> float:
    age_weight = 30 if position in {Position.QB, Position.TE} else 40
    capital_weight = 45 if position in {Position.QB, Position.TE} else 35
    role_feature = {
        Position.QB: "rushing_profile",
        Position.RB: "workload_earning",
        Position.WR: "target_earning",
        Position.TE: "route_role",
    }[position]
    return weighted_average(
        features,
        {"draft_capital": capital_weight, "age_trajectory": age_weight, role_feature: 25},
    )


def _internal_score(
    main: float,
    league_fit: float,
    opportunity: float,
    long_term: float,
    trade: float,
) -> float:
    return round(
        clamp_score(
            (main * FINAL_WEIGHTS["main_prospect_score"])
            + (league_fit * FINAL_WEIGHTS["league_fit_score"])
            + (opportunity * FINAL_WEIGHTS["rookie_opportunity_score"])
            + (long_term * FINAL_WEIGHTS["long_term_dynasty_score"])
            + (trade * FINAL_WEIGHTS["trade_insulation_score"])
        ),
        2,
    )


def _apply_confidence_cap(
    score: float,
    confidence: float,
    features: Mapping[str, float | None],
    position: Position,
) -> float:
    missing_count = sum(
        1 for feature in FEATURES_BY_POSITION[position] if features.get(feature) is None
    )
    if missing_count >= 3:
        score = min(score, 70.0)
    if confidence < 55:
        score = min(score, 68.0)
    return clamp_score(score)


def _spread(values: list[float]) -> float:
    if not values:
        return 0.0
    return max(values) - min(values)
