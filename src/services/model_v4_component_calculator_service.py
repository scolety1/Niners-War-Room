from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config.lve_scoring import LVE_SCORING
from src.services.age_curve_service import age_curve_profile
from src.services.young_nfl_bridge_service import young_nfl_bridge_prior_from_row
from src.utils.scoring import clamp_score

MODEL_V4_FORMULA_CONFIG_PATH = Path("docs/model_v4/MODEL_V4_FORMULA_CONFIG.json")
MODEL_V4_COMPONENT_CALCULATOR_VERSION = "model_v4_component_skeleton_0.2.1"

PRODUCTION_FIELDS = (
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_attempts",
    "rushing_yards",
    "rushing_tds",
    "targets",
    "receiving_yards",
    "receiving_tds",
    "receptions",
    "fumbles_lost",
)

FIRST_DOWN_FIELDS = ("rushing_first_downs", "receiving_first_downs")

USAGE_FIELDS = (
    "target_share",
    "targets",
    "team_targets",
    "rb_carry_share",
    "rb_target_share",
    "rushing_attempts",
    "team_rushing_attempts",
    "weighted_opportunities",
    "red_zone_carries",
    "red_zone_targets",
    "goal_line_carries",
    "goal_line_targets",
    "short_yardage_carries",
    "games_with_usage",
)

SNAP_SHARE_FIELDS = ("snap_share", "offense_pct", "offense_snap_share")
SNAP_EVIDENCE_FIELDS = (
    "snap_share",
    "offense_pct",
    "offense_snap_share",
    "offense_snaps",
    "games",
    "games_with_offensive_snaps",
)

PROJECTION_FIELDS = (
    "projected_games",
    "projected_starts",
    "projected_passing_yards",
    "projected_passing_tds",
    "projected_interceptions",
    "projected_rushing_attempts",
    "projected_rushing_yards",
    "projected_rushing_tds",
    "projected_targets",
    "projected_receiving_yards",
    "projected_receiving_tds",
    "projected_receptions",
    "projected_rushing_first_downs",
    "projected_receiving_first_downs",
    "projected_fumbles_lost",
)

AGE_FIELDS = ("age",)

ROUTE_METRIC_FIELDS = ("route_participation", "routes_run", "tprr", "yprr")
ROUTE_UNAVAILABLE_WARNINGS = (
    "route_participation_unavailable",
    "routes_run_unavailable",
    "tprr_unavailable",
    "yprr_unavailable",
)

POINT_NORMALIZATION_CEILINGS = {
    "production": {"QB": 330.0, "RB": 300.0, "WR": 300.0, "TE": 220.0},
    "first_down_scoring_fit": {"QB": 60.0, "RB": 40.0, "WR": 40.0, "TE": 30.0},
    "projection": {"QB": 330.0, "RB": 300.0, "WR": 300.0, "TE": 220.0},
}


@dataclass(frozen=True)
class ModelV4ComponentReceipt:
    component: str
    raw_fields_used: tuple[str, ...]
    raw_values: dict[str, object]
    normalized_score: float
    source_status: str
    contribution: float
    weight: float
    warning: str
    unavailable_reason: str
    review_only: bool = True

    def as_row(self) -> dict[str, object]:
        return {
            "component": self.component,
            "raw_fields_used": "|".join(self.raw_fields_used),
            "raw_values": json.dumps(self.raw_values, sort_keys=True),
            "normalized_score": self.normalized_score,
            "source_status": self.source_status,
            "contribution": self.contribution,
            "weight": self.weight,
            "warning": self.warning,
            "unavailable_reason": self.unavailable_reason,
            "review_only": self.review_only,
        }


def load_model_v4_formula_config(
    path: str | Path = MODEL_V4_FORMULA_CONFIG_PATH,
) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def calculate_all_model_v4_components(
    row: dict[str, object],
    *,
    position: str | None = None,
    season: int = 2026,
    config: dict[str, Any] | None = None,
) -> tuple[ModelV4ComponentReceipt, ...]:
    resolved_config = config or load_model_v4_formula_config()
    resolved_position = _position(row, position)
    components: list[ModelV4ComponentReceipt] = [
        calculate_production_component(
            row,
            position=resolved_position,
            config=resolved_config,
        ),
        calculate_first_down_scoring_fit_component(
            row,
            position=resolved_position,
            config=resolved_config,
        ),
        calculate_usage_opportunity_component(
            row,
            position=resolved_position,
            config=resolved_config,
        ),
        calculate_snap_proxy_role_component(
            row,
            position=resolved_position,
            config=resolved_config,
        ),
        calculate_projection_component(
            row,
            position=resolved_position,
            config=resolved_config,
        ),
        calculate_age_dropoff_component(
            row,
            position=resolved_position,
            config=resolved_config,
        ),
    ]
    if resolved_position == "QB":
        components.append(
            calculate_qb_position_scarcity_suppression_component(
                row,
                position=resolved_position,
                config=resolved_config,
            ),
        )
    if resolved_position == "TE":
        components.append(
            calculate_te_no_premium_suppression_component(
                row,
                position=resolved_position,
                config=resolved_config,
            ),
        )
    components.append(
        calculate_young_player_prior_component(
            row,
            position=resolved_position,
            season=season,
            config=resolved_config,
        ),
    )
    confidence_row = _row_with_component_context(row, components)
    components.append(calculate_confidence_component(confidence_row))
    return tuple(components)


