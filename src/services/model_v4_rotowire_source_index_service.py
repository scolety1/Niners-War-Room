from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_RAW_ROOT = Path("local_exports/model_v4/raw_user_exports/rotowire_manual")
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/rotowire_intake/latest")

SOURCE_INDEX_VERSION = "model_v4_rotowire_source_index_0.1.0"
SCHEMA_CATALOG_VERSION = "model_v4_rotowire_schema_catalog_0.1.0"

SOURCE_INDEX_HEADER = (
    "relative_path",
    "season",
    "source_family",
    "source_detail",
    "file_name",
    "is_canonical_file",
    "active_for_intake",
    "inactive_reason",
    "bytes",
    "sha256",
    "csv_rows",
    "data_rows",
    "header_row_index",
    "column_count",
    "row_widths",
    "malformed_row_count",
    "validation_status",
    "model_lane",
    "allowed_use",
    "notes",
    "index_version",
)

SCHEMA_CATALOG_HEADER = (
    "source_family",
    "source_detail",
    "file_count",
    "seasons",
    "column_count",
    "header_fingerprint",
    "header_columns",
    "duplicate_header_names",
    "schema_status",
    "example_file",
    "catalog_version",
)

FAMILY_POLICIES = {
    "passing": ("historical_player_evidence", "scoring_allowed"),
    "rushing": ("historical_player_evidence", "scoring_allowed"),
    "receiving": ("historical_player_evidence", "scoring_allowed"),
    "first_downs": ("direct_first_down_scoring_evidence", "scoring_allowed"),
    "returns": ("direct_return_scoring_evidence", "scoring_allowed"),
    "snaps": ("role_evidence", "scoring_allowed_with_confidence_penalty"),
    "alignment": ("role_context", "scoring_allowed_with_confidence_penalty"),
    "te_routes": ("route_evidence", "scoring_allowed_with_confidence_penalty"),
    "targets": ("usage_evidence", "scoring_allowed"),
    "team_pace_proe": ("team_environment_context", "context_only"),
    "team_stats": ("team_environment_context", "context_only"),
    "team_context": ("team_environment_context", "context_only"),
    "depth_charts": ("current_role_context", "context_only"),
    "injuries": ("injury_context", "context_only"),
    "projections": ("projection_context", "review_only"),
    "rankings_context": ("sanity_context", "review_only"),
    "market_context": ("market_context", "context_only"),
    "combine_workout": ("rookie_bridge_context", "review_only"),
    "offensive_line_rankings": ("team_environment_context", "context_only"),
    "team_trends_samples": ("sample_only", "review_only"),
}


@dataclass(frozen=True)
class RotoWireSourceIndexResult:
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_rotowire_source_index(
    raw_root: str | Path = DEFAULT_RAW_ROOT,
) -> RotoWireSourceIndexResult:
    root = Path(raw_root)
    rows: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".csv":
            continue
        relative = path.relative_to(root).as_posix()
        parts = path.relative_to(root).parts
        season = parts[0] if parts and parts[0].isdigit() else ""
        source_family = parts[1] if len(parts) > 1 else "unclassified"
        source_detail = _source_detail(parts, path)
        csv_profile = _profile_csv(path)
        model_lane, allowed_use = FAMILY_POLICIES.get(
            source_family, ("unclassified", "review_only")
        )
        is_canonical = _is_canonical_file(source_family, path.name)
        active_for_intake = is_canonical and source_family not in {
            "team_trends_samples",
            "unclassified",
        }
        inactive_reason = _inactive_reason(source_family, path.name, active_for_intake)
        validation_status = _validation_status(csv_profile)
        rows.append(
            {
                "relative_path": relative,
                "season": season,
                "source_family": source_family,
                "source_detail": source_detail,
                "file_name": path.name,
                "is_canonical_file": is_canonical,
                "active_for_intake": active_for_intake,
                "inactive_reason": inactive_reason,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "csv_rows": csv_profile.get("csv_rows", ""),
                "data_rows": csv_profile.get("data_rows", ""),
                "header_row_index": csv_profile.get("header_row_index", ""),
                "column_count": csv_profile.get("column_count", ""),
                "row_widths": csv_profile.get("row_widths", ""),
                "malformed_row_count": csv_profile.get("malformed_row_count", ""),
                "validation_status": validation_status,
                "model_lane": model_lane,
                "allowed_use": allowed_use,
                "notes": _notes_for(source_family, path.name),
                "index_version": SOURCE_INDEX_VERSION,
            }
        )
    summary = _summary(rows)
    return RotoWireSourceIndexResult(rows=tuple(rows), summary=summary)


