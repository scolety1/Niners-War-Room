from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_fantasypros_identity_mapping_service import (
    ModelIdentityCandidate,
    build_model_identity_candidates,
    normalize_player_name,
)
from src.services.model_v4_rotowire_player_stats_intake_service import (
    build_rotowire_player_stats_intake,
)
from src.services.model_v4_rotowire_source_index_service import DEFAULT_RAW_ROOT

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/first_downs/latest")

FIRST_DOWN_CANONICALIZATION_VERSION = "model_v4_first_down_canonicalization_0.1.0"

RUSHING_HEADER = (
    "season",
    "player_name",
    "normalized_player_name",
    "nfl_team",
    "position",
    "rotowire_player_id",
    "matched_model_player",
    "sleeper_id",
    "gsis_id",
    "join_status",
    "join_method",
    "join_confidence",
    "rushing_yards",
    "rushing_attempts",
    "rushing_touchdowns",
    "rushing_20_plus",
    "rushing_40_plus",
    "rushing_long",
    "rushing_first_downs",
    "rushing_first_down_rate",
    "rushing_fumbles",
    "source_name",
    "source_status",
    "source_file",
    "source_hash",
    "validation_status",
    "cleanup_warnings",
    "canonicalization_version",
)

RECEIVING_HEADER = (
    "season",
    "player_name",
    "normalized_player_name",
    "nfl_team",
    "position",
    "rotowire_player_id",
    "matched_model_player",
    "sleeper_id",
    "gsis_id",
    "join_status",
    "join_method",
    "join_confidence",
    "receptions",
    "receiving_yards",
    "receiving_touchdowns",
    "receiving_20_plus",
    "receiving_40_plus",
    "receiving_long",
    "receiving_first_downs",
    "receiving_first_down_rate",
    "receiving_fumbles",
    "receiving_yards_after_catch_context",
    "targets",
    "source_name",
    "source_status",
    "source_file",
    "source_hash",
    "validation_status",
    "cleanup_warnings",
    "canonicalization_version",
)

VALIDATION_HEADER = (
    "season",
    "stat_family",
    "source_file",
    "source_hash",
    "raw_rows",
    "header_present",
    "header_inferred",
    "repeated_header_rows_removed",
    "exact_duplicate_rows_removed",
    "malformed_rows_removed",
    "clean_rows",
    "imported_real_data_rows",
    "matched_rows",
    "missing_join_rows",
    "ambiguous_join_rows",
    "numeric_issue_rows",
    "validation_status",
    "notes",
    "canonicalization_version",
)

RECEIPT_HEADER = (
    "season",
    "player_name",
    "normalized_player_name",
    "stat_family",
    "component",
    "source_status",
    "source_file",
    "source_hash",
    "raw_fields_json",
    "normalized_fields_json",
    "join_status",
    "warning",
    "canonicalization_version",
)

COVERAGE_HEADER = (
    "season",
    "player_name",
    "normalized_player_name",
    "stat_family",
    "has_first_down_evidence",
    "source_status",
    "source_file",
    "source_hash",
    "join_status",
    "coverage_status",
    "warning",
    "canonicalization_version",
)

SUMMARY_HEADER = ("metric", "value")

EXPECTED_RAW_HEADERS = {
    "rushing": (
        "Player",
        "Rush Yds",
        "Att",
        "TD",
        "20+",
        "40+",
        "Lng",
        "Rush 1st",
        "Rush 1st%",
        "Rush FUM",
    ),
    "receiving": (
        "Player",
        "Rec",
        "Yds",
        "TD",
        "20+",
        "40+",
        "LNG",
        "Rec 1st",
        "1st%",
        "Rec FUM",
        "Rec YAC/R",
        "Tgts",
    ),
}

TEAM_ALIASES = {
    "JAC": "JAX",
    "LA": "LAR",
    "STL": "LAR",
    "SD": "LAC",
    "OAK": "LV",
    "WSH": "WAS",
}


