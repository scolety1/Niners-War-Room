from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING

FIRST_DOWN_RATE_HEADER = (
    "rate_scope",
    "player_name",
    "position",
    "rushing_attempts",
    "rushing_first_downs",
    "rushing_first_downs_per_rush",
    "targets",
    "receiving_first_downs",
    "receptions",
    "receiving_first_downs_per_target",
    "receiving_first_downs_per_reception",
    "rate_source_status",
    "source",
)

FIRST_DOWN_ESTIMATE_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "projected_rushing_attempts",
    "projected_targets",
    "projected_receptions",
    "projected_rushing_first_downs_raw",
    "projected_receiving_first_downs_raw",
    "rushing_first_down_rate",
    "rushing_first_down_rate_scope",
    "receiving_first_down_rate_basis",
    "receiving_first_down_rate",
    "receiving_first_down_rate_scope",
    "preview_rushing_first_downs",
    "preview_receiving_first_downs",
    "preview_first_down_points",
    "first_down_estimate_status",
    "rate_source_status",
    "model_usage_status",
    "warning_flags",
    "source_url",
    "notes",
)

FIRST_DOWN_ESTIMATE_SUMMARY_HEADER = (
    "metric",
    "value",
)

POSITIONS = ("QB", "RB", "WR", "TE")


@dataclass(frozen=True)
class FirstDownEstimatorResult:
    rate_rows: tuple[dict[str, object], ...]
    estimate_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_first_down_estimator_preview(
    projection_path: str | Path,
    historical_stats_path: str | Path,
) -> FirstDownEstimatorResult:
    historical_rows = _read_rows(Path(historical_stats_path))
    projection_rows = _read_rows(Path(projection_path))
    rate_rows = build_position_first_down_rate_rows(
        historical_rows,
        source=str(historical_stats_path),
    )
    player_rate_rows = build_player_first_down_rate_rows(
        historical_rows,
        source=str(historical_stats_path),
    )
    rate_rows = (*player_rate_rows, *rate_rows)
    rates_by_position = {
        str(row["position"]): row
        for row in rate_rows
        if row["rate_scope"] == "position_recent"
        and row["rate_source_status"] == "historical_nflverse_player_stats"
    }
    rates_by_player = {
        (_name_key(str(row["player_name"])), str(row["position"])): row
        for row in rate_rows
        if row["rate_scope"] == "player_recent"
        and row["rate_source_status"] == "historical_nflverse_player_stats"
    }
    estimate_rows = tuple(
        _estimate_projection_row(
            row,
            rates_by_player.get(
                (_name_key(str(row.get("player_name") or "")), str(row.get("position") or "")),
            ),
            rates_by_position.get(str(row.get("position") or "")),
        )
        for row in projection_rows
    )
    summary = {
        "projection_rows": len(estimate_rows),
        "historical_rows": len(historical_rows),
        "rate_positions": sum(
            row["rate_scope"] == "position_recent"
            and row["rate_source_status"] == "historical_nflverse_player_stats"
            for row in rate_rows
        ),
        "rate_players": sum(
            row["rate_scope"] == "player_recent"
            and row["rate_source_status"] == "historical_nflverse_player_stats"
            for row in rate_rows
        ),
        "direct_first_down_projection_rows": sum(
            row["first_down_estimate_status"] == "direct_first_down_projection"
            for row in estimate_rows
        ),
        "estimated_from_history_rows": sum(
            row["first_down_estimate_status"] == "estimated_from_history" for row in estimate_rows
        ),
        "missing_first_down_projection_rows": sum(
            row["first_down_estimate_status"] == "missing_first_down_projection"
            for row in estimate_rows
        ),
        "preview_first_down_points_total": round(
            sum(_float(row["preview_first_down_points"]) for row in estimate_rows),
            2,
        ),
        "model_usage_status": "preview_only_not_active_scoring",
    }
    return FirstDownEstimatorResult(
        rate_rows=tuple(rate_rows),
        estimate_rows=estimate_rows,
        summary=summary,
    )


