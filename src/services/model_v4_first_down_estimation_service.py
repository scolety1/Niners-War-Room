from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.model_v4_fantasypros_identity_mapping_service import normalize_player_name

DEFAULT_DIRECT_FIRST_DOWNS = Path(
    "local_exports/model_v4/source_reports/truth_set_v3_production_player_season.csv"
)

FIRST_DOWN_ESTIMATE_VERSION = "model_v4_first_down_estimate_0.1.0"
MIN_PLAYER_RUSH_ATTEMPTS = 20.0
MIN_PLAYER_RECEIVING_TARGETS = 20.0


@dataclass(frozen=True)
class FirstDownEstimate:
    rushing_first_downs: float
    receiving_first_downs: float
    first_down_points: float
    rushing_rate: float
    receiving_rate: float
    rushing_rate_source: str
    receiving_rate_source: str
    source_status: str
    warning: str


@dataclass(frozen=True)
class FirstDownRateProfile:
    player_rates: dict[tuple[str, str], dict[str, float]]
    position_rates: dict[str, dict[str, float]]
    source_row_count: int
    source_seasons: tuple[int, ...]
    source_status: str


def build_first_down_rate_profile(
    direct_first_downs_path: str | Path = DEFAULT_DIRECT_FIRST_DOWNS,
) -> FirstDownRateProfile:
    player_totals: dict[tuple[str, str], dict[str, float]] = {}
    position_totals: dict[str, dict[str, float]] = {}
    source_seasons: set[int] = set()
    source_rows = 0
    for row in _read_rows(Path(direct_first_downs_path)):
        if row.get("source_status") != "imported_real_data":
            continue
        position = row.get("position", "")
        if position not in {"QB", "RB", "WR", "TE"}:
            continue
        source_rows += 1
        season = _int(row.get("season"))
        if season is not None:
            source_seasons.add(season)
        key = (normalize_player_name(row.get("truth_set_player_name", "")), position)
        player_total = player_totals.setdefault(key, _empty_totals())
        position_total = position_totals.setdefault(position, _empty_totals())
        _add_first_down_totals(player_total, row)
        _add_first_down_totals(position_total, row)
    return FirstDownRateProfile(
        player_rates={key: _rates(value) for key, value in player_totals.items()},
        position_rates={key: _rates(value) for key, value in position_totals.items()},
        source_row_count=source_rows,
        source_seasons=tuple(sorted(source_seasons)),
        source_status="imported_real_data",
    )


def estimate_first_downs(
    *,
    player_name: str,
    position: str,
    metrics: dict[str, object],
    profile: FirstDownRateProfile,
) -> FirstDownEstimate:
    player_rate = profile.player_rates.get((normalize_player_name(player_name), position), {})
    position_rate = profile.position_rates.get(position, {})
    rushing_attempts = _float(metrics.get("rushing_att"))
    receiving_targets = _float(metrics.get("receiving_tar"))
    receiving_receptions = _float(metrics.get("receiving_rec"))
    receiving_opportunities = receiving_targets or receiving_receptions

    rush_rate, rush_source = _choose_rate(
        player_rate,
        position_rate,
        denominator_key="rushing_attempts",
        rate_key="rushing_first_down_rate",
        minimum=MIN_PLAYER_RUSH_ATTEMPTS,
    )
    rec_rate, rec_source = _choose_rate(
        player_rate,
        position_rate,
        denominator_key="receiving_targets",
        rate_key="receiving_first_down_rate",
        minimum=MIN_PLAYER_RECEIVING_TARGETS,
    )

    rushing_first_downs = rushing_attempts * rush_rate
    receiving_first_downs = receiving_opportunities * rec_rate
    first_down_points = (
        rushing_first_downs + receiving_first_downs
    ) * LVE_SCORING["rushing_receiving_first_down"]
    warning = "first_downs_estimated_from_history_not_direct"
    if rush_source == "position_fallback" or rec_source == "position_fallback":
        warning = "first_downs_estimated_from_position_history_not_direct"
    return FirstDownEstimate(
        rushing_first_downs=round(rushing_first_downs, 4),
        receiving_first_downs=round(receiving_first_downs, 4),
        first_down_points=round(first_down_points, 4),
        rushing_rate=round(rush_rate, 6),
        receiving_rate=round(rec_rate, 6),
        rushing_rate_source=rush_source,
        receiving_rate_source=rec_source,
        source_status="estimated_from_history",
        warning=warning,
    )


def _choose_rate(
    player_rate: dict[str, float],
    position_rate: dict[str, float],
    *,
    denominator_key: str,
    rate_key: str,
    minimum: float,
) -> tuple[float, str]:
    if player_rate.get(denominator_key, 0.0) >= minimum:
        return player_rate.get(rate_key, 0.0), "player_history"
    return position_rate.get(rate_key, 0.0), "position_fallback"


def _add_first_down_totals(total: dict[str, float], row: dict[str, str]) -> None:
    total["rushing_first_downs"] += _float(row.get("rushing_first_downs"))
    total["receiving_first_downs"] += _float(row.get("receiving_first_downs"))
    total["rushing_attempts"] += _float(row.get("rushing_attempts"))
    total["receiving_targets"] += _float(row.get("targets"))
    total["receiving_receptions"] += _float(row.get("receptions"))


def _rates(total: dict[str, float]) -> dict[str, float]:
    receiving_denominator = total["receiving_targets"] or total["receiving_receptions"]
    return {
        **total,
        "rushing_first_down_rate": _safe_rate(
            total["rushing_first_downs"],
            total["rushing_attempts"],
        ),
        "receiving_first_down_rate": _safe_rate(
            total["receiving_first_downs"],
            receiving_denominator,
        ),
    }


def _safe_rate(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _empty_totals() -> dict[str, float]:
    return {
        "rushing_first_downs": 0.0,
        "receiving_first_downs": 0.0,
        "rushing_attempts": 0.0,
        "receiving_targets": 0.0,
        "receiving_receptions": 0.0,
    }


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(csv.DictReader(handle))


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
