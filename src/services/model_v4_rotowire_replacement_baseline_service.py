from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.model_v4_fantasypros_identity_mapping_service import normalize_player_name
from src.services.model_v4_first_down_estimation_service import (
    DEFAULT_DIRECT_FIRST_DOWNS,
    FirstDownEstimate,
    build_first_down_rate_profile,
    estimate_first_downs,
)

DEFAULT_PLAYER_STATS = Path(
    "local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/rotowire_replacement/latest")

REPLACEMENT_VERSION = "model_v4_rotowire_replacement_baseline_0.1.0"
SKILL_POSITIONS = ("QB", "RB", "WR", "TE")
FLEX_POSITIONS = ("RB", "WR", "TE")

LINEUP_STARTERS = {
    "QB": 10,
    "RB": 20,
    "WR": 30,
    "TE": 10,
}
FLEX_STARTERS = 20

BASELINE_HEADER = (
    "position",
    "required_starters",
    "flex_selected",
    "total_selected",
    "replacement_rank",
    "replacement_player",
    "replacement_team",
    "replacement_lve_base_points",
    "replacement_estimated_rushing_first_downs",
    "replacement_estimated_receiving_first_downs",
    "replacement_estimated_first_down_points",
    "replacement_first_down_adjusted_points",
    "replacement_first_down_source_status",
    "replacement_first_down_warning",
    "season",
    "baseline_version",
)

PLAYER_POOL_HEADER = (
    "player_name",
    "normalized_player_name",
    "position",
    "nfl_team",
    "season",
    "lve_base_points",
    "estimated_rushing_first_downs",
    "estimated_receiving_first_downs",
    "estimated_first_down_points",
    "first_down_adjusted_points",
    "first_down_source_status",
    "first_down_warning",
    "selected_as_required_starter",
    "selected_as_flex",
    "overall_skill_pool_rank",
    "position_rank",
    "baseline_version",
)

SUMMARY_HEADER = ("metric", "value")


@dataclass(frozen=True)
class ReplacementBaselineResult:
    baseline_rows: tuple[dict[str, object], ...]
    player_pool_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class _PlayerSeason:
    player_name: str
    normalized_player_name: str
    position: str
    nfl_team: str
    season: int
    lve_base_points: float
    first_down_estimate: FirstDownEstimate

    @property
    def first_down_adjusted_points(self) -> float:
        return self.lve_base_points + self.first_down_estimate.first_down_points


def build_rotowire_replacement_baselines(
    *,
    player_stats_path: str | Path = DEFAULT_PLAYER_STATS,
    direct_first_downs_path: str | Path = DEFAULT_DIRECT_FIRST_DOWNS,
    season: int = 2025,
) -> ReplacementBaselineResult:
    first_down_profile = build_first_down_rate_profile(direct_first_downs_path)
    player_pool = _player_pool(Path(player_stats_path), season, first_down_profile)
    selected_required = _required_starters(player_pool)
    selected_flex = _flex_starters(player_pool, selected_required)
    selected_keys = selected_required | selected_flex

    pool_rows = _player_pool_rows(player_pool, selected_required, selected_flex)
    baseline_rows = _baseline_rows(player_pool, selected_keys, selected_flex, season)
    summary = {
        "baseline_version": REPLACEMENT_VERSION,
        "season": season,
        "player_pool_count": len(player_pool),
        "selected_required_count": len(selected_required),
        "selected_flex_count": len(selected_flex),
        "selected_total_count": len(selected_keys),
        "projection_rows_used": 0,
        "market_rows_used": 0,
        "league_rank_used": False,
        "first_down_source_status": "estimated_from_history",
        "direct_first_down_source_status": first_down_profile.source_status,
        "direct_first_down_source_rows": first_down_profile.source_row_count,
        "direct_first_down_source_seasons": "|".join(
            str(season_value) for season_value in first_down_profile.source_seasons
        ),
        "review_status": "review_only",
    }
    return ReplacementBaselineResult(
        baseline_rows=tuple(baseline_rows),
        player_pool_rows=tuple(pool_rows),
        summary=summary,
    )


