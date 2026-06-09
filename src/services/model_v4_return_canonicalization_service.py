from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.model_v4_fantasypros_identity_mapping_service import (
    ModelIdentityCandidate,
    build_model_identity_candidates,
    normalize_player_name,
)
from src.services.model_v4_rotowire_player_stats_intake_service import (
    build_rotowire_player_stats_intake,
)
from src.services.model_v4_rotowire_source_index_service import DEFAULT_RAW_ROOT

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/returns/latest")

RETURN_CANONICALIZATION_VERSION = "model_v4_return_canonicalization_0.1.0"

CANONICAL_RETURN_HEADER = (
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
    "kick_return_attempts",
    "kick_return_yards",
    "kick_return_touchdowns",
    "kick_return_20_plus",
    "kick_return_40_plus",
    "kick_return_long",
    "kick_return_fair_catches",
    "kick_return_fumbles",
    "punt_return_attempts",
    "punt_return_yards",
    "punt_return_touchdowns",
    "punt_return_20_plus",
    "punt_return_40_plus",
    "punt_return_long",
    "punt_return_fair_catches",
    "punt_return_fumbles",
    "return_yards_total",
    "return_td_total",
    "return_lve_points",
    "source_name",
    "source_status",
    "source_files",
    "source_hashes",
    "validation_status",
    "cleanup_warnings",
    "scoring_role",
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
    "shifted_header_inferred",
    "repeated_header_rows_removed",
    "exact_duplicate_rows_removed",
    "malformed_rows_removed",
    "clean_rows",
    "imported_real_data_rows",
    "matched_rows",
    "missing_join_rows",
    "ambiguous_join_rows",
    "numeric_issue_rows",
    "total_return_yards",
    "total_return_tds",
    "validation_status",
    "notes",
    "canonicalization_version",
)

RECEIPT_HEADER = (
    "season",
    "player_name",
    "normalized_player_name",
    "component",
    "source_status",
    "source_files",
    "source_hashes",
    "raw_fields_json",
    "normalized_fields_json",
    "scoring_constants_json",
    "contribution",
    "warning",
    "scoring_role",
    "canonicalization_version",
)

COVERAGE_HEADER = (
    "season",
    "player_name",
    "normalized_player_name",
    "has_return_evidence",
    "source_status",
    "source_files",
    "source_hashes",
    "join_status",
    "coverage_status",
    "warning",
    "canonicalization_version",
)

SUMMARY_HEADER = ("metric", "value")

EXPECTED_RAW_HEADERS = {
    "kick": (
        "Player",
        "Avg",
        "Ret",
        "Yds",
        "KRet TD",
        "20+",
        "40+",
        "Lng",
        "FC",
        "FUM",
    ),
    "punt": (
        "Player",
        "Avg",
        "Ret",
        "Yds",
        "PRet T",
        "20+",
        "40+",
        "Lng",
        "FC",
        "FUM",
    ),
}

SCORING_ROLE = "small_direct_return_scoring_evidence_not_talent_signal"

TEAM_ALIASES = {
    "JAC": "JAX",
    "LA": "LAR",
    "STL": "LAR",
    "SD": "LAC",
    "OAK": "LV",
    "WSH": "WAS",
}


@dataclass(frozen=True)
class CanonicalReturnResult:
    canonical_rows: tuple[dict[str, object], ...]
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
    shifted_header_inferred: bool
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


