from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.model_v4_fantasypros_identity_mapping_service import (
    normalize_player_name,
)

DEFAULT_CLEAN_ROWS = Path(
    "local_exports/model_v4/historical_fantasypros_advanced/latest/"
    "fantasypros_advanced_clean_rows.csv"
)
DEFAULT_IDENTITY_MAPPING = Path(
    "local_exports/model_v4/historical_fantasypros_advanced/latest/"
    "fantasypros_advanced_identity_mapping.csv"
)
DEFAULT_PRODUCTION_SEASON = Path(
    "local_exports/model_v4/source_reports/truth_set_v3_production_player_season.csv"
)
DEFAULT_USAGE_SEASON = Path(
    "local_exports/model_v4/source_reports/truth_set_v3_usage_player_season.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/stats_first_expected_value/latest")

EXPECTED_VALUE_LAYER_VERSION = "model_v4_stats_first_expected_value_0.1.0"

TEAM_ALIASES = {
    "JAC": "JAX",
    "LA": "LAR",
    "STL": "LAR",
    "SD": "LAC",
    "OAK": "LV",
    "WSH": "WAS",
}

SEASON_WEIGHTS = {
    2025: 1.0,
    2024: 0.65,
    2023: 0.35,
}
DEEP_HISTORY_WEIGHT = 0.12
MAX_RECENCY_WEIGHT = sum(SEASON_WEIGHTS.values()) + DEEP_HISTORY_WEIGHT

COMPONENTS = (
    "production_trend",
    "target_carry_volume",
    "target_share_team_share",
    "air_yard_role",
    "red_zone_involvement",
    "explosive_play_profile",
    "yards_after_catch_contact",
    "broken_tackle_context",
    "drop_catchable_context",
    "qb_pressure_air_yard_context",
)

COMPONENT_WEIGHTS = {
    "QB": {
        "production_trend": 0.30,
        "target_carry_volume": 0.15,
        "air_yard_role": 0.15,
        "red_zone_involvement": 0.10,
        "explosive_play_profile": 0.10,
        "qb_pressure_air_yard_context": 0.20,
    },
    "RB": {
        "production_trend": 0.28,
        "target_carry_volume": 0.24,
        "target_share_team_share": 0.12,
        "red_zone_involvement": 0.14,
        "explosive_play_profile": 0.08,
        "yards_after_catch_contact": 0.08,
        "broken_tackle_context": 0.06,
    },
    "WR": {
        "production_trend": 0.25,
        "target_carry_volume": 0.18,
        "target_share_team_share": 0.15,
        "air_yard_role": 0.12,
        "red_zone_involvement": 0.10,
        "explosive_play_profile": 0.08,
        "yards_after_catch_contact": 0.07,
        "broken_tackle_context": 0.03,
        "drop_catchable_context": 0.02,
    },
    "TE": {
        "production_trend": 0.24,
        "target_carry_volume": 0.20,
        "target_share_team_share": 0.14,
        "air_yard_role": 0.10,
        "red_zone_involvement": 0.12,
        "explosive_play_profile": 0.06,
        "yards_after_catch_contact": 0.06,
        "broken_tackle_context": 0.03,
        "drop_catchable_context": 0.05,
    },
}

EXPECTED_VALUE_HEADER = (
    "matched_model_player",
    "position",
    "sleeper_id",
    "gsis_id",
    "latest_season",
    "weighted_seasons",
    "stats_first_expected_value",
    "evidence_coverage",
    "component_scores",
    "component_contributions",
    "component_weights",
    "source_warning_count",
    "unavailable_section_count",
    "external_projection_context_status",
    "review_status",
    "layer_version",
)

COMPONENT_EVIDENCE_HEADER = (
    "matched_model_player",
    "position",
    "sleeper_id",
    "gsis_id",
    "component",
    "season",
    "season_weight",
    "raw_value",
    "weighted_raw_value",
    "normalized_score",
    "component_weight",
    "contribution",
    "source_fields",
    "source_name",
    "source_status",
    "source_warning",
)

UNAVAILABLE_HEADER = (
    "matched_model_player",
    "position",
    "component_or_section",
    "reason",
    "severity",
)

SOURCE_WARNING_HEADER = (
    "matched_model_player",
    "position",
    "season",
    "source_name",
    "warning",
    "detail",
)

SUMMARY_HEADER = ("metric", "value")


