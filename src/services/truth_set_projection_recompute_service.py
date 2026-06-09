from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING

TRUTH_SET_PROJECTION_RECOMPUTE_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "reference_nfl_team",
    "projection_source",
    "projection_date",
    "projected_games",
    "projected_starts",
    "passing_points",
    "rushing_points",
    "receiving_points",
    "first_down_points",
    "turnover_points",
    "recomputed_lve_points",
    "recomputed_lve_points_no_first_downs",
    "supplied_projected_points",
    "supplied_minus_recomputed",
    "points_column_status",
    "first_down_projection_status",
    "projection_availability_status",
    "projection_source_quality_status",
    "projection_source_quality_flags",
    "scoring_profile_id",
    "scoring_effect",
    "source_url",
    "notes",
)

TRUTH_SET_PROJECTION_FLAG_HEADER = (
    "category",
    "player_name",
    "flag",
    "severity",
    "detail",
)


@dataclass(frozen=True)
class TruthSetProjectionRecomputeResult:
    rows: tuple[dict[str, object], ...]
    flags: tuple[dict[str, str], ...]
    summary: dict[str, object]


def recompute_truth_set_projection_rows(
    source_path: str | Path,
    reference_player_path: str | Path | None = None,
    high_active_value_threshold: float = 70.0,
) -> TruthSetProjectionRecomputeResult:
    rows = _read_rows(Path(source_path))
    reference_rows = _read_rows(Path(reference_player_path)) if reference_player_path else []
    reference_by_name = {_name_key(row.get("player_name")): row for row in reference_rows}
    recomputed = tuple(
        _recompute_row(
            row,
            reference_by_name.get(_name_key(row.get("player_name"))),
            high_active_value_threshold=high_active_value_threshold,
        )
        for row in rows
    )
    flags = tuple(_flags_for_row(row) for row in recomputed)
    flat_flags = tuple(flag for row_flags in flags for flag in row_flags)
    summary = {
        "rows": len(recomputed),
        "projection_rows": sum(
            row["projection_availability_status"] == "projection_stat_line_present"
            for row in recomputed
        ),
        "missing_projection_rows": sum(
            row["projection_availability_status"] != "projection_stat_line_present"
            for row in recomputed
        ),
        "supplied_points_rejected_rows": sum(
            row["points_column_status"] == "supplied_points_rejected_not_lve"
            for row in recomputed
        ),
        "first_down_direct_rows": sum(
            row["first_down_projection_status"] == "direct" for row in recomputed
        ),
        "first_down_estimated_missing_rows": sum(
            row["first_down_projection_status"] == "estimated_missing"
            for row in recomputed
        ),
        "first_down_missing_rows": sum(
            row["first_down_projection_status"] == "missing" for row in recomputed
        ),
        "team_mismatch_rows": sum(
            "team_mismatch" in str(row["projection_source_quality_flags"])
            for row in recomputed
        ),
        "high_active_value_missing_projection_rows": sum(
            "high_active_value_missing_projection"
            in str(row["projection_source_quality_flags"])
            for row in recomputed
        ),
        "scoring_effect": "preview-only projection recompute; no model mutation",
    }
    return TruthSetProjectionRecomputeResult(
        rows=recomputed,
        flags=flat_flags,
        summary=summary,
    )