def calculate_production_component(
    row: dict[str, object],
    *,
    position: str | None = None,
    config: dict[str, Any] | None = None,
) -> ModelV4ComponentReceipt:
    resolved_position = _position(row, position)
    weight = _component_weight(config, resolved_position, "production")
    fields = _present_fields(row, PRODUCTION_FIELDS)
    if not fields:
        return _missing_component(
            "production",
            weight,
            "missing_production_data",
            "No imported production fields were present.",
        )

    points = _lve_points_without_first_downs(row, prefix="")
    normalized = _normalize_points("production", resolved_position, points)
    return _receipt(
        component="production",
        raw_fields_used=fields,
        raw_values={
            **_raw_values(row, fields),
            "lve_points_no_first_downs": round(points, 3),
        },
        normalized_score=normalized,
        source_status=_source_status(row, "production", "imported_real_data"),
        weight=weight,
        warning=_source_warning(row, "production"),
    )


def calculate_first_down_scoring_fit_component(
    row: dict[str, object],
    *,
    position: str | None = None,
    config: dict[str, Any] | None = None,
) -> ModelV4ComponentReceipt:
    resolved_position = _position(row, position)
    weight = _component_weight(config, resolved_position, "first_down_scoring_fit")
    fields = _present_fields(row, FIRST_DOWN_FIELDS)
    if not fields:
        return _missing_component(
            "first_down_scoring_fit",
            weight,
            "missing_first_down_data",
            "No rushing or receiving first-down fields were present.",
        )

    first_downs = _float(row.get("rushing_first_downs")) + _float(
        row.get("receiving_first_downs")
    )
    points = first_downs * LVE_SCORING["rushing_receiving_first_down"]
    normalized = _normalize_points("first_down_scoring_fit", resolved_position, points)
    return _receipt(
        component="first_down_scoring_fit",
        raw_fields_used=fields,
        raw_values={
            **_raw_values(row, fields),
            "first_downs": round(first_downs, 3),
            "first_down_points": round(points, 3),
            "first_down_point_value": LVE_SCORING["rushing_receiving_first_down"],
        },
        normalized_score=normalized,
        source_status=_source_status(row, "first_down", "imported_real_data"),
        weight=weight,
        warning=_source_warning(row, "first_down"),
    )


def calculate_usage_opportunity_component(
    row: dict[str, object],
    *,
    position: str | None = None,
    config: dict[str, Any] | None = None,
) -> ModelV4ComponentReceipt:
    resolved_position = _position(row, position)
    weight = _component_weight(config, resolved_position, "usage_opportunity")
    fields = _present_fields(row, USAGE_FIELDS)
    if not fields:
        return _missing_component(
            "usage_opportunity",
            weight,
            "missing_usage_opportunity_data",
            "No target, carry, weighted-opportunity, red-zone, or goal-line fields were present.",
        )

    sub_scores = _usage_sub_scores(row, resolved_position)
    if not sub_scores:
        return _missing_component(
            "usage_opportunity",
            weight,
            "missing_usage_opportunity_data",
            "Usage count fields were present, but no share, weighted-opportunity, "
            "red-zone, or goal-line scoring sub-score could be calculated.",
            source_status=_source_status(row, "usage", "missing"),
            raw_fields=fields,
            raw_values=_raw_values(row, fields),
        )
    normalized = _average(tuple(sub_scores.values()))
    warnings = [_source_warning(row, "usage"), *ROUTE_UNAVAILABLE_WARNINGS]
    if _present_fields(row, ROUTE_METRIC_FIELDS):
        warnings.append("route_metrics_ignored_unavailable")
    return _receipt(
        component="usage_opportunity",
        raw_fields_used=fields,
        raw_values={
            **_raw_values(row, fields),
            "sub_scores": sub_scores,
            "route_metrics_used": False,
        },
        normalized_score=normalized,
        source_status=_source_status(row, "usage", "derived_real_data"),
        weight=weight,
        warning="|".join(dict.fromkeys(warning for warning in warnings if warning)),
    )


