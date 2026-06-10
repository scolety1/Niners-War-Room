from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.services.nwr_outcome_historical_row_factory import (
    SUPPORTED_HISTORICAL_ROW_TYPES,
)
from src.services.nwr_outcome_scoring_service import ScoringRules

READINESS_STATUSES = (
    "ready",
    "needs_data",
    "manual_review_required",
    "blocked",
)

SOURCE_CLASSIFICATIONS = (
    "allowed",
    "blocked",
    "unknown",
    "display_only",
)

DEFAULT_SOURCE_TIMESTAMP_FIELDS = (
    "source_max_timestamp",
    "source_available_at",
    "collected_at_utc",
    "generated_at",
    "snapshot_date",
    "as_of_date",
    "source_date",
)

FORBIDDEN_SOURCE_TOKENS = (
    "adp",
    "fantasypros",
    "public_rank",
    "public_projection",
    "consensus",
    "startup",
    "trade_calculator",
    "trade_value",
    "market_rank",
    "league_rank",
    "rotowire_projection",
    "rotowire_ranking",
    "rotowire_outlook",
    "rotowire_value",
    "prior_fantasy_draft_history",
    "prior_nwr_private_score",
    "legacy_private_score",
    "private_score",
    "same_season_final_stats",
    "hindsight_note",
    "post_cutoff_update",
)

DISPLAY_ONLY_TOKENS = (
    "draft_prep",
    "prior_league_draft",
    "market_context",
    "league_context",
    "comparison",
)

ALLOWED_SOURCE_HINTS = {
    "nwr_scoring_rules": "nwr_scoring_rules",
    "scoring_rules": "nwr_scoring_rules",
    "historical_week_scores": "nwr_historical_week_scores",
    "week_scores": "nwr_historical_week_scores",
    "weekly_stats": "nflverse_raw_stats",
    "raw_stats": "nflverse_raw_stats",
    "nflverse": "nflverse_raw_stats",
    "season_labels": "nwr_historical_season_labels",
    "outcome_labels": "nwr_historical_season_labels",
    "player_dim": "nwr_player_dim",
    "players": "nwr_player_dim",
    "draft_capital": "official_draft_capital",
    "injury_status": "injury_status_source",
    "rotowire_raw_stats": "rotowire_raw_stats",
    "rotowire_role_usage": "rotowire_role_usage",
    "rotowire_workouts": "rotowire_workouts",
}

ROW_FAMILY_REQUIRED_SOURCE_FAMILIES = {
    "rookie_post_draft": (
        "nwr_player_dim",
        "official_draft_capital",
        "nwr_historical_week_scores",
        "nwr_historical_season_labels",
    ),
    "all_player_pre_week1": (
        "nwr_player_dim",
        "nwr_historical_week_scores",
        "nwr_historical_season_labels",
    ),
    "offseason_carryover": (
        "nwr_player_dim",
        "nwr_historical_week_scores",
        "nwr_historical_season_labels",
    ),
}


@dataclass(frozen=True)
class SourceManifestEntry:
    source_path: str
    source_family: str
    classification: str
    readiness_status: str
    row_count: int | None
    columns: tuple[str, ...]
    source_max_timestamp: str | None
    missing_timestamp: bool
    manual_review_required: bool
    notes: str


@dataclass(frozen=True)
class RowFamilySourceManifest:
    manifest_id: str
    row_family: str
    cutoff_id: str
    input_snapshot_date: str
    source_entries: tuple[SourceManifestEntry, ...]
    required_source_families: tuple[str, ...]
    missing_required_source_families: tuple[str, ...]
    readiness_status: str
    manifest_hash: str


@dataclass(frozen=True)
class CutoffDefinition:
    cutoff_id: str
    row_family: str
    prediction_date: str
    input_snapshot_date: str
    notes: str = ""


@dataclass(frozen=True)
class RowLevelLeakageAudit:
    row_identifier: str
    row_family: str
    source_family: str
    source_path: str
    source_max_timestamp: str | None
    input_snapshot_date: str
    readiness_status: str
    issue_type: str
    notes: str


@dataclass(frozen=True)
class RawStatMappingIssue:
    scoring_component: str
    accepted_source_fields: tuple[str, ...]
    present_source_field: str
    readiness_status: str
    notes: str


@dataclass(frozen=True)
class DataReadinessReport:
    report_id: str
    readiness_status: str
    manifest_count: int
    blocked_manifest_count: int
    manual_review_manifest_count: int
    leakage_audit_blocked_count: int
    missing_mapping_count: int
    notes: str