def build_canonical_returns(
    *,
    raw_root: str | Path = DEFAULT_RAW_ROOT,
) -> CanonicalReturnResult:
    root = Path(raw_root)
    identity_lookup = _build_rotowire_identity_lookup(raw_root=root)
    model_resolver = _ModelIdentityResolver(build_model_identity_candidates())

    source_specs = (
        ("2024", "kick", root / "2024" / "returns" / "kick_returns.csv"),
        ("2025", "kick", root / "2025" / "returns" / "kick_returns.csv"),
        ("2024", "punt", root / "2024" / "returns" / "punt_returns.csv"),
        ("2025", "punt", root / "2025" / "returns" / "punt_returns.csv"),
    )

    source_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []
    for season, stat_family, path in source_specs:
        profile = _parse_source_file(path, root=root, stat_family=stat_family)
        parsed_rows = [
            _source_return_row(
                season=season,
                stat_family=stat_family,
                raw_row=raw_row,
                profile=profile,
                identity_lookup=identity_lookup,
                model_resolver=model_resolver,
            )
            for raw_row in profile.rows
        ]
        source_rows.extend(parsed_rows)
        validation_rows.append(_validation_row(season, stat_family, profile, parsed_rows))

    canonical_rows = tuple(_aggregate_return_rows(source_rows))
    receipt_rows = tuple(_receipt_row(row) for row in canonical_rows)
    coverage_rows = tuple(_coverage_row(row) for row in canonical_rows)
    summary = {
        "canonicalization_version": RETURN_CANONICALIZATION_VERSION,
        "canonical_row_count": len(canonical_rows),
        "validation_file_count": len(validation_rows),
        "receipt_row_count": len(receipt_rows),
        "coverage_row_count": len(coverage_rows),
        "imported_real_data_rows": sum(
            1 for row in canonical_rows if row["source_status"] == "imported_real_data"
        ),
        "admitted_return_rows": sum(
            1 for row in canonical_rows if row["join_status"] == "matched"
        ),
        "missing_join_rows": sum(
            1 for row in canonical_rows if row["join_status"] == "missing_join"
        ),
        "ambiguous_join_rows": sum(
            1 for row in canonical_rows if row["join_status"] == "ambiguous_join"
        ),
        "total_return_yards": sum(float(row["return_yards_total"]) for row in canonical_rows),
        "total_return_tds": sum(float(row["return_td_total"]) for row in canonical_rows),
        "total_return_lve_points": round(
            sum(float(row["return_lve_points"]) for row in canonical_rows),
            2,
        ),
        "model_scores_changed": False,
        "active_rankings_overwritten": False,
        "review_only": True,
        "scoring_role": SCORING_ROLE,
    }
    return CanonicalReturnResult(
        canonical_rows=canonical_rows,
        validation_rows=tuple(validation_rows),
        receipt_rows=receipt_rows,
        coverage_rows=coverage_rows,
        summary=summary,
    )


def write_canonical_return_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: CanonicalReturnResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_canonical_returns()
    paths = {
        "canonical": output / "canonical_return_stats.csv",
        "admitted": output / "admitted_return_scoring_evidence.csv",
        "validation": output / "return_canonicalization_validation.csv",
        "receipts": output / "return_scoring_receipts.csv",
        "coverage": output / "return_source_coverage.csv",
        "summary": output / "return_canonicalization_summary.csv",
    }
    _write_csv(paths["canonical"], CANONICAL_RETURN_HEADER, result.canonical_rows)
    _write_csv(paths["admitted"], CANONICAL_RETURN_HEADER, _matched_rows(result.canonical_rows))
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
    first_row = csv_rows[0] if csv_rows else []
    header_present = _is_header(first_row, expected_header)
    shifted_header_inferred = _is_shifted_header(first_row, expected_header)
    header_inferred = not header_present
    data_rows = csv_rows[1:] if header_present or shifted_header_inferred else csv_rows
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
        if _is_header(raw, expected_header) or _is_shifted_header(raw, expected_header):
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
        raw_rows=max(len(csv_rows) - (1 if header_present or shifted_header_inferred else 0), 0),
        header_present=header_present,
        header_inferred=header_inferred,
        shifted_header_inferred=shifted_header_inferred,
        repeated_header_rows_removed=repeated_headers,
        exact_duplicate_rows_removed=exact_duplicates,
        malformed_rows_removed=malformed,
        numeric_issue_rows=len(numeric_issue_names),
    )


def _source_return_row(
    *,
    season: str,
    stat_family: str,
    raw_row: dict[str, str],
    profile: _SourceFileProfile,
    identity_lookup: dict[tuple[str, str], list[_RotoWireIdentity]],
    model_resolver: _ModelIdentityResolver,
) -> dict[str, object]:
    player_name = raw_row["Player"].strip()
    normalized = normalize_player_name(player_name)
    warnings: list[str] = []
    if profile.shifted_header_inferred:
        warnings.append("shifted_header_expected_player_header_inferred")
    elif profile.header_inferred:
        warnings.append("missing_header_inferred")
    if profile.repeated_header_rows_removed:
        warnings.append(f"repeated_header_rows_removed={profile.repeated_header_rows_removed}")
    warnings.extend(_numeric_issues(raw_row, stat_family))

    identity_candidates = identity_lookup.get((season, normalized), [])
    identity: _RotoWireIdentity | None = None
    join_status = "matched"
    join_method = "rotowire_season_exact_name"
    join_confidence = 92
    if len(identity_candidates) == 1:
        identity = identity_candidates[0]
    elif len(identity_candidates) > 1:
        join_status = "ambiguous_join"
        join_method = "ambiguous_rotowire_season_exact_name"
        join_confidence = 0
        warnings.append("ambiguous_rotowire_identity_join")
    else:
        join_status = "missing_join"
        join_method = "missing_rotowire_season_exact_name"
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

    yards = _number(raw_row["Yds"])
    touchdowns = _number(raw_row["KRet TD" if stat_family == "kick" else "PRet T"])
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
        "source_name": "RotoWire manual return export",
        "source_status": "imported_real_data",
        "source_file": profile.source_file,
        "source_hash": profile.source_hash,
        "validation_status": "clean" if not warnings else "clean_with_warnings",
        "cleanup_warnings": "|".join(_unique_preserve_order(warnings)),
        "raw_fields_json": json.dumps(raw_row, sort_keys=True),
        "canonicalization_version": RETURN_CANONICALIZATION_VERSION,
    }
    prefix = "kick_return" if stat_family == "kick" else "punt_return"
    return {
        **base,
        "stat_family": stat_family,
        f"{prefix}_attempts": _number(raw_row["Ret"]),
        f"{prefix}_yards": yards,
        f"{prefix}_touchdowns": touchdowns,
        f"{prefix}_20_plus": _number(raw_row["20+"]),
        f"{prefix}_40_plus": _number(raw_row["40+"]),
        f"{prefix}_long": _number(raw_row["Lng"]),
        f"{prefix}_fair_catches": _number(raw_row["FC"]),
        f"{prefix}_fumbles": _number(raw_row["FUM"]),
    }


