from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_rotowire_player_stats_intake_service import (
    _metric_keys,
    _normalize_value,
)
from src.services.model_v4_rotowire_source_index_service import (
    DEFAULT_RAW_ROOT,
    build_rotowire_source_index,
)

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/rotowire_intake/latest")

CONTEXT_INTAKE_VERSION = "model_v4_rotowire_context_intake_0.1.0"

CONTEXT_HEADER = (
    "season",
    "source_family",
    "entity_type",
    "entity_name",
    "nfl_team",
    "position",
    "metrics_json",
    "metric_count",
    "model_lane",
    "allowed_use",
    "source_name",
    "source_status",
    "source_file",
    "source_hash",
    "validation_status",
    "warning",
    "intake_version",
)

CONTEXT_VALIDATION_HEADER = (
    "relative_path",
    "season",
    "source_family",
    "data_rows",
    "clean_rows",
    "warning_rows",
    "validation_status",
    "notes",
)

CONTEXT_FAMILIES = {
    "depth_charts",
    "injuries",
    "projections",
    "rankings_context",
    "market_context",
    "combine_workout",
    "team_pace_proe",
    "team_stats",
    "team_context",
    "offensive_line_rankings",
}

FAMILY_LANES = {
    "depth_charts": ("current_role_context", "context_only", "current_depth_chart_context"),
    "injuries": ("injury_context", "context_only", "sourced_injury_context"),
    "projections": ("projection_context", "review_only", "raw_projection_stats_context"),
    "rankings_context": ("sanity_context", "review_only", "external_rankings_sanity_context"),
    "market_context": ("market_context", "context_only", "early_market_context"),
    "combine_workout": ("rookie_bridge_context", "review_only", "prospect_workout_context"),
    "team_pace_proe": ("team_environment_context", "context_only", "team_pace_proe_context"),
    "team_stats": ("team_environment_context", "context_only", "team_stats_context"),
    "team_context": ("team_environment_context", "context_only", "team_rankings_context"),
    "offensive_line_rankings": (
        "team_environment_context",
        "context_only",
        "offensive_line_context",
    ),
}


@dataclass(frozen=True)
class RotoWireContextIntakeResult:
    clean_rows: tuple[dict[str, object], ...]
    validation_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_rotowire_context_intake(
    raw_root: str | Path = DEFAULT_RAW_ROOT,
) -> RotoWireContextIntakeResult:
    root = Path(raw_root)
    index = build_rotowire_source_index(root).rows
    clean_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []
    for source_row in index:
        if not source_row.get("active_for_intake"):
            continue
        if source_row["source_family"] not in CONTEXT_FAMILIES:
            continue
        path = root / str(source_row["relative_path"])
        parsed = _parse_context_file(path, source_row)
        clean_rows.extend(parsed)
        warning_rows = sum(1 for row in parsed if row["warning"])
        validation_rows.append(
            {
                "relative_path": source_row["relative_path"],
                "season": source_row["season"],
                "source_family": source_row["source_family"],
                "data_rows": source_row["data_rows"],
                "clean_rows": len(parsed),
                "warning_rows": warning_rows,
                "validation_status": "clean" if warning_rows == 0 else "clean_with_warnings",
                "notes": "",
            }
        )
    summary = {
        "intake_version": CONTEXT_INTAKE_VERSION,
        "clean_row_count": len(clean_rows),
        "validation_file_count": len(validation_rows),
        "warning_row_count": sum(1 for row in clean_rows if row["warning"]),
        "source_families": "|".join(sorted({str(row["source_family"]) for row in clean_rows})),
        "model_scores_changed": False,
    }
    return RotoWireContextIntakeResult(
        clean_rows=tuple(clean_rows),
        validation_rows=tuple(validation_rows),
        summary=summary,
    )