def default_cutoff_definitions() -> dict[str, CutoffDefinition]:
    return {
        "rookie_post_draft": CutoffDefinition(
            cutoff_id="rookie_post_draft_v1",
            row_family="rookie_post_draft",
            prediction_date="YYYY-05-01",
            input_snapshot_date="YYYY-05-01",
            notes="Post-NFL-draft rookie snapshot after draft capital and landing team are known.",
        ),
        "all_player_pre_week1": CutoffDefinition(
            cutoff_id="all_player_pre_week1_v1",
            row_family="all_player_pre_week1",
            prediction_date="YYYY-09-01",
            input_snapshot_date="YYYY-09-01",
            notes="All-player preseason snapshot before Week 1 games.",
        ),
        "offseason_carryover": CutoffDefinition(
            cutoff_id="offseason_carryover_v1",
            row_family="offseason_carryover",
            prediction_date="YYYY-02-15",
            input_snapshot_date="YYYY-02-15",
            notes="Offseason carryover snapshot after prior season labels are available.",
        ),
    }


def classify_source(
    source_path: str | Path,
    columns: Sequence[str] = (),
) -> tuple[str, str, bool, str]:
    haystack = _normalize(" ".join([str(source_path), *columns]))
    if any(_normalize(token) in haystack for token in FORBIDDEN_SOURCE_TOKENS):
        return (
            _matching_family(haystack, FORBIDDEN_SOURCE_TOKENS),
            "blocked",
            False,
            "Blocked by forbidden source/input policy.",
        )
    if any(_normalize(token) in haystack for token in DISPLAY_ONLY_TOKENS):
        return (
            _matching_family(haystack, DISPLAY_ONLY_TOKENS),
            "display_only",
            True,
            "Display/context-only source; manual review required before training use.",
        )
    for token, family in ALLOWED_SOURCE_HINTS.items():
        if _normalize(token) in haystack:
            return (family, "allowed", False, "Allowed source family if timestamps pass.")
    return (
        "unknown",
        "unknown",
        True,
        "Unknown source family; manual review required and not allowed automatically.",
    )


def inspect_source_manifest_entry(
    source_path: str | Path,
    *,
    timestamp_fields: Sequence[str] = DEFAULT_SOURCE_TIMESTAMP_FIELDS,
) -> SourceManifestEntry:
    path = Path(source_path)
    columns: tuple[str, ...] = ()
    row_count: int | None = None
    source_max_timestamp: str | None = None
    notes: list[str] = []
    if path.exists() and path.suffix.lower() == ".csv":
        try:
            rows = _read_csv_dicts(path)
            row_count = len(rows)
            columns = tuple(rows[0].keys()) if rows else tuple(_read_csv_header(path))
            source_max_timestamp = calculate_source_max_timestamp(
                rows,
                timestamp_fields=timestamp_fields,
            )
        except OSError as exc:
            notes.append(f"Could not inspect CSV: {exc}")
    elif not path.exists():
        notes.append("Source file missing.")
    else:
        notes.append("Non-CSV source; manifest contract only.")

    source_family, classification, manual_review, classification_note = classify_source(
        path,
        columns,
    )
    notes.append(classification_note)
    missing_timestamp = classification == "allowed" and source_max_timestamp is None
    if missing_timestamp:
        notes.append("Missing source timestamp blocks production row emission.")
    readiness_status = _entry_readiness(
        classification=classification,
        missing_timestamp=missing_timestamp,
    )
    return SourceManifestEntry(
        source_path=str(path),
        source_family=source_family,
        classification=classification,
        readiness_status=readiness_status,
        row_count=row_count,
        columns=columns,
        source_max_timestamp=source_max_timestamp,
        missing_timestamp=missing_timestamp,
        manual_review_required=manual_review or readiness_status == "manual_review_required",
        notes=" ".join(notes),
    )