def _aggregate_return_rows(
    source_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    aggregates: dict[tuple[str, str], dict[str, object]] = {}
    for row in source_rows:
        key = (str(row["season"]), str(row["normalized_player_name"]))
        current = aggregates.setdefault(key, _empty_aggregate(row))
        stat_family = str(row["stat_family"])
        prefix = "kick_return" if stat_family == "kick" else "punt_return"
        for suffix in (
            "attempts",
            "yards",
            "touchdowns",
            "20_plus",
            "40_plus",
            "long",
            "fair_catches",
            "fumbles",
        ):
            target = f"{prefix}_{suffix}"
            if suffix == "long":
                current[target] = max(_float(current.get(target)), _float(row.get(target)))
            else:
                current[target] = _clean_number(
                    _float(current.get(target)) + _float(row.get(target))
                )
        current["source_files"] = _pipe_join(
            str(current["source_files"]),
            str(row["source_file"]),
        )
        current["source_hashes"] = _pipe_join(
            str(current["source_hashes"]),
            str(row["source_hash"]),
        )
        current["raw_fields"].append(
            {
                "stat_family": stat_family,
                "source_file": row["source_file"],
                "raw_fields": json.loads(str(row["raw_fields_json"])),
            }
        )
        current["cleanup_warnings"] = _pipe_join(
            str(current["cleanup_warnings"]),
            str(row["cleanup_warnings"]),
        )
        if current["join_status"] == "missing_join" and row["join_status"] == "matched":
            _copy_identity(current, row)
        elif (
            current["join_status"] != row["join_status"]
            and row["join_status"] == "ambiguous_join"
        ):
            current["join_status"] = "ambiguous_join"
            current["join_method"] = "ambiguous_return_identity_aggregate"
            current["join_confidence"] = 0

    output: list[dict[str, object]] = []
    for row in aggregates.values():
        kick_yards = _float(row["kick_return_yards"])
        punt_yards = _float(row["punt_return_yards"])
        kick_tds = _float(row["kick_return_touchdowns"])
        punt_tds = _float(row["punt_return_touchdowns"])
        return_yards = kick_yards + punt_yards
        return_tds = kick_tds + punt_tds
        row["return_yards_total"] = _clean_number(return_yards)
        row["return_td_total"] = _clean_number(return_tds)
        row["return_lve_points"] = round(
            (return_yards * LVE_SCORING["return_yard"])
            + (return_tds * LVE_SCORING["return_td"]),
            2,
        )
        row["validation_status"] = (
            "clean" if not str(row["cleanup_warnings"]) else "clean_with_warnings"
        )
        row["raw_fields_json"] = json.dumps(row.pop("raw_fields"), sort_keys=True)
        output.append(row)
    return sorted(
        output,
        key=lambda item: (
            str(item["season"]),
            -float(item["return_lve_points"]),
            str(item["player_name"]),
        ),
    )


def _empty_aggregate(row: dict[str, object]) -> dict[str, object]:
    aggregate = {
        "season": row["season"],
        "player_name": row["player_name"],
        "normalized_player_name": row["normalized_player_name"],
        "nfl_team": row["nfl_team"],
        "position": row["position"],
        "rotowire_player_id": row["rotowire_player_id"],
        "matched_model_player": row["matched_model_player"],
        "sleeper_id": row["sleeper_id"],
        "gsis_id": row["gsis_id"],
        "join_status": row["join_status"],
        "join_method": row["join_method"],
        "join_confidence": row["join_confidence"],
        "source_name": "RotoWire manual return export",
        "source_status": "imported_real_data",
        "source_files": "",
        "source_hashes": "",
        "validation_status": "clean",
        "cleanup_warnings": "",
        "scoring_role": SCORING_ROLE,
        "canonicalization_version": RETURN_CANONICALIZATION_VERSION,
        "raw_fields": [],
    }
    for prefix in ("kick_return", "punt_return"):
        for suffix in (
            "attempts",
            "yards",
            "touchdowns",
            "20_plus",
            "40_plus",
            "long",
            "fair_catches",
            "fumbles",
        ):
            aggregate[f"{prefix}_{suffix}"] = 0
    aggregate["return_yards_total"] = 0
    aggregate["return_td_total"] = 0
    aggregate["return_lve_points"] = 0
    return aggregate


def _copy_identity(target: dict[str, object], source: dict[str, object]) -> None:
    for key in (
        "nfl_team",
        "position",
        "rotowire_player_id",
        "matched_model_player",
        "sleeper_id",
        "gsis_id",
        "join_status",
        "join_method",
        "join_confidence",
    ):
        target[key] = source[key]


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
    if profile.shifted_header_inferred:
        notes.append("shifted_header_expected_player_header_inferred")
    elif profile.header_inferred:
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
        "shifted_header_inferred": profile.shifted_header_inferred,
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
        "total_return_yards": sum(float(row[f"{stat_family}_return_yards"]) for row in parsed_rows),
        "total_return_tds": sum(
            float(row[f"{stat_family}_return_touchdowns"]) for row in parsed_rows
        ),
        "validation_status": "usable_after_cleanup" if notes else "clean",
        "notes": "|".join(notes),
        "canonicalization_version": RETURN_CANONICALIZATION_VERSION,
    }


