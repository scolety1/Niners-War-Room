from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CANONICAL_INDEX = Path(
    "local_exports/model_v4/raw_user_exports/fantasypros_advanced/"
    "FANTASYPROS_ADVANCED_CANONICAL_FILE_INDEX.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/historical_fantasypros_advanced/latest")

SOURCE_NAME = "FantasyPros Advanced Stats Export"
SOURCE_STATUS = "imported_real_data"

COMMON_OUTPUT_HEADER = (
    "season",
    "position",
    "player_name",
    "nfl_team",
    "games",
    "source_rank",
    "source_name",
    "source_status",
    "source_file",
    "source_hash",
    "validation_status",
    "validation_warnings",
    "model_intake_role",
)

FANTASYPROS_ADVANCED_CLEAN_HEADER = COMMON_OUTPUT_HEADER + (
    "completions",
    "pass_attempts",
    "completion_pct",
    "passing_yards",
    "passing_yards_per_attempt",
    "passing_air_yards",
    "passing_air_yards_per_attempt",
    "passing_10_plus",
    "passing_20_plus",
    "passing_30_plus",
    "passing_40_plus",
    "passing_50_plus",
    "pocket_time",
    "sacks",
    "knockdowns",
    "hurries",
    "blitzes",
    "poor_throws",
    "dropped_passes",
    "red_zone_pass_attempts",
    "passer_rating",
    "rushing_attempts",
    "rushing_yards",
    "rushing_yards_per_attempt",
    "rushing_yards_before_contact",
    "rushing_yards_before_contact_per_attempt",
    "rushing_yards_after_contact",
    "rushing_yards_after_contact_per_attempt",
    "broken_tackles",
    "tackles_for_loss",
    "tackles_for_loss_yards",
    "long_touchdown",
    "rushing_10_plus",
    "rushing_20_plus",
    "rushing_30_plus",
    "rushing_40_plus",
    "rushing_50_plus",
    "long_rush",
    "receptions",
    "targets",
    "red_zone_targets",
    "receiving_yards_after_contact_or_yac_context",
    "receiving_yards",
    "receiving_yards_per_reception",
    "receiving_yards_before_catch",
    "receiving_yards_before_catch_per_reception",
    "receiving_air_yards",
    "receiving_air_yards_per_reception",
    "receiving_yards_after_catch",
    "receiving_yards_after_catch_per_reception",
    "receiving_yards_after_contact",
    "receiving_yards_after_contact_per_reception",
    "team_target_share_pct",
    "catchable_targets",
    "drops",
    "receiving_10_plus",
    "receiving_20_plus",
    "receiving_30_plus",
    "receiving_40_plus",
    "receiving_50_plus",
    "long_reception",
)

FANTASYPROS_ADVANCED_VALIDATION_HEADER = (
    "season",
    "position",
    "source_file",
    "source_hash",
    "index_hash",
    "index_hash_match",
    "raw_row_count",
    "index_row_count",
    "raw_column_count",
    "index_column_count",
    "duplicate_headers",
    "validation_status",
    "cleaned_rows",
    "row_length_issues",
    "player_parse_warnings",
    "numeric_warnings",
    "notes",
)

FANTASYPROS_ADVANCED_SUMMARY_HEADER = ("metric", "value")

QB_FIELD_MAP = (
    ("RK", "source_rank"),
    ("Player", "player"),
    ("G", "games"),
    ("COMP", "completions"),
    ("ATT", "pass_attempts"),
    ("PCT", "completion_pct"),
    ("YDS", "passing_yards"),
    ("Y/A", "passing_yards_per_attempt"),
    ("AIR", "passing_air_yards"),
    ("AIR/A", "passing_air_yards_per_attempt"),
    ("10+ YDS", "passing_10_plus"),
    ("20+ YDS", "passing_20_plus"),
    ("30+ YDS", "passing_30_plus"),
    ("40+ YDS", "passing_40_plus"),
    ("50+ YDS", "passing_50_plus"),
    ("PKT TIME", "pocket_time"),
    ("SACK", "sacks"),
    ("KNCK", "knockdowns"),
    ("HRRY", "hurries"),
    ("BLITZ", "blitzes"),
    ("POOR", "poor_throws"),
    ("DROP", "dropped_passes"),
    ("RZ ATT", "red_zone_pass_attempts"),
    ("RTG", "passer_rating"),
)