def build_row_family_source_manifest(
    *,
    row_family: str,
    source_paths: Sequence[str | Path],
    cutoff: CutoffDefinition,
    required_source_families: Sequence[str] | None = None,
) -> RowFamilySourceManifest:
    _require_supported_row_family(row_family)
    if cutoff.row_family != row_family:
        raise ValueError("Cutoff definition row_family must match manifest row_family.")
    entries = tuple(inspect_source_manifest_entry(path) for path in source_paths)
    required = tuple(
        required_source_families
        if required_source_families is not None
        else ROW_FAMILY_REQUIRED_SOURCE_FAMILIES[row_family]
    )
    ready_families = {
        entry.source_family for entry in entries if entry.readiness_status == "ready"
    }
    missing_required = tuple(family for family in required if family not in ready_families)
    readiness = _manifest_readiness(entries, missing_required)
    payload = {
        "row_family": row_family,
        "cutoff_id": cutoff.cutoff_id,
        "input_snapshot_date": cutoff.input_snapshot_date,
        "source_entries": [asdict(entry) for entry in entries],
        "required_source_families": required,
        "missing_required_source_families": missing_required,
        "readiness_status": readiness,
    }
    manifest_hash = _sha256(payload)
    return RowFamilySourceManifest(
        manifest_id=f"nwr_manifest_{row_family}_{manifest_hash[:12]}",
        row_family=row_family,
        cutoff_id=cutoff.cutoff_id,
        input_snapshot_date=cutoff.input_snapshot_date,
        source_entries=entries,
        required_source_families=required,
        missing_required_source_families=missing_required,
        readiness_status=readiness,
        manifest_hash=manifest_hash,
    )


def calculate_source_max_timestamp(
    rows: Sequence[Mapping[str, Any]],
    *,
    timestamp_fields: Sequence[str] = DEFAULT_SOURCE_TIMESTAMP_FIELDS,
) -> str | None:
    timestamps: list[str] = []
    for row in rows:
        for field in timestamp_fields:
            value = row.get(field)
            if not _missing(value):
                timestamps.append(str(value))
                break
    if not timestamps:
        return None
    parsed = [_parse_datetime(value) for value in timestamps]
    return max(parsed).isoformat()


def label_available_date(
    *,
    target_season: int,
    target_horizon: str,
    outcome_window: str = "regular_season",
) -> str | None:
    horizon_years = _horizon_years(target_horizon)
    if horizon_years is None:
        return None
    month_day = (1, 15)
    if outcome_window in {"postseason", "full_season_plus_playoffs"}:
        month_day = (2, 15)
    year = target_season + horizon_years
    month, day = month_day
    return f"{year:04d}-{month:02d}-{day:02d}"


def future_window_status(
    *,
    target_season: int,
    target_horizon: str,
    as_of_date: str,
    outcome_window: str = "regular_season",
) -> str:
    available = label_available_date(
        target_season=target_season,
        target_horizon=target_horizon,
        outcome_window=outcome_window,
    )
    if available is None:
        return "needs_data"
    return "ready" if _parse_datetime(as_of_date) >= _parse_datetime(available) else "needs_data"


def raw_stat_field_mapping_contract() -> dict[str, tuple[str, ...]]:
    return {
        "pass_yds": ("pass_yds", "passing_yards"),
        "pass_td": ("pass_td", "passing_tds"),
        "pass_int": ("pass_int", "interceptions"),
        "pass_first_downs": ("pass_first_downs", "passing_first_downs"),
        "pass_2pt": ("pass_2pt", "passing_2pt"),
        "sacks_suffered": ("sacks_suffered",),
        "carries": ("carries", "rush_att", "rushing_attempts"),
        "rush_yds": ("rush_yds", "rushing_yards"),
        "rush_td": ("rush_td", "rushing_tds"),
        "rush_first_downs": ("rush_first_downs", "rushing_first_downs"),
        "rush_2pt": ("rush_2pt", "rushing_2pt"),
        "receptions": ("receptions", "rec"),
        "rec_yds": ("rec_yds", "receiving_yards"),
        "rec_td": ("rec_td", "receiving_tds"),
        "rec_first_downs": ("rec_first_downs", "receiving_first_downs"),
        "rec_2pt": ("rec_2pt", "receiving_2pt"),
        "fumbles_lost": ("fumbles_lost", "fumble_lost"),
        "return_yds": ("return_yds", "return_yards"),
        "return_td": ("return_td", "return_tds"),
        "special_td": ("special_td", "special_tds"),
        "fumble_recovery_td": ("fumble_recovery_td", "fumble_recovery_tds"),
        "misc_yds": ("misc_yds", "misc_yards"),
    }


