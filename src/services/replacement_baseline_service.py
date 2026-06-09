from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASELINE_PATH = (
    Path(__file__).resolve().parents[2]
    / "sample_data"
    / "replacement_baselines"
    / "lve_replacement_thresholds.csv"
)

REPLACEMENT_CONTEXTS = {"steady_state", "declaration_window"}
REPLACEMENT_POSITIONS = {"QB", "RB", "WR", "TE"}


@dataclass(frozen=True)
class ReplacementBaseline:
    context: str
    position: str
    effective_weekly_starter_demand: int
    weekly_replacement_rank: int
    stash_threshold_rank: int
    elite_anchor_rank: int
    flex_share_assumption: float
    source_type: str
    notes: str


def load_replacement_baselines(
    path: str | Path = DEFAULT_BASELINE_PATH,
) -> dict[tuple[str, str], ReplacementBaseline]:
    baseline_path = Path(path)
    with baseline_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    baselines: dict[tuple[str, str], ReplacementBaseline] = {}
    for row_number, row in enumerate(rows, start=2):
        baseline = _parse_baseline_row(row, row_number)
        key = (baseline.context, baseline.position)
        if key in baselines:
            raise ValueError(
                f"Duplicate replacement baseline for {baseline.context}/{baseline.position}."
            )
        baselines[key] = baseline

    missing = {
        (context, position)
        for context in REPLACEMENT_CONTEXTS
        for position in REPLACEMENT_POSITIONS
    } - set(baselines)
    if missing:
        missing_text = ", ".join(f"{context}/{position}" for context, position in sorted(missing))
        raise ValueError(f"Missing replacement baselines: {missing_text}.")
    return baselines


def replacement_baseline_rows(
    path: str | Path = DEFAULT_BASELINE_PATH,
) -> list[dict[str, object]]:
    return [
        {
            "context": baseline.context,
            "position": baseline.position,
            "effective_weekly_starter_demand": baseline.effective_weekly_starter_demand,
            "weekly_replacement_rank": baseline.weekly_replacement_rank,
            "stash_threshold_rank": baseline.stash_threshold_rank,
            "elite_anchor_rank": baseline.elite_anchor_rank,
            "flex_share_assumption": baseline.flex_share_assumption,
            "source_type": baseline.source_type,
            "notes": baseline.notes,
        }
        for baseline in load_replacement_baselines(path).values()
    ]


def replacement_gap_score(
    position: str,
    projected_position_rank: int | None,
    *,
    context: str = "steady_state",
    baselines: dict[tuple[str, str], ReplacementBaseline] | None = None,
) -> float:
    if projected_position_rank is None:
        return 50.0
    rank = int(projected_position_rank)
    if rank <= 0:
        return 50.0

    baseline_map = baselines if baselines is not None else load_replacement_baselines()
    baseline = baseline_map.get((context, position))
    if baseline is None:
        return 50.0
    elite = baseline.elite_anchor_rank
    weekly = baseline.weekly_replacement_rank
    stash = baseline.stash_threshold_rank

    if rank <= elite:
        if elite <= 1:
            return 100.0
        return round(_interpolate(rank, 1, elite, 100.0, 85.0), 2)
    if rank <= weekly:
        return round(_interpolate(rank, elite, weekly, 85.0, 50.0), 2)
    if rank <= stash:
        return round(_interpolate(rank, weekly, stash, 50.0, 20.0), 2)
    if rank <= stash + 6:
        return round(_interpolate(rank, stash, stash + 6, 20.0, 0.0), 2)
    return 0.0


def _parse_baseline_row(row: dict[str, str], row_number: int) -> ReplacementBaseline:
    context = str(row.get("context") or "").strip()
    position = str(row.get("position") or "").strip()
    if context not in REPLACEMENT_CONTEXTS:
        raise ValueError(f"Row {row_number}: invalid replacement context {context!r}.")
    if position not in REPLACEMENT_POSITIONS:
        raise ValueError(f"Row {row_number}: invalid replacement position {position!r}.")

    elite = _int_value(row, "elite_anchor_rank", row_number)
    weekly = _int_value(row, "weekly_replacement_rank", row_number)
    stash = _int_value(row, "stash_threshold_rank", row_number)
    if not (1 <= elite < weekly < stash):
        raise ValueError(
            f"Row {row_number}: expected elite_anchor_rank < "
            "weekly_replacement_rank < stash_threshold_rank."
        )

    return ReplacementBaseline(
        context=context,
        position=position,
        effective_weekly_starter_demand=_int_value(
            row, "effective_weekly_starter_demand", row_number
        ),
        weekly_replacement_rank=weekly,
        stash_threshold_rank=stash,
        elite_anchor_rank=elite,
        flex_share_assumption=_float_value(row, "flex_share_assumption", row_number),
        source_type=str(row.get("source_type") or "").strip(),
        notes=str(row.get("notes") or "").strip(),
    )


def _int_value(row: dict[str, str], column: str, row_number: int) -> int:
    try:
        return int(str(row.get(column) or ""))
    except ValueError as exc:
        raise ValueError(f"Row {row_number}: {column} must be an integer.") from exc


def _float_value(row: dict[str, str], column: str, row_number: int) -> float:
    try:
        return float(str(row.get(column) or ""))
    except ValueError as exc:
        raise ValueError(f"Row {row_number}: {column} must be numeric.") from exc


def _interpolate(
    x_value: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> float:
    if x_max == x_min:
        return y_max
    progress = (x_value - x_min) / (x_max - x_min)
    return max(0.0, min(100.0, y_min + ((y_max - y_min) * progress)))