RB_FIELD_MAP = (
    ("RK", "source_rank"),
    ("Player", "player"),
    ("G", "games"),
    ("ATT", "rushing_attempts"),
    ("YDS", "rushing_yards"),
    ("Y/ATT", "rushing_yards_per_attempt"),
    ("YBCON", "rushing_yards_before_contact"),
    ("YBCON/ATT", "rushing_yards_before_contact_per_attempt"),
    ("YACON", "rushing_yards_after_contact"),
    ("YACON/ATT", "rushing_yards_after_contact_per_attempt"),
    ("BRKTKL", "broken_tackles"),
    ("TK LOSS", "tackles_for_loss"),
    ("TK LOSS YDS", "tackles_for_loss_yards"),
    ("LNG TD", "long_touchdown"),
    ("10+ YDS", "rushing_10_plus"),
    ("20+ YDS", "rushing_20_plus"),
    ("30+ YDS", "rushing_30_plus"),
    ("40+ YDS", "rushing_40_plus"),
    ("50+ YDS", "rushing_50_plus"),
    ("LNG", "long_rush"),
    ("REC", "receptions"),
    ("TGT", "targets"),
    ("RZ TGT", "red_zone_targets"),
    ("YACON", "receiving_yards_after_contact_or_yac_context"),
)

RECEIVING_FIELD_MAP = (
    ("RK", "source_rank"),
    ("Player", "player"),
    ("G", "games"),
    ("REC", "receptions"),
    ("YDS", "receiving_yards"),
    ("Y/R", "receiving_yards_per_reception"),
    ("YBC", "receiving_yards_before_catch"),
    ("YBC/R", "receiving_yards_before_catch_per_reception"),
    ("AIR", "receiving_air_yards"),
    ("AIR/R", "receiving_air_yards_per_reception"),
    ("YAC", "receiving_yards_after_catch"),
    ("YAC/R", "receiving_yards_after_catch_per_reception"),
    ("YACON", "receiving_yards_after_contact"),
    ("YACON/R", "receiving_yards_after_contact_per_reception"),
    ("BRKTKL", "broken_tackles"),
    ("TGT", "targets"),
    ("% TM", "team_target_share_pct"),
    ("CATCHABLE", "catchable_targets"),
    ("DROP", "drops"),
    ("RZ TGT", "red_zone_targets"),
    ("10+ YDS", "receiving_10_plus"),
    ("20+ YDS", "receiving_20_plus"),
    ("30+ YDS", "receiving_30_plus"),
    ("40+ YDS", "receiving_40_plus"),
    ("50+ YDS", "receiving_50_plus"),
    ("LNG", "long_reception"),
)

POSITION_FIELD_MAPS = {
    "QB": QB_FIELD_MAP,
    "RB": RB_FIELD_MAP,
    "WR": RECEIVING_FIELD_MAP,
    "TE": RECEIVING_FIELD_MAP,
}

TEAM_CODES = {
    "ARI",
    "ATL",
    "BAL",
    "BUF",
    "CAR",
    "CHI",
    "CIN",
    "CLE",
    "DAL",
    "DEN",
    "DET",
    "FA",
    "GB",
    "HOU",
    "IND",
    "JAC",
    "JAX",
    "KC",
    "LA",
    "LAC",
    "LAR",
    "LV",
    "MIA",
    "MIN",
    "NE",
    "NO",
    "NYG",
    "NYJ",
    "OAK",
    "PHI",
    "PIT",
    "SD",
    "SEA",
    "SF",
    "STL",
    "TB",
    "TEN",
    "WAS",
    "WSH",
}


