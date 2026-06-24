from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

MODEL_INPUT_ALLOWED = "no"
APP_WIRING_ALLOWED = "no"

REQUIRED_PBP_COLUMNS = {
    "season",
    "week",
    "posteam",
    "yardline_100",
    "rusher_player_id",
    "rusher_player_name",
    "receiver_player_id",
    "receiver_player_name",
}

DERIVED_FIELD_TYPES = {
    "touches": "TRUE_DERIVED_FACT",
    "opportunities": "TRUE_DERIVED_FACT",
    "red_zone_carries": "TRUE_DERIVED_FACT",
    "red_zone_targets": "TRUE_DERIVED_FACT",
    "red_zone_touches": "TRUE_DERIVED_FACT",
    "inside_10_carries": "TRUE_DERIVED_FACT",
    "inside_10_targets": "TRUE_DERIVED_FACT",
    "inside_10_touches": "TRUE_DERIVED_FACT",
    "inside_5_carries": "TRUE_DERIVED_FACT",
    "inside_5_targets": "TRUE_DERIVED_FACT",
    "inside_5_touches": "TRUE_DERIVED_FACT",
    "first_downs_per_touch": "DERIVED_PROXY",
    "red_zone_share": "DERIVED_PROXY",
    "inside_10_share": "DERIVED_PROXY",
    "inside_5_share": "DERIVED_PROXY",
}


@dataclass(frozen=True)
class NflUsageDerivedResult:
    status: str
    rows: tuple[dict[str, Any], ...]
    validation_rows: tuple[dict[str, str], ...]
    proxy_report_rows: tuple[dict[str, str], ...]