@dataclass(frozen=True)
class StatsFirstExpectedValueResult:
    expected_value_rows: tuple[dict[str, object], ...]
    component_evidence_rows: tuple[dict[str, object], ...]
    unavailable_rows: tuple[dict[str, object], ...]
    source_warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class _SourceEvidence:
    player: str
    position: str
    sleeper_id: str
    gsis_id: str
    component: str
    season: int
    raw_value: float
    source_fields: tuple[str, ...]
    source_name: str
    source_status: str
    source_warning: str


def build_stats_first_expected_value_layer(
    *,
    clean_rows_path: str | Path = DEFAULT_CLEAN_ROWS,
    identity_mapping_path: str | Path = DEFAULT_IDENTITY_MAPPING,
    production_season_path: str | Path = DEFAULT_PRODUCTION_SEASON,
    usage_season_path: str | Path = DEFAULT_USAGE_SEASON,
    projection_context_path: str | Path | None = None,
) -> StatsFirstExpectedValueResult:
    clean_rows = _read_rows(Path(clean_rows_path))
    mapping_rows = _read_rows(Path(identity_mapping_path))
    mapping_by_key = {_mapping_key(row): row for row in mapping_rows}
    production_by_player_season = _production_by_player_season(
        _read_rows_if_exists(Path(production_season_path))
    )
    usage_by_player_season = _usage_by_player_season(
        _read_rows_if_exists(Path(usage_season_path))
    )

    evidence_rows: list[_SourceEvidence] = []
    source_warning_rows: list[dict[str, object]] = []
    skipped_projection_context = bool(projection_context_path)

    for clean_row in clean_rows:
        mapping = mapping_by_key.get(_clean_key(clean_row))
        if not mapping or not mapping.get("matched_model_player"):
            if mapping:
                source_warning_rows.append(_mapping_warning(mapping))
            continue
        warning = str(mapping.get("warning") or "")
        if warning in {"ambiguous_name_position", "unmatched_player"}:
            source_warning_rows.append(_mapping_warning(mapping))
            continue
        if warning:
            source_warning_rows.append(_mapping_warning(mapping))

        player = str(mapping["matched_model_player"])
        season = _int(clean_row.get("season"))
        production = production_by_player_season.get((normalize_player_name(player), season))
        usage = usage_by_player_season.get((normalize_player_name(player), season))
        evidence_rows.extend(
            _fantasypros_evidence_rows(
                clean_row,
                mapping,
                production=production,
                usage=usage,
            )
        )

    expected_rows, component_rows, unavailable_rows = _build_player_outputs(evidence_rows)
    summary = {
        "status": "ready",
        "review_status": "review_only",
        "layer_version": EXPECTED_VALUE_LAYER_VERSION,
        "clean_rows_path": str(clean_rows_path),
        "identity_mapping_path": str(identity_mapping_path),
        "production_season_path": str(production_season_path),
        "usage_season_path": str(usage_season_path),
        "projection_context_path": str(projection_context_path or ""),
        "projection_context_rows_used_for_core_value": 0,
        "projection_context_explicitly_ignored": skipped_projection_context,
        "players": len(expected_rows),
        "component_evidence_rows": len(component_rows),
        "unavailable_rows": len(unavailable_rows),
        "source_warning_rows": len(source_warning_rows),
        "season_weight_policy": json.dumps(SEASON_WEIGHTS, sort_keys=True),
        "deep_history_weight": DEEP_HISTORY_WEIGHT,
        "route_metrics_used": False,
        "market_value_used": False,
        "league_rank_used": False,
        "active_rankings_overwritten": False,
        "model_scores_changed": False,
    }
    return StatsFirstExpectedValueResult(
        expected_value_rows=tuple(expected_rows),
        component_evidence_rows=tuple(component_rows),
        unavailable_rows=tuple(unavailable_rows),
        source_warning_rows=tuple(source_warning_rows),
        summary=summary,
    )


