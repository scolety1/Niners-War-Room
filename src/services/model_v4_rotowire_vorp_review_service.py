from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.model_v4_fantasypros_identity_mapping_service import normalize_player_name
from src.services.model_v4_first_down_estimation_service import (
    DEFAULT_DIRECT_FIRST_DOWNS,
    build_first_down_rate_profile,
    estimate_first_downs,
)

DEFAULT_COMPONENTS = Path(
    "local_exports/model_v4/rotowire_stats_first/latest/rotowire_stats_first_component_rows.csv"
)
DEFAULT_BASELINES = Path(
    "local_exports/model_v4/rotowire_replacement/latest/rotowire_replacement_baselines.csv"
)
DEFAULT_PLAYER_STATS = Path(
    "local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/rotowire_vorp_review/latest")

VORP_REVIEW_VERSION = "model_v4_rotowire_vorp_review_0.1.0"

VORP_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "weighted_lve_base_points",
    "current_lve_base_points",
    "estimated_rushing_first_downs",
    "estimated_receiving_first_downs",
    "estimated_first_down_points",
    "first_down_adjusted_points",
    "first_down_source_status",
    "replacement_rank",
    "replacement_player",
    "replacement_lve_base_points",
    "replacement_first_down_adjusted_points",
    "pre_first_down_vorp_points",
    "production_vorp_points",
    "vorp_status",
    "warning",
    "allowed_use",
    "vorp_review_version",
)

SUMMARY_HEADER = ("metric", "value")


@dataclass(frozen=True)
class RotoWireVorpReviewResult:
    vorp_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_rotowire_vorp_review(
    *,
    components_path: str | Path = DEFAULT_COMPONENTS,
    baselines_path: str | Path = DEFAULT_BASELINES,
    player_stats_path: str | Path = DEFAULT_PLAYER_STATS,
    direct_first_downs_path: str | Path = DEFAULT_DIRECT_FIRST_DOWNS,
    season: int = 2025,
) -> RotoWireVorpReviewResult:
    baselines = _baselines_by_position(Path(baselines_path))
    first_down_profile = build_first_down_rate_profile(direct_first_downs_path)
    current_metrics = _best_player_metrics_by_name(Path(player_stats_path), season)
    component_rows = [
        row
        for row in _read_rows(Path(components_path))
        if row.get("component") == "lve_base_production"
    ]
    vorp_rows = [
        _vorp_row(
            row,
            baselines.get(row.get("position", ""), {}),
            current_metrics.get(normalize_player_name(row.get("player_name", ""))),
            first_down_profile,
        )
        for row in component_rows
    ]
    summary = {
        "vorp_review_version": VORP_REVIEW_VERSION,
        "row_count": len(vorp_rows),
        "positive_vorp_count": sum(
            1 for row in vorp_rows if _float(row["production_vorp_points"]) > 0
        ),
        "review_status": "review_only",
        "baseline_warning": "first_downs_estimated_from_history_not_direct",
        "first_down_source_status": "estimated_from_history",
        "direct_first_down_source_rows": first_down_profile.source_row_count,
        "direct_first_down_source_seasons": "|".join(
            str(season_value) for season_value in first_down_profile.source_seasons
        ),
        "projection_rows_used": 0,
        "market_rows_used": 0,
        "league_rank_used": False,
    }
    return RotoWireVorpReviewResult(vorp_rows=tuple(vorp_rows), summary=summary)


