from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.feature_data_truth_contract_service import classify_feature_truth
from src.services.lve_injury_durability_service import derive_lve_injury_durability_rows
from src.services.lve_projection_import_service import (
    PROJECTION_SOURCE_DISABLED,
    PROJECTION_SOURCE_INDEPENDENT,
    PROJECTION_SOURCE_LOCAL_BASELINE,
    PROJECTION_SOURCE_MISSING,
    derive_lve_projection_feature_rows,
    projection_source_status_from_row,
)
from src.services.lve_role_usage_service import derive_lve_role_usage_feature_rows
from src.services.lve_scoring_derivation_service import derive_lve_weekly_scoring_rows
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

NORMALIZED_FEATURE_HEADER = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[
    "lve_normalized_veteran_features.csv"
]
NORMALIZED_FEATURE_RECEIPT_HEADER = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[
    "lve_normalized_feature_receipts.csv"
]

FINAL_NORMALIZED_FEATURE_BUCKETS = (
    "production",
    "opportunity",
    "role",
    "efficiency",
    "first_down_td_fit",
    "age_window",
    "injury_durability",
)
MARKET_ONLY_FEATURES = frozenset({"market_liquidity", "trade_liquidity"})

POSITION_PPG_ANCHORS = {
    "QB": 24.0,
    "RB": 16.0,
    "WR": 15.0,
    "TE": 11.0,
}
POSITION_FIRST_DOWN_ANCHORS = {
    "QB": 5.0,
    "RB": 7.0,
    "WR": 6.0,
    "TE": 4.5,
}
POSITION_EFFICIENCY_ANCHORS = {
    "QB": 24.0,
    "RB": 1.05,
    "WR": 1.65,
    "TE": 1.35,
}


@dataclass(frozen=True)
class NormalizedFeatureSpec:
    feature_name: str
    feature_bucket: str
    source_key: str
    source_field: str
    model_usage: str


NORMALIZED_FEATURE_SPECS = (
    NormalizedFeatureSpec(
        "weighted_recent_lve_ppg_score",
        "production",
        "nflverse_player_stats_weekly",
        "lve_points_per_game",
        "private_stat_feature",
    ),
    NormalizedFeatureSpec(
        "expected_lve_points_score",
        "opportunity",
        "projection_raw_import",
        "lve_projected_ppg",
        "private_stat_feature",
    ),
    NormalizedFeatureSpec(
        "lve_projection_value",
        "opportunity",
        "normalization_policy",
        "expected_recent_confidence_composite",
        "private_stat_feature",
    ),
    NormalizedFeatureSpec(
        "role_security",
        "role",
        "nflverse_snap_participation_depth",
        "role_security",
        "private_stat_feature",
    ),
    NormalizedFeatureSpec(
        "workload_earning",
        "role",
        "nflverse_player_stats_weekly",
        "workload_earning_score",
        "private_stat_feature",
    ),
    NormalizedFeatureSpec(
        "target_earning_stability",
        "role",
        "nflverse_participation_player_weekly",
        "target_earning_stability_score",
        "private_stat_feature",
    ),
    NormalizedFeatureSpec(
        "route_role",
        "role",
        "nflverse_participation_player_weekly",
        "route_role_score",
        "private_stat_feature",
    ),
    NormalizedFeatureSpec(
        "efficiency_score",
        "efficiency",
        "nflverse_player_stats_weekly",
        "lve_points_per_opportunity",
        "private_stat_feature",
    ),
    NormalizedFeatureSpec(
        "first_down_td_fit",
        "first_down_td_fit",
        "nflverse_player_stats_weekly",
        "rush_rec_first_downs_and_rush_rec_td_points",
        "private_stat_feature",
    ),
    NormalizedFeatureSpec(
        "age_curve",
        "age_window",
        "normalization_policy",
        "age_unavailable_neutral_placeholder",
        "private_stat_feature",
    ),
    NormalizedFeatureSpec(
        "injury_durability",
        "injury_durability",
        "nflverse_injuries_weekly",
        "injury_durability_score",
        "private_stat_feature",
    ),
)


@dataclass(frozen=True)
class NormalizationResult:
    status: str
    rows: tuple[dict[str, object], ...]
    issues: tuple[str, ...]