def write_rotowire_source_index(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: RotoWireSourceIndexResult | None = None,
    raw_root: str | Path = DEFAULT_RAW_ROOT,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rotowire_source_index(raw_root)
    index_path = output / "rotowire_source_index.csv"
    summary_path = output / "rotowire_source_index_summary.csv"
    schema_path = output / "rotowire_schema_catalog.csv"
    _write_csv(index_path, SOURCE_INDEX_HEADER, result.rows)
    _write_csv(
        summary_path,
        ("metric", "value"),
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    _write_csv(
        schema_path,
        SCHEMA_CATALOG_HEADER,
        build_rotowire_schema_catalog(raw_root=raw_root, index_rows=result.rows),
    )
    return {"index": index_path, "summary": summary_path, "schema": schema_path}


def build_rotowire_schema_catalog(
    *,
    raw_root: str | Path = DEFAULT_RAW_ROOT,
    index_rows: tuple[dict[str, object], ...] | None = None,
) -> tuple[dict[str, object], ...]:
    root = Path(raw_root)
    rows = index_rows or build_rotowire_source_index(root).rows
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        if not row.get("active_for_intake"):
            continue
        key = (str(row["source_family"]), str(row["source_detail"]))
        grouped.setdefault(key, []).append(row)

    catalog: list[dict[str, object]] = []
    for (family, detail), group_rows in sorted(grouped.items()):
        headers = []
        seasons = []
        for row in group_rows:
            path = root / str(row["relative_path"])
            header = _csv_header(path, int(row["header_row_index"]))
            headers.append(header)
            if row.get("season"):
                seasons.append(str(row["season"]))
        fingerprints = {_fingerprint(header) for header in headers}
        first_header = headers[0] if headers else ()
        duplicate_names = _duplicate_header_names(first_header)
        catalog.append(
            {
                "source_family": family,
                "source_detail": detail,
                "file_count": len(group_rows),
                "seasons": "|".join(sorted(set(seasons))),
                "column_count": len(first_header),
                "header_fingerprint": sorted(fingerprints)[0] if fingerprints else "",
                "header_columns": "|".join(first_header),
                "duplicate_header_names": "|".join(duplicate_names),
                "schema_status": "stable" if len(fingerprints) == 1 else "review_header_drift",
                "example_file": str(group_rows[0]["relative_path"]),
                "catalog_version": SCHEMA_CATALOG_VERSION,
            }
        )
    return tuple(catalog)


def _profile_csv(path: Path) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return {
            "csv_rows": 0,
            "data_rows": 0,
            "header_row_index": "",
            "column_count": 0,
            "row_widths": "",
            "malformed_row_count": 0,
        }
    header_index = _header_index(rows)
    header = rows[header_index] if header_index is not None else rows[0]
    data = rows[(header_index + 1) if header_index is not None else 1 :]
    column_count = len(header)
    widths = sorted({len(row) for row in data})
    malformed = sum(1 for row in data if len(row) != column_count)
    return {
        "csv_rows": len(rows),
        "data_rows": len(data),
        "header_row_index": header_index if header_index is not None else 0,
        "column_count": column_count,
        "row_widths": "|".join(str(width) for width in widths),
        "malformed_row_count": malformed,
    }


def _csv_header(path: Path, header_row_index: int) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for index, row in enumerate(csv.reader(handle)):
            if index == header_row_index:
                return tuple(cell.strip() for cell in row)
    return ()


def _fingerprint(header: tuple[str, ...]) -> str:
    normalized = [cell.strip().lower() for cell in header]
    payload = "\x1f".join(normalized).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _duplicate_header_names(header: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for cell in header:
        normalized = cell.strip().lower()
        if normalized in seen:
            duplicates.add(cell.strip())
        seen.add(normalized)
    return tuple(sorted(duplicates))


def _header_index(rows: list[list[str]]) -> int | None:
    for index, row in enumerate(rows[:3]):
        normalized = {cell.strip().lower() for cell in row}
        if {"name", "team"}.issubset(normalized):
            return index
        if "player name" in normalized and "team" in normalized:
            return index
        if "team" in normalized and ("rank" in normalized or "games" in normalized):
            return index
    return 0 if rows else None


def _validation_status(profile: dict[str, object]) -> str:
    malformed = int(profile.get("malformed_row_count") or 0)
    columns = int(profile.get("column_count") or 0)
    if columns == 0:
        return "non_csv_or_empty"
    if malformed:
        return "review_malformed_rows"
    return "clean"


def _source_detail(parts: tuple[str, ...], path: Path) -> str:
    if len(parts) > 2:
        return "/".join(parts[2:-1]) or path.stem
    return path.stem


def _notes_for(source_family: str, file_name: str) -> str:
    if source_family == "projections":
        return "Raw projected stats only; recompute LVE points locally."
    if source_family == "rankings_context":
        return "External ranking sanity context only."
    if source_family == "market_context":
        return "Market context only; never private football value."
    if source_family == "first_downs":
        return "Direct rushing/receiving first-down evidence after source validation."
    if source_family == "returns":
        return "Direct return scoring evidence only; keep small and separate from talent signal."
    if source_family == "injuries":
        return "Sourced negative/risk context only; absence is not healthy evidence."
    if source_family == "depth_charts":
        return "Current role context; parse status suffixes before identity matching."
    if source_family == "combine_workout":
        return "Rookie/prospect bridge context only."
    if source_family == "offensive_line_rankings" and file_name.endswith("_manual.csv"):
        return "Manually structured from pasted RotoWire page."
    return ""


def _is_canonical_file(source_family: str, file_name: str) -> bool:
    canonical_by_family = {
        "passing": {"basic.csv", "advanced.csv", "redzone.csv", "fantasy.csv"},
        "rushing": {"basic.csv", "advanced.csv", "redzone.csv", "fantasy.csv"},
        "receiving": {"basic.csv", "advanced.csv", "redzone.csv", "fantasy.csv"},
        "first_downs": {"receiving_first_downs.csv", "rushing_first_downs.csv"},
        "returns": {"kick_returns.csv", "punt_returns.csv"},
        "snaps": {"snap_counts.csv"},
        "alignment": {"plays.csv"},
        "te_routes": {"te_route_data.csv"},
        "targets": {"target_leaders_weekly.csv"},
        "team_pace_proe": {"pace_pass_rate_over_expectation.csv"},
        "team_stats": {"overall_team_stats.csv", "overall_opponent_team_stats.csv"},
        "team_context": {"rotowire_team_rankings.csv"},
        "projections": {"rotowire_full_season_raw_stat_projections.csv"},
        "depth_charts": {
            "depthcharts_by_pos_qb.csv",
            "depthcharts_by_pos_rb.csv",
            "depthcharts_by_pos_wr.csv",
            "depthcharts_by_pos_te.csv",
        },
        "injuries": {
            "qb_injury_report.csv",
            "rb_injury_report.csv",
            "wr_injury_report.csv",
            "te_injury_report.csv",
        },
        "rankings_context": {
            "rotowire_dynasty_cheatsheet_overall.csv",
            "rotowire_standard_cheatsheet_overall.csv",
        },
        "market_context": {"rotowire_early_adp_all.csv"},
        "combine_workout": {
            "workout_stats_qb.csv",
            "workout_stats_rb.csv",
            "workout_stats_wr.csv",
            "workout_stats_te.csv",
        },
        "offensive_line_rankings": {"rotowire_offensive_line_rankings_manual.csv"},
        "team_trends_samples": {"nfl_trends_snapcount_sample.csv"},
    }
    return file_name in canonical_by_family.get(source_family, {file_name})


def _inactive_reason(source_family: str, file_name: str, active_for_intake: bool) -> str:
    if active_for_intake:
        return ""
    if source_family == "unclassified":
        return "unclassified_not_active_for_intake"
    if source_family == "team_trends_samples":
        return "sample_only_not_full_league_source"
    if not _is_canonical_file(source_family, file_name):
        return "duplicate_raw_export_preserved_but_not_read"
    return "inactive_by_policy"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _summary(rows: list[dict[str, object]]) -> dict[str, object]:
    by_family: dict[str, int] = {}
    by_allowed_use: dict[str, int] = {}
    clean_count = 0
    active_count = 0
    for row in rows:
        family = str(row["source_family"])
        allowed_use = str(row["allowed_use"])
        by_family[family] = by_family.get(family, 0) + 1
        by_allowed_use[allowed_use] = by_allowed_use.get(allowed_use, 0) + 1
        if row["validation_status"] == "clean":
            clean_count += 1
        if row["active_for_intake"]:
            active_count += 1
    return {
        "index_version": SOURCE_INDEX_VERSION,
        "file_count": len(rows),
        "clean_file_count": clean_count,
        "review_file_count": len(rows) - clean_count,
        "active_file_count": active_count,
        "inactive_file_count": len(rows) - active_count,
        "families": ";".join(f"{key}:{value}" for key, value in sorted(by_family.items())),
        "allowed_uses": ";".join(
            f"{key}:{value}" for key, value in sorted(by_allowed_use.items())
        ),
    }


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | object,
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