def calculate_snap_proxy_role_component(
    row: dict[str, object],
    *,
    position: str | None = None,
    config: dict[str, Any] | None = None,
) -> ModelV4ComponentReceipt:
    resolved_position = _position(row, position)
    weight = _component_weight(config, resolved_position, "snap_proxy_role")
    fields = _present_fields(row, SNAP_EVIDENCE_FIELDS)
    share_fields = _present_fields(row, SNAP_SHARE_FIELDS)
    if not share_fields:
        return _missing_component(
            "snap_proxy_role",
            weight,
            "missing_snap_share_data",
            "No offensive snap-share field was present.",
        )

    snap_share = _first_numeric(row, SNAP_SHARE_FIELDS)
    normalized = _share_score(snap_share)
    return _receipt(
        component="snap_proxy_role",
        raw_fields_used=fields,
        raw_values={
            **_raw_values(row, fields),
            "snap_share_score": normalized,
            "proxy_only": True,
            "route_participation_used": False,
            "routes_run_used": False,
            "tprr_used": False,
            "yprr_used": False,
        },
        normalized_score=normalized,
        source_status=_source_status(row, "snap", "imported_real_data"),
        weight=weight,
        warning="|".join(
            ("snap_share_proxy_only_not_route_participation", *ROUTE_UNAVAILABLE_WARNINGS)
        ),
    )


def calculate_projection_component(
    row: dict[str, object],
    *,
    position: str | None = None,
    config: dict[str, Any] | None = None,
) -> ModelV4ComponentReceipt:
    resolved_position = _position(row, position)
    weight = _component_weight(config, resolved_position, "projection")
    fields = _present_fields(row, PROJECTION_FIELDS)
    if not fields:
        return _missing_component(
            "projection",
            weight,
            "missing_projection_data",
            "No raw projection stat fields were present.",
            source_status="missing_projection",
        )

    points_no_first_downs = _lve_points_without_first_downs(row, prefix="projected_")
    projected_first_downs = _float(row.get("projected_rushing_first_downs")) + _float(
        row.get("projected_receiving_first_downs")
    )
    first_down_points = (
        projected_first_downs * LVE_SCORING["rushing_receiving_first_down"]
    )
    points = points_no_first_downs + first_down_points
    normalized = _normalize_points("projection", resolved_position, points)
    first_down_status = (
        str(row.get("first_down_projection_status") or "")
        or (
            "direct_first_down_projection"
            if _present_fields(
                row,
                ("projected_rushing_first_downs", "projected_receiving_first_downs"),
            )
            else "missing_first_down_projection"
        )
    )
    source_status = str(
        row.get("projection_source_status")
        or row.get("projection_availability_status")
        or "projection_stat_recompute"
    )
    warnings = [first_down_status]
    if first_down_status == "estimated_from_history":
        warnings.append("projection_first_downs_estimated_from_history")
    if row.get("first_down_projection_model_usage_status") == (
        "preview_only_not_active_scoring"
    ):
        warnings.append("first_down_projection_preview_only")
    if source_status == "local_baseline_projection":
        warnings.append("local_baseline_projection_not_independent_forecast")
    if row.get("projected_lve_points_if_calculable") not in (None, ""):
        warnings.append("supplied_projection_points_ignored")
    return _receipt(
        component="projection",
        raw_fields_used=fields,
        raw_values={
            **_raw_values(row, fields),
            "recomputed_lve_points": round(points, 3),
            "recomputed_lve_points_no_first_downs": round(points_no_first_downs, 3),
            "raw_stat_projection_status": row.get(
                "raw_stat_projection_status",
                "independent_raw_stat_projection",
            ),
            "recomputed_lve_projection_status": row.get(
                "recomputed_lve_projection_status",
                "recomputed_from_raw_projection_stats",
            ),
            "first_down_points": round(first_down_points, 3),
            "first_down_projection_status": first_down_status,
            "first_down_projection_rate_source_status": row.get(
                "first_down_projection_rate_source_status",
                "",
            ),
            "first_down_projection_model_usage_status": row.get(
                "first_down_projection_model_usage_status",
                "",
            ),
            "rushing_first_down_rate": row.get("rushing_first_down_rate", ""),
            "rushing_first_down_rate_scope": row.get(
                "rushing_first_down_rate_scope",
                "",
            ),
            "receiving_first_down_rate_basis": row.get(
                "receiving_first_down_rate_basis",
                "",
            ),
            "receiving_first_down_rate": row.get("receiving_first_down_rate", ""),
            "receiving_first_down_rate_scope": row.get(
                "receiving_first_down_rate_scope",
                "",
            ),
        },
        normalized_score=normalized,
        source_status=source_status,
        weight=weight,
        warning="|".join(warnings),
    )


