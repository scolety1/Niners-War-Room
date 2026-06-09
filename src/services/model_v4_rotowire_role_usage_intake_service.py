from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_rotowire_player_stats_intake_service import (
    _metric_keys,
    _metrics_from_row,
)
from src.services.model_v4_rotowire_source_index_service import (
    DEFAULT_RAW_ROOT,
    build_rotowire_source_index,
)

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/rotowire_intake/latest")

ROLE_USAGE_INTAKE_VERSION = "model_v4_rotowire_role_usage_intake_0.1.0"

ROLE_USAGE_HEADER = (
    "season",
    "source_family",
    "player_name",
    "nfl_team",
    "position",
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

ROLE_USAGE_VALIDATION_HEADER = (
    "relative_path",
    "season",
    "source_family",
    "data_rows",
    "clean_rows",
    "warning_rows",
    "validation_status",
    "notes",
)

ROLE_USAGE_FAMILIES = {"snaps", "targets", "alignment", "te_routes"}


@dataclass(frozen=True)
class RotoWireRoleUsageIntakeResult:
    clean_rows: tuple[dict[str, object], ...]
    validation_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_rotowire_role_usage_intake(
    raw_root: str | Path = DEFAULT_RAW_ROOT,
) -> RotoWireRoleUsageIntakeResult:
    root = Path(raw_root)
    index = build_rotowire_source_index(root).rows
    clean_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []
    for source_row in index:
        if not source_row.get("active_for_intake"):
            continue
        if source_row["source_family"] not in ROLE_USAGE_FAMILIES:
            continue
        path = root / str(source_row["relative_path"])
        parsed = _parse_role_usage_file(path, source_row)
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
        "intake_version": ROLE_USAGE_INTAKE_VERSION,
        "clean_row_count": len(clean_rows),
        "validation_file_count": len(validation_rows),
        "warning_row_count": sum(1 for row in clean_rows if row["warning"]),
        "seasons": "|".join(sorted({str(row["season"]) for row in clean_rows})),
        "source_families": "|".join(sorted({str(row["source_family"]) for row in clean_rows})),
        "model_scores_changed": False,
    }
    return RotoWireRoleUsageIntakeResult(
        clean_rows=tuple(clean_rows),
        validation_rows=tuple(validation_rows),
        summary=summary,
    )


def write_rotowire_role_usage_intake_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: RotoWireRoleUsageIntakeResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rotowire_role_usage_intake()
    clean_path = output / "rotowire_role_usage_clean_rows.csv"
    validation_path = output / "rotowire_role_usage_validation.csv"
    summary_path = output / "rotowire_role_usage_summary.csv"
    _write_csv(clean_path, ROLE_USAGE_HEADER, result.clean_rows)
    _write_csv(validation_path, ROLE_USAGE_VALIDATION_HEADER, result.validation_rows)
    _write_csv(
        summary_path,
        ("metric", "value"),
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    return {"clean": clean_path, "validation": validation_path, "summary": summary_path}


def _parse_role_usage_file(
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
        player_name = str(row_map.get("name") or "").strip()
        if not player_name:
            continue
        clean_rows.append(
            {
                "season": source_row["season"],
                "source_family": source_row["source_family"],
                "player_name": player_name,
                "nfl_team": row_map.get("team", ""),
                "position": row_map.get("pos", ""),
                "metrics_json": json.dumps(metrics, sort_keys=True),
                "metric_count": len(metrics),
                "source_name": "RotoWire manual export",
                "source_status": _source_status(str(source_row["source_family"])),
                "source_file": source_row["relative_path"],
                "source_hash": source_row["sha256"],
                "validation_status": "clean" if not warnings else "clean_with_warnings",
                "warning": "|".join(warnings),
                "intake_version": ROLE_USAGE_INTAKE_VERSION,
            }
        )
    return clean_rows


def _source_status(source_family: str) -> str:
    if source_family == "alignment":
        return "imported_alignment_context"
    if source_family == "te_routes":
        return "imported_route_data"
    if source_family == "snaps":
        return "imported_snap_data"
    if source_family == "targets":
        return "imported_target_data"
    return "imported_real_data"


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