@dataclass(frozen=True)
class CanonicalFirstDownResult:
    rushing_rows: tuple[dict[str, object], ...]
    receiving_rows: tuple[dict[str, object], ...]
    validation_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    coverage_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class _SourceFileProfile:
    rows: tuple[dict[str, str], ...]
    source_file: str
    source_hash: str
    raw_rows: int
    header_present: bool
    header_inferred: bool
    repeated_header_rows_removed: int
    exact_duplicate_rows_removed: int
    malformed_rows_removed: int
    numeric_issue_rows: int


@dataclass(frozen=True)
class _RotoWireIdentity:
    player_name: str
    rotowire_player_id: str
    nfl_team: str
    position: str


def build_canonical_first_downs(
    *,
    raw_root: str | Path = DEFAULT_RAW_ROOT,
) -> CanonicalFirstDownResult:
    root = Path(raw_root)
    rotowire_lookup = _build_rotowire_identity_lookup(raw_root=root)
    model_resolver = _ModelIdentityResolver(build_model_identity_candidates())

    rushing_rows: list[dict[str, object]] = []
    receiving_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []
    receipt_rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []

    source_specs = (
        ("2024", "rushing", root / "2024" / "first_downs" / "rushing_first_downs.csv"),
        ("2025", "rushing", root / "2025" / "first_downs" / "rushing_first_downs.csv"),
        (
            "2024",
            "receiving",
            root / "2024" / "first_downs" / "receiving_first_downs.csv",
        ),
        (
            "2025",
            "receiving",
            root / "2025" / "first_downs" / "receiving_first_downs.csv",
        ),
    )
    for season, stat_family, path in source_specs:
        profile = _parse_source_file(path, root=root, stat_family=stat_family)
        parsed_rows = []
        for raw_row in profile.rows:
            canonical = _canonical_row(
                season=season,
                stat_family=stat_family,
                raw_row=raw_row,
                source_file=profile.source_file,
                source_hash=profile.source_hash,
                rotowire_lookup=rotowire_lookup,
                model_resolver=model_resolver,
            )
            parsed_rows.append(canonical)
            receipt_rows.append(_receipt_row(canonical, raw_row, stat_family))
            coverage_rows.append(_coverage_row(canonical, stat_family))
        if stat_family == "rushing":
            rushing_rows.extend(parsed_rows)
        else:
            receiving_rows.extend(parsed_rows)
        validation_rows.append(_validation_row(season, stat_family, profile, parsed_rows))

    summary = {
        "canonicalization_version": FIRST_DOWN_CANONICALIZATION_VERSION,
        "rushing_row_count": len(rushing_rows),
        "receiving_row_count": len(receiving_rows),
        "validation_file_count": len(validation_rows),
        "receipt_row_count": len(receipt_rows),
        "coverage_row_count": len(coverage_rows),
        "imported_real_data_rows": sum(
            1
            for row in (*rushing_rows, *receiving_rows)
            if row["source_status"] == "imported_real_data"
        ),
        "admitted_rushing_rows": sum(
            1 for row in rushing_rows if row["join_status"] == "matched"
        ),
        "admitted_receiving_rows": sum(
            1 for row in receiving_rows if row["join_status"] == "matched"
        ),
        "missing_join_rows": sum(
            1 for row in (*rushing_rows, *receiving_rows) if row["join_status"] == "missing_join"
        ),
        "ambiguous_join_rows": sum(
            1 for row in (*rushing_rows, *receiving_rows) if row["join_status"] == "ambiguous_join"
        ),
        "model_scores_changed": False,
        "active_rankings_overwritten": False,
        "review_only": True,
    }
    return CanonicalFirstDownResult(
        rushing_rows=tuple(rushing_rows),
        receiving_rows=tuple(receiving_rows),
        validation_rows=tuple(validation_rows),
        receipt_rows=tuple(receipt_rows),
        coverage_rows=tuple(coverage_rows),
        summary=summary,
    )


