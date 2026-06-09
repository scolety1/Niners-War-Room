from __future__ import annotations

import csv
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.model_v4_fantasypros_identity_mapping_service import normalize_player_name

DEFAULT_TRUTH_SET = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")
DEFAULT_PLAYER_STATS = Path(
    "local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv"
)
DEFAULT_ROLE_USAGE = Path(
    "local_exports/model_v4/rotowire_intake/latest/rotowire_role_usage_clean_rows.csv"
)
DEFAULT_CONTEXT = Path(
    "local_exports/model_v4/rotowire_intake/latest/rotowire_context_clean_rows.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/rotowire_stats_first/latest")

STATS_FIRST_VERSION = "model_v4_rotowire_stats_first_value_0.1.0"

SEASON_WEIGHTS = {
    2025: 1.0,
    2024: 0.65,
    2023: 0.35,
}
DEEP_HISTORY_WEIGHT = 0.12

COMPONENT_WEIGHTS = {
    "QB": {
        "lve_base_production": 0.45,
        "opportunity_volume": 0.25,
        "efficiency": 0.15,
        "red_zone_role": 0.15,
    },
    "RB": {
        "lve_base_production": 0.35,
        "opportunity_volume": 0.25,
        "red_zone_role": 0.15,
        "efficiency": 0.10,
        "snap_role": 0.10,
        "route_receiving_role": 0.05,
    },
    "WR": {
        "lve_base_production": 0.30,
        "opportunity_volume": 0.20,
        "route_receiving_role": 0.20,
        "red_zone_role": 0.10,
        "snap_role": 0.10,
        "efficiency": 0.10,
    },
    "TE": {
        "lve_base_production": 0.30,
        "opportunity_volume": 0.20,
        "route_receiving_role": 0.20,
        "red_zone_role": 0.10,
        "snap_role": 0.10,
        "efficiency": 0.10,
    },
}

POSITION_VALUE_MULTIPLIERS = {
    "RB": 1.00,
    "WR": 0.96,
    "QB": 0.72,
    "TE": 0.62,
}

VALUE_HEADER = (
    "overall_rank",
    "position_rank",
    "player_name",
    "normalized_player_name",
    "position",
    "nfl_team",
    "lifecycle_expected",
    "pre_format_stats_first_value",
    "format_position_multiplier",
    "stats_first_value",
    "confidence_label",
    "weighted_seasons",
    "component_scores_json",
    "component_contributions_json",
    "warnings",
    "projections_used_for_core_value",
    "market_used_for_private_value",
    "league_rank_used_for_private_value",
    "value_version",
)

COMPONENT_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "component",
    "raw_weighted_value",
    "normalized_score",
    "component_weight",
    "contribution",
    "weighted_seasons",
    "source_status",
    "allowed_use",
    "warning",
    "value_version",
)

WARNING_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "warning_type",
    "severity",
    "detail",
    "value_version",
)


@dataclass(frozen=True)
class RotoWireStatsFirstValueResult:
    value_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class _RawComponent:
    player_name: str
    position: str
    nfl_team: str
    component: str
    raw_weighted_value: float | None
    weighted_seasons: str
    source_status: str
    allowed_use: str
    warning: str


def build_rotowire_stats_first_value_layer(
    *,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET,
    player_stats_path: str | Path = DEFAULT_PLAYER_STATS,
    role_usage_path: str | Path = DEFAULT_ROLE_USAGE,
    context_path: str | Path = DEFAULT_CONTEXT,
) -> RotoWireStatsFirstValueResult:
    truth_rows = _read_rows(Path(truth_set_path))
    player_stats = _rows_by_name(Path(player_stats_path), "player_name")
    role_usage = _rows_by_name(Path(role_usage_path), "player_name")
    context = _rows_by_name(Path(context_path), "entity_name")

    raw_components: list[_RawComponent] = []
    warnings: list[dict[str, object]] = []
    truth_by_player = {row["player_name"]: row for row in truth_rows}

    for truth in truth_rows:
        player = truth["player_name"]
        normalized = normalize_player_name(player)
        stats_rows = player_stats.get(normalized, [])
        role_rows = role_usage.get(normalized, [])
        context_rows = context.get(normalized, [])
        player_components, player_warnings = _player_raw_components(
            truth,
            stats_rows,
            role_rows,
            context_rows,
        )
        raw_components.extend(player_components)
        warnings.extend(player_warnings)

    component_rows = _normalize_components(raw_components)
    value_rows = _build_value_rows(truth_rows, component_rows, warnings)
    _rank_value_rows(value_rows)

    summary = {
        "value_version": STATS_FIRST_VERSION,
        "review_status": "review_only",
        "truth_player_count": len(truth_by_player),
        "value_row_count": len(value_rows),
        "component_row_count": len(component_rows),
        "warning_row_count": len(warnings),
        "strong_confidence_count": sum(
            1 for row in value_rows if row["confidence_label"] == "strong"
        ),
        "review_confidence_count": sum(
            1 for row in value_rows if "review" in str(row["confidence_label"])
        ),
        "projection_rows_used_for_core_value": 0,
        "market_value_used_for_private_value": False,
        "league_rank_used_for_private_value": False,
        "position_value_multipliers": json.dumps(POSITION_VALUE_MULTIPLIERS, sort_keys=True),
        "active_rankings_overwritten": False,
        "model_scores_changed": False,
    }
    return RotoWireStatsFirstValueResult(
        value_rows=tuple(value_rows),
        component_rows=tuple(component_rows),
        warning_rows=tuple(warnings),
        summary=summary,
    )