def calculate_age_dropoff_component(
    row: dict[str, object],
    *,
    position: str | None = None,
    config: dict[str, Any] | None = None,
) -> ModelV4ComponentReceipt:
    resolved_position = _position(row, position)
    weight = _component_weight(config, resolved_position, "age_dropoff")
    age = _optional_float(row.get("age"))
    profile = age_curve_profile(
        resolved_position,
        age,
        role_score=_float(row.get("role_security"), 50.0),
        target_score=_share_score(_optional_float(row.get("target_share"))),
        workload_score=_share_score(_optional_float(row.get("rb_carry_share"))),
        injury_score=_float(row.get("injury_durability"), 75.0),
        rushing_profile_score=_float(row.get("rushing_profile_score"), 50.0),
        route_score=0.0 if _present_fields(row, ROUTE_METRIC_FIELDS) else 50.0,
    )
    if profile.source_status == "neutral_imputation":
        return _missing_component(
            "age_dropoff",
            weight,
            "age_not_available",
            "Age was unavailable; neutral age default is visible and contributes 0.",
            source_status="neutral_imputation",
            raw_values={"neutral_default_not_scored": profile.age_curve_score},
        )
    return _receipt(
        component="age_dropoff",
        raw_fields_used=AGE_FIELDS,
        raw_values={
            "age": profile.age,
            "age_bucket": profile.age_bucket,
            "age_curve_score": profile.age_curve_score,
            "age_interaction_flags": "|".join(profile.age_interaction_flags),
        },
        normalized_score=profile.age_curve_score,
        source_status=profile.source_status,
        weight=weight,
        warning=profile.age_warning,
    )


def calculate_young_player_prior_component(
    row: dict[str, object],
    *,
    position: str | None = None,
    season: int = 2026,
    config: dict[str, Any] | None = None,
) -> ModelV4ComponentReceipt:
    resolved_position = _position(row, position)
    weight = _component_weight(config, resolved_position, "young_player_prior")
    prior = young_nfl_bridge_prior_from_row(
        {**row, "position": resolved_position},
        season=season,
    )
    fields = _present_fields(
        row,
        (
            "draft_year",
            "draft_round",
            "draft_overall",
            "draft_ovr",
            "draft_pick_overall",
            "rookie_model_grade",
            "prospect_grade",
        ),
    )
    raw_values = {
        "experience_bucket": prior.experience_bucket,
        "draft_year": prior.draft_year or "",
        "draft_round": prior.draft_round or "",
        "draft_overall": prior.draft_overall or "",
        "draft_capital_prior_score": prior.draft_capital_prior_score,
        "rookie_prior_score": prior.rookie_prior_score,
        "base_decay_weight": prior.base_decay_weight,
        "nfl_evidence_weight": prior.nfl_evidence_weight,
        "bridge_weight": prior.bridge_weight,
    }
    if prior.bridge_weight <= 0:
        expected_young = _expected_young_lifecycle(row, prior.experience_bucket)
        return _missing_component(
            "young_player_prior",
            weight,
            "missing_young_player_prior" if expected_young else "young_player_prior_not_applicable",
            (
                "Young-player bridge data was expected but missing."
                if expected_young
                else "Player is not lifecycle-eligible for a young-player prior."
            ),
            source_status="missing" if expected_young else "not_applicable",
            raw_values=raw_values,
        )
    contribution = _round((prior.rookie_prior_score * weight * prior.bridge_weight) / 100.0)
    return ModelV4ComponentReceipt(
        component="young_player_prior",
        raw_fields_used=fields,
        raw_values=raw_values,
        normalized_score=prior.rookie_prior_score,
        source_status=prior.source,
        contribution=contribution,
        weight=weight,
        warning="young_player_prior_review_only",
        unavailable_reason="",
    )