@dataclass(frozen=True)
class FantasyProsAdvancedIntakeResult:
    clean_rows: tuple[dict[str, object], ...]
    validation_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_fantasypros_advanced_intake(
    canonical_index_path: str | Path = DEFAULT_CANONICAL_INDEX,
) -> FantasyProsAdvancedIntakeResult:
    index_rows = _read_index(Path(canonical_index_path))
    clean_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []

    for index_row in index_rows:
        position = str(index_row.get("position") or "").strip().upper()
        if position not in POSITION_FIELD_MAPS:
            validation_rows.append(_unsupported_position_validation(index_row))
            continue
        source_path = Path(str(index_row.get("canonical_file") or ""))
        file_result = _clean_canonical_file(index_row, source_path, position)
        clean_rows.extend(file_result.clean_rows)
        validation_rows.append(file_result.validation_row)

    summary = _summary(clean_rows, validation_rows, canonical_index_path)
    return FantasyProsAdvancedIntakeResult(
        clean_rows=tuple(clean_rows),
        validation_rows=tuple(validation_rows),
        summary=summary,
    )


def write_fantasypros_advanced_intake_outputs(
    output_root: str | Path,
    result: FantasyProsAdvancedIntakeResult,
) -> dict[str, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "clean": root / "fantasypros_advanced_clean_rows.csv",
        "validation": root / "fantasypros_advanced_validation_report.csv",
        "summary_csv": root / "fantasypros_advanced_summary.csv",
        "summary_json": root / "fantasypros_advanced_summary.json",
    }
    _write_csv(paths["clean"], FANTASYPROS_ADVANCED_CLEAN_HEADER, result.clean_rows)
    _write_csv(
        paths["validation"],
        FANTASYPROS_ADVANCED_VALIDATION_HEADER,
        result.validation_rows,
    )
    _write_csv(
        paths["summary_csv"],
        FANTASYPROS_ADVANCED_SUMMARY_HEADER,
        [{"metric": key, "value": value} for key, value in result.summary.items()],
    )
    paths["summary_json"].write_text(
        json.dumps(result.summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


@dataclass(frozen=True)
class _FileCleanResult:
    clean_rows: tuple[dict[str, object], ...]
    validation_row: dict[str, object]


def _clean_canonical_file(
    index_row: dict[str, str],
    source_path: Path,
    position: str,
) -> _FileCleanResult:
    season = _int(index_row.get("season"))
    source_hash = _sha256(source_path) if source_path.exists() else ""
    index_hash = str(index_row.get("sha256") or "").strip().upper()
    field_map = POSITION_FIELD_MAPS[position]
    notes: list[str] = []
    clean_rows: list[dict[str, object]] = []
    row_length_issues = 0
    player_parse_warnings = 0
    numeric_warnings = 0

    if not source_path.exists():
        return _FileCleanResult(
            clean_rows=(),
            validation_row=_validation_row(
                index_row,
                source_hash=source_hash,
                raw_row_count=0,
                raw_column_count=0,
                cleaned_rows=0,
                row_length_issues=0,
                player_parse_warnings=0,
                numeric_warnings=0,
                validation_status="missing_source_file",
                notes="canonical_file_not_found",
            ),
        )

    header, raw_rows = _read_raw_rows(source_path)
    if len(header) != len(field_map):
        notes.append("header_length_does_not_match_position_schema")
    if position == "RB":
        notes.append("rb_duplicate_yacon_disambiguated_second_context_only")

    for row_number, values in enumerate(raw_rows, start=2):
        warnings: list[str] = []
        if len(values) != len(field_map):
            row_length_issues += 1
            warnings.append(f"row_length_{len(values)}_expected_{len(field_map)}")
        mapped = _mapped_values(field_map, values)
        player_name, nfl_team, player_warning = parse_player_team(str(mapped.get("player") or ""))
        if player_warning:
            player_parse_warnings += 1
            warnings.append(player_warning)

        output = _empty_output_row(
            season=season,
            position=position,
            player_name=player_name,
            nfl_team=nfl_team,
            source_file=source_path,
            source_hash=source_hash,
            validation_status=_clean_row_status(index_row, position, warnings),
            validation_warnings="|".join(warnings),
            model_intake_role=str(index_row.get("model_intake_role") or ""),
        )
        for _, output_field in field_map:
            if output_field == "player":
                continue
            normalized, warning = normalize_numeric(mapped.get(output_field))
            output[output_field] = normalized
            if warning:
                numeric_warnings += 1
                warnings.append(f"row_{row_number}_{output_field}_{warning}")
        if warnings:
            output["validation_warnings"] = "|".join(warnings)
            if output["validation_status"] == "clean":
                output["validation_status"] = "review_needed"
        clean_rows.append(output)

    validation_status = _file_validation_status(
        index_row=index_row,
        position=position,
        header=header,
        field_map=field_map,
        row_length_issues=row_length_issues,
        source_hash=source_hash,
        index_hash=index_hash,
    )
    return _FileCleanResult(
        clean_rows=tuple(clean_rows),
        validation_row=_validation_row(
            index_row,
            source_hash=source_hash,
            raw_row_count=len(raw_rows),
            raw_column_count=len(header),
            cleaned_rows=len(clean_rows),
            row_length_issues=row_length_issues,
            player_parse_warnings=player_parse_warnings,
            numeric_warnings=numeric_warnings,
            validation_status=validation_status,
            notes="|".join(notes),
        ),
    )


def parse_player_team(value: str) -> tuple[str, str, str]:
    raw = re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()
    spaced_match = re.match(r"^(?P<name>.*?)\s{2,}(?P<team>[A-Z]{2,3}|FA)$", value.strip())
    if spaced_match:
        return (
            re.sub(r"\s+", " ", spaced_match.group("name")).strip(),
            spaced_match.group("team").strip(),
            "",
        )
    if raw:
        parts = raw.rsplit(" ", 1)
        if len(parts) == 2 and parts[1] in TEAM_CODES:
            return parts[0].strip(), parts[1].strip(), "team_suffix_single_space_fallback"
    return raw, "", "team_suffix_missing"


def normalize_numeric(value: object) -> tuple[float | int | str, str]:
    raw = str(value or "").strip()
    if raw in {"", "-", "--", "N/A", "NA"}:
        return "", ""
    cleaned = raw.replace(",", "")
    if cleaned.endswith("%"):
        cleaned = cleaned[:-1]
    try:
        number = float(cleaned)
    except ValueError:
        return raw, "non_numeric_value"
    if number.is_integer():
        return int(number), ""
    return round(number, 3), ""


def _read_index(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _read_raw_rows(path: Path) -> tuple[tuple[str, ...], list[list[str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = tuple(next(reader, ()))
        return header, [row for row in reader if any(str(cell).strip() for cell in row)]


def _mapped_values(
    field_map: tuple[tuple[str, str], ...],
    values: list[str],
) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for index, (_, output_field) in enumerate(field_map):
        mapped[output_field] = values[index] if index < len(values) else ""
    return mapped


def _empty_output_row(
    *,
    season: int,
    position: str,
    player_name: str,
    nfl_team: str,
    source_file: Path,
    source_hash: str,
    validation_status: str,
    validation_warnings: str,
    model_intake_role: str,
) -> dict[str, object]:
    row = {field: "" for field in FANTASYPROS_ADVANCED_CLEAN_HEADER}
    row.update(
        {
            "season": season,
            "position": position,
            "player_name": player_name,
            "nfl_team": nfl_team,
            "source_name": SOURCE_NAME,
            "source_status": SOURCE_STATUS,
            "source_file": str(source_file),
            "source_hash": source_hash,
            "validation_status": validation_status,
            "validation_warnings": validation_warnings,
            "model_intake_role": model_intake_role,
        }
    )
    return row


def _clean_row_status(
    index_row: dict[str, str],
    position: str,
    warnings: list[str],
) -> str:
    if warnings:
        return "review_needed"
    if position == "RB" or str(index_row.get("duplicate_headers") or "").strip():
        return "cleaned_with_header_disambiguation"
    return "clean"


def _file_validation_status(
    *,
    index_row: dict[str, str],
    position: str,
    header: tuple[str, ...],
    field_map: tuple[tuple[str, str], ...],
    row_length_issues: int,
    source_hash: str,
    index_hash: str,
) -> str:
    if source_hash and index_hash and source_hash != index_hash:
        return "review_needed_hash_mismatch"
    if len(header) != len(field_map) or row_length_issues:
        return "review_needed"
    if position == "RB" or str(index_row.get("duplicate_headers") or "").strip():
        return "cleaned_with_header_disambiguation"
    return "clean"


def _validation_row(
    index_row: dict[str, str],
    *,
    source_hash: str,
    raw_row_count: int,
    raw_column_count: int,
    cleaned_rows: int,
    row_length_issues: int,
    player_parse_warnings: int,
    numeric_warnings: int,
    validation_status: str,
    notes: str,
) -> dict[str, object]:
    index_hash = str(index_row.get("sha256") or "").strip().upper()
    return {
        "season": _int(index_row.get("season")),
        "position": str(index_row.get("position") or ""),
        "source_file": str(index_row.get("canonical_file") or ""),
        "source_hash": source_hash,
        "index_hash": index_hash,
        "index_hash_match": bool(source_hash and index_hash and source_hash == index_hash),
        "raw_row_count": raw_row_count,
        "index_row_count": _int(index_row.get("row_count")),
        "raw_column_count": raw_column_count,
        "index_column_count": _int(index_row.get("column_count")),
        "duplicate_headers": str(index_row.get("duplicate_headers") or ""),
        "validation_status": validation_status,
        "cleaned_rows": cleaned_rows,
        "row_length_issues": row_length_issues,
        "player_parse_warnings": player_parse_warnings,
        "numeric_warnings": numeric_warnings,
        "notes": notes,
    }


def _unsupported_position_validation(index_row: dict[str, str]) -> dict[str, object]:
    return _validation_row(
        index_row,
        source_hash="",
        raw_row_count=0,
        raw_column_count=0,
        cleaned_rows=0,
        row_length_issues=0,
        player_parse_warnings=0,
        numeric_warnings=0,
        validation_status="unsupported_position",
        notes="position_not_supported_for_fantasypros_advanced_intake",
    )


def _summary(
    clean_rows: list[dict[str, object]],
    validation_rows: list[dict[str, object]],
    canonical_index_path: str | Path,
) -> dict[str, object]:
    seasons = sorted({str(row.get("season")) for row in clean_rows if row.get("season")})
    positions = sorted({str(row.get("position")) for row in clean_rows if row.get("position")})
    return {
        "status": "ready" if clean_rows else "blocked",
        "review_status": "review_only",
        "source_name": SOURCE_NAME,
        "source_status": SOURCE_STATUS,
        "canonical_index_path": str(canonical_index_path),
        "canonical_files_read": len(validation_rows),
        "cleaned_rows": len(clean_rows),
        "seasons": "|".join(seasons),
        "positions": "|".join(positions),
        "validation_rows": len(validation_rows),
        "validation_rows_requiring_review": sum(
            1
            for row in validation_rows
            if "review" in str(row.get("validation_status") or "")
            or str(row.get("validation_status") or "").startswith("missing")
        ),
        "rb_duplicate_yacon_policy": (
            "first YACON is rushing_yards_after_contact; "
            "second YACON is receiving_yards_after_contact_or_yac_context and context-only"
        ),
        "fantasypros_advanced_stats_are_projections": False,
        "active_rankings_overwritten": False,
        "model_scores_changed": False,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0