def derive_lve_normalized_veteran_feature_rows(
    source_root: str | Path,
    *,
    computed_at: str = "",
) -> NormalizationResult:
    inputs = _derive_normalization_inputs(source_root)
    if inputs["blocked"]:
        return NormalizationResult(status="blocked", rows=(), issues=inputs["issues"])
    scoring = inputs["scoring"]
    role = inputs["role"]
    injury = inputs["injury"]
    projection = inputs["projection"]
    keys = sorted(
        {
            _row_key(row)
            for row in (*scoring.rows, *role.rows, *injury.rows, *projection.rows)
            if _row_key(row)[0]
        }
    )
    scoring_by_key = _rows_by_key(scoring.rows)
    role_by_key = _rows_by_key(role.rows)
    injury_by_key = _rows_by_key(injury.rows)
    projection_by_key = _rows_by_key(projection.rows)
    rows = tuple(
        _normalized_row(
            key,
            scoring_by_key.get(key, []),
            role_by_key.get(key, []),
            injury_by_key.get(key, []),
            projection_by_key.get(key, []),
            computed_at,
        )
        for key in keys
    )
    status = "review" if any(
        result.status == "review" for result in (scoring, role, injury, projection)
    ) else "ready"
    return NormalizationResult(status=status, rows=rows, issues=inputs["issues"])


def derive_lve_normalized_feature_receipt_rows(
    source_root: str | Path,
    *,
    computed_at: str = "",
) -> NormalizationResult:
    inputs = _derive_normalization_inputs(source_root)
    if inputs["blocked"]:
        return NormalizationResult(status="blocked", rows=(), issues=inputs["issues"])
    scoring = inputs["scoring"]
    role = inputs["role"]
    injury = inputs["injury"]
    projection = inputs["projection"]
    keys = sorted(
        {
            _row_key(row)
            for row in (*scoring.rows, *role.rows, *injury.rows, *projection.rows)
            if _row_key(row)[0]
        }
    )
    scoring_by_key = _rows_by_key(scoring.rows)
    role_by_key = _rows_by_key(role.rows)
    injury_by_key = _rows_by_key(injury.rows)
    projection_by_key = _rows_by_key(projection.rows)
    rows = tuple(
        receipt_row
        for key in keys
        for receipt_row in _feature_receipt_rows(
            key,
            scoring_by_key.get(key, []),
            role_by_key.get(key, []),
            injury_by_key.get(key, []),
            projection_by_key.get(key, []),
            computed_at,
        )
    )
    status = "review" if any(
        result.status == "review" for result in (scoring, role, injury, projection)
    ) else "ready"
    return NormalizationResult(status=status, rows=rows, issues=inputs["issues"])