def build_position_first_down_rate_rows(
    historical_rows: list[dict[str, str]],
    *,
    source: str,
    minimum_rushing_attempts: float = 25.0,
    minimum_targets: float = 25.0,
    minimum_receptions: float = 10.0,
) -> tuple[dict[str, object], ...]:
    totals: dict[str, defaultdict[str, float]] = {
        position: defaultdict(float) for position in POSITIONS
    }
    for row in historical_rows:
        position = str(row.get("position") or "").upper()
        if position not in totals:
            continue
        totals[position]["rushing_attempts"] += _float(row.get("rushing_attempts"))
        totals[position]["rushing_first_downs"] += _float(row.get("rushing_first_downs"))
        totals[position]["targets"] += _float(row.get("targets"))
        totals[position]["receptions"] += _float(row.get("receptions"))
        totals[position]["receiving_first_downs"] += _float(row.get("receiving_first_downs"))

    rows: list[dict[str, object]] = []
    for position in POSITIONS:
        position_totals = totals[position]
        rush_attempts = position_totals["rushing_attempts"]
        targets = position_totals["targets"]
        receptions = position_totals["receptions"]
        has_rush_rate = rush_attempts >= minimum_rushing_attempts
        has_target_rate = targets >= minimum_targets
        has_reception_rate = receptions >= minimum_receptions
        has_any_rate = has_rush_rate or has_target_rate or has_reception_rate
        rows.append(
            {
                "position": position,
                "rate_scope": "position_recent",
                "player_name": "",
                "rushing_attempts": round(rush_attempts, 2),
                "rushing_first_downs": round(position_totals["rushing_first_downs"], 2),
                "rushing_first_downs_per_rush": _rate(
                    position_totals["rushing_first_downs"],
                    rush_attempts,
                    has_rush_rate,
                ),
                "targets": round(targets, 2),
                "receiving_first_downs": round(
                    position_totals["receiving_first_downs"],
                    2,
                ),
                "receptions": round(receptions, 2),
                "receiving_first_downs_per_target": _rate(
                    position_totals["receiving_first_downs"],
                    targets,
                    has_target_rate,
                ),
                "receiving_first_downs_per_reception": _rate(
                    position_totals["receiving_first_downs"],
                    receptions,
                    has_reception_rate,
                ),
                "rate_source_status": "historical_nflverse_player_stats"
                if has_any_rate
                else "insufficient_history",
                "source": source,
            }
        )
    return tuple(rows)