def calculate_qb_position_scarcity_suppression_component(
    row: dict[str, object],
    *,
    position: str | None = None,
    config: dict[str, Any] | None = None,
) -> ModelV4ComponentReceipt:
    resolved_position = _position(row, position)
    weight = _component_weight(config, resolved_position, "position_scarcity_suppression")
    if resolved_position != "QB" or weight <= 0:
        return _missing_component(
            "position_scarcity_suppression",
            weight,
            "position_scarcity_not_applicable",
            "Position scarcity suppression applies only to QBs.",
            source_status="not_applicable",
        )

    production_score = _normalize_points(
        "production",
        "QB",
        _lve_points_without_first_downs(row, prefix=""),
    )
    projection_score = (
        _normalize_points("projection", "QB", _lve_projection_points(row))
        if _present_fields(row, PROJECTION_FIELDS)
        else 0.0
    )
    ceiling_score = max(production_score, projection_score)
    rushing_edge_score = _qb_rushing_edge_score(row)
    start_security_score = _start_security_score(row)
    elite_rushing_exception = ceiling_score >= 75.0 and rushing_edge_score >= 70.0
    partial_rushing_exception = ceiling_score >= 65.0 and rushing_edge_score >= 55.0
    stable_starter_exception = (
        projection_score > 0.0
        and start_security_score >= 80.0
        and ceiling_score >= 60.0
    )
    if elite_rushing_exception:
        normalized = 8.0
    elif partial_rushing_exception:
        normalized = 5.0
    elif rushing_edge_score < 25.0:
        normalized = 0.0
    elif stable_starter_exception:
        normalized = 2.0
    else:
        normalized = 0.0
    warning = "one_qb_suppression_review_only"
    if elite_rushing_exception:
        warning += "|elite_rushing_qb_exception_review_only"
    elif partial_rushing_exception:
        warning += "|partial_rushing_qb_exception_review_only"
    elif rushing_edge_score < 25.0:
        warning += "|replaceable_qb_suppressed"
    return _receipt(
        component="position_scarcity_suppression",
        raw_fields_used=_present_fields(
            row,
            (
                "rushing_yards",
                "rushing_tds",
                "rushing_first_downs",
                "projected_rushing_yards",
                "projected_rushing_tds",
                "projected_rushing_first_downs",
                "projected_starts",
                "snap_share",
                "offense_pct",
                "offense_snap_share",
            ),
        ),
        raw_values={
            "production_score": production_score,
            "projection_score": projection_score,
            "ceiling_score": ceiling_score,
            "rushing_edge_score": rushing_edge_score,
            "start_security_score": start_security_score,
            "one_qb_league": True,
            "elite_rushing_exception": elite_rushing_exception,
            "partial_rushing_exception": partial_rushing_exception,
            "stable_starter_exception": stable_starter_exception,
            "one_qb_exception_cap": 8.0,
            "replaceable_qb_score": 0.0,
        },
        normalized_score=normalized,
        source_status="derived_formula_adjustment",
        weight=weight,
        warning=warning,
    )


def calculate_te_no_premium_suppression_component(
    row: dict[str, object],
    *,
    position: str | None = None,
    config: dict[str, Any] | None = None,
) -> ModelV4ComponentReceipt:
    resolved_position = _position(row, position)
    weight = _component_weight(config, resolved_position, "no_premium_suppression")
    if resolved_position != "TE" or weight <= 0:
        return _missing_component(
            "no_premium_suppression",
            weight,
            "no_premium_suppression_not_applicable",
            "No-premium TE suppression applies only to TEs.",
            source_status="not_applicable",
        )

    production_score = _normalize_points(
        "production",
        "TE",
        _lve_points_without_first_downs(row, prefix=""),
    )
    first_down_score = _normalize_points(
        "first_down_scoring_fit",
        "TE",
        (
            _float(row.get("rushing_first_downs"))
            + _float(row.get("receiving_first_downs"))
        )
        * LVE_SCORING["rushing_receiving_first_down"],
    )
    usage_score = _average(tuple(_usage_sub_scores(row, "TE").values()))
    projection_score = (
        _normalize_points("projection", "TE", _lve_projection_points(row))
        if _present_fields(row, PROJECTION_FIELDS)
        else production_score
    )
    volume_exception_score = _average(
        (
            production_score,
            first_down_score,
            usage_score,
            projection_score,
        ),
    )
    age = _optional_float(row.get("age"))
    elite_exception = volume_exception_score >= 60.0 and (
        usage_score >= 25.0 or projection_score >= 60.0
    )
    if elite_exception:
        normalized = 30.0 + (volume_exception_score * 0.18)
    else:
        normalized = 8.0 + (volume_exception_score * 0.2)
    if age is not None and age >= 30.0:
        normalized -= 4.0
    if age is not None and age >= 32.0:
        normalized -= 6.0
    normalized = min(58.0, max(6.0, normalized))
    warning = "no_premium_te_suppression_review_only"
    if elite_exception:
        warning += "|elite_te_exception_review_only"
    else:
        warning += "|replaceable_no_premium_te_review"
    return _receipt(
        component="no_premium_suppression",
        raw_fields_used=_present_fields(
            row,
            (
                "targets",
                "receiving_yards",
                "receiving_tds",
                "receiving_first_downs",
                "target_share",
                "weighted_opportunities",
                "projected_targets",
                "projected_receiving_yards",
                "projected_receiving_tds",
                "age",
            ),
        ),
        raw_values={
            "production_score": production_score,
            "first_down_score": first_down_score,
            "usage_score": usage_score,
            "projection_score": projection_score,
            "volume_exception_score": volume_exception_score,
            "elite_exception": elite_exception,
            "no_te_premium": True,
            "route_metrics_used": False,
        },
        normalized_score=normalized,
        source_status="derived_formula_adjustment",
        weight=weight,
        warning=warning,
    )


