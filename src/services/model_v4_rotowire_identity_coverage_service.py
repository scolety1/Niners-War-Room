from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_fantasypros_identity_mapping_service import normalize_player_name

DEFAULT_TRUTH_SET = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")
DEFAULT_PLAYER_STATS = Path(
    "local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv"
)
DEFAULT_RAW_ROOT = Path("local_exports/model_v4/raw_user_exports/rotowire_manual")
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/rotowire_intake/latest")

IDENTITY_COVERAGE_VERSION = "model_v4_rotowire_identity_coverage_0.1.0"

IDENTITY_COVERAGE_HEADER = (
    "truth_player_name",
    "normalized_player_name",
    "position",
    "expected_team",
    "source_priority",
    "player_stats_rows",
    "projection_rows",
    "dynasty_rank_rows",
    "standard_rank_rows",
    "adp_rows",
    "depth_chart_rows",
    "injury_rows",
    "combine_workout_rows",
    "matched_source_names",
    "coverage_status",
    "warning",
    "coverage_version",
)


@dataclass(frozen=True)
class RotoWireIdentityCoverageResult:
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_rotowire_identity_coverage(
    *,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET,
    player_stats_path: str | Path = DEFAULT_PLAYER_STATS,
    raw_root: str | Path = DEFAULT_RAW_ROOT,
) -> RotoWireIdentityCoverageResult:
    truth_rows = _read_dict_rows(Path(truth_set_path))
    root = Path(raw_root)
    source_maps = {
        "player_stats_rows": _name_counts_from_dict_csv(
            Path(player_stats_path), "player_name"
        ),
        "projection_rows": _name_counts_from_two_header_csv(
            root / "2026/projections/rotowire_full_season_raw_stat_projections.csv",
            "Name",
        ),
        "dynasty_rank_rows": _name_counts_from_two_header_csv(
            root / "2026/rankings_context/rotowire_dynasty_cheatsheet_overall.csv",
            "Player Name",
        ),
        "standard_rank_rows": _name_counts_from_two_header_csv(
            root / "2026/rankings_context/rotowire_standard_cheatsheet_overall.csv",
            "Player Name",
        ),
        "adp_rows": _name_counts_from_two_header_csv(
            root / "2026/market_context/rotowire_early_adp_all.csv",
            "Name",
        ),
        "depth_chart_rows": _name_counts_from_depth_charts(root / "2026/depth_charts"),
        "injury_rows": _name_counts_from_injuries(root / "2026/injuries"),
        "combine_workout_rows": _name_counts_from_workouts(root / "2026/combine_workout"),
    }
    source_names = _source_names(source_maps)

    rows: list[dict[str, object]] = []
    for truth in truth_rows:
        normalized = normalize_player_name(truth["player_name"])
        counts = {
            key: source_map.get(normalized, 0)
            for key, source_map in source_maps.items()
        }
        matched_names = sorted(source_names.get(normalized, set()))
        coverage_status, warning = _coverage_status(counts)
        rows.append(
            {
                "truth_player_name": truth["player_name"],
                "normalized_player_name": normalized,
                "position": truth["position"],
                "expected_team": truth.get("nfl_team", ""),
                "source_priority": truth.get("source_priority", ""),
                **counts,
                "matched_source_names": "|".join(matched_names),
                "coverage_status": coverage_status,
                "warning": warning,
                "coverage_version": IDENTITY_COVERAGE_VERSION,
            }
        )

    summary = {
        "coverage_version": IDENTITY_COVERAGE_VERSION,
        "truth_player_count": len(rows),
        "covered_player_count": sum(1 for row in rows if row["coverage_status"] == "covered"),
        "review_player_count": sum(1 for row in rows if row["coverage_status"] != "covered"),
        "model_scores_changed": False,
    }
    return RotoWireIdentityCoverageResult(rows=tuple(rows), summary=summary)


def write_rotowire_identity_coverage_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: RotoWireIdentityCoverageResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rotowire_identity_coverage()
    coverage_path = output / "rotowire_truth_set_identity_coverage.csv"
    summary_path = output / "rotowire_truth_set_identity_coverage_summary.csv"
    _write_csv(coverage_path, IDENTITY_COVERAGE_HEADER, result.rows)
    _write_csv(
        summary_path,
        ("metric", "value"),
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    return {"coverage": coverage_path, "summary": summary_path}


def _coverage_status(counts: dict[str, int]) -> tuple[str, str]:
    if counts["player_stats_rows"] or counts["projection_rows"] or counts["dynasty_rank_rows"]:
        return "covered", ""
    if counts["combine_workout_rows"]:
        return "rookie_context_only", "no_nfl_or_projection_rows"
    return "review_missing", "no_rotowire_rows_found"


def _name_counts_from_dict_csv(path: Path, name_column: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not path.exists():
        return counts
    for row in _read_dict_rows(path):
        _add_name(counts, row.get(name_column, ""))
    return counts


def _name_counts_from_two_header_csv(path: Path, name_column: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not path.exists():
        return counts
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2:
        return counts
    header = rows[1]
    if name_column not in header:
        return counts
    index = header.index(name_column)
    for row in rows[2:]:
        if len(row) > index:
            _add_name(counts, row[index])
    return counts


def _name_counts_from_depth_charts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for file_path in sorted(path.glob("*.csv")):
        with file_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
        for row in rows[1:]:
            for cell in row[1:]:
                _add_name(counts, _strip_status_suffix(cell))
    return counts


def _name_counts_from_injuries(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for file_path in sorted(path.glob("*.csv")):
        for row in _read_dict_rows(file_path):
            _add_name(counts, row.get("Player", ""))
    return counts


def _name_counts_from_workouts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for file_path in sorted(path.glob("*.csv")):
        with file_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
        if len(rows) < 2:
            continue
        header = rows[1]
        if "Name" not in header:
            continue
        index = header.index("Name")
        for row in rows[2:]:
            if len(row) > index:
                _add_name(counts, row[index])
    return counts


def _source_names(source_maps: dict[str, dict[str, int]]) -> dict[str, set[str]]:
    names: dict[str, set[str]] = {}
    raw_root = DEFAULT_RAW_ROOT
    files = [
        DEFAULT_PLAYER_STATS,
        raw_root / "2026/projections/rotowire_full_season_raw_stat_projections.csv",
        raw_root / "2026/rankings_context/rotowire_dynasty_cheatsheet_overall.csv",
        raw_root / "2026/rankings_context/rotowire_standard_cheatsheet_overall.csv",
        raw_root / "2026/market_context/rotowire_early_adp_all.csv",
    ]
    for file_path in files:
        if not file_path.exists():
            continue
        for value in _all_name_values(file_path):
            normalized = normalize_player_name(value)
            if normalized:
                names.setdefault(normalized, set()).add(value)
    return names


def _all_name_values(path: Path) -> tuple[str, ...]:
    if path == DEFAULT_PLAYER_STATS:
        return tuple(row["player_name"] for row in _read_dict_rows(path))
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2:
        return ()
    header = rows[1]
    name_column = "Player Name" if "Player Name" in header else "Name"
    if name_column not in header:
        return ()
    index = header.index(name_column)
    return tuple(row[index] for row in rows[2:] if len(row) > index)


def _strip_status_suffix(value: str) -> str:
    return str(value).split(" - ", 1)[0].strip()


def _add_name(counts: dict[str, int], value: object) -> None:
    normalized = normalize_player_name(value)
    if not normalized:
        return
    counts[normalized] = counts.get(normalized, 0) + 1


def _read_dict_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