def validate_raw_stat_mapping(
    source_columns: Sequence[str],
    *,
    mapping: Mapping[str, Sequence[str]] | None = None,
) -> tuple[RawStatMappingIssue, ...]:
    mapping = mapping or raw_stat_field_mapping_contract()
    source_set = {column.lower() for column in source_columns}
    issues: list[RawStatMappingIssue] = []
    for scoring_component, aliases in mapping.items():
        present = next((alias for alias in aliases if alias.lower() in source_set), "")
        issues.append(
            RawStatMappingIssue(
                scoring_component=scoring_component,
                accepted_source_fields=tuple(aliases),
                present_source_field=present,
                readiness_status="ready" if present else "needs_data",
                notes=(
                    "Mapped to Sprint 1 scoring component."
                    if present
                    else "Missing required raw stat field for Sprint 1 scoring component."
                ),
            )
        )
    return tuple(issues)


def audit_source_records_for_leakage(
    *,
    row_family: str,
    source_path: str | Path,
    source_family: str,
    records: Sequence[Mapping[str, Any]],
    input_snapshot_date: str,
    timestamp_fields: Sequence[str] = DEFAULT_SOURCE_TIMESTAMP_FIELDS,
) -> tuple[RowLevelLeakageAudit, ...]:
    _require_supported_row_family(row_family)
    classification_family, classification, manual_review, note = classify_source(
        source_path,
        tuple(records[0].keys()) if records else (),
    )
    resolved_family = source_family or classification_family
    audits: list[RowLevelLeakageAudit] = []
    for index, record in enumerate(records, start=1):
        row_id = str(
            record.get("row_id")
            or record.get("player_id")
            or record.get("player_name")
            or f"row_{index}"
        )
        timestamp = _record_timestamp(record, timestamp_fields)
        readiness = "ready"
        issue_type = ""
        notes = "Passed timestamp and source checks."
        if classification == "blocked" or _record_has_forbidden_context(record):
            readiness = "blocked"
            issue_type = "forbidden_source_or_field"
            notes = "Forbidden source/path/header/value detected."
        elif classification == "unknown" or manual_review:
            readiness = "manual_review_required"
            issue_type = "unknown_source"
            notes = note
        elif timestamp is None:
            readiness = "blocked"
            issue_type = "missing_source_timestamp"
            notes = "Missing source timestamp blocks production row emission."
        elif _parse_datetime(timestamp) > _parse_datetime(input_snapshot_date):
            readiness = "blocked"
            issue_type = "post_cutoff_source_timestamp"
            notes = "Source timestamp is after input snapshot date."
        audits.append(
            RowLevelLeakageAudit(
                row_identifier=row_id,
                row_family=row_family,
                source_family=resolved_family,
                source_path=str(source_path),
                source_max_timestamp=timestamp,
                input_snapshot_date=input_snapshot_date,
                readiness_status=readiness,
                issue_type=issue_type,
                notes=notes,
            )
        )
    return tuple(audits)


def build_data_readiness_report(
    *,
    manifests: Sequence[RowFamilySourceManifest],
    leakage_audits: Sequence[RowLevelLeakageAudit],
    raw_stat_mapping_issues: Sequence[RawStatMappingIssue],
) -> DataReadinessReport:
    blocked_manifest_count = sum(
        1 for manifest in manifests if manifest.readiness_status == "blocked"
    )
    manual_manifest_count = sum(
        1 for manifest in manifests if manifest.readiness_status == "manual_review_required"
    )
    blocked_audits = sum(1 for audit in leakage_audits if audit.readiness_status == "blocked")
    missing_mapping = sum(
        1 for issue in raw_stat_mapping_issues if issue.readiness_status != "ready"
    )
    status = "ready"
    blockers: list[str] = []
    if blocked_manifest_count or blocked_audits:
        status = "blocked"
        blockers.append("blocked manifest or row-level leakage audit")
    if missing_mapping:
        status = "needs_data" if status == "ready" else status
        blockers.append("missing raw stat scoring component mapping")
    if manual_manifest_count and status == "ready":
        status = "manual_review_required"
        blockers.append("manual source review required")
    notes = "Ready for Sprint 4 v0 base-rate dry run." if not blockers else "; ".join(blockers)
    payload = {
        "manifest_hashes": [manifest.manifest_hash for manifest in manifests],
        "blocked_manifest_count": blocked_manifest_count,
        "manual_manifest_count": manual_manifest_count,
        "blocked_audits": blocked_audits,
        "missing_mapping": missing_mapping,
        "status": status,
    }
    return DataReadinessReport(
        report_id="nwr_readiness_" + _sha256(payload)[:16],
        readiness_status=status,
        manifest_count=len(manifests),
        blocked_manifest_count=blocked_manifest_count,
        manual_review_manifest_count=manual_manifest_count,
        leakage_audit_blocked_count=blocked_audits,
        missing_mapping_count=missing_mapping,
        notes=notes,
    )