def calculate_confidence_component(row: dict[str, object]) -> ModelV4ComponentReceipt:
    base = _optional_float(row.get("confidence_score"))
    if base is None:
        base = _optional_float(row.get("confidence"))
    if base is None:
        base = 100.0
    warnings = list(_warning_parts(row))
    critical_missing = _int(row.get("critical_missing_count"))
    review_gaps = _int(row.get("review_gap_count"))
    missing_warning_count = sum(1 for warning in warnings if warning.startswith("missing_"))
    proxy_warning_count = sum(1 for warning in warnings if "proxy" in warning)
    local_baseline_count = sum(
        1 for warning in warnings if "local_baseline_projection" in warning
    )
    score = clamp_score(
        base
        - (critical_missing * 18.0)
        - (review_gaps * 5.0)
        - (missing_warning_count * 6.0)
        - (proxy_warning_count * 4.0)
        - (local_baseline_count * 5.0)
    )
    incoming_rookie_missing_evidence = _incoming_rookie_missing_all_evidence(
        row,
        tuple(warnings),
    )
    confidence_cap = ""
    if incoming_rookie_missing_evidence:
        score = 45.0
        confidence_cap = "incoming_rookie_missing_all_evidence_weak_cap"
        warnings.append("incoming_rookie_missing_evidence_confidence_cap")
        warnings = list(dict.fromkeys(warnings))
    raw_values = {
        "base_confidence": base,
        "critical_missing_count": critical_missing,
        "review_gap_count": review_gaps,
        "warning_count": len(warnings),
        "incoming_rookie_missing_all_evidence": incoming_rookie_missing_evidence,
        "confidence_cap": confidence_cap,
        "confidence_label": _confidence_label(score),
    }
    return ModelV4ComponentReceipt(
        component="confidence",
        raw_fields_used=_present_fields(
            row,
            (
                "confidence_score",
                "confidence",
                "critical_missing_count",
                "review_gap_count",
                "warnings",
                "warning",
            ),
        ),
        raw_values=raw_values,
        normalized_score=_round(score),
        source_status="derived_audit_status",
        contribution=0.0,
        weight=0.0,
        warning="|".join(warnings),
        unavailable_reason="",
    )


def _row_with_component_context(
    row: dict[str, object],
    components: list[ModelV4ComponentReceipt],
) -> dict[str, object]:
    warnings = list(_warning_parts(row))
    review_gap_count = _int(row.get("review_gap_count"))
    critical_missing_count = _int(row.get("critical_missing_count"))
    for component in components:
        warnings.extend(
            part
            for part in str(component.warning or "").split("|")
            if part.strip()
        )
        if component.source_status == "missing" or (
            component.unavailable_reason
            and component.source_status not in {"not_applicable", "disabled"}
        ):
            review_gap_count += 1
        if (
            component.source_status == "missing"
            and component.component
            in {
                "production",
                "first_down_scoring_fit",
                "usage_opportunity",
                "snap_proxy_role",
                "projection",
            }
        ):
            critical_missing_count += 1
    output = dict(row)
    output["warnings"] = "|".join(dict.fromkeys(warnings))
    output["review_gap_count"] = review_gap_count
    output["critical_missing_count"] = critical_missing_count
    return output