def write_rotowire_stats_first_value_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: RotoWireStatsFirstValueResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rotowire_stats_first_value_layer()
    value_path = output / "rotowire_stats_first_value_rows.csv"
    component_path = output / "rotowire_stats_first_component_rows.csv"
    warning_path = output / "rotowire_stats_first_warning_rows.csv"
    summary_path = output / "rotowire_stats_first_summary.csv"
    _write_csv(value_path, VALUE_HEADER, result.value_rows)
    _write_csv(component_path, COMPONENT_HEADER, result.component_rows)
    _write_csv(warning_path, WARNING_HEADER, result.warning_rows)
    _write_csv(
        summary_path,
        ("metric", "value"),
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    return {
        "value": value_path,
        "components": component_path,
        "warnings": warning_path,
        "summary": summary_path,
    }


def _player_raw_components(
    truth: dict[str, str],
    stats_rows: list[dict[str, str]],
    role_rows: list[dict[str, str]],
    context_rows: list[dict[str, str]],
) -> tuple[list[_RawComponent], list[dict[str, object]]]:
    position = truth["position"]
    stats_by_season = _season_metric_maps(stats_rows)
    role_by_season = _season_metric_maps(role_rows)
    player_warnings = _player_warnings(truth, stats_rows, role_rows, context_rows)
    components = [
        _component(
            truth,
            "lve_base_production",
            _weighted_component(stats_by_season, lambda season: _lve_base(position, season)),
            source_status="imported_real_data",
            allowed_use="scoring_allowed",
        ),
        _component(
            truth,
            "opportunity_volume",
            _weighted_component(
                stats_by_season,
                lambda season: _opportunity_volume(position, season),
            ),
            source_status="imported_real_data",
            allowed_use="scoring_allowed",
        ),
        _component(
            truth,
            "efficiency",
            _weighted_component(stats_by_season, lambda season: _efficiency(position, season)),
            source_status="imported_real_data",
            allowed_use="scoring_allowed_with_confidence_penalty",
        ),
        _component(
            truth,
            "red_zone_role",
            _weighted_component(stats_by_season, lambda season: _red_zone_role(position, season)),
            source_status="imported_real_data",
            allowed_use="scoring_allowed",
        ),
        _component(
            truth,
            "snap_role",
            _weighted_component(role_by_season, lambda season: _snap_role(position, season)),
            source_status="imported_snap_data",
            allowed_use="scoring_allowed_with_confidence_penalty",
            missing_status="not_applicable" if position == "QB" else "missing",
            missing_allowed_use="not_applicable"
            if position == "QB"
            else "scoring_allowed_with_confidence_penalty",
            missing_warning="not_applicable_for_qb" if position == "QB" else "missing_snap_role",
        ),
        _component(
            truth,
            "route_receiving_role",
            _weighted_component(
                _merge_season_maps(stats_by_season, role_by_season),
                lambda season: _route_receiving_role(position, season),
            ),
            source_status="licensed_user_export_route_data",
            allowed_use="scoring_allowed_with_confidence_penalty",
            missing_status="not_applicable" if position == "QB" else "missing",
            missing_allowed_use="not_applicable"
            if position == "QB"
            else "scoring_allowed_with_confidence_penalty",
            missing_warning="not_applicable_for_qb" if position == "QB" else "missing_route_role",
        ),
    ]
    return (
        tuple(
            component
            for component in components
            if component.component in COMPONENT_WEIGHTS.get(position, {})
        ),
        player_warnings,
    )


def _component(
    truth: dict[str, str],
    component: str,
    weighted: tuple[float | None, str],
    *,
    source_status: str,
    allowed_use: str,
    missing_status: str = "missing",
    missing_allowed_use: str | None = None,
    missing_warning: str = "missing_component_evidence",
) -> _RawComponent:
    raw_value, weighted_seasons = weighted
    has_value = raw_value is not None
    return _RawComponent(
        player_name=truth["player_name"],
        position=truth["position"],
        nfl_team=truth.get("nfl_team", ""),
        component=component,
        raw_weighted_value=raw_value,
        weighted_seasons=weighted_seasons,
        source_status=source_status if has_value else missing_status,
        allowed_use=allowed_use if has_value else (missing_allowed_use or allowed_use),
        warning="" if has_value else missing_warning,
    )


def _weighted_component(
    by_season: dict[int, dict[str, float]],
    value_fn: Callable[[dict[str, float]], float | None],
) -> tuple[float | None, str]:
    weighted_values: list[tuple[float, float, str]] = []
    deep_history_values: list[float] = []
    deep_history_seasons: list[int] = []
    for season, metrics in sorted(by_season.items()):
        value = value_fn(metrics)
        if value is None:
            continue
        if season in SEASON_WEIGHTS:
            weight = SEASON_WEIGHTS[season]
            weighted_values.append((value, weight, f"{season}:{weight}"))
        elif season <= 2022:
            deep_history_values.append(value)
            deep_history_seasons.append(season)
    if deep_history_values:
        value = sum(deep_history_values) / len(deep_history_values)
        seasons = f"{min(deep_history_seasons)}-{max(deep_history_seasons)}"
        weighted_values.append(
            (
                value,
                DEEP_HISTORY_WEIGHT,
                f"deep_history_through_2022:{DEEP_HISTORY_WEIGHT}({seasons})",
            )
        )
    if not weighted_values:
        return None, ""
    numerator = sum(value * weight for value, weight, _label in weighted_values)
    denominator = sum(weight for _value, weight, _label in weighted_values)
    labels = "|".join(label for _value, _weight, label in weighted_values)
    return numerator / denominator, labels


def _normalize_components(raw_components: list[_RawComponent]) -> list[dict[str, object]]:
    raw_by_position_component: dict[tuple[str, str], list[float]] = {}
    for component in raw_components:
        if component.raw_weighted_value is None:
            continue
        key = (component.position, component.component)
        raw_by_position_component.setdefault(key, []).append(component.raw_weighted_value)

    rows: list[dict[str, object]] = []
    for component in raw_components:
        weight = COMPONENT_WEIGHTS[component.position][component.component]
        raw_value = component.raw_weighted_value
        normalized = 0.0
        if raw_value is not None:
            values = raw_by_position_component[(component.position, component.component)]
            normalized = _percentile_score(raw_value, values)
        rows.append(
            {
                "player_name": component.player_name,
                "position": component.position,
                "nfl_team": component.nfl_team,
                "component": component.component,
                "raw_weighted_value": "" if raw_value is None else round(raw_value, 4),
                "normalized_score": round(normalized, 4),
                "component_weight": weight,
                "contribution": round(normalized * weight, 4),
                "weighted_seasons": component.weighted_seasons,
                "source_status": component.source_status,
                "allowed_use": component.allowed_use,
                "warning": component.warning,
                "value_version": STATS_FIRST_VERSION,
            }
        )
    return rows


def _build_value_rows(
    truth_rows: tuple[dict[str, str], ...],
    component_rows: list[dict[str, object]],
    warning_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    components_by_player: dict[str, list[dict[str, object]]] = {}
    warnings_by_player: dict[str, list[dict[str, object]]] = {}
    for component in component_rows:
        components_by_player.setdefault(str(component["player_name"]), []).append(component)
    for warning in warning_rows:
        warnings_by_player.setdefault(str(warning["player_name"]), []).append(warning)

    value_rows: list[dict[str, object]] = []
    for truth in truth_rows:
        player = truth["player_name"]
        components = components_by_player.get(player, [])
        warning_types = sorted(
            {
                str(warning["warning_type"])
                for warning in warnings_by_player.get(player, [])
                if warning["severity"] != "info"
            }
        )
        component_scores = {
            str(row["component"]): row["normalized_score"] for row in components
        }
        component_contributions = {
            str(row["component"]): row["contribution"] for row in components
        }
        weighted_seasons = sorted(
            {str(row["weighted_seasons"]) for row in components if row["weighted_seasons"]}
        )
        pre_format_value = sum(float(row["contribution"]) for row in components)
        multiplier = POSITION_VALUE_MULTIPLIERS.get(truth["position"], 1.0)
        value = pre_format_value * multiplier
        value_rows.append(
            {
                "overall_rank": "",
                "position_rank": "",
                "player_name": player,
                "normalized_player_name": normalize_player_name(player),
                "position": truth["position"],
                "nfl_team": truth.get("nfl_team", ""),
                "lifecycle_expected": truth.get("lifecycle_expected", ""),
                "pre_format_stats_first_value": round(pre_format_value, 4),
                "format_position_multiplier": multiplier,
                "stats_first_value": round(value, 4),
                "confidence_label": _confidence_label(components, warning_types),
                "weighted_seasons": "|".join(weighted_seasons),
                "component_scores_json": json.dumps(component_scores, sort_keys=True),
                "component_contributions_json": json.dumps(
                    component_contributions,
                    sort_keys=True,
                ),
                "warnings": "|".join(warning_types),
                "projections_used_for_core_value": False,
                "market_used_for_private_value": False,
                "league_rank_used_for_private_value": False,
                "value_version": STATS_FIRST_VERSION,
            }
        )
    return value_rows


def _rank_value_rows(value_rows: list[dict[str, object]]) -> None:
    value_rows.sort(key=lambda row: float(row["stats_first_value"]), reverse=True)
    for index, row in enumerate(value_rows, start=1):
        row["overall_rank"] = index
    by_position: dict[str, int] = {}
    for row in value_rows:
        position = str(row["position"])
        by_position[position] = by_position.get(position, 0) + 1
        row["position_rank"] = by_position[position]


def _confidence_label(components: list[dict[str, object]], warning_types: list[str]) -> str:
    if "missing_historical_production" in warning_types:
        return "weak_review"
    if "sourced_injury_status" in warning_types:
        return "review"
    missing = sum(1 for component in components if component["source_status"] == "missing")
    if missing >= 2:
        return "moderate_review"
    if missing == 1:
        return "moderate"
    return "strong"


def _player_warnings(
    truth: dict[str, str],
    stats_rows: list[dict[str, str]],
    role_rows: list[dict[str, str]],
    context_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    warnings: list[dict[str, object]] = []
    player = truth["player_name"]
    position = truth["position"]
    team = truth.get("nfl_team", "")
    if not stats_rows:
        warnings.append(
            _warning(truth, "missing_historical_production", "review", "No RotoWire NFL stat rows.")
        )
    if position != "QB" and not role_rows:
        warnings.append(
            _warning(truth, "missing_role_usage", "review", "No snap/target/route rows.")
        )
    if _context_rows(context_rows, "injuries"):
        statuses = sorted(
            {
                str(
                    metric.get("status")
                    or metric.get("listed_status")
                    or metric.get("injury")
                    or ""
                )
                for row in _context_rows(context_rows, "injuries")
                for metric in [json.loads(row.get("metrics_json") or "{}")]
            }
        )
        warnings.append(
            {
                "player_name": player,
                "position": position,
                "nfl_team": team,
                "warning_type": "sourced_injury_status",
                "severity": "context",
                "detail": "|".join(status for status in statuses if status),
                "value_version": STATS_FIRST_VERSION,
            }
        )
    return warnings


def _warning(
    truth: dict[str, str],
    warning_type: str,
    severity: str,
    detail: str,
) -> dict[str, object]:
    return {
        "player_name": truth["player_name"],
        "position": truth["position"],
        "nfl_team": truth.get("nfl_team", ""),
        "warning_type": warning_type,
        "severity": severity,
        "detail": detail,
        "value_version": STATS_FIRST_VERSION,
    }


def _season_metric_maps(rows: list[dict[str, str]]) -> dict[int, dict[str, float]]:
    by_season: dict[int, dict[str, float]] = {}
    for row in rows:
        season = _int(row.get("season"))
        if season is None:
            continue
        metrics = json.loads(row.get("metrics_json") or "{}")
        by_season.setdefault(season, {}).update(
            {key: _float(value) for key, value in metrics.items() if _float(value) is not None}
        )
    return by_season


def _merge_season_maps(
    left: dict[int, dict[str, float]],
    right: dict[int, dict[str, float]],
) -> dict[int, dict[str, float]]:
    seasons = sorted(set(left) | set(right))
    merged: dict[int, dict[str, float]] = {}
    for season in seasons:
        merged[season] = {**left.get(season, {}), **right.get(season, {})}
    return merged


def _lve_base(position: str, metrics: dict[str, float]) -> float | None:
    values = [
        metrics.get("passing_yds", 0) * LVE_SCORING["passing_yard"],
        metrics.get("passing_td", 0) * LVE_SCORING["passing_td"],
        metrics.get("passing_int", 0) * LVE_SCORING["interception"],
        metrics.get("rushing_yds", 0) * LVE_SCORING["rushing_yard"],
        metrics.get("rushing_td", 0) * LVE_SCORING["rushing_td"],
        metrics.get("receiving_yds", 0) * LVE_SCORING["receiving_yard"],
        metrics.get("receiving_td", 0) * LVE_SCORING["receiving_td"],
        metrics.get("fumbles_lost", 0) * LVE_SCORING["fumble_lost"],
    ]
    if position == "QB" and not metrics.get("passing_att") and not metrics.get("rushing_att"):
        return None
    if position != "QB" and not any(
        metrics.get(key) for key in ("rushing_att", "receiving_tar", "receiving_rec")
    ):
        return None
    return sum(values)


def _opportunity_volume(position: str, metrics: dict[str, float]) -> float | None:
    passing_att = metrics.get("passing_att", 0)
    rushing_att = metrics.get("rushing_att", 0)
    targets = metrics.get("receiving_tar", metrics.get("receiving_totals_tar", 0))
    if position == "QB":
        value = passing_att * 0.35 + rushing_att
    elif position == "RB":
        value = rushing_att + targets * 1.3
    else:
        value = targets
    return value or None


def _efficiency(position: str, metrics: dict[str, float]) -> float | None:
    if position == "QB":
        ypa = metrics.get("passing_ypa", 0)
        qbr = metrics.get("passing_qbr", 0) / 20
        rush = _safe_div(metrics.get("rushing_yds", 0), metrics.get("rushing_att", 0))
        value = ypa + qbr + rush * 0.25
    elif position == "RB":
        rush = _safe_div(metrics.get("rushing_yds", 0), metrics.get("rushing_att", 0))
        rec = _safe_div(metrics.get("receiving_yds", 0), metrics.get("receiving_tar", 0))
        after_contact = metrics.get("after_contact_avg", 0)
        value = rush + rec * 0.35 + after_contact * 0.5
    else:
        ypt = metrics.get("receiving_ypt", 0)
        yprr = metrics.get("routes_run_yprr", 0)
        adot = metrics.get("air_yards_ay_depth_of_target_adot", 0)
        value = ypt + yprr * 2 + adot * 0.15
    return value or None


def _red_zone_role(position: str, metrics: dict[str, float]) -> float | None:
    if position == "QB":
        value = metrics.get("red_zone_passes_in20", 0) + metrics.get("red_zone_rush_att_in20", 0)
    elif position == "RB":
        value = metrics.get("red_zone_rush_att_in20", 0) + metrics.get("red_zone_targets_in20", 0)
    else:
        value = metrics.get("red_zone_targets_in20", 0)
    return value or None


def _snap_role(position: str, metrics: dict[str, float]) -> float | None:
    if position == "QB":
        return None
    value = metrics.get("snap_count_off_2", 0)
    return value or None


def _route_receiving_role(position: str, metrics: dict[str, float]) -> float | None:
    if position == "QB":
        return None
    routes = metrics.get("routes_run_rts", 0)
    tprr = metrics.get("routes_run_tprr", 0)
    yprr = metrics.get("routes_run_yprr", 0)
    team_tar = metrics.get("team_tar", 0)
    te_route_total = metrics.get("route_data_route", 0)
    if routes or tprr or yprr or team_tar:
        return routes * 0.05 + tprr * 1.5 + yprr * 12 + team_tar
    if te_route_total:
        return te_route_total * 0.05
    return None


def _context_rows(rows: list[dict[str, str]], family: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("source_family") == family]


def _rows_by_name(path: Path, name_column: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in _read_rows(path):
        normalized = normalize_player_name(row.get(name_column, ""))
        if not normalized:
            continue
        grouped.setdefault(normalized, []).append(row)
    return grouped


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _percentile_score(value: float, values: list[float]) -> float:
    if not values:
        return 0.0
    lower_or_equal = sum(1 for candidate in values if candidate <= value)
    return (lower_or_equal / len(values)) * 100


def _safe_div(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator


def _int(value: object) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(str(value))
    except ValueError:
        return None


def _float(value: object) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(str(value).replace(",", "").replace("%", ""))
    except ValueError:
        return None