def write_stats_first_expected_value_outputs(
    output_root: str | Path,
    result: StatsFirstExpectedValueResult,
) -> dict[str, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "expected": root / "stats_first_expected_value_rows.csv",
        "components": root / "stats_first_component_evidence_rows.csv",
        "unavailable": root / "stats_first_unavailable_sections.csv",
        "warnings": root / "stats_first_source_warnings.csv",
        "summary_csv": root / "stats_first_expected_value_summary.csv",
        "summary_json": root / "stats_first_expected_value_summary.json",
    }
    _write_csv(paths["expected"], EXPECTED_VALUE_HEADER, result.expected_value_rows)
    _write_csv(paths["components"], COMPONENT_EVIDENCE_HEADER, result.component_evidence_rows)
    _write_csv(paths["unavailable"], UNAVAILABLE_HEADER, result.unavailable_rows)
    _write_csv(paths["warnings"], SOURCE_WARNING_HEADER, result.source_warning_rows)
    _write_csv(
        paths["summary_csv"],
        SUMMARY_HEADER,
        [{"metric": key, "value": value} for key, value in result.summary.items()],
    )
    paths["summary_json"].write_text(
        json.dumps(result.summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return paths


def _fantasypros_evidence_rows(
    clean_row: dict[str, str],
    mapping: dict[str, str],
    *,
    production: dict[str, str] | None,
    usage: dict[str, str] | None,
) -> list[_SourceEvidence]:
    position = str(clean_row.get("position") or "")
    player = str(mapping.get("matched_model_player") or "")
    season = _int(clean_row.get("season"))
    base = {
        "player": player,
        "position": position,
        "sleeper_id": str(mapping.get("sleeper_id") or ""),
        "gsis_id": str(mapping.get("gsis_id") or ""),
        "season": season,
    }
    output: list[_SourceEvidence] = []

    production_value, production_fields, production_source = _production_value(
        clean_row,
        position,
        production,
    )
    _append_evidence(
        output,
        base,
        "production_trend",
        production_value,
        production_fields,
        production_source,
    )
    _append_evidence(
        output,
        base,
        "target_carry_volume",
        _target_carry_volume(clean_row, position, usage),
        _target_carry_fields(position, usage),
        _source_name("FantasyPros Advanced Stats Export", usage, "nflverse_play_by_play"),
    )
    _append_evidence(
        output,
        base,
        "target_share_team_share",
        _team_share(clean_row, position, usage),
        _team_share_fields(position, usage),
        _source_name("FantasyPros Advanced Stats Export", usage, "nflverse_play_by_play"),
    )
    _append_evidence(
        output,
        base,
        "air_yard_role",
        _air_yard_role(clean_row, position),
        _air_yard_fields(position),
        "FantasyPros Advanced Stats Export",
    )
    _append_evidence(
        output,
        base,
        "red_zone_involvement",
        _red_zone_involvement(clean_row, position, usage),
        _red_zone_fields(position, usage),
        _source_name("FantasyPros Advanced Stats Export", usage, "nflverse_play_by_play"),
    )
    _append_evidence(
        output,
        base,
        "explosive_play_profile",
        _explosive_profile(clean_row, position),
        _explosive_fields(position),
        "FantasyPros Advanced Stats Export",
    )
    _append_evidence(
        output,
        base,
        "yards_after_catch_contact",
        _yards_after_catch_contact(clean_row, position),
        _yac_fields(position),
        "FantasyPros Advanced Stats Export",
    )
    _append_evidence(
        output,
        base,
        "broken_tackle_context",
        _float(clean_row.get("broken_tackles")),
        ("broken_tackles",),
        "FantasyPros Advanced Stats Export",
    )
    _append_evidence(
        output,
        base,
        "drop_catchable_context",
        _drop_catchable_context(clean_row, position),
        _drop_catchable_fields(position),
        "FantasyPros Advanced Stats Export",
    )
    _append_evidence(
        output,
        base,
        "qb_pressure_air_yard_context",
        _qb_pressure_air_context(clean_row, position),
        _qb_context_fields(position),
        "FantasyPros Advanced Stats Export",
    )
    return output


def _append_evidence(
    output: list[_SourceEvidence],
    base: dict[str, object],
    component: str,
    raw_value: float | None,
    source_fields: tuple[str, ...],
    source_name: str,
) -> None:
    if raw_value is None:
        return
    if not source_fields:
        return
    output.append(
        _SourceEvidence(
            player=str(base["player"]),
            position=str(base["position"]),
            sleeper_id=str(base["sleeper_id"]),
            gsis_id=str(base["gsis_id"]),
            component=component,
            season=int(base["season"]),
            raw_value=round(raw_value, 6),
            source_fields=source_fields,
            source_name=source_name,
            source_status="stats_first_historical_evidence",
            source_warning="",
        )
    )


def _build_player_outputs(
    evidence_rows: list[_SourceEvidence],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    grouped: dict[tuple[str, str], list[_SourceEvidence]] = {}
    for row in evidence_rows:
        grouped.setdefault((row.player, row.position), []).append(row)

    weighted_by_player_component: dict[tuple[str, str, str], dict[str, object]] = {}
    for (player, position), rows in grouped.items():
        for component in COMPONENTS:
            component_rows = [row for row in rows if row.component == component]
            if not component_rows:
                continue
            weighted_raw = _recency_weighted_raw(component_rows)
            if weighted_raw is None:
                continue
            weighted_by_player_component[(player, position, component)] = {
                "weighted_raw": weighted_raw,
                "rows": component_rows,
            }

    normalized_scores = _normalized_component_scores(weighted_by_player_component)
    component_output_rows: list[dict[str, object]] = []
    for key, item in weighted_by_player_component.items():
        player, position, component = key
        score = normalized_scores[key]
        component_weight = COMPONENT_WEIGHTS.get(position, {}).get(component, 0.0)
        contribution = round(score * component_weight, 4)
        for source_row in item["rows"]:
            season_weight = _season_weight(source_row.season)
            component_output_rows.append(
                {
                    "matched_model_player": player,
                    "position": position,
                    "sleeper_id": source_row.sleeper_id,
                    "gsis_id": source_row.gsis_id,
                    "component": component,
                    "season": source_row.season,
                    "season_weight": season_weight,
                    "raw_value": source_row.raw_value,
                    "weighted_raw_value": round(source_row.raw_value * season_weight, 6),
                    "normalized_score": score,
                    "component_weight": component_weight,
                    "contribution": contribution,
                    "source_fields": "|".join(source_row.source_fields),
                    "source_name": source_row.source_name,
                    "source_status": source_row.source_status,
                    "source_warning": source_row.source_warning,
                }
            )

    expected_rows: list[dict[str, object]] = []
    unavailable_rows: list[dict[str, object]] = []
    for (player, position), rows in grouped.items():
        weights = COMPONENT_WEIGHTS.get(position, {})
        component_scores: dict[str, float] = {}
        component_contributions: dict[str, float] = {}
        missing_weight = 0.0
        for component, weight in weights.items():
            key = (player, position, component)
            if key not in normalized_scores:
                missing_weight += weight
                unavailable_rows.append(
                    _unavailable_row(
                        player,
                        position,
                        component,
                        "no_historical_evidence_for_component",
                        "review",
                    )
                )
                continue
            component_scores[component] = normalized_scores[key]
            component_contributions[component] = round(normalized_scores[key] * weight, 4)
        _add_route_unavailable_rows(unavailable_rows, player, position)
        seasons = sorted({row.season for row in rows})
        representative = rows[0]
        total_weight = sum(weights.values())
        expected_value = round(sum(component_contributions.values()), 4)
        evidence_coverage = round((total_weight - missing_weight) / total_weight, 4)
        expected_rows.append(
            {
                "matched_model_player": player,
                "position": position,
                "sleeper_id": representative.sleeper_id,
                "gsis_id": representative.gsis_id,
                "latest_season": max(seasons),
                "weighted_seasons": _weighted_season_label(seasons),
                "stats_first_expected_value": expected_value,
                "evidence_coverage": evidence_coverage,
                "component_scores": json.dumps(component_scores, sort_keys=True),
                "component_contributions": json.dumps(
                    component_contributions,
                    sort_keys=True,
                ),
                "component_weights": json.dumps(weights, sort_keys=True),
                "source_warning_count": 0,
                "unavailable_section_count": sum(
                    1
                    for row in unavailable_rows
                    if row["matched_model_player"] == player
                    and row["position"] == position
                ),
                "external_projection_context_status": "comparison_only_not_core_value",
                "review_status": "review_only",
                "layer_version": EXPECTED_VALUE_LAYER_VERSION,
            }
        )

    return (
        sorted(
            expected_rows,
            key=lambda row: (
                str(row["position"]),
                -float(row["stats_first_expected_value"]),
                str(row["matched_model_player"]),
            ),
        ),
        sorted(
            component_output_rows,
            key=lambda row: (
                str(row["matched_model_player"]),
                str(row["component"]),
                int(row["season"]),
            ),
        ),
        sorted(
            unavailable_rows,
            key=lambda row: (
                str(row["matched_model_player"]),
                str(row["component_or_section"]),
            ),
        ),
    )


def _normalized_component_scores(
    weighted_by_player_component: dict[tuple[str, str, str], dict[str, object]],
) -> dict[tuple[str, str, str], float]:
    by_position_component: dict[tuple[str, str], list[tuple[tuple[str, str, str], float]]] = {}
    for key, item in weighted_by_player_component.items():
        _, position, component = key
        by_position_component.setdefault((position, component), []).append(
            (key, float(item["weighted_raw"]))
        )

    output: dict[tuple[str, str, str], float] = {}
    for values in by_position_component.values():
        raw_values = [value for _, value in values]
        minimum = min(raw_values)
        maximum = max(raw_values)
        for key, value in values:
            if maximum == minimum:
                output[key] = 50.0
            else:
                output[key] = round(((value - minimum) / (maximum - minimum)) * 100, 4)
    return output


def _recency_weighted_raw(rows: list[_SourceEvidence]) -> float | None:
    recent_by_season: dict[int, list[float]] = {}
    older_values: list[float] = []
    for row in rows:
        if row.season in SEASON_WEIGHTS:
            recent_by_season.setdefault(row.season, []).append(row.raw_value)
        else:
            older_values.append(row.raw_value)

    weighted_sum = 0.0
    for season, season_weight in SEASON_WEIGHTS.items():
        values = recent_by_season.get(season, [])
        if values:
            weighted_sum += (sum(values) / len(values)) * season_weight
    if older_values:
        weighted_sum += (sum(older_values) / len(older_values)) * DEEP_HISTORY_WEIGHT
    if weighted_sum == 0:
        return None
    return round(weighted_sum / MAX_RECENCY_WEIGHT, 6)


def _production_value(
    clean_row: dict[str, str],
    position: str,
    production: dict[str, str] | None,
) -> tuple[float | None, tuple[str, ...], str]:
    if production:
        return (
            _lve_points(production),
            (
                "nflverse_passing_yards",
                "nflverse_rushing_yards",
                "nflverse_receiving_yards",
                "nflverse_first_downs",
                "nflverse_touchdowns",
            ),
            "nflverse_player_stats",
        )
    if position == "QB":
        return (
            _float(clean_row.get("passing_yards")) * LVE_SCORING["passing_yard"],
            ("passing_yards",),
            "FantasyPros Advanced Stats Export",
        )
    if position == "RB":
        return (
            _float(clean_row.get("rushing_yards")) * LVE_SCORING["rushing_yard"],
            ("rushing_yards",),
            "FantasyPros Advanced Stats Export",
        )
    if position in {"WR", "TE"}:
        return (
            _float(clean_row.get("receiving_yards")) * LVE_SCORING["receiving_yard"],
            ("receiving_yards",),
            "FantasyPros Advanced Stats Export",
        )
    return None, (), ""


def _target_carry_volume(
    clean_row: dict[str, str],
    position: str,
    usage: dict[str, str] | None,
) -> float | None:
    if usage:
        return (
            _float(usage.get("weighted_opportunities"))
            or _float(usage.get("targets")) + _float(usage.get("rushing_attempts"))
        )
    if position == "QB":
        return _float(clean_row.get("pass_attempts"))
    if position == "RB":
        return _float(clean_row.get("rushing_attempts")) + _float(clean_row.get("targets"))
    if position in {"WR", "TE"}:
        return _float(clean_row.get("targets"))
    return None


def _team_share(
    clean_row: dict[str, str],
    position: str,
    usage: dict[str, str] | None,
) -> float | None:
    if usage:
        if position == "RB":
            return max(
                _float(usage.get("rb_carry_share")),
                _float(usage.get("rb_target_share")),
            )
        return _float(usage.get("target_share"))
    if position in {"WR", "TE"}:
        return _float(clean_row.get("team_target_share_pct"))
    return None


def _air_yard_role(clean_row: dict[str, str], position: str) -> float | None:
    if position == "QB":
        return _float(clean_row.get("passing_air_yards"))
    if position in {"WR", "TE"}:
        return _float(clean_row.get("receiving_air_yards"))
    return None


def _red_zone_involvement(
    clean_row: dict[str, str],
    position: str,
    usage: dict[str, str] | None,
) -> float | None:
    if usage:
        return (
            _float(usage.get("red_zone_carries"))
            + _float(usage.get("red_zone_targets"))
            + (_float(usage.get("goal_line_carries")) * 1.5)
            + (_float(usage.get("goal_line_targets")) * 1.5)
        )
    if position == "QB":
        return _float(clean_row.get("red_zone_pass_attempts"))
    if position in {"RB", "WR", "TE"}:
        return _float(clean_row.get("red_zone_targets"))
    return None


def _explosive_profile(clean_row: dict[str, str], position: str) -> float | None:
    prefix = "passing" if position == "QB" else "rushing" if position == "RB" else "receiving"
    return (
        _float(clean_row.get(f"{prefix}_10_plus"))
        + _float(clean_row.get(f"{prefix}_20_plus")) * 2
        + _float(clean_row.get(f"{prefix}_30_plus")) * 3
        + _float(clean_row.get(f"{prefix}_40_plus")) * 4
        + _float(clean_row.get(f"{prefix}_50_plus")) * 5
    )


def _yards_after_catch_contact(
    clean_row: dict[str, str],
    position: str,
) -> float | None:
    if position == "RB":
        return _float(clean_row.get("rushing_yards_after_contact"))
    if position in {"WR", "TE"}:
        return _float(clean_row.get("receiving_yards_after_catch")) + _float(
            clean_row.get("receiving_yards_after_contact")
        )
    return None


def _drop_catchable_context(clean_row: dict[str, str], position: str) -> float | None:
    if position not in {"WR", "TE"}:
        return None
    catchable = _float(clean_row.get("catchable_targets"))
    drops = _float(clean_row.get("drops"))
    if catchable <= 0:
        return None
    return catchable - drops * 3


def _qb_pressure_air_context(clean_row: dict[str, str], position: str) -> float | None:
    if position != "QB":
        return None
    return (
        _float(clean_row.get("passing_air_yards"))
        + _float(clean_row.get("passer_rating")) * 25
        - _float(clean_row.get("sacks")) * 10
        - _float(clean_row.get("knockdowns")) * 4
        - _float(clean_row.get("hurries")) * 2
        - _float(clean_row.get("poor_throws")) * 3
    )


def _target_carry_fields(position: str, usage: dict[str, str] | None) -> tuple[str, ...]:
    if usage:
        return ("weighted_opportunities", "targets", "rushing_attempts")
    if position == "QB":
        return ("pass_attempts",)
    if position == "RB":
        return ("rushing_attempts", "targets")
    return ("targets",)


def _team_share_fields(position: str, usage: dict[str, str] | None) -> tuple[str, ...]:
    if usage:
        return ("target_share", "rb_carry_share", "rb_target_share")
    if position in {"WR", "TE"}:
        return ("team_target_share_pct",)
    return ()


def _air_yard_fields(position: str) -> tuple[str, ...]:
    if position == "QB":
        return ("passing_air_yards",)
    if position in {"WR", "TE"}:
        return ("receiving_air_yards",)
    return ()


def _red_zone_fields(position: str, usage: dict[str, str] | None) -> tuple[str, ...]:
    if usage:
        return (
            "red_zone_carries",
            "red_zone_targets",
            "goal_line_carries",
            "goal_line_targets",
        )
    if position == "QB":
        return ("red_zone_pass_attempts",)
    return ("red_zone_targets",)


def _explosive_fields(position: str) -> tuple[str, ...]:
    prefix = "passing" if position == "QB" else "rushing" if position == "RB" else "receiving"
    return (
        f"{prefix}_10_plus",
        f"{prefix}_20_plus",
        f"{prefix}_30_plus",
        f"{prefix}_40_plus",
        f"{prefix}_50_plus",
    )


def _yac_fields(position: str) -> tuple[str, ...]:
    if position == "RB":
        return ("rushing_yards_after_contact",)
    if position in {"WR", "TE"}:
        return ("receiving_yards_after_catch", "receiving_yards_after_contact")
    return ()


def _drop_catchable_fields(position: str) -> tuple[str, ...]:
    if position in {"WR", "TE"}:
        return ("catchable_targets", "drops")
    return ()


def _qb_context_fields(position: str) -> tuple[str, ...]:
    if position != "QB":
        return ()
    return (
        "passing_air_yards",
        "passer_rating",
        "sacks",
        "knockdowns",
        "hurries",
        "poor_throws",
    )


def _lve_points(row: dict[str, str]) -> float:
    return round(
        _float(row.get("passing_yards")) * LVE_SCORING["passing_yard"]
        + _float(row.get("passing_tds")) * LVE_SCORING["passing_td"]
        + _float(row.get("interceptions")) * LVE_SCORING["interception"]
        + _float(row.get("rushing_yards")) * LVE_SCORING["rushing_yard"]
        + _float(row.get("rushing_tds")) * LVE_SCORING["rushing_td"]
        + _float(row.get("receiving_yards")) * LVE_SCORING["receiving_yard"]
        + _float(row.get("receiving_tds")) * LVE_SCORING["receiving_td"]
        + (
            _float(row.get("rushing_first_downs"))
            + _float(row.get("receiving_first_downs"))
        )
        * LVE_SCORING["rushing_receiving_first_down"]
        + _float(row.get("fumbles_lost")) * LVE_SCORING["fumble_lost"],
        6,
    )


def _source_name(
    fallback: str,
    optional_source_row: dict[str, str] | None,
    source_name: str,
) -> str:
    return source_name if optional_source_row else fallback


def _unavailable_row(
    player: str,
    position: str,
    section: str,
    reason: str,
    severity: str,
) -> dict[str, object]:
    return {
        "matched_model_player": player,
        "position": position,
        "component_or_section": section,
        "reason": reason,
        "severity": severity,
    }


def _add_route_unavailable_rows(
    rows: list[dict[str, object]],
    player: str,
    position: str,
) -> None:
    if position not in {"RB", "WR", "TE"}:
        return
    rows.append(
        _unavailable_row(
            player,
            position,
            "route_metrics",
            "licensed_route_metrics_not_available;not_used_in_stats_first_value",
            "source_limitation",
        )
    )


def _mapping_warning(mapping: dict[str, str]) -> dict[str, object]:
    return {
        "matched_model_player": mapping.get("matched_model_player", ""),
        "position": mapping.get("position", ""),
        "season": mapping.get("season", ""),
        "source_name": "FantasyPros Advanced Stats Export",
        "warning": mapping.get("warning", ""),
        "detail": (
            f"{mapping.get('fantasypros_player_name', '')} "
            f"match_method={mapping.get('match_method', '')}"
        ),
    }


def _production_by_player_season(
    rows: list[dict[str, str]],
) -> dict[tuple[str, int], dict[str, str]]:
    return {
        (normalize_player_name(row.get("truth_set_player_name")), _int(row.get("season"))): row
        for row in rows
    }


def _usage_by_player_season(
    rows: list[dict[str, str]],
) -> dict[tuple[str, int], dict[str, str]]:
    return {
        (normalize_player_name(row.get("truth_set_player_name")), _int(row.get("season"))): row
        for row in rows
    }


def _season_weight(season: int) -> float:
    return SEASON_WEIGHTS.get(season, DEEP_HISTORY_WEIGHT)


def _weighted_season_label(seasons: list[int]) -> str:
    labels = [
        f"{season}:{SEASON_WEIGHTS[season]}"
        for season in sorted(seasons)
        if season in SEASON_WEIGHTS
    ]
    older = [season for season in seasons if season not in SEASON_WEIGHTS]
    if older:
        labels.insert(
            0,
            (
                f"deep_history_through_2022:{DEEP_HISTORY_WEIGHT}"
                f"({min(older)}-{max(older)})"
            ),
        )
    return "|".join(labels)


def _mapping_key(row: dict[str, str]) -> tuple[str, str, str, str, str, str]:
    return (
        str(row.get("fantasypros_player_name") or ""),
        str(row.get("season") or ""),
        str(row.get("position") or ""),
        _team_key(row.get("fantasypros_team")),
        str(row.get("source_file") or ""),
        str(row.get("source_hash") or ""),
    )


def _clean_key(row: dict[str, str]) -> tuple[str, str, str, str, str, str]:
    return (
        str(row.get("player_name") or ""),
        str(row.get("season") or ""),
        str(row.get("position") or ""),
        _team_key(row.get("nfl_team")),
        str(row.get("source_file") or ""),
        str(row.get("source_hash") or ""),
    )


def _team_key(value: object) -> str:
    team = str(value or "").strip().upper()
    return TEAM_ALIASES.get(team, team)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _read_rows_if_exists(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return _read_rows(path)


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def _float(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0