def _receipt(
    *,
    component: str,
    raw_fields_used: tuple[str, ...],
    raw_values: dict[str, object],
    normalized_score: float,
    source_status: str,
    weight: float,
    warning: str = "",
) -> ModelV4ComponentReceipt:
    return ModelV4ComponentReceipt(
        component=component,
        raw_fields_used=raw_fields_used,
        raw_values=raw_values,
        normalized_score=_round(normalized_score),
        source_status=source_status,
        contribution=_round((normalized_score * weight) / 100.0),
        weight=weight,
        warning=warning,
        unavailable_reason="",
    )


def _missing_component(
    component: str,
    weight: float,
    warning: str,
    unavailable_reason: str,
    *,
    source_status: str = "missing",
    raw_fields: tuple[str, ...] = (),
    raw_values: dict[str, object] | None = None,
) -> ModelV4ComponentReceipt:
    return ModelV4ComponentReceipt(
        component=component,
        raw_fields_used=raw_fields,
        raw_values=raw_values or {},
        normalized_score=0.0,
        source_status=source_status,
        contribution=0.0,
        weight=weight,
        warning=warning,
        unavailable_reason=unavailable_reason,
    )


def _component_weight(
    config: dict[str, Any] | None,
    position: str,
    component: str,
) -> float:
    resolved = config or load_model_v4_formula_config()
    return _float(
        resolved.get("position_component_weights", {})
        .get(position, {})
        .get(component),
        0.0,
    )


def _lve_points_without_first_downs(row: dict[str, object], *, prefix: str) -> float:
    return (
        _float(row.get(f"{prefix}passing_yards")) * LVE_SCORING["passing_yard"]
        + _float(row.get(f"{prefix}passing_tds")) * LVE_SCORING["passing_td"]
        + _float(row.get(f"{prefix}interceptions")) * LVE_SCORING["interception"]
        + _float(row.get(f"{prefix}rushing_yards")) * LVE_SCORING["rushing_yard"]
        + _float(row.get(f"{prefix}rushing_tds")) * LVE_SCORING["rushing_td"]
        + _float(row.get(f"{prefix}receiving_yards")) * LVE_SCORING["receiving_yard"]
        + _float(row.get(f"{prefix}receiving_tds")) * LVE_SCORING["receiving_td"]
        + _float(row.get(f"{prefix}receptions")) * LVE_SCORING["reception"]
        + _float(row.get(f"{prefix}fumbles_lost")) * LVE_SCORING["fumble_lost"]
    )


def _lve_projection_points(row: dict[str, object]) -> float:
    points = _lve_points_without_first_downs(row, prefix="projected_")
    first_downs = _float(row.get("projected_rushing_first_downs")) + _float(
        row.get("projected_receiving_first_downs"),
    )
    return points + (first_downs * LVE_SCORING["rushing_receiving_first_down"])


def _qb_rushing_edge_score(row: dict[str, object]) -> float:
    historical = (
        _float(row.get("rushing_yards")) * LVE_SCORING["rushing_yard"]
        + _float(row.get("rushing_tds")) * LVE_SCORING["rushing_td"]
        + _float(row.get("rushing_first_downs"))
        * LVE_SCORING["rushing_receiving_first_down"]
    )
    projected = (
        _float(row.get("projected_rushing_yards")) * LVE_SCORING["rushing_yard"]
        + _float(row.get("projected_rushing_tds")) * LVE_SCORING["rushing_td"]
        + _float(row.get("projected_rushing_first_downs"))
        * LVE_SCORING["rushing_receiving_first_down"]
    )
    return _round(clamp_score((max(historical, projected) / 115.0) * 100.0))


def _start_security_score(row: dict[str, object]) -> float:
    projected_starts = _optional_float(row.get("projected_starts"))
    if projected_starts is not None:
        return _round(clamp_score((projected_starts / 17.0) * 100.0))
    snap_share = _first_numeric(row, SNAP_SHARE_FIELDS)
    if snap_share:
        return _share_score(snap_share)
    return 50.0


def _usage_sub_scores(row: dict[str, object], position: str) -> dict[str, float]:
    sub_scores: dict[str, float] = {}
    target_share = _optional_float(row.get("target_share"))
    if target_share is not None:
        sub_scores["target_share"] = _share_score(target_share)
    if position == "RB":
        rb_carry_share = _optional_float(row.get("rb_carry_share"))
        rb_target_share = _optional_float(row.get("rb_target_share"))
        if rb_carry_share is not None:
            sub_scores["rb_carry_share"] = _share_score(rb_carry_share)
        if rb_target_share is not None:
            sub_scores["rb_target_share"] = _share_score(rb_target_share)
    weighted_opportunities = _optional_float(row.get("weighted_opportunities"))
    if weighted_opportunities is not None:
        sub_scores["weighted_opportunities"] = clamp_score(
            (weighted_opportunities / 350.0) * 100.0
        )
    red_zone = _float(row.get("red_zone_carries")) + _float(row.get("red_zone_targets"))
    if _has_any_value(row, ("red_zone_carries", "red_zone_targets")):
        sub_scores["red_zone_usage"] = clamp_score((red_zone / 60.0) * 100.0)
    goal_line = _float(row.get("goal_line_carries")) + _float(row.get("goal_line_targets"))
    if _has_any_value(row, ("goal_line_carries", "goal_line_targets")):
        sub_scores["goal_line_usage"] = clamp_score((goal_line / 20.0) * 100.0)
    return sub_scores