def derive_usage_features(pbp_rows: list[dict[str, Any]]) -> NflUsageDerivedResult:
    if not pbp_rows:
        return NflUsageDerivedResult(
            status="YELLOW_NO_ROWS",
            rows=(),
            validation_rows=(_validation_row("pbp", "YELLOW", "no rows supplied"),),
            proxy_report_rows=tuple(proxy_vs_true_rows()),
        )

    missing = sorted(REQUIRED_PBP_COLUMNS - set().union(*(set(row) for row in pbp_rows)))
    if missing:
        return NflUsageDerivedResult(
            status="QUARANTINED_MISSING_REQUIRED_FIELDS",
            rows=(),
            validation_rows=(_validation_row("pbp", "RED", f"missing={';'.join(missing)}"),),
            proxy_report_rows=tuple(proxy_vs_true_rows()),
        )

    aggregates: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    team_totals: dict[tuple[str, str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in pbp_rows:
        season = str(row.get("season", ""))
        week = str(row.get("week", ""))
        team = str(row.get("posteam", ""))
        yardline = _number(row.get("yardline_100"))
        is_red_zone = yardline is not None and yardline <= 20
        is_inside_10 = yardline is not None and yardline <= 10
        is_inside_5 = yardline is not None and yardline <= 5

        if _truthy(row.get("rush_attempt")) or str(row.get("play_type", "")).lower() == "run":
            player_id = str(row.get("rusher_player_id") or "")
            player_name = str(row.get("rusher_player_name") or "")
            if player_id or player_name:
                agg = _aggregate(aggregates, season, week, team, player_id, player_name)
                _increment(agg, "carries", 1)
                if _truthy(row.get("first_down_rush")) or _truthy(row.get("rush_first_down")):
                    _increment(agg, "rushing_first_downs", 1)
                _zone_increment(
                    agg,
                    team_totals[(season, week, team)],
                    "carries",
                    is_red_zone,
                    is_inside_10,
                    is_inside_5,
                )

        if _truthy(row.get("pass_attempt")) or _truthy(row.get("qb_dropback")):
            player_id = str(row.get("receiver_player_id") or "")
            player_name = str(row.get("receiver_player_name") or "")
            if player_id or player_name:
                agg = _aggregate(aggregates, season, week, team, player_id, player_name)
                _increment(agg, "targets", 1)
                if _truthy(row.get("complete_pass")):
                    _increment(agg, "receptions", 1)
                if _truthy(row.get("first_down_pass")) or _truthy(row.get("pass_first_down")):
                    _increment(agg, "receiving_first_downs", 1)
                _zone_increment(
                    agg,
                    team_totals[(season, week, team)],
                    "targets",
                    is_red_zone,
                    is_inside_10,
                    is_inside_5,
                )

    output_rows = [_finalize(row, team_totals) for row in aggregates.values()]
    return NflUsageDerivedResult(
        status="AVAILABLE_REVIEW_ONLY",
        rows=tuple(
            sorted(
                output_rows,
                key=lambda r: (r["season"], r["week"], r["team"], r["player_name"]),
            )
        ),
        validation_rows=(_validation_row("pbp", "GREEN", "derived from supplied in-memory rows"),),
        proxy_report_rows=tuple(proxy_vs_true_rows()),
    )


def derived_field_inventory_rows() -> list[dict[str, str]]:
    return [
        {
            "field_name": field_name,
            "source_family": "pbp/player_stats",
            "field_type": field_type,
            "grain": "player_week",
            "formula_notes": _formula_notes(field_name),
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        }
        for field_name, field_type in sorted(DERIVED_FIELD_TYPES.items())
    ]


def proxy_vs_true_rows() -> list[dict[str, str]]:
    return [
        {
            "metric_family": "routes_run",
            "v0_status": "LICENSED_DATA_GAP",
            "approved_label": "licensed-data gap for true routes run",
            "blocked_label": "true routes run from public participation unless verified",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        },
        {
            "metric_family": "tprr",
            "v0_status": "LICENSED_DATA_GAP",
            "approved_label": "targets per route proxy only if denominator is proxy",
            "blocked_label": "true TPRR",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        },
        {
            "metric_family": "yprr",
            "v0_status": "LICENSED_DATA_GAP",
            "approved_label": "yards per route proxy only if denominator is proxy",
            "blocked_label": "true YPRR",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        },
    ]


def _aggregate(
    aggregates: dict[tuple[str, str, str, str], dict[str, Any]],
    season: str,
    week: str,
    team: str,
    player_id: str,
    player_name: str,
) -> dict[str, Any]:
    key = (season, week, team, player_id or player_name)
    if key not in aggregates:
        aggregates[key] = {
            "season": season,
            "week": week,
            "team": team,
            "player_id": player_id,
            "player_name": player_name,
            "carries": 0,
            "targets": 0,
            "receptions": 0,
            "rushing_first_downs": 0,
            "receiving_first_downs": 0,
            "red_zone_carries": 0,
            "red_zone_targets": 0,
            "inside_10_carries": 0,
            "inside_10_targets": 0,
            "inside_5_carries": 0,
            "inside_5_targets": 0,
        }
    return aggregates[key]


def _zone_increment(
    agg: dict[str, Any],
    team_total: dict[str, int],
    event: str,
    red_zone: bool,
    inside_10: bool,
    inside_5: bool,
) -> None:
    if red_zone:
        _increment(agg, f"red_zone_{event}", 1)
        team_total[f"red_zone_{event}"] += 1
    if inside_10:
        _increment(agg, f"inside_10_{event}", 1)
        team_total[f"inside_10_{event}"] += 1
    if inside_5:
        _increment(agg, f"inside_5_{event}", 1)
        team_total[f"inside_5_{event}"] += 1


def _finalize(
    row: dict[str, Any],
    team_totals: dict[tuple[str, str, str], dict[str, int]],
) -> dict[str, Any]:
    row = dict(row)
    row["touches"] = int(row["carries"]) + int(row["receptions"])
    row["opportunities"] = int(row["carries"]) + int(row["targets"])
    row["red_zone_touches"] = int(row["red_zone_carries"]) + _red_zone_receptions_proxy(row)
    row["inside_10_touches"] = int(row["inside_10_carries"]) + _inside_receptions_proxy(
        row,
        "inside_10",
    )
    row["inside_5_touches"] = int(row["inside_5_carries"]) + _inside_receptions_proxy(
        row,
        "inside_5",
    )
    first_downs = int(row["rushing_first_downs"]) + int(row["receiving_first_downs"])
    row["first_downs_per_touch"] = _rate(first_downs, int(row["touches"]))
    totals = team_totals[(str(row["season"]), str(row["week"]), str(row["team"]))]
    row["red_zone_share"] = _rate(
        int(row["red_zone_carries"]) + int(row["red_zone_targets"]),
        int(totals.get("red_zone_carries", 0)) + int(totals.get("red_zone_targets", 0)),
    )
    row["inside_10_share"] = _rate(
        int(row["inside_10_carries"]) + int(row["inside_10_targets"]),
        int(totals.get("inside_10_carries", 0)) + int(totals.get("inside_10_targets", 0)),
    )
    row["inside_5_share"] = _rate(
        int(row["inside_5_carries"]) + int(row["inside_5_targets"]),
        int(totals.get("inside_5_carries", 0)) + int(totals.get("inside_5_targets", 0)),
    )
    row["model_input_allowed"] = MODEL_INPUT_ALLOWED
    row["app_wiring_allowed"] = APP_WIRING_ALLOWED
    row["field_status"] = "AVAILABLE_REVIEW_ONLY"
    return row


def _red_zone_receptions_proxy(row: dict[str, Any]) -> int:
    return min(int(row["red_zone_targets"]), int(row["receptions"]))


def _inside_receptions_proxy(row: dict[str, Any], prefix: str) -> int:
    return min(int(row[f"{prefix}_targets"]), int(row["receptions"]))


def _increment(row: dict[str, Any], key: str, value: int) -> None:
    row[key] = int(row.get(key, 0)) + value


def _rate(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return ""
    return f"{numerator / denominator:.4f}".rstrip("0").rstrip(".")


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _validation_row(source_family: str, status: str, notes: str) -> dict[str, str]:
    return {
        "source_family": source_family,
        "validation_status": status,
        "notes": notes,
        "model_input_allowed": MODEL_INPUT_ALLOWED,
        "app_wiring_allowed": APP_WIRING_ALLOWED,
    }


def _formula_notes(field_name: str) -> str:
    notes = {
        "touches": "carries + receptions",
        "opportunities": "carries + targets",
        "first_downs_per_touch": "(rushing_first_downs + receiving_first_downs) / touches",
        "red_zone_share": (
            "player red-zone carries+targets divided by team/week red-zone "
            "carries+targets"
        ),
        "inside_10_share": (
            "player inside-10 carries+targets divided by team/week inside-10 "
            "carries+targets"
        ),
        "inside_5_share": (
            "player inside-5 carries+targets divided by team/week inside-5 "
            "carries+targets"
        ),
    }
    return notes.get(field_name, "derived from pbp yardline_100 threshold and event owner")
