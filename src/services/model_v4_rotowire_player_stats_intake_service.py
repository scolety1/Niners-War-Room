from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_rotowire_source_index_service import (
    DEFAULT_RAW_ROOT,
    build_rotowire_source_index,
)

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/rotowire_intake/latest")

PLAYER_STATS_INTAKE_VERSION = "model_v4_rotowire_player_stats_intake_0.1.0"

PLAYER_STATS_HEADER = (
    "season",
    "source_family",
    "source_detail",
    "rotowire_player_id",
    "player_name",
    "nfl_team",
    "position",
    "games",
    "metrics_json",
    "metric_count",
    "source_name",
    "source_status",
    "source_file",
    "source_hash",
    "validation_status",
    "warning",
    "intake_version",
)

VALIDATION_HEADER = (
    "relative_path",
    "season",
    "source_family",
    "source_detail",
    "data_rows",
    "clean_rows",
    "warning_rows",
    "validation_status",
    "notes",
)

PLAYER_STAT_FAMILIES = {"passing", "rushing", "receiving"}


@dataclass(frozen=True)
class RotoWirePlayerStatsIntakeResult:
    clean_rows: tuple[dict[str, object], ...]
    validation_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_rotowire_player_stats_intake(
    raw_root: str | Path = DEFAULT_RAW_ROOT,
) -> RotoWirePlayerStatsIntakeResult:
    root = Path(raw_root)
    index = build_rotowire_source_index(root).rows
    clean_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []

    for source_row in index:
        if not source_row.get("active_for_intake"):
            continue
        if source_row["source_family"] not in PLAYER_STAT_FAMILIES:
            continue
        path = root / str(source_row["relative_path"])
        parsed = _parse_player_stats_file(path, source_row)
        clean_rows.extend(parsed)
        warning_rows = sum(1 for row in parsed if row["warning"])
        validation_rows.append(
            {
                "relative_path": source_row["relative_path"],
                "season": source_row["season"],
                "source_family": source_row["source_family"],
                "source_detail": source_row["source_detail"],
                "data_rows": source_row["data_rows"],
                "clean_rows": len(parsed),
                "warning_rows": warning_rows,
                "validation_status": "clean" if warning_rows == 0 else "clean_with_warnings",
                "notes": "",
            }
        )

    summary = {
        "intake_version": PLAYER_STATS_INTAKE_VERSION,
        "clean_row_count": len(clean_rows),
        "validation_file_count": len(validation_rows),
        "warning_row_count": sum(1 for row in clean_rows if row["warning"]),
        "seasons": "|".join(sorted({str(row["season"]) for row in clean_rows})),
        "source_families": "|".join(sorted({str(row["source_family"]) for row in clean_rows})),
        "model_scores_changed": False,
    }
    return RotoWirePlayerStatsIntakeResult(
        clean_rows=tuple(clean_rows),
        validation_rows=tuple(validation_rows),
        summary=summary,
    )


def write_rotowire_player_stats_intake_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: RotoWirePlayerStatsIntakeResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rotowire_player_stats_intake()
    clean_path = output / "rotowire_player_stats_clean_rows.csv"
    validation_path = output / "rotowire_player_stats_validation.csv"
    summary_path = output / "rotowire_player_stats_summary.csv"
    _write_csv(clean_path, PLAYER_STATS_HEADER, result.clean_rows)
    _write_csv(validation_path, VALIDATION_HEADER, result.validation_rows)
    _write_csv(
        summary_path,
        ("metric", "value"),
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    return {"clean": clean_path, "validation": validation_path, "summary": summary_path}


def _parse_player_stats_file(
    path: Path,
    source_row: dict[str, object],
) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    header_index = int(source_row["header_row_index"])
    group_row = rows[header_index - 1] if header_index > 0 else [""] * len(rows[header_index])
    header = rows[header_index]
    metric_keys = _metric_keys(group_row, header)
    clean_rows = []
    for row in rows[header_index + 1 :]:
        if not row or len(row) != len(header):
            continue
        row_map = dict(zip(metric_keys, row, strict=True))
        metrics, warnings = _metrics_from_row(row_map)
        player_name = row_map.get("name", "")
        clean_rows.append(
            {
                "season": source_row["season"],
                "source_family": source_row["source_family"],
                "source_detail": source_row["source_detail"],
                "rotowire_player_id": row_map.get("playerid", ""),
                "player_name": player_name,
                "nfl_team": row_map.get("team", ""),
                "position": row_map.get("pos", ""),
                "games": row_map.get("g", ""),
                "metrics_json": json.dumps(metrics, sort_keys=True),
                "metric_count": len(metrics),
                "source_name": "RotoWire manual export",
                "source_status": "imported_real_data",
                "source_file": source_row["relative_path"],
                "source_hash": source_row["sha256"],
                "validation_status": "clean" if not warnings else "clean_with_warnings",
                "warning": "|".join(warnings),
                "intake_version": PLAYER_STATS_INTAKE_VERSION,
            }
        )
    return clean_rows


def _metric_keys(group_row: list[str], header: list[str]) -> tuple[str, ...]:
    active_group = ""
    keys: list[str] = []
    seen: dict[str, int] = {}
    identity_columns = {"playerid", "name", "team", "pos", "g"}
    for index, raw_header in enumerate(header):
        group = group_row[index].strip() if index < len(group_row) else ""
        if group:
            active_group = group
        base = _slug(raw_header)
        if base in identity_columns:
            key = base
        else:
            group_slug = _slug(active_group) or "metric"
            key = f"{group_slug}_{base}" if base else group_slug
        count = seen.get(key, 0)
        seen[key] = count + 1
        if count:
            key = f"{key}_{count + 1}"
        keys.append(key)
    return tuple(keys)


def _metrics_from_row(row: dict[str, str]) -> tuple[dict[str, object], list[str]]:
    metrics: dict[str, object] = {}
    warnings: list[str] = []
    for key, value in row.items():
        if key in {"playerid", "name", "team", "pos", "g"}:
            continue
        normalized, warning = _normalize_value(value)
        metrics[key] = normalized
        if warning:
            warnings.append(f"{key}:{warning}")
    return metrics, warnings


def _normalize_value(value: str) -> tuple[object, str]:
    value = str(value).strip()
    if value in {"", "-"}:
        return "", ""
    cleaned = value.replace(",", "")
    if cleaned.endswith("%"):
        cleaned = cleaned[:-1]
    try:
        number = float(cleaned)
    except ValueError:
        return value, "non_numeric_value"
    if number.is_integer():
        return int(number), ""
    return number, ""


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return slug.strip("_")


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