def _normalize_points(component: str, position: str, points: float) -> float:
    ceiling = POINT_NORMALIZATION_CEILINGS[component].get(position, 300.0)
    if ceiling <= 0:
        return 0.0
    return _round(clamp_score((points / ceiling) * 100.0))


def _source_status(
    row: dict[str, object],
    prefix: str,
    default: str,
) -> str:
    return str(
        row.get(f"{prefix}_source_status")
        or row.get(f"{prefix}_status")
        or default
    )


def _source_warning(row: dict[str, object], prefix: str) -> str:
    return str(
        row.get(f"{prefix}_warning")
        or row.get(f"{prefix}_warning_reason")
        or ""
    )


def _present_fields(
    row: dict[str, object],
    fields: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(field for field in fields if _value_is_present(row.get(field)))


def _raw_values(row: dict[str, object], fields: tuple[str, ...]) -> dict[str, object]:
    return {field: row.get(field) for field in fields}


def _has_any_value(row: dict[str, object], fields: tuple[str, ...]) -> bool:
    return any(_value_is_present(row.get(field)) for field in fields)


def _value_is_present(value: object) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return text not in {"", "NA", "nan", "None"}


def _position(row: dict[str, object], position: str | None = None) -> str:
    return str(position or row.get("position") or "").upper()


def _optional_float(value: object) -> float | None:
    if not _value_is_present(value):
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _float(value: object, default: float = 0.0) -> float:
    parsed = _optional_float(value)
    return default if parsed is None else parsed


def _int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except (TypeError, ValueError):
        return 0


def _first_numeric(row: dict[str, object], fields: tuple[str, ...]) -> float:
    for field in fields:
        value = _optional_float(row.get(field))
        if value is not None:
            return value
    return 0.0


def _share_score(value: float | None) -> float:
    if value is None:
        return 0.0
    share = value / 100.0 if value > 1.0 else value
    return _round(clamp_score(share * 100.0))


def _average(values: tuple[float, ...]) -> float:
    if not values:
        return 0.0
    return _round(sum(values) / len(values))


def _round(value: float) -> float:
    return round(float(value), 3)


def _warning_parts(row: dict[str, object]) -> tuple[str, ...]:
    warnings = []
    for field in ("warnings", "warning", "warning_reason"):
        warnings.extend(
            part
            for part in str(row.get(field) or "").split("|")
            if part.strip()
        )
    return tuple(dict.fromkeys(warnings))


def _confidence_label(score: float) -> str:
    if score >= 85:
        return "strong"
    if score >= 70:
        return "usable"
    if score >= 50:
        return "review"
    if score > 0:
        return "weak"
    return "blocked"


def _incoming_rookie_missing_all_evidence(
    row: dict[str, object],
    warnings: tuple[str, ...],
) -> bool:
    lifecycle = str(
        row.get("asset_lifecycle")
        or row.get("asset_lifecycle_label")
        or row.get("lifecycle")
        or ""
    ).lower()
    if "incoming_rookie" not in lifecycle and "incoming rookie" not in lifecycle:
        return False
    warning_set = set(warnings)
    required_missing_warnings = {
        "missing_production_data",
        "missing_first_down_data",
        "missing_usage_opportunity_data",
        "missing_snap_share_data",
        "missing_projection_data",
        "age_not_available",
        "missing_young_player_prior",
    }
    return required_missing_warnings.issubset(warning_set)


def _expected_young_lifecycle(
    row: dict[str, object],
    experience_bucket: str,
) -> bool:
    lifecycle = str(
        row.get("asset_lifecycle")
        or row.get("asset_lifecycle_label")
        or row.get("lifecycle")
        or ""
    ).lower()
    return (
        "young" in lifecycle
        or "rookie" in lifecycle
        or experience_bucket
        in {
            "true_rookie",
            "year_one_nfl_player",
            "year_two_nfl_player",
            "year_three_nfl_player",
        }
    )