def build_player_first_down_rate_rows(
    historical_rows: list[dict[str, str]],
    *,
    source: str,
    minimum_rushing_attempts: float = 10.0,
    minimum_targets: float = 10.0,
    minimum_receptions: float = 5.0,
) -> tuple[dict[str, object], ...]:
    totals: dict[tuple[str, str], defaultdict[str, float]] = {}
    display_names: dict[tuple[str, str], str] = {}
    for row in historical_rows:
        position = str(row.get("position") or "").upper()
        player_name = str(
            row.get("truth_set_player_name")
            or row.get("player_name")
            or row.get("matched_player_name")
            or ""
        ).strip()
        if position not in POSITIONS or not player_name:
            continue
        key = (_name_key(player_name), position)
        bucket = totals.setdefault(key, defaultdict(float))
        display_names[key] = player_name
        bucket["rushing_attempts"] += _float(row.get("rushing_attempts"))
        bucket["rushing_first_downs"] += _float(row.get("rushing_first_downs"))
        bucket["targets"] += _float(row.get("targets"))
        bucket["receptions"] += _float(row.get("receptions"))
        bucket["receiving_first_downs"] += _float(row.get("receiving_first_downs"))

    rows: list[dict[str, object]] = []
    for (player_key, position), player_totals in sorted(totals.items()):
        rush_attempts = player_totals["rushing_attempts"]
        targets = player_totals["targets"]
        receptions = player_totals["receptions"]
        has_rush_rate = rush_attempts >= minimum_rushing_attempts
        has_target_rate = targets >= minimum_targets
        has_reception_rate = receptions >= minimum_receptions
        has_any_rate = has_rush_rate or has_target_rate or has_reception_rate
        name = display_names[(player_key, position)]
        rows.append(
            {
                "rate_scope": "player_recent",
                "player_name": name,
                "position": position,
                "rushing_attempts": round(rush_attempts, 2),
                "rushing_first_downs": round(player_totals["rushing_first_downs"], 2),
                "rushing_first_downs_per_rush": _rate(
                    player_totals["rushing_first_downs"],
                    rush_attempts,
                    has_rush_rate,
                ),
                "targets": round(targets, 2),
                "receiving_first_downs": round(
                    player_totals["receiving_first_downs"],
                    2,
                ),
                "receptions": round(receptions, 2),
                "receiving_first_downs_per_target": _rate(
                    player_totals["receiving_first_downs"],
                    targets,
                    has_target_rate,
                ),
                "receiving_first_downs_per_reception": _rate(
                    player_totals["receiving_first_downs"],
                    receptions,
                    has_reception_rate,
                ),
                "rate_source_status": "historical_nflverse_player_stats"
                if has_any_rate
                else "insufficient_history",
                "source": source,
            }
        )
    return tuple(rows)


def write_first_down_estimator_outputs(
    *,
    estimate_path: str | Path,
    rate_path: str | Path,
    summary_path: str | Path,
    result: FirstDownEstimatorResult,
) -> None:
    _write_dicts(estimate_path, FIRST_DOWN_ESTIMATE_HEADER, result.estimate_rows)
    _write_dicts(rate_path, FIRST_DOWN_RATE_HEADER, result.rate_rows)
    summary_rows = tuple({"metric": key, "value": value} for key, value in result.summary.items())
    _write_dicts(summary_path, FIRST_DOWN_ESTIMATE_SUMMARY_HEADER, summary_rows)