def write_source_manifest_exports(
    *,
    output_dir: str | Path,
    manifests: Sequence[RowFamilySourceManifest],
    leakage_audits: Sequence[RowLevelLeakageAudit],
    raw_stat_mapping_issues: Sequence[RawStatMappingIssue],
    readiness_report: DataReadinessReport,
) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_dicts(
        output / "row_family_source_manifests.csv",
        [_manifest_export_row(manifest) for manifest in manifests],
    )
    _write_dicts(
        output / "source_manifest_entries.csv",
        [
            {"manifest_id": manifest.manifest_id, **asdict(entry)}
            for manifest in manifests
            for entry in manifest.source_entries
        ],
    )
    _write_dicts(
        output / "row_level_leakage_audit.csv",
        [asdict(audit) for audit in leakage_audits],
    )
    _write_dicts(
        output / "raw_stat_mapping_readiness.csv",
        [asdict(issue) for issue in raw_stat_mapping_issues],
    )
    _write_dicts(
        output / "data_readiness_report.csv",
        [asdict(readiness_report)],
    )


def scoring_component_names() -> tuple[str, ...]:
    # The scoring rules dataclass is the source of truth for point weights; these are the raw stat
    # components consumed by score_player_week through alias mapping.
    _ = ScoringRules()
    return tuple(raw_stat_field_mapping_contract().keys())


def _entry_readiness(*, classification: str, missing_timestamp: bool) -> str:
    if classification == "blocked" or missing_timestamp:
        return "blocked"
    if classification in {"unknown", "display_only"}:
        return "manual_review_required"
    return "ready"


def _manifest_readiness(
    entries: Sequence[SourceManifestEntry],
    missing_required: Sequence[str],
) -> str:
    if missing_required or any(entry.readiness_status == "blocked" for entry in entries):
        return "blocked"
    if any(entry.readiness_status == "manual_review_required" for entry in entries):
        return "manual_review_required"
    return "ready"


def _record_timestamp(
    record: Mapping[str, Any],
    timestamp_fields: Sequence[str],
) -> str | None:
    for field in timestamp_fields:
        value = record.get(field)
        if not _missing(value):
            return _parse_datetime(str(value)).isoformat()
    return None


def _record_has_forbidden_context(record: Mapping[str, Any]) -> bool:
    for key, value in record.items():
        blob = _normalize(f"{key} {value}")
        if any(_normalize(token) in blob for token in FORBIDDEN_SOURCE_TOKENS):
            return True
    return False


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_csv_header(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(next(csv.reader(handle), ()))


def _manifest_export_row(manifest: RowFamilySourceManifest) -> dict[str, Any]:
    return {
        "manifest_id": manifest.manifest_id,
        "row_family": manifest.row_family,
        "cutoff_id": manifest.cutoff_id,
        "input_snapshot_date": manifest.input_snapshot_date,
        "source_count": len(manifest.source_entries),
        "required_source_families": "|".join(manifest.required_source_families),
        "missing_required_source_families": "|".join(
            manifest.missing_required_source_families
        ),
        "readiness_status": manifest.readiness_status,
        "manifest_hash": manifest.manifest_hash,
    }


def _write_dicts(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = tuple(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _horizon_years(target_horizon: str) -> int | None:
    normalized = _normalize(target_horizon)
    if normalized in {"sameyeartarget", "sameyear", "year1", "y1", "nextseason"}:
        return 1
    if normalized in {"nextyear", "year2", "y2"}:
        return 2
    if normalized in {"next3year", "next3years", "next3y", "years13", "year13"}:
        return 3
    if normalized in {"next5year", "next5years", "next5y", "years15", "year15"}:
        return 5
    return None


def _parse_datetime(value: str) -> datetime:
    if not value:
        raise ValueError("date value is required")
    cleaned = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _require_supported_row_family(row_family: str) -> None:
    if row_family not in SUPPORTED_HISTORICAL_ROW_TYPES:
        raise ValueError(
            f"Unsupported row_family {row_family!r}; supported families are "
            f"{', '.join(SUPPORTED_HISTORICAL_ROW_TYPES)}."
        )


def _matching_family(haystack: str, tokens: Sequence[str]) -> str:
    for token in tokens:
        if _normalize(token) in haystack:
            return token
    return "unknown"


def _normalize(value: str) -> str:
    return "".join(char for char in str(value).lower() if char.isalnum())


def _missing(value: Any) -> bool:
    return value is None or str(value).strip() == ""