def write_lve_normalized_veteran_feature_rows(
    output_path: str | Path,
    rows: tuple[dict[str, object], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    extra_fields = [
        field
        for row in rows
        for field in row
        if field not in NORMALIZED_FEATURE_HEADER
    ]
    fieldnames = list(NORMALIZED_FEATURE_HEADER) + sorted(set(extra_fields))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_lve_normalized_feature_receipt_rows(
    output_path: str | Path,
    rows: tuple[dict[str, object], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NORMALIZED_FEATURE_RECEIPT_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def normalized_feature_summary_rows(
    rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    by_position: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_position.setdefault(str(row.get("position") or ""), []).append(row)
    output: list[dict[str, object]] = []
    for position in sorted(by_position):
        position_rows = by_position[position]
        avg_private = sum(
            float(row["private_stat_value"]) for row in position_rows
        ) / len(position_rows)
        avg_confidence = sum(
            float(row["confidence"]) for row in position_rows
        ) / len(position_rows)
        output.append(
            {
                "position": position,
                "rows": len(position_rows),
                "avg_private_stat_value": round(avg_private, 2),
                "avg_confidence": round(avg_confidence, 2),
                "scoring_effect": "normalized feature preview only; no model mutation",
            }
        )
    return output


def _derive_normalization_inputs(source_root: str | Path) -> dict[str, object]:
    scoring = derive_lve_weekly_scoring_rows(source_root)
    role = derive_lve_role_usage_feature_rows(source_root)
    injury = derive_lve_injury_durability_rows(source_root)
    projection = derive_lve_projection_feature_rows(source_root)
    results = (scoring, role, injury, projection)
    blockers = [result for result in results if result.status == "blocked"]
    issues = tuple(issue for result in results for issue in result.issues)
    return {
        "scoring": scoring,
        "role": role,
        "injury": injury,
        "projection": projection,
        "blocked": bool(blockers),
        "issues": tuple(issue for result in blockers for issue in result.issues)
        if blockers
        else issues,
    }


def _normalized_row(
    key: tuple[str, str, str, str],
    scoring_rows: list[dict[str, object]],
    role_rows: list[dict[str, object]],
    injury_rows: list[dict[str, object]],
    projection_rows: list[dict[str, object]],
    computed_at: str,
) -> dict[str, object]:
    player_id, player_name, position, team = key
    scoring_row = _first(scoring_rows)
    role_row = _best_source_row(role_rows)
    injury_row = _best_source_row(injury_rows)
    projection_row = _best_source_row(projection_rows)
    position = _latest_value(
        "position",
        scoring_rows,
        role_rows,
        injury_rows,
        projection_rows,
    ) or position
    player_name = _latest_value(
        "player_name",
        scoring_rows,
        role_rows,
        injury_rows,
        projection_rows,
    ) or player_name
    team = _latest_value(
        "team",
        scoring_rows,
        role_rows,
        injury_rows,
        projection_rows,
    ) or team
    weighted_recent_ppg_score = _weighted_recent_lve_ppg_score(scoring_rows, position)
    projection_is_independent = _is_independent_projection_row(projection_row)
    projection_source_status = _projection_source_status(projection_row)
    expected_lve_points_score = (
        _score(_float(projection_row.get("lve_projection_score"), default=50.0))
        if projection_is_independent
        else 50.0
    )
    lve_projection_value = _score(
        (0.45 * expected_lve_points_score)
        + (0.35 * weighted_recent_ppg_score)
        + (
            0.20
            * (
                _float(projection_row.get("confidence"), default=50.0)
                if projection_is_independent
                else 50.0
            )
        )
    )
    role_security = _score(_float(role_row.get("role_security"), default=50.0))
    workload_earning = _score(_float(role_row.get("workload_earning_score"), default=50.0))
    target_earning = _score(_float(role_row.get("target_earning_stability_score"), default=50.0))
    route_role = _score(_float(role_row.get("route_role_score"), default=50.0))
    efficiency_score = _efficiency_score(scoring_rows, position)
    first_down_td_fit = _first_down_td_fit(scoring_rows, position)
    age_curve = 50.0
    injury_durability = _injury_durability_score(injury_row, scoring_rows)
    private_stat_value = _private_stat_value(
        position,
        lve_projection_value,
        role_security,
        workload_earning,
        target_earning,
        route_role,
        efficiency_score,
        first_down_td_fit,
        age_curve,
        injury_durability,
    )
    confidence = _confidence(role_row, injury_row, projection_row, scoring_rows)
    warnings = _warnings(role_row, injury_row, projection_row, scoring_rows)
    missing_data_penalty = _missing_data_penalty(role_row, injury_row, projection_row, scoring_rows)
    source_season, source_week = _latest_source_period(
        scoring_rows,
        role_rows,
        injury_rows,
        projection_rows,
    )
    return {
        "season": source_season,
        "as_of_week": source_week,
        "player_id": player_id,
        "gsis_id": _first_value(scoring_row, role_row, injury_row, projection_row, "gsis_id"),
        "sleeper_id": _first_value(scoring_row, role_row, injury_row, projection_row, "sleeper_id"),
        "player_name": player_name,
        "position": position,
        "team": team,
        "weighted_recent_lve_ppg_score": round(weighted_recent_ppg_score, 2),
        "expected_lve_points_score": round(expected_lve_points_score, 2),
        "lve_projection_value": round(lve_projection_value, 2),
        "projection_source_status": projection_source_status,
        "role_security": round(role_security, 2),
        "workload_earning": round(workload_earning, 2),
        "target_earning_stability": round(target_earning, 2),
        "route_role": round(route_role, 2),
        "efficiency_score": round(efficiency_score, 2),
        "first_down_td_fit": round(first_down_td_fit, 2),
        "age_curve": round(age_curve, 2),
        "injury_durability": round(injury_durability, 2),
        "private_stat_value": round(private_stat_value, 2),
        "confidence": round(confidence, 2),
        "missing_data_penalty": round(missing_data_penalty, 2),
        "warnings": "|".join(sorted(warnings)),
        "source_version": "nflverse_stats_upgrade_v1",
        "computed_at": computed_at,
    }


def _weighted_recent_lve_ppg_score(
    scoring_rows: list[dict[str, object]],
    position: str,
) -> float:
    if not scoring_rows:
        return 50.0
    points = [_float(row.get("lve_points")) for row in scoring_rows]
    ppg = sum(points) / len(points)
    return _score(ppg / POSITION_PPG_ANCHORS.get(position, 14.0) * 100.0)


def _first_down_td_fit(
    scoring_rows: list[dict[str, object]],
    position: str,
) -> float:
    if not scoring_rows:
        return 50.0
    fd_per_game = sum(
        _float(row.get("rush_rec_first_downs")) for row in scoring_rows
    ) / len(scoring_rows)
    fd_score = _score(fd_per_game / POSITION_FIRST_DOWN_ANCHORS.get(position, 5.0) * 100.0)
    td_proxy_points = sum(
        _float(row.get("rushing_points")) + _float(row.get("receiving_points"))
        for row in scoring_rows
    ) / len(scoring_rows)
    td_score = _score(td_proxy_points / POSITION_PPG_ANCHORS.get(position, 14.0) * 100.0)
    return _score((0.65 * fd_score) + (0.35 * td_score))


def _efficiency_score(
    scoring_rows: list[dict[str, object]],
    position: str,
) -> float:
    if not scoring_rows:
        return 50.0
    if position == "QB":
        return _weighted_recent_lve_ppg_score(scoring_rows, position)
    points_per_opportunity = _points_per_opportunity(scoring_rows, position)
    return _score(
        points_per_opportunity / POSITION_EFFICIENCY_ANCHORS.get(position, 1.45) * 100.0
    )


def _private_stat_value(
    position: str,
    lve_projection_value: float,
    role_security: float,
    workload_earning: float,
    target_earning: float,
    route_role: float,
    efficiency_score: float,
    first_down_td_fit: float,
    age_curve: float,
    injury_durability: float,
) -> float:
    if position == "QB":
        return _score(
            (0.31 * lve_projection_value)
            + (0.30 * role_security)
            + (0.06 * efficiency_score)
            + (0.12 * first_down_td_fit)
            + (0.11 * age_curve)
            + (0.10 * injury_durability)
            - 8.0
        )
    if position == "RB":
        return _score(
            (0.27 * lve_projection_value)
            + (0.25 * role_security)
            + (0.17 * workload_earning)
            + (0.08 * efficiency_score)
            + (0.12 * first_down_td_fit)
            + (0.05 * age_curve)
            + (0.07 * injury_durability)
    )
    if position == "WR":
        bonus = (
            3.0
            if role_security >= 75 and target_earning >= 70
            else 1.0
            if role_security >= 65
            else 0.0
        )
        return _score(
            (0.25 * lve_projection_value)
            + (0.24 * role_security)
            + (0.20 * target_earning)
            + (0.08 * efficiency_score)
            + (0.10 * first_down_td_fit)
            + (0.07 * age_curve)
            + (0.07 * injury_durability)
            + bonus
        )
    penalty = (
        0.0
        if route_role >= 75 and target_earning >= 70
        else 8.0
        if route_role >= 55
        else 14.0
    )
    return _score(
        (0.21 * lve_projection_value)
        + (0.26 * route_role)
        + (0.20 * target_earning)
        + (0.07 * efficiency_score)
        + (0.08 * first_down_td_fit)
        + (0.08 * age_curve)
        + (0.10 * injury_durability)
        - penalty
    )


def _feature_receipt_rows(
    key: tuple[str, str, str, str],
    scoring_rows: list[dict[str, object]],
    role_rows: list[dict[str, object]],
    injury_rows: list[dict[str, object]],
    projection_rows: list[dict[str, object]],
    computed_at: str,
) -> tuple[dict[str, object], ...]:
    normalized = _normalized_row(
        key,
        scoring_rows,
        role_rows,
        injury_rows,
        projection_rows,
        computed_at,
    )
    player_id, _player_name, _position, _team = key
    player_name = str(normalized.get("player_name") or _player_name)
    position = str(normalized.get("position") or _position)
    team = str(normalized.get("team") or _team)
    return tuple(
        _feature_receipt_row(
            spec,
            normalized,
            player_id,
            player_name,
            position,
            team,
            scoring_rows,
            role_rows,
            injury_rows,
            projection_rows,
            computed_at,
        )
        for spec in NORMALIZED_FEATURE_SPECS
    )


def _feature_receipt_row(
    spec: NormalizedFeatureSpec,
    normalized: dict[str, object],
    player_id: str,
    player_name: str,
    position: str,
    team: str,
    scoring_rows: list[dict[str, object]],
    role_rows: list[dict[str, object]],
    injury_rows: list[dict[str, object]],
    projection_rows: list[dict[str, object]],
    computed_at: str,
) -> dict[str, object]:
    raw_value, warning_status, warning_reason, is_missing, imputation_value = (
        _feature_raw_context(
            spec.feature_name,
            position,
            scoring_rows,
            _best_source_row(role_rows),
            _best_source_row(injury_rows),
            _best_source_row(projection_rows),
        )
    )
    truth = classify_feature_truth(
        spec.feature_name,
        normalized,
        raw_value=raw_value,
        warning_reason=warning_reason,
    )
    normalized_value = normalized.get(spec.feature_name, "")
    projection_source_status = (
        normalized.get("projection_source_status", "")
        if spec.feature_name in {"expected_lve_points_score", "lve_projection_value"}
        else ""
    )
    return {
        "season": normalized.get("season", ""),
        "as_of_week": normalized.get("as_of_week", ""),
        "player_id": player_id,
        "gsis_id": normalized.get("gsis_id", ""),
        "sleeper_id": normalized.get("sleeper_id", ""),
        "player_name": player_name,
        "position": position,
        "team": team,
        "feature_bucket": spec.feature_bucket,
        "feature_name": spec.feature_name,
        "raw_value": raw_value,
        "normalized_value": normalized_value,
        "normalized_score": normalized_value,
        "source_key": spec.source_key,
        "source_status": truth.source_status,
        "projection_source_status": projection_source_status,
        "source_field": spec.source_field,
        "warning_status": warning_status,
        "warning_reason": truth.warning_reason or warning_reason,
        "imputed_flag": str(truth.imputed_flag or is_missing).lower(),
        "is_missing": str(truth.imputed_flag or is_missing).lower(),
        "imputation_value": truth.neutral_default_value or imputation_value,
        "model_usage": truth.model_usage,
        "computed_at": computed_at,
    }


def _feature_raw_context(
    feature_name: str,
    position: str,
    scoring_rows: list[dict[str, object]],
    role_row: dict[str, object],
    injury_row: dict[str, object],
    projection_row: dict[str, object],
) -> tuple[object, str, str, bool, object]:
    if feature_name == "weighted_recent_lve_ppg_score":
        if not scoring_rows:
            return "", "imputed", "missing_lve_scoring_history", True, 50.0
        return round(_avg(row.get("lve_points") for row in scoring_rows), 2), "ready", "", False, ""
    if feature_name == "expected_lve_points_score":
        if not projection_row:
            return "", "imputed", "missing_projection_features", True, 50.0
        if not _is_independent_projection_row(projection_row):
            warning = _projection_warning_reason(projection_row)
            return (
                projection_row.get("projection_scope", "local_baseline_recent_lve"),
                "imputed",
                warning,
                True,
                50.0,
            )
        return projection_row.get("lve_projected_ppg", ""), "ready", "", False, ""
    if feature_name == "lve_projection_value":
        if not projection_row and not scoring_rows:
            return "", "imputed", "missing_projection_and_production_sources", True, 50.0
        projection_warning = ""
        if projection_row and not _is_independent_projection_row(projection_row):
            projection_warning = _projection_warning_reason(projection_row)
        raw = (
            f"recent_ppg={round(_avg(row.get('lve_points') for row in scoring_rows), 2)};"
            f"projection_score={projection_row.get('lve_projection_score', 'imputed_50')};"
            f"projection_confidence={projection_row.get('confidence', 'imputed_50')}"
        )
        if not projection_row:
            return raw, "imputed", "missing_projection_component", True, 50.0
        if projection_warning:
            return raw, "imputed", projection_warning, True, 50.0
        if not scoring_rows:
            return raw, "imputed", "missing_recent_production_component", True, 50.0
        return raw, "ready", "", False, ""
    if feature_name in {
        "role_security",
        "workload_earning",
        "target_earning_stability",
        "route_role",
    }:
        role_field = {
            "role_security": "role_security",
            "workload_earning": "workload_earning_score",
            "target_earning_stability": "target_earning_stability_score",
            "route_role": "route_role_score",
        }[feature_name]
        if not role_row:
            return "", "imputed", "missing_role_usage_features", True, 50.0
        warning = str(role_row.get("warnings") or "")
        status = "review" if warning else "ready"
        if feature_name == "target_earning_stability":
            raw_value = role_row.get("target_earning_source_detail") or role_row.get(role_field, "")
            return raw_value, status, warning, False, ""
        return role_row.get(role_field, ""), status, warning, False, ""
    if feature_name == "efficiency_score":
        if not scoring_rows:
            return "", "imputed", "missing_efficiency_source_stats", True, 50.0
        return round(_points_per_opportunity(scoring_rows, position), 3), "ready", "", False, ""
    if feature_name == "first_down_td_fit":
        if not scoring_rows:
            return "", "imputed", "missing_first_down_td_source_stats", True, 50.0
        raw = round(
            _avg(row.get("rush_rec_first_downs") for row in scoring_rows),
            2,
        )
        return raw, "ready", "", False, ""
    if feature_name == "age_curve":
        return 50.0, "review", "age_curve_source_not_imported_yet", True, 50.0
    if feature_name == "injury_durability":
        if not injury_row:
            return "", "imputed", "missing_injury_features", True, 75.0
        warning = str(injury_row.get("warnings") or injury_row.get("risk_flags") or "")
        if not scoring_rows and "no_injury_report_rows" in warning:
            return (
                injury_row.get("injury_durability_score", ""),
                "imputed",
                "no_injury_report_rows_without_nfl_activity",
                True,
                50.0,
            )
        status = "review" if warning else "ready"
        return injury_row.get("injury_durability_score", ""), status, warning, False, ""
    return "", "missing", "unknown_feature_spec", True, ""


def _injury_durability_score(
    injury_row: dict[str, object],
    scoring_rows: list[dict[str, object]],
) -> float:
    warning = str(injury_row.get("warnings") or injury_row.get("risk_flags") or "")
    if not scoring_rows and "no_injury_report_rows" in warning:
        return 50.0
    return _score(_float(injury_row.get("injury_durability_score"), default=75.0))


def _confidence(
    role_row: dict[str, object],
    injury_row: dict[str, object],
    projection_row: dict[str, object],
    scoring_rows: list[dict[str, object]],
) -> float:
    projection_confidence = (
        _float(projection_row.get("confidence"), default=50.0)
        if _is_independent_projection_row(projection_row)
        else 50.0
    )
    parts = [
        90.0 if scoring_rows else 50.0,
        _float(role_row.get("confidence"), default=50.0),
        _float(injury_row.get("confidence"), default=70.0),
        projection_confidence,
    ]
    return _score(
        sum(parts) / len(parts)
        - _missing_data_penalty(role_row, injury_row, projection_row, scoring_rows)
    )


def _missing_data_penalty(
    role_row: dict[str, object],
    injury_row: dict[str, object],
    projection_row: dict[str, object],
    scoring_rows: list[dict[str, object]],
) -> float:
    penalty = 0.0
    if not scoring_rows:
        penalty += 8.0
    if not role_row:
        penalty += 10.0
    if not projection_row:
        penalty += 8.0
    elif not _is_independent_projection_row(projection_row):
        penalty += 4.0
    if not injury_row:
        penalty += 4.0
    return min(20.0, penalty)


def _warnings(
    role_row: dict[str, object],
    injury_row: dict[str, object],
    projection_row: dict[str, object],
    scoring_rows: list[dict[str, object]],
) -> set[str]:
    warnings: set[str] = set()
    for row in (role_row, injury_row, projection_row):
        warning_text = str(row.get("warnings") or "")
        warnings.update(part for part in warning_text.split("|") if part)
    if not scoring_rows:
        warnings.add("missing_lve_scoring_history")
    elif _latest_non_scoring_season(role_row, injury_row, projection_row) > _latest_scoring_season(
        scoring_rows
    ):
        warnings.add("stale_lve_scoring_source")
    if projection_row and not _is_independent_projection_row(projection_row):
        warnings.add(_projection_warning_reason(projection_row))
    if not role_row:
        warnings.add("missing_role_usage_features")
    if not projection_row:
        warnings.add("missing_projection_features")
    if not injury_row:
        warnings.add("missing_injury_features")
    return warnings


def _latest_scoring_season(scoring_rows: list[dict[str, object]]) -> int:
    return max((int(_float(row.get("season"), 0)) for row in scoring_rows), default=0)


def _latest_non_scoring_season(*rows: dict[str, object]) -> int:
    return max((int(_float(row.get("season"), 0)) for row in rows if row), default=0)


def _is_independent_projection_row(row: dict[str, object]) -> bool:
    return projection_source_status_from_row(row) == PROJECTION_SOURCE_INDEPENDENT


def _projection_source_status(row: dict[str, object]) -> str:
    return projection_source_status_from_row(row)


def _projection_warning_reason(row: dict[str, object]) -> str:
    status = projection_source_status_from_row(row)
    if status == PROJECTION_SOURCE_LOCAL_BASELINE:
        return "local_baseline_projection_not_independent"
    if status == PROJECTION_SOURCE_DISABLED:
        return PROJECTION_SOURCE_DISABLED
    if status == PROJECTION_SOURCE_MISSING:
        return "missing_projection_features"
    return status


def _rows_by_key(
    rows: tuple[dict[str, object], ...],
) -> dict[tuple[str, str, str, str], list[dict[str, object]]]:
    output: dict[tuple[str, str, str, str], list[dict[str, object]]] = {}
    for row in rows:
        output.setdefault(_row_key(row), []).append(row)
    return output


def _row_key(row: dict[str, object]) -> tuple[str, str, str, str]:
    return (
        str(row.get("player_id") or row.get("gsis_id") or row.get("sleeper_id") or ""),
        "",
        "",
        "",
    )


def _first(rows: list[dict[str, object]]) -> dict[str, object]:
    return rows[0] if rows else {}


def _best_source_row(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {}

    def sort_key(row: dict[str, object]) -> tuple[float, int, int, int]:
        warnings = str(row.get("warnings") or "").split("|")
        warning_count = len([warning for warning in warnings if warning])
        return (
            _float(row.get("confidence"), 0),
            -warning_count,
            int(_float(row.get("season"), 0)),
            int(_float(row.get("week"), 0)),
        )

    return max(rows, key=sort_key)


def _first_value(*rows_and_column) -> str:
    *rows, column = rows_and_column
    for row in rows:
        value = row.get(column, "")
        if value:
            return str(value)
    return ""


def _latest_value(
    column: str,
    *row_groups: list[dict[str, object]],
) -> str:
    latest_sort_key = (-1, -1)
    latest_value = ""
    for rows in row_groups:
        for row in rows:
            value = str(row.get(column) or "")
            if not value:
                continue
            sort_key = (
                int(_float(row.get("season"), 0)),
                int(_float(row.get("week"), 0)),
            )
            if sort_key >= latest_sort_key:
                latest_sort_key = sort_key
                latest_value = value
    return latest_value


def _latest_source_period(
    *row_groups: list[dict[str, object]],
) -> tuple[str, str]:
    latest_sort_key = (-1, -1)
    latest_row: dict[str, object] = {}
    for rows in row_groups:
        for row in rows:
            if not row.get("season"):
                continue
            sort_key = (
                int(_float(row.get("season"), 0)),
                int(_float(row.get("week"), 0)),
            )
            if sort_key >= latest_sort_key:
                latest_sort_key = sort_key
                latest_row = row
    return str(latest_row.get("season") or ""), str(latest_row.get("week") or "")


def _avg(values) -> float:
    numeric = [_float(value) for value in values]
    if not numeric:
        return 0.0
    return sum(numeric) / len(numeric)


def _points_per_opportunity(
    scoring_rows: list[dict[str, object]],
    position: str,
) -> float:
    if position == "QB":
        return _avg(row.get("lve_points") for row in scoring_rows)
    points = sum(_float(row.get("lve_points")) for row in scoring_rows)
    opportunities = sum(
        max(_float(row.get("touches")) + _float(row.get("targets")), 1.0)
        for row in scoring_rows
    )
    return points / max(opportunities, 1.0)


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _score(value: float) -> float:
    return max(0.0, min(100.0, value))