def _estimate_projection_row(
    row: dict[str, str],
    player_rate_row: dict[str, object] | None,
    position_rate_row: dict[str, object] | None,
) -> dict[str, object]:
    position = str(row.get("position") or "")
    direct_rushing = _optional_float(row.get("projected_rushing_first_downs"))
    direct_receiving = _optional_float(row.get("projected_receiving_first_downs"))
    has_direct = direct_rushing is not None or direct_receiving is not None
    projected_rushes = _float(row.get("projected_rushing_attempts"))
    projected_targets = _float(row.get("projected_targets"))
    projected_receptions = _float(row.get("projected_receptions"))
    warnings: list[str] = []

    if has_direct:
        status = "direct_first_down_projection"
        rush_first_downs = 0.0 if direct_rushing is None else direct_rushing
        receiving_first_downs = 0.0 if direct_receiving is None else direct_receiving
        rush_rate = ""
        rush_scope = "direct"
        receiving_rate = ""
        receiving_scope = "direct"
        receiving_basis = "direct"
        rate_status = "direct_source_projection"
    elif _has_estimable_projection(row) and (player_rate_row or position_rate_row):
        status = "estimated_from_history"
        rush_rate, rush_scope = _best_rate(
            player_rate_row,
            position_rate_row,
            "rushing_first_downs_per_rush",
        )
        target_rate, target_scope = _best_rate(
            player_rate_row,
            position_rate_row,
            "receiving_first_downs_per_target",
        )
        reception_rate, reception_scope = _best_rate(
            player_rate_row,
            position_rate_row,
            "receiving_first_downs_per_reception",
        )
        rush_first_downs = projected_rushes * (rush_rate or 0.0)
        if projected_targets and target_rate is not None:
            receiving_first_downs = projected_targets * target_rate
            receiving_basis = "targets"
            receiving_rate = target_rate
            receiving_scope = target_scope
        elif projected_receptions and reception_rate is not None:
            receiving_first_downs = projected_receptions * reception_rate
            receiving_basis = "receptions"
            receiving_rate = reception_rate
            receiving_scope = reception_scope
        else:
            receiving_first_downs = 0.0
            receiving_basis = "none"
            receiving_rate = ""
            receiving_scope = "missing"
            if projected_targets or projected_receptions:
                warnings.append("missing_receiving_first_down_rate")
        if projected_rushes and rush_rate is None:
            warnings.append("missing_rushing_first_down_rate")
        rate_status = "historical_nflverse_player_stats"
    else:
        status = "missing_first_down_projection"
        rush_first_downs = 0.0
        receiving_first_downs = 0.0
        rush_rate = ""
        rush_scope = "missing"
        receiving_rate = ""
        receiving_scope = "missing"
        receiving_basis = "none"
        rate_status = (
            "missing_historical_rate" if _has_estimable_projection(row) else "no_projection"
        )
        warnings.append(rate_status)

    first_down_points = (rush_first_downs + receiving_first_downs) * LVE_SCORING[
        "rushing_receiving_first_down"
    ]
    return {
        "player_name": row.get("player_name", ""),
        "position": position,
        "nfl_team": row.get("nfl_team", ""),
        "projected_rushing_attempts": row.get("projected_rushing_attempts", ""),
        "projected_targets": row.get("projected_targets", ""),
        "projected_receptions": row.get("projected_receptions", ""),
        "projected_rushing_first_downs_raw": row.get("projected_rushing_first_downs", ""),
        "projected_receiving_first_downs_raw": row.get(
            "projected_receiving_first_downs",
            "",
        ),
        "rushing_first_down_rate": _format_optional_rate(rush_rate),
        "rushing_first_down_rate_scope": rush_scope,
        "receiving_first_down_rate_basis": receiving_basis,
        "receiving_first_down_rate": _format_optional_rate(receiving_rate),
        "receiving_first_down_rate_scope": receiving_scope,
        "preview_rushing_first_downs": round(rush_first_downs, 2),
        "preview_receiving_first_downs": round(receiving_first_downs, 2),
        "preview_first_down_points": round(first_down_points, 2),
        "first_down_estimate_status": status,
        "rate_source_status": rate_status,
        "model_usage_status": "preview_only_not_active_scoring",
        "warning_flags": "|".join(dict.fromkeys(warnings)),
        "source_url": row.get("source_url", ""),
        "notes": row.get("notes", ""),
    }


def _has_estimable_projection(row: dict[str, str]) -> bool:
    return any(
        _float(row.get(column)) != 0
        for column in (
            "projected_rushing_attempts",
            "projected_targets",
            "projected_receptions",
        )
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_dicts(
    path: str | Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _rate(numerator: float, denominator: float, has_enough_volume: bool) -> float | str:
    if not has_enough_volume or denominator <= 0:
        return ""
    return round(numerator / denominator, 4)


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def _float(value: object) -> float:
    parsed = _optional_float(value)
    return 0.0 if parsed is None else parsed


def _format_optional_rate(value: object) -> float | str:
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    return round(parsed, 4)


def _best_rate(
    player_rate_row: dict[str, object] | None,
    position_rate_row: dict[str, object] | None,
    field: str,
) -> tuple[float | None, str]:
    for scope, row in (
        ("player_recent", player_rate_row),
        ("position_recent", position_rate_row),
    ):
        if not row:
            continue
        rate = _optional_float(row.get(field))
        if rate is not None:
            return rate, scope
    return None, "missing"


def _name_key(value: str) -> str:
    lowered = value.lower().replace("&", "and")
    normalized = "".join(char if char.isalnum() else " " for char in lowered)
    return " ".join(normalized.split())