def _receipt_row(row: dict[str, object]) -> dict[str, object]:
    normalized_fields = {
        key: value
        for key, value in row.items()
        if key.startswith("kick_return")
        or key.startswith("punt_return")
        or key in {"return_yards_total", "return_td_total", "return_lve_points"}
    }
    constants = {
        "return_yard": LVE_SCORING["return_yard"],
        "return_td": LVE_SCORING["return_td"],
    }
    return {
        "season": row["season"],
        "player_name": row["player_name"],
        "normalized_player_name": row["normalized_player_name"],
        "component": "return_scoring",
        "source_status": row["source_status"],
        "source_files": row["source_files"],
        "source_hashes": row["source_hashes"],
        "raw_fields_json": row["raw_fields_json"],
        "normalized_fields_json": json.dumps(normalized_fields, sort_keys=True),
        "scoring_constants_json": json.dumps(constants, sort_keys=True),
        "contribution": row["return_lve_points"],
        "warning": row["cleanup_warnings"],
        "scoring_role": row["scoring_role"],
        "canonicalization_version": RETURN_CANONICALIZATION_VERSION,
    }


def _coverage_row(row: dict[str, object]) -> dict[str, object]:
    if row["join_status"] == "matched":
        coverage = "covered"
    elif row["join_status"] == "ambiguous_join":
        coverage = "review_ambiguous_join"
    else:
        coverage = "review_missing_join"
    return {
        "season": row["season"],
        "player_name": row["player_name"],
        "normalized_player_name": row["normalized_player_name"],
        "has_return_evidence": True,
        "source_status": row["source_status"],
        "source_files": row["source_files"],
        "source_hashes": row["source_hashes"],
        "join_status": row["join_status"],
        "coverage_status": coverage,
        "warning": row["cleanup_warnings"],
        "canonicalization_version": RETURN_CANONICALIZATION_VERSION,
    }


def _build_rotowire_identity_lookup(
    *,
    raw_root: Path,
) -> dict[tuple[str, str], list[_RotoWireIdentity]]:
    intake = build_rotowire_player_stats_intake(raw_root).clean_rows
    lookup: dict[tuple[str, str], list[_RotoWireIdentity]] = {}
    for row in intake:
        if row.get("source_detail") != "basic":
            continue
        normalized = normalize_player_name(row.get("player_name"))
        key = (str(row["season"]), normalized)
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
                        (normalized, candidate.position, _team_key(candidate.team)),
                        [],
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


def _float(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0


def _clean_number(value: float) -> int | float:
    return int(value) if value.is_integer() else value


def _is_header(row: list[str], expected_header: tuple[str, ...]) -> bool:
    normalized = tuple(cell.strip().lower() for cell in row)
    expected = tuple(cell.strip().lower() for cell in expected_header)
    return normalized == expected or (bool(row) and row[0].strip().lower() == "player")


def _is_shifted_header(row: list[str], expected_header: tuple[str, ...]) -> bool:
    normalized = tuple(cell.strip().lower() for cell in row)
    shifted = tuple(cell.strip().lower() for cell in (*expected_header[1:], "0"))
    return normalized == shifted


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


def _pipe_join(existing: str, new_value: str) -> str:
    parts: list[str] = []
    for value in (*existing.split("|"), *new_value.split("|")):
        if value and value not in parts:
            parts.append(value)
    return "|".join(parts)


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