def write_rotowire_context_intake_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: RotoWireContextIntakeResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rotowire_context_intake()
    clean_path = output / "rotowire_context_clean_rows.csv"
    validation_path = output / "rotowire_context_validation.csv"
    summary_path = output / "rotowire_context_summary.csv"
    _write_csv(clean_path, CONTEXT_HEADER, result.clean_rows)
    _write_csv(validation_path, CONTEXT_VALIDATION_HEADER, result.validation_rows)
    _write_csv(
        summary_path,
        ("metric", "value"),
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    return {"clean": clean_path, "validation": validation_path, "summary": summary_path}


def _parse_context_file(path: Path, source_row: dict[str, object]) -> list[dict[str, object]]:
    family = str(source_row["source_family"])
    if family == "depth_charts":
        return _parse_depth_chart(path, source_row)
    if family == "injuries":
        return _parse_injury_file(path, source_row)
    return _parse_table_context(path, source_row)


def _parse_depth_chart(path: Path, source_row: dict[str, object]) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    header = rows[0]
    position = _depth_position(path.name)
    output = []
    for row in rows[1:]:
        if len(row) != len(header):
            continue
        team = row[0]
        for index, cell in enumerate(row[1:], start=1):
            player, status = _split_status(cell)
            if not player:
                continue
            metrics = {
                "depth_slot": header[index],
                "depth_rank": index,
                "listed_status": status,
            }
            output.append(
                _context_row(
                    source_row=source_row,
                    entity_type="player",
                    entity_name=player,
                    nfl_team=team,
                    position=position,
                    metrics=metrics,
                    warnings=[],
                )
            )
    return output


def _parse_injury_file(path: Path, source_row: dict[str, object]) -> list[dict[str, object]]:
    position = path.name.split("_", 1)[0].upper()
    output = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            player = row.get("Player", "")
            if not player:
                continue
            metrics = {
                "injury": row.get("Injury", ""),
                "status": row.get("Status", ""),
                "estimated_return": row.get("Est. Return", ""),
            }
            output.append(
                _context_row(
                    source_row=source_row,
                    entity_type="player",
                    entity_name=player,
                    nfl_team=row.get("Team", ""),
                    position=position,
                    metrics=metrics,
                    warnings=[],
                )
            )
    return output


def _parse_table_context(path: Path, source_row: dict[str, object]) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    header_index = int(source_row["header_row_index"])
    group_row = rows[header_index - 1] if header_index > 0 else [""] * len(rows[header_index])
    header = rows[header_index]
    metric_keys = _metric_keys(group_row, header)
    output = []
    for row in rows[header_index + 1 :]:
        if not row or len(row) != len(header):
            continue
        row_map = dict(zip(metric_keys, row, strict=True))
        entity_name, entity_type = _entity_name(row_map, str(source_row["source_family"]))
        if not entity_name:
            continue
        metrics, warnings = _context_metrics_from_row(row_map)
        output.append(
            _context_row(
                source_row=source_row,
                entity_type=entity_type,
                entity_name=entity_name,
                nfl_team=row_map.get("team", ""),
                position=row_map.get("pos", _workout_position(path.name)),
                metrics=metrics,
                warnings=warnings,
            )
        )
    return output


def _context_row(
    *,
    source_row: dict[str, object],
    entity_type: str,
    entity_name: str,
    nfl_team: str,
    position: str,
    metrics: dict[str, object],
    warnings: list[str],
) -> dict[str, object]:
    model_lane, allowed_use, source_status = FAMILY_LANES[str(source_row["source_family"])]
    return {
        "season": source_row["season"],
        "source_family": source_row["source_family"],
        "entity_type": entity_type,
        "entity_name": entity_name,
        "nfl_team": nfl_team,
        "position": position,
        "metrics_json": json.dumps(metrics, sort_keys=True),
        "metric_count": len(metrics),
        "model_lane": model_lane,
        "allowed_use": allowed_use,
        "source_name": "RotoWire manual export",
        "source_status": source_status,
        "source_file": source_row["relative_path"],
        "source_hash": source_row["sha256"],
        "validation_status": "clean" if not warnings else "clean_with_warnings",
        "warning": "|".join(warnings),
        "intake_version": CONTEXT_INTAKE_VERSION,
    }


def _entity_name(row_map: dict[str, str], family: str) -> tuple[str, str]:
    if family in {"team_pace_proe", "team_stats", "team_context", "offensive_line_rankings"}:
        return row_map.get("team", ""), "team"
    return row_map.get("name") or row_map.get("player_name") or "", "player"


def _context_metrics_from_row(row: dict[str, str]) -> tuple[dict[str, object], list[str]]:
    metrics: dict[str, object] = {}
    identity_keys = {"playerid", "name", "player_name", "team", "pos", "g"}
    for key, value in row.items():
        if key in identity_keys:
            continue
        normalized, warning = _normalize_value(value)
        metrics[key] = value.strip() if warning == "non_numeric_value" else normalized
    return metrics, []


def _split_status(value: str) -> tuple[str, str]:
    if " - " not in str(value):
        return str(value).strip(), ""
    player, status = str(value).split(" - ", 1)
    return player.strip(), status.strip()


def _depth_position(file_name: str) -> str:
    if "_qb" in file_name:
        return "QB"
    if "_rb" in file_name:
        return "RB"
    if "_wr" in file_name:
        return "WR"
    if "_te" in file_name:
        return "TE"
    return ""


def _workout_position(file_name: str) -> str:
    parts = file_name.lower().replace(".csv", "").split("_")
    return parts[-1].upper() if parts and parts[-1] in {"qb", "rb", "wr", "te"} else ""


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