def write_canonical_first_down_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: CanonicalFirstDownResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_canonical_first_downs()
    paths = {
        "rushing": output / "canonical_rushing_first_downs.csv",
        "receiving": output / "canonical_receiving_first_downs.csv",
        "admitted_rushing": output / "admitted_rushing_first_downs.csv",
        "admitted_receiving": output / "admitted_receiving_first_downs.csv",
        "validation": output / "first_down_canonicalization_validation.csv",
        "receipts": output / "first_down_receipts.csv",
        "coverage": output / "first_down_source_coverage.csv",
        "summary": output / "first_down_canonicalization_summary.csv",
    }
    _write_csv(paths["rushing"], RUSHING_HEADER, result.rushing_rows)
    _write_csv(paths["receiving"], RECEIVING_HEADER, result.receiving_rows)
    _write_csv(paths["admitted_rushing"], RUSHING_HEADER, _matched_rows(result.rushing_rows))
    _write_csv(
        paths["admitted_receiving"],
        RECEIVING_HEADER,
        _matched_rows(result.receiving_rows),
    )
    _write_csv(paths["validation"], VALIDATION_HEADER, result.validation_rows)
    _write_csv(paths["receipts"], RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths["coverage"], COVERAGE_HEADER, result.coverage_rows)
    _write_csv(
        paths["summary"],
        SUMMARY_HEADER,
        [{"metric": key, "value": value} for key, value in result.summary.items()],
    )
    return paths