def write_rotowire_replacement_baseline_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: ReplacementBaselineResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rotowire_replacement_baselines()
    baseline_path = output / "rotowire_replacement_baselines.csv"
    pool_path = output / "rotowire_replacement_player_pool.csv"
    summary_path = output / "rotowire_replacement_summary.csv"
    _write_csv(baseline_path, BASELINE_HEADER, result.baseline_rows)
    _write_csv(pool_path, PLAYER_POOL_HEADER, result.player_pool_rows)
    _write_csv(
        summary_path,
        SUMMARY_HEADER,
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    return {
        "baselines": baseline_path,
        "player_pool": pool_path,
        "summary": summary_path,
    }


def _player_pool(path: Path, season: int, first_down_profile: object) -> list[_PlayerSeason]:
    best_by_player: dict[tuple[str, str], _PlayerSeason] = {}
    for row in _read_rows(path):
        if row.get("source_detail") != "fantasy":
            continue
        if _int(row.get("season")) != season:
            continue
        position = row.get("position", "")
        if position not in SKILL_POSITIONS:
            continue
        metrics = json.loads(row.get("metrics_json") or "{}")
        lve = _lve_base(metrics)
        first_down_estimate = estimate_first_downs(
            player_name=row.get("player_name", ""),
            position=position,
            metrics=metrics,
            profile=first_down_profile,
        )
        key = (normalize_player_name(row.get("player_name", "")), position)
        current = best_by_player.get(key)
        if not current or lve > current.lve_base_points:
            best_by_player[key] = _PlayerSeason(
                player_name=row.get("player_name", ""),
                normalized_player_name=key[0],
                position=position,
                nfl_team=row.get("nfl_team", ""),
                season=season,
                lve_base_points=lve,
                first_down_estimate=first_down_estimate,
            )
    return sorted(
        best_by_player.values(),
        key=lambda player: player.first_down_adjusted_points,
        reverse=True,
    )


def _required_starters(player_pool: list[_PlayerSeason]) -> set[tuple[str, str]]:
    selected: set[tuple[str, str]] = set()
    for position, count in LINEUP_STARTERS.items():
        ranked = [player for player in player_pool if player.position == position]
        selected.update(_player_key(player) for player in ranked[:count])
    return selected


def _flex_starters(
    player_pool: list[_PlayerSeason],
    selected_required: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    flex_candidates = [
        player
        for player in player_pool
        if player.position in FLEX_POSITIONS and _player_key(player) not in selected_required
    ]
    return {_player_key(player) for player in flex_candidates[:FLEX_STARTERS]}


def _baseline_rows(
    player_pool: list[_PlayerSeason],
    selected_keys: set[tuple[str, str]],
    selected_flex: set[tuple[str, str]],
    season: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for position in SKILL_POSITIONS:
        selected = [
            player
            for player in player_pool
            if player.position == position and _player_key(player) in selected_keys
        ]
        selected.sort(key=lambda player: player.lve_base_points, reverse=True)
        selected.sort(key=lambda player: player.first_down_adjusted_points, reverse=True)
        replacement = selected[-1] if selected else None
        flex_count = sum(1 for player in selected if _player_key(player) in selected_flex)
        rows.append(
            {
                "position": position,
                "required_starters": LINEUP_STARTERS[position],
                "flex_selected": flex_count,
                "total_selected": len(selected),
                "replacement_rank": len(selected),
                "replacement_player": replacement.player_name if replacement else "",
                "replacement_team": replacement.nfl_team if replacement else "",
                "replacement_lve_base_points": round(replacement.lve_base_points, 4)
                if replacement
                else "",
                "replacement_estimated_rushing_first_downs": round(
                    replacement.first_down_estimate.rushing_first_downs,
                    4,
                )
                if replacement
                else "",
                "replacement_estimated_receiving_first_downs": round(
                    replacement.first_down_estimate.receiving_first_downs,
                    4,
                )
                if replacement
                else "",
                "replacement_estimated_first_down_points": round(
                    replacement.first_down_estimate.first_down_points,
                    4,
                )
                if replacement
                else "",
                "replacement_first_down_adjusted_points": round(
                    replacement.first_down_adjusted_points,
                    4,
                )
                if replacement
                else "",
                "replacement_first_down_source_status": (
                    replacement.first_down_estimate.source_status if replacement else ""
                ),
                "replacement_first_down_warning": (
                    replacement.first_down_estimate.warning if replacement else ""
                ),
                "season": season,
                "baseline_version": REPLACEMENT_VERSION,
            }
        )
    return rows


def _player_pool_rows(
    player_pool: list[_PlayerSeason],
    selected_required: set[tuple[str, str]],
    selected_flex: set[tuple[str, str]],
) -> list[dict[str, object]]:
    position_counts: dict[str, int] = {}
    rows: list[dict[str, object]] = []
    for overall_rank, player in enumerate(player_pool, start=1):
        position_counts[player.position] = position_counts.get(player.position, 0) + 1
        key = _player_key(player)
        rows.append(
            {
                "player_name": player.player_name,
                "normalized_player_name": player.normalized_player_name,
                "position": player.position,
                "nfl_team": player.nfl_team,
                "season": player.season,
                "lve_base_points": round(player.lve_base_points, 4),
                "estimated_rushing_first_downs": round(
                    player.first_down_estimate.rushing_first_downs,
                    4,
                ),
                "estimated_receiving_first_downs": round(
                    player.first_down_estimate.receiving_first_downs,
                    4,
                ),
                "estimated_first_down_points": round(
                    player.first_down_estimate.first_down_points,
                    4,
                ),
                "first_down_adjusted_points": round(player.first_down_adjusted_points, 4),
                "first_down_source_status": player.first_down_estimate.source_status,
                "first_down_warning": player.first_down_estimate.warning,
                "selected_as_required_starter": key in selected_required,
                "selected_as_flex": key in selected_flex,
                "overall_skill_pool_rank": overall_rank,
                "position_rank": position_counts[player.position],
                "baseline_version": REPLACEMENT_VERSION,
            }
        )
    return rows


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


def _player_key(player: _PlayerSeason) -> tuple[str, str]:
    return (player.normalized_player_name, player.position)


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


def _int(value: object) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(str(value))
    except ValueError:
        return None


def _float(value: object) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(str(value).replace(",", "").replace("%", ""))
    except ValueError:
        return 0.0