def write_rotowire_vorp_review_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: RotoWireVorpReviewResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rotowire_vorp_review()
    vorp_path = output / "rotowire_vorp_review_rows.csv"
    summary_path = output / "rotowire_vorp_review_summary.csv"
    _write_csv(vorp_path, VORP_HEADER, result.vorp_rows)
    _write_csv(
        summary_path,
        SUMMARY_HEADER,
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    return {"vorp": vorp_path, "summary": summary_path}


def _vorp_row(
    row: dict[str, str],
    baseline: dict[str, str],
    metrics: dict[str, object] | None,
    first_down_profile: object,
) -> dict[str, object]:
    weighted_raw = _float(row.get("raw_weighted_value"))
    has_raw = row.get("source_status") != "missing" and row.get("raw_weighted_value") != ""
    has_current_metrics = bool(metrics)
    current_lve = _lve_base(metrics or {}) if has_current_metrics else weighted_raw
    first_down_estimate = estimate_first_downs(
        player_name=row.get("player_name", ""),
        position=row.get("position", ""),
        metrics=metrics or {},
        profile=first_down_profile,
    )
    replacement_base = _float(baseline.get("replacement_lve_base_points"))
    replacement_adjusted = _float(baseline.get("replacement_first_down_adjusted_points"))
    if not replacement_adjusted:
        replacement_adjusted = replacement_base
    adjusted_points = current_lve + first_down_estimate.first_down_points
    pre_first_down_vorp = current_lve - replacement_base if has_raw and baseline else 0.0
    vorp = adjusted_points - replacement_adjusted if has_raw and baseline else 0.0
    warning = first_down_estimate.warning
    if not has_current_metrics and has_raw:
        warning = "first_downs_not_estimated_current_player_stats_missing"
    if not has_raw:
        warning = "missing_lve_base_production"
    elif not baseline:
        warning = "missing_position_replacement_baseline"
    return {
        "player_name": row.get("player_name", ""),
        "position": row.get("position", ""),
        "nfl_team": row.get("nfl_team", ""),
        "weighted_lve_base_points": round(weighted_raw, 4) if has_raw else "",
        "current_lve_base_points": round(current_lve, 4) if has_raw else "",
        "estimated_rushing_first_downs": (
            first_down_estimate.rushing_first_downs if has_current_metrics else ""
        ),
        "estimated_receiving_first_downs": (
            first_down_estimate.receiving_first_downs if has_current_metrics else ""
        ),
        "estimated_first_down_points": (
            first_down_estimate.first_down_points if has_current_metrics else ""
        ),
        "first_down_adjusted_points": round(adjusted_points, 4)
        if has_raw and has_current_metrics
        else "",
        "first_down_source_status": first_down_estimate.source_status
        if has_current_metrics
        else "",
        "replacement_rank": baseline.get("replacement_rank", ""),
        "replacement_player": baseline.get("replacement_player", ""),
        "replacement_lve_base_points": baseline.get("replacement_lve_base_points", ""),
        "replacement_first_down_adjusted_points": baseline.get(
            "replacement_first_down_adjusted_points",
            "",
        ),
        "pre_first_down_vorp_points": round(pre_first_down_vorp, 4)
        if has_raw and baseline
        else "",
        "production_vorp_points": round(vorp, 4) if has_raw and baseline else "",
        "vorp_status": "available" if has_raw and baseline else "review",
        "warning": warning,
        "allowed_use": "review_only_first_downs_estimated_from_history",
        "vorp_review_version": VORP_REVIEW_VERSION,
    }


def _baselines_by_position(path: Path) -> dict[str, dict[str, str]]:
    return {row["position"]: row for row in _read_rows(path)}


def _best_player_metrics_by_name(path: Path, season: int) -> dict[str, dict[str, object]]:
    output: dict[str, dict[str, object]] = {}
    best_lve: dict[str, float] = {}
    for row in _read_rows(path):
        if row.get("source_detail") != "fantasy":
            continue
        if _int(row.get("season")) != season:
            continue
        metrics = json.loads(row.get("metrics_json") or "{}")
        lve = _lve_base(metrics)
        key = normalize_player_name(row.get("player_name", ""))
        if key and lve > best_lve.get(key, -1.0):
            output[key] = metrics
            best_lve[key] = lve
    return output


def _lve_base(metrics: dict[str, object]) -> float:
    return (
        _float(metrics.get("passing_yds")) * LVE_SCORING["passing_yard"]
        + _float(metrics.get("passing_td")) * LVE_SCORING["passing_td"]
        + _float(metrics.get("passing_int")) * LVE_SCORING["interception"]
        + _float(metrics.get("rushing_yds")) * LVE_SCORING["rushing_yard"]
        + _float(metrics.get("rushing_td")) * LVE_SCORING["rushing_td"]
        + _float(metrics.get("receiving_yds")) * LVE_SCORING["receiving_yard"]
        + _float(metrics.get("receiving_td")) * LVE_SCORING["receiving_td"]
        + _float(metrics.get("fumbles_lost")) * LVE_SCORING["fumble_lost"]
    )


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


def _float(value: object) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(str(value))
    except ValueError:
        return 0.0


def _int(value: object) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(str(value))
    except ValueError:
        return None