def _matched_rows(rows: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    return [row for row in rows if row.get("join_status") == "matched"]


def _parse_source_file(path: Path, *, root: Path, stat_family: str) -> _SourceFileProfile:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        csv_rows = list(csv.reader(handle))
    expected_header = EXPECTED_RAW_HEADERS[stat_family]
    header_present = _is_header(csv_rows[0], expected_header) if csv_rows else False
    header_inferred = not header_present
    data_rows = csv_rows[1:] if header_present else csv_rows
    source_file = path.relative_to(root).as_posix()
    source_hash = _sha256(path)

    clean_rows: list[dict[str, str]] = []
    seen_exact: set[tuple[str, ...]] = set()
    repeated_headers = 0
    exact_duplicates = 0
    malformed = 0
    numeric_issue_names: set[str] = set()
    for raw in data_rows:
        if not raw or all(not cell.strip() for cell in raw):
            continue
        if _is_header(raw, expected_header):
            repeated_headers += 1
            continue
        normalized_raw = tuple(cell.strip() for cell in raw)
        if normalized_raw in seen_exact:
            exact_duplicates += 1
            continue
        seen_exact.add(normalized_raw)
        if len(raw) != len(expected_header):
            malformed += 1
            continue
        row = dict(zip(expected_header, (cell.strip() for cell in raw), strict=True))
        if _numeric_issues(row, stat_family):
            numeric_issue_names.add(row.get("Player", ""))
        clean_rows.append(row)

    return _SourceFileProfile(
        rows=tuple(clean_rows),
        source_file=source_file,
        source_hash=source_hash,
        raw_rows=max(len(csv_rows) - (1 if header_present else 0), 0),
        header_present=header_present,
        header_inferred=header_inferred,
        repeated_header_rows_removed=repeated_headers,
        exact_duplicate_rows_removed=exact_duplicates,
        malformed_rows_removed=malformed,
        numeric_issue_rows=len(numeric_issue_names),
    )


def _canonical_row(
    *,
    season: str,
    stat_family: str,
    raw_row: dict[str, str],
    source_file: str,
    source_hash: str,
    rotowire_lookup: dict[tuple[str, str, str], list[_RotoWireIdentity]],
    model_resolver: _ModelIdentityResolver,
) -> dict[str, object]:
    player_name = raw_row["Player"].strip()
    normalized = normalize_player_name(player_name)
    warnings: list[str] = []
    numeric_warnings = _numeric_issues(raw_row, stat_family)
    warnings.extend(numeric_warnings)

    identity_candidates = rotowire_lookup.get((season, stat_family, normalized), [])
    identity: _RotoWireIdentity | None = None
    join_status = "matched"
    join_method = "rotowire_season_family_exact_name"
    join_confidence = 96
    if len(identity_candidates) == 1:
        identity = identity_candidates[0]
    elif len(identity_candidates) > 1:
        join_status = "ambiguous_join"
        join_method = "ambiguous_rotowire_season_family_exact_name"
        join_confidence = 0
        warnings.append("ambiguous_rotowire_identity_join")
    else:
        join_status = "missing_join"
        join_method = "missing_rotowire_season_family_exact_name"
        join_confidence = 0
        warnings.append("missing_rotowire_identity_join")

    matched_model_player = ""
    sleeper_id = ""
    gsis_id = ""
    if identity:
        model_match = model_resolver.resolve(
            player_name=identity.player_name,
            position=identity.position,
            nfl_team=identity.nfl_team,
        )
        if model_match["warning"]:
            warnings.append(str(model_match["warning"]))
        matched_model_player = str(model_match["matched_model_player"])
        sleeper_id = str(model_match["sleeper_id"])
        gsis_id = str(model_match["gsis_id"])
        if not matched_model_player:
            join_status = "missing_join"
            join_method = f"{join_method}+missing_model_identity"
            join_confidence = min(join_confidence, int(model_match["match_confidence"]))
    base = {
        "season": season,
        "player_name": player_name,
        "normalized_player_name": normalized,
        "nfl_team": identity.nfl_team if identity else "",
        "position": identity.position if identity else "",
        "rotowire_player_id": identity.rotowire_player_id if identity else "",
        "matched_model_player": matched_model_player,
        "sleeper_id": sleeper_id,
        "gsis_id": gsis_id,
        "join_status": join_status,
        "join_method": join_method,
        "join_confidence": join_confidence,
        "source_name": "RotoWire manual first-down export",
        "source_status": "imported_real_data",
        "source_file": source_file,
        "source_hash": source_hash,
        "validation_status": "clean" if not warnings else "clean_with_warnings",
        "cleanup_warnings": "|".join(_unique_preserve_order(warnings)),
        "canonicalization_version": FIRST_DOWN_CANONICALIZATION_VERSION,
    }
    if stat_family == "rushing":
        return {
            **base,
            "rushing_yards": _number(raw_row["Rush Yds"]),
            "rushing_attempts": _number(raw_row["Att"]),
            "rushing_touchdowns": _number(raw_row["TD"]),
            "rushing_20_plus": _number(raw_row["20+"]),
            "rushing_40_plus": _number(raw_row["40+"]),
            "rushing_long": _number(raw_row["Lng"]),
            "rushing_first_downs": _number(raw_row["Rush 1st"]),
            "rushing_first_down_rate": _number(raw_row["Rush 1st%"]),
            "rushing_fumbles": _number(raw_row["Rush FUM"]),
        }
    return {
        **base,
        "receptions": _number(raw_row["Rec"]),
        "receiving_yards": _number(raw_row["Yds"]),
        "receiving_touchdowns": _number(raw_row["TD"]),
        "receiving_20_plus": _number(raw_row["20+"]),
        "receiving_40_plus": _number(raw_row["40+"]),
        "receiving_long": _number(raw_row["LNG"]),
        "receiving_first_downs": _number(raw_row["Rec 1st"]),
        "receiving_first_down_rate": _number(raw_row["1st%"]),
        "receiving_fumbles": _number(raw_row["Rec FUM"]),
        "receiving_yards_after_catch_context": _number(raw_row["Rec YAC/R"]),
        "targets": _number(raw_row["Tgts"]),
    }


def _validation_row(
    season: str,
    stat_family: str,
    profile: _SourceFileProfile,
    parsed_rows: list[dict[str, object]],
) -> dict[str, object]:
    missing = sum(1 for row in parsed_rows if row["join_status"] == "missing_join")
    ambiguous = sum(1 for row in parsed_rows if row["join_status"] == "ambiguous_join")
    matched = sum(1 for row in parsed_rows if row["join_status"] == "matched")
    notes = []
    if profile.header_inferred:
        notes.append("missing_header_inferred")
    if profile.repeated_header_rows_removed:
        notes.append(f"repeated_header_rows_removed={profile.repeated_header_rows_removed}")
    if profile.exact_duplicate_rows_removed:
        notes.append(f"exact_duplicate_rows_removed={profile.exact_duplicate_rows_removed}")
    if missing:
        notes.append(f"missing_join_rows={missing}")
    if ambiguous:
        notes.append(f"ambiguous_join_rows={ambiguous}")
    return {
        "season": season,
        "stat_family": stat_family,
        "source_file": profile.source_file,
        "source_hash": profile.source_hash,
        "raw_rows": profile.raw_rows,
        "header_present": profile.header_present,
        "header_inferred": profile.header_inferred,
        "repeated_header_rows_removed": profile.repeated_header_rows_removed,
        "exact_duplicate_rows_removed": profile.exact_duplicate_rows_removed,
        "malformed_rows_removed": profile.malformed_rows_removed,
        "clean_rows": len(parsed_rows),
        "imported_real_data_rows": sum(
            1 for row in parsed_rows if row["source_status"] == "imported_real_data"
        ),
        "matched_rows": matched,
        "missing_join_rows": missing,
        "ambiguous_join_rows": ambiguous,
        "numeric_issue_rows": profile.numeric_issue_rows,
        "validation_status": "usable_after_cleanup" if notes else "clean",
        "notes": "|".join(notes),
        "canonicalization_version": FIRST_DOWN_CANONICALIZATION_VERSION,
    }


def _receipt_row(
    canonical: dict[str, object],
    raw_row: dict[str, str],
    stat_family: str,
) -> dict[str, object]:
    normalized_fields = {
        key: value
        for key, value in canonical.items()
        if key.endswith("first_downs")
        or key.endswith("first_down_rate")
        or key in {"targets", "receptions", "rushing_attempts", "rushing_yards", "receiving_yards"}
    }
    return {
        "season": canonical["season"],
        "player_name": canonical["player_name"],
        "normalized_player_name": canonical["normalized_player_name"],
        "stat_family": stat_family,
        "component": f"{stat_family}_first_downs",
        "source_status": canonical["source_status"],
        "source_file": canonical["source_file"],
        "source_hash": canonical["source_hash"],
        "raw_fields_json": json.dumps(raw_row, sort_keys=True),
        "normalized_fields_json": json.dumps(normalized_fields, sort_keys=True),
        "join_status": canonical["join_status"],
        "warning": canonical["cleanup_warnings"],
        "canonicalization_version": FIRST_DOWN_CANONICALIZATION_VERSION,
    }


def _coverage_row(
    canonical: dict[str, object],
    stat_family: str,
) -> dict[str, object]:
    warning = str(canonical["cleanup_warnings"])
    if canonical["join_status"] == "matched":
        coverage = "covered"
    elif canonical["join_status"] == "ambiguous_join":
        coverage = "review_ambiguous_join"
    else:
        coverage = "review_missing_join"
    return {
        "season": canonical["season"],
        "player_name": canonical["player_name"],
        "normalized_player_name": canonical["normalized_player_name"],
        "stat_family": stat_family,
        "has_first_down_evidence": True,
        "source_status": canonical["source_status"],
        "source_file": canonical["source_file"],
        "source_hash": canonical["source_hash"],
        "join_status": canonical["join_status"],
        "coverage_status": coverage,
        "warning": warning,
        "canonicalization_version": FIRST_DOWN_CANONICALIZATION_VERSION,
    }


def _build_rotowire_identity_lookup(
    *,
    raw_root: Path,
) -> dict[tuple[str, str, str], list[_RotoWireIdentity]]:
    intake = build_rotowire_player_stats_intake(raw_root).clean_rows
    lookup: dict[tuple[str, str, str], list[_RotoWireIdentity]] = {}
    for row in intake:
        if row.get("source_family") not in {"rushing", "receiving"}:
            continue
        if row.get("source_detail") != "basic":
            continue
        normalized = normalize_player_name(row.get("player_name"))
        key = (str(row["season"]), str(row["source_family"]), normalized)
        lookup.setdefault(key, []).append(
            _RotoWireIdentity(
                player_name=str(row.get("player_name") or ""),
                rotowire_player_id=str(row.get("rotowire_player_id") or ""),
                nfl_team=_team_key(row.get("nfl_team")),
                position=str(row.get("position") or ""),
            )
        )
    for key, values in list(lookup.items()):
        unique = {
            (
                value.player_name,
                value.rotowire_player_id,
                value.nfl_team,
                value.position,
            ): value
            for value in values
        }
        lookup[key] = list(unique.values())
    return lookup


class _ModelIdentityResolver:
    def __init__(self, candidates: tuple[ModelIdentityCandidate, ...]) -> None:
        self.by_name_position_team: dict[tuple[str, str, str], list[ModelIdentityCandidate]] = {}
        self.by_name_position: dict[tuple[str, str], list[ModelIdentityCandidate]] = {}
        for candidate in candidates:
            for name in candidate.names:
                normalized = normalize_player_name(name)
                if not normalized or not candidate.position:
                    continue
                self.by_name_position.setdefault((normalized, candidate.position), []).append(
                    candidate
                )
                if candidate.team:
                    self.by_name_position_team.setdefault(
                        (normalized, candidate.position, _team_key(candidate.team)), []
                    ).append(candidate)

    def resolve(self, *, player_name: str, position: str, nfl_team: str) -> dict[str, object]:
        normalized = normalize_player_name(player_name)
        team = _team_key(nfl_team)
        team_matches = _unique_candidates(
            self.by_name_position_team.get((normalized, position, team), [])
        )
        if len(team_matches) == 1:
            return _model_match_row(team_matches[0], "name_team_position", 98, "")
        if len(team_matches) > 1:
            return _no_model_match("ambiguous_name_team_position", "ambiguous_model_identity")
        name_matches = _unique_candidates(self.by_name_position.get((normalized, position), []))
        if len(name_matches) == 1:
            warning = "team_mismatch_or_missing_model_team" if team and name_matches[0].team else ""
            return _model_match_row(
                name_matches[0],
                "exact_normalized_name_position",
                88 if warning else 94,
                warning,
            )
        if len(name_matches) > 1:
            return _no_model_match("ambiguous_name_position", "ambiguous_model_identity")
        return _no_model_match("unmatched", "unmatched_model_identity")


def _model_match_row(
    candidate: ModelIdentityCandidate,
    method: str,
    confidence: int,
    warning: str,
) -> dict[str, object]:
    return {
        "matched_model_player": candidate.model_player_name,
        "sleeper_id": candidate.sleeper_id,
        "gsis_id": candidate.gsis_id,
        "match_method": method,
        "match_confidence": confidence,
        "warning": warning,
    }


def _no_model_match(method: str, warning: str) -> dict[str, object]:
    return {
        "matched_model_player": "",
        "sleeper_id": "",
        "gsis_id": "",
        "match_method": method,
        "match_confidence": 0,
        "warning": warning,
    }


def _unique_candidates(
    candidates: list[ModelIdentityCandidate],
) -> list[ModelIdentityCandidate]:
    by_key = {}
    for candidate in candidates:
        key = candidate.sleeper_id or candidate.gsis_id or (
            f"{normalize_player_name(candidate.model_player_name)}:{candidate.position}"
        )
        by_key[key] = candidate
    return list(by_key.values())


def _numeric_issues(row: dict[str, str], stat_family: str) -> list[str]:
    issues = []
    for key in EXPECTED_RAW_HEADERS[stat_family]:
        if key == "Player":
            continue
        value = row.get(key, "")
        if value == "":
            issues.append(f"{key}:blank")
            continue
        try:
            _number(value)
        except ValueError:
            issues.append(f"{key}:non_numeric")
    return issues


def _number(value: str) -> int | float | str:
    text = str(value or "").strip()
    if text == "":
        return ""
    cleaned = text.replace(",", "").replace("%", "")
    number = float(cleaned)
    if number.is_integer():
        return int(number)
    return number


def _is_header(row: list[str], expected_header: tuple[str, ...]) -> bool:
    normalized = tuple(cell.strip().lower() for cell in row)
    expected = tuple(cell.strip().lower() for cell in expected_header)
    return normalized == expected or (bool(row) and row[0].strip().lower() == "player")


def _team_key(value: object) -> str:
    team = str(value or "").strip().upper()
    return TEAM_ALIASES.get(team, team)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique_preserve_order(values: list[str]) -> tuple[str, ...]:
    seen = set()
    output = []
    for value in values:
        if value and value not in seen:
            output.append(value)
            seen.add(value)
    return tuple(output)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return slug.strip("_")


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