def write_truth_set_projection_recompute(
    output_path: str | Path,
    rows: tuple[dict[str, object], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRUTH_SET_PROJECTION_RECOMPUTE_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def write_truth_set_projection_flags(
    output_path: str | Path,
    flags: tuple[dict[str, str], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRUTH_SET_PROJECTION_FLAG_HEADER)
        writer.writeheader()
        writer.writerows(flags)


def _recompute_row(
    row: dict[str, str],
    reference: dict[str, str] | None = None,
    *,
    high_active_value_threshold: float = 70.0,
) -> dict[str, object]:
    passing_points = (
        _float(row.get("projected_passing_yards")) * LVE_SCORING["passing_yard"]
        + _float(row.get("projected_passing_tds")) * LVE_SCORING["passing_td"]
    )
    rushing_points = (
        _float(row.get("projected_rushing_yards")) * LVE_SCORING["rushing_yard"]
        + _float(row.get("projected_rushing_tds")) * LVE_SCORING["rushing_td"]
    )
    receiving_points = (
        _float(row.get("projected_receiving_yards")) * LVE_SCORING["receiving_yard"]
        + _float(row.get("projected_receiving_tds")) * LVE_SCORING["receiving_td"]
    )
    first_downs = (
        _float(row.get("projected_rushing_first_downs"))
        + _float(row.get("projected_receiving_first_downs"))
    )
    first_down_points = first_downs * LVE_SCORING["rushing_receiving_first_down"]
    turnover_points = _float(row.get("projected_interceptions")) * LVE_SCORING[
        "interception"
    ]
    lve_no_first_downs = (
        passing_points + rushing_points + receiving_points + turnover_points
    )
    lve_points = lve_no_first_downs + first_down_points
    supplied = _optional_float(row.get("projected_lve_points_if_calculable"))
    supplied_minus = None if supplied is None else supplied - lve_points
    availability_status = _projection_availability_status(row)
    first_down_status = _first_down_projection_status(row)
    quality_flags = _projection_source_quality_flags(
        row,
        reference,
        availability_status=availability_status,
        first_down_status=first_down_status,
        high_active_value_threshold=high_active_value_threshold,
    )
    return {
        "player_name": row.get("player_name", ""),
        "position": row.get("position", ""),
        "nfl_team": row.get("nfl_team", ""),
        "reference_nfl_team": _reference_team(reference),
        "projection_source": row.get("projection_source", ""),
        "projection_date": row.get("projection_date", ""),
        "projected_games": row.get("projected_games", ""),
        "projected_starts": row.get("projected_starts", ""),
        "passing_points": round(passing_points, 2),
        "rushing_points": round(rushing_points, 2),
        "receiving_points": round(receiving_points, 2),
        "first_down_points": round(first_down_points, 2),
        "turnover_points": round(turnover_points, 2),
        "recomputed_lve_points": round(lve_points, 2),
        "recomputed_lve_points_no_first_downs": round(lve_no_first_downs, 2),
        "supplied_projected_points": "" if supplied is None else round(supplied, 2),
        "supplied_minus_recomputed": ""
        if supplied_minus is None
        else round(supplied_minus, 2),
        "points_column_status": _points_column_status(supplied, supplied_minus),
        "first_down_projection_status": first_down_status,
        "projection_availability_status": availability_status,
        "projection_source_quality_status": _projection_source_quality_status(
            quality_flags
        ),
        "projection_source_quality_flags": "|".join(quality_flags),
        "scoring_profile_id": "lve_1qb_non_ppr_0_4_rush_rec_fd",
        "scoring_effect": "preview-only projection recompute; no model mutation",
        "source_url": row.get("source_url", ""),
        "notes": row.get("notes", ""),
    }


def _flags_for_row(row: dict[str, object]) -> tuple[dict[str, str], ...]:
    player = str(row["player_name"])
    flags: list[dict[str, str]] = []
    if row["points_column_status"] == "supplied_points_rejected_not_lve":
        flags.append(
            {
                "category": "projection_recompute",
                "player_name": player,
                "flag": "supplied_points_rejected_not_lve",
                "severity": "blocking_for_supplied_points_column",
                "detail": (
                    "Supplied projection points differ from recomputed LVE points; "
                    "use recomputed points only."
                ),
            }
        )
    if row["first_down_projection_status"] == "estimated_missing":
        flags.append(
            {
                "category": "projection_recompute",
                "player_name": player,
                "flag": "first_down_projection_estimable_but_missing",
                "severity": "review",
                "detail": (
                    "Projection has volume/stat inputs but no rushing/receiving "
                    "first-down projection."
                ),
            }
        )
    if "team_mismatch" in str(row["projection_source_quality_flags"]):
        flags.append(
            {
                "category": "projection_source_quality",
                "player_name": player,
                "flag": "projection_team_mismatch",
                "severity": "review",
                "detail": (
                    "Projection NFL team does not match the active model reference team; "
                    "review before relying on this projection row."
                ),
            }
        )
    if "high_active_value_missing_projection" in str(row["projection_source_quality_flags"]):
        flags.append(
            {
                "category": "projection_source_quality",
                "player_name": player,
                "flag": "high_active_value_missing_projection",
                "severity": "review",
                "detail": (
                    "Active model value is high but no offensive projection row is present."
                ),
            }
        )
    if row["projection_availability_status"] != "projection_stat_line_present":
        flags.append(
            {
                "category": "projection_recompute",
                "player_name": player,
                "flag": "missing_offensive_projection",
                "severity": "review",
                "detail": "No usable offensive projection stat line was present.",
            }
        )
    return tuple(flags)


def _points_column_status(supplied: float | None, supplied_minus: float | None) -> str:
    if supplied is None:
        return "no_supplied_points"
    if supplied_minus is not None and abs(supplied_minus) > 5.0:
        return "supplied_points_rejected_not_lve"
    return "supplied_points_matches_recomputed"


def _first_down_projection_status(row: dict[str, str]) -> str:
    has_direct = bool(
        str(row.get("projected_rushing_first_downs") or "").strip()
        or str(row.get("projected_receiving_first_downs") or "").strip()
    )
    if has_direct:
        return "direct"
    if _has_offensive_projection(row):
        return "estimated_missing"
    return "missing"


def _projection_availability_status(row: dict[str, str]) -> str:
    if _has_offensive_projection(row):
        return "projection_stat_line_present"
    return "missing_offensive_projection"


def _projection_source_quality_flags(
    row: dict[str, str],
    reference: dict[str, str] | None,
    *,
    availability_status: str,
    first_down_status: str,
    high_active_value_threshold: float,
) -> tuple[str, ...]:
    flags: list[str] = []
    if availability_status != "projection_stat_line_present":
        flags.append("missing_projection")
    if first_down_status != "direct":
        flags.append("missing_first_down_projection")
    projection_team = str(row.get("nfl_team") or "")
    reference_team = _reference_team(reference)
    if (
        projection_team
        and reference_team
        and _team_key(projection_team) != _team_key(reference_team)
    ):
        flags.append("team_mismatch")
    active_value = _optional_float(
        (reference or {}).get("private_lve_value")
        or (reference or {}).get("model_value")
    )
    if (
        availability_status != "projection_stat_line_present"
        and active_value is not None
        and active_value >= high_active_value_threshold
    ):
        flags.append("high_active_value_missing_projection")
    return tuple(dict.fromkeys(flags))


def _projection_source_quality_status(flags: tuple[str, ...]) -> str:
    if not flags:
        return "clean"
    if "team_mismatch" in flags:
        return "team_mismatch"
    if "high_active_value_missing_projection" in flags:
        return "review_needed"
    if "missing_projection" in flags:
        return "missing_projection"
    if "missing_first_down_projection" in flags:
        return "missing_first_down_projection"
    return "review_needed"


def _has_offensive_projection(row: dict[str, str]) -> bool:
    stat_columns = (
        "projected_passing_yards",
        "projected_passing_tds",
        "projected_interceptions",
        "projected_rushing_attempts",
        "projected_rushing_yards",
        "projected_rushing_tds",
        "projected_targets",
        "projected_receptions",
        "projected_receiving_yards",
        "projected_receiving_tds",
    )
    return any(_float(row.get(column)) != 0 for column in stat_columns)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _reference_team(reference: dict[str, str] | None) -> str:
    return str(
        (reference or {}).get("team")
        or (reference or {}).get("nfl_team")
        or ""
    )


def _team_key(value: object) -> str:
    team = str(value or "").strip().upper()
    aliases = {
        "LAR": "LA",
    }
    return aliases.get(team, team)


def _name_key(value: object) -> str:
    return "".join(char for char in str(value or "").lower() if char.isalnum())


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
