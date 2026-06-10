from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.services.nwr_outcome_training_row_service import (
    FeatureLegalityAudit,
    FeatureLegalityIssue,
    FeatureSnapshot,
    PredictionSnapshot,
    SourceAllowlistRule,
    TrainingRow,
    build_training_row,
    materialize_training_row_if_label_available,
    missingness_mask,
    validate_feature_legality,
)

SUPPORTED_HISTORICAL_ROW_TYPES = (
    "rookie_post_draft",
    "all_player_pre_week1",
    "offseason_carryover",
)

REQUIRED_IDENTITY_FIELDS = ("player_id", "player_name", "position")
DEFAULT_OPTIONAL_FEATURES = (
    "age_at_snapshot",
    "experience_at_snapshot",
    "team_at_snapshot",
    "previous_season_qualified_ppg",
    "previous_season_total_points",
    "draft_round",
    "draft_pick",
    "games_played_previous_season",
    "rush_first_downs_previous_season",
    "receiving_first_downs_previous_season",
    "injury_context_status",
    "opportunity_context_status",
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
    "prior_draft_history",
    "legacy_private_score",
    "private_score",
    "prior_model_output",
    "hindsight_note",
)

DISPLAY_ONLY_TOKENS = (
    "draft_prep",
    "prior_league_draft",
    "market_context",
    "league_context",
    "comparison",
)

ALLOWED_SOURCE_HINTS = {
    "scoring": "nwr_scoring_rules",
    "week": "nwr_historical_week_scores",
    "weekly": "nwr_historical_week_scores",
    "stats": "nflverse_raw_stats",
    "season_label": "nwr_historical_season_labels",
    "outcome": "nwr_historical_season_labels",
    "player_dim": "nwr_player_dim",
    "players": "nwr_player_dim",
    "draft_capital": "official_draft_capital",
    "injury": "injury_status_source",
    "rotowire_raw": "rotowire_raw_stats",
    "rotowire_stats": "rotowire_raw_stats",
    "rotowire_role": "rotowire_role_usage",
    "workout": "rotowire_workouts",
}


@dataclass(frozen=True)
class HistoricalSourceInventoryEntry:
    source_path: str
    source_family: str
    classification: str
    row_count: int | None
    columns: tuple[str, ...]
    required_fields_present: tuple[str, ...]
    required_fields_missing: tuple[str, ...]
    manual_review_required: bool
    notes: str


@dataclass(frozen=True)
class HistoricalSourceInventory:
    entries: tuple[HistoricalSourceInventoryEntry, ...]


@dataclass(frozen=True)
class CandidateRowEmission:
    row_type: str
    row_id: str | None
    snapshot_hash: str | None
    player_id: str
    player_name: str
    position: str
    prediction_snapshot: PredictionSnapshot
    feature_snapshots: tuple[FeatureSnapshot, ...]
    feature_vector: dict[str, Any]
    missingness_mask: dict[str, bool]
    legality_audit: FeatureLegalityAudit
    training_row: TrainingRow | None
    blocked_reason: str


@dataclass(frozen=True)
class SourceCoverageReport:
    report_type: str
    total_rows: int
    covered_rows: int
    missing_rows: int
    notes: str


def build_historical_source_inventory(
    source_paths: Sequence[str | Path],
    *,
    required_fields: Sequence[str] = REQUIRED_IDENTITY_FIELDS,
) -> HistoricalSourceInventory:
    entries = tuple(_inventory_entry(Path(path), required_fields) for path in source_paths)
    return HistoricalSourceInventory(entries=entries)


def emit_candidate_training_row(
    *,
    row_type: str,
    player_record: Mapping[str, Any],
    snapshot: PredictionSnapshot,
    feature_snapshots: Sequence[FeatureSnapshot],
    as_of_date: str,
    optional_feature_names: Sequence[str] = DEFAULT_OPTIONAL_FEATURES,
    source_allowlist: Mapping[str, SourceAllowlistRule] | None = None,
    parser_version: str = "nwr_outcome_historical_row_factory_v1",
    label_schema_version: str = "nwr_outcome_labels_v1",
    outcome_window: str = "regular_season",
) -> CandidateRowEmission:
    _require_supported_row_type(row_type)
    _reject_stale_prior_row(player_record, snapshot)
    missing_identity = tuple(
        field for field in REQUIRED_IDENTITY_FIELDS if _missing(player_record.get(field))
    )
    if missing_identity:
        return _blocked_candidate(
            row_type=row_type,
            player_record=player_record,
            snapshot=snapshot,
            feature_snapshots=tuple(feature_snapshots),
            issue_type="missing_identity_fields",
            message="Missing required identity fields: " + ", ".join(missing_identity),
        )

    legality = validate_feature_legality(
        list(feature_snapshots),
        input_snapshot_date=snapshot.input_snapshot_date,
        label_available_date=snapshot.label_available_date,
        source_allowlist=source_allowlist,
    )
    feature_vector = _feature_vector(feature_snapshots, optional_feature_names)
    mask = missingness_mask(feature_vector)
    if not legality.valid:
        return CandidateRowEmission(
            row_type=row_type,
            row_id=None,
            snapshot_hash=None,
            player_id=str(player_record["player_id"]),
            player_name=str(player_record["player_name"]),
            position=str(player_record["position"]).upper(),
            prediction_snapshot=snapshot,
            feature_snapshots=tuple(feature_snapshots),
            feature_vector=feature_vector,
            missingness_mask=mask,
            legality_audit=legality,
            training_row=None,
            blocked_reason="feature_legality_failed",
        )

    row = build_training_row(
        player_id=str(player_record["player_id"]),
        player_name=str(player_record["player_name"]),
        position=str(player_record["position"]).upper(),
        snapshot=snapshot,
        team_at_snapshot=str(
            player_record.get("team_at_snapshot") or player_record.get("team") or ""
        ),
        age_at_snapshot=_optional_float(player_record.get("age_at_snapshot")),
        experience_at_snapshot=_optional_int(player_record.get("experience_at_snapshot")),
        feature_vector=feature_vector,
        outcome_window=outcome_window,
        label_schema_version=label_schema_version,
        source_max_timestamp=_source_max_timestamp(feature_snapshots, snapshot.input_snapshot_date),
        manual_review_status=str(player_record.get("manual_review_status") or "not_required"),
        probability_status="in_development",
    )
    materialized = materialize_training_row_if_label_available(row, as_of_date=as_of_date)
    blocked_reason = "" if materialized is not None else "label_not_available"
    return CandidateRowEmission(
        row_type=row_type,
        row_id=row.row_id,
        snapshot_hash=row.snapshot_hash,
        player_id=row.player_id,
        player_name=row.player_name,
        position=row.position,
        prediction_snapshot=snapshot,
        feature_snapshots=tuple(feature_snapshots),
        feature_vector=feature_vector,
        missingness_mask=row.missingness_mask,
        legality_audit=legality,
        training_row=materialized,
        blocked_reason=blocked_reason,
    )


def coverage_reports(
    candidates: Sequence[CandidateRowEmission],
) -> tuple[SourceCoverageReport, ...]:
    total = len(candidates)
    identity_covered = sum(
        1 for row in candidates if row.player_id and row.player_name and row.position
    )
    legality_covered = sum(1 for row in candidates if row.legality_audit.valid)
    materialized = sum(1 for row in candidates if row.training_row is not None)
    first_down_covered = sum(
        1
        for row in candidates
        if any("first_down" in feature.feature_name for feature in row.feature_snapshots)
    )
    injury_covered = sum(
        1
        for row in candidates
        if any("injury" in feature.feature_name for feature in row.feature_snapshots)
    )
    return (
        SourceCoverageReport(
            report_type="player_identity_coverage",
            total_rows=total,
            covered_rows=identity_covered,
            missing_rows=total - identity_covered,
            notes="Requires player_id, player_name, and position.",
        ),
        SourceCoverageReport(
            report_type="feature_legality_coverage",
            total_rows=total,
            covered_rows=legality_covered,
            missing_rows=total - legality_covered,
            notes="Rows with all feature snapshots passing Sprint 2 legality checks.",
        ),
        SourceCoverageReport(
            report_type="materialized_training_rows",
            total_rows=total,
            covered_rows=materialized,
            missing_rows=total - materialized,
            notes="Materialized only when label_available_date has passed.",
        ),
        SourceCoverageReport(
            report_type="first_down_field_coverage",
            total_rows=total,
            covered_rows=first_down_covered,
            missing_rows=total - first_down_covered,
            notes="Feature names containing first_down.",
        ),
        SourceCoverageReport(
            report_type="injury_opportunity_coverage",
            total_rows=total,
            covered_rows=injury_covered,
            missing_rows=total - injury_covered,
            notes="Feature names containing injury.",
        ),
    )


def missingness_summary(candidates: Sequence[CandidateRowEmission]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for candidate in candidates:
        for feature_name, is_missing in candidate.missingness_mask.items():
            if is_missing:
                counts[feature_name] += 1
    return dict(counts)


def blocked_source_summary(inventory: HistoricalSourceInventory) -> dict[str, int]:
    counts: Counter[str] = Counter(entry.classification for entry in inventory.entries)
    return dict(counts)


def write_dry_run_exports(
    *,
    output_dir: str | Path,
    inventory: HistoricalSourceInventory,
    candidates: Sequence[CandidateRowEmission],
) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_dict_rows(
        output / "historical_source_inventory.csv",
        [asdict(entry) for entry in inventory.entries],
    )
    _write_dict_rows(
        output / "candidate_training_rows_dry_run.csv",
        [_candidate_export_row(candidate) for candidate in candidates],
    )
    _write_dict_rows(
        output / "source_coverage_report.csv",
        [asdict(report) for report in coverage_reports(candidates)],
    )
    _write_dict_rows(
        output / "missingness_summary.csv",
        [
            {"feature_name": feature_name, "missing_count": count}
            for feature_name, count in sorted(missingness_summary(candidates).items())
        ],
    )
    _write_dict_rows(
        output / "blocked_forbidden_source_summary.csv",
        [
            {"classification": classification, "source_count": count}
            for classification, count in sorted(blocked_source_summary(inventory).items())
        ],
    )


def _inventory_entry(path: Path, required_fields: Sequence[str]) -> HistoricalSourceInventoryEntry:
    columns: tuple[str, ...] = ()
    row_count: int | None = None
    notes: list[str] = []
    if path.exists() and path.suffix.lower() == ".csv":
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.reader(handle)
                columns = tuple(next(reader, ()))
                row_count = sum(1 for _ in reader)
        except OSError as exc:
            notes.append(f"Could not inspect CSV: {exc}")
    elif not path.exists():
        notes.append("Source file missing.")

    source_family = _source_family(path, columns)
    classification = _classification(path, columns, source_family)
    present = tuple(field for field in required_fields if field in columns)
    missing = tuple(field for field in required_fields if field not in columns)
    manual_review_required = classification in ("unknown", "display_only") or bool(missing)
    if classification == "blocked":
        notes.append("Blocked by forbidden source/input policy.")
    if classification == "unknown":
        notes.append("Unknown source family; manual review required before training use.")
    if missing:
        notes.append("Missing required fields: " + ", ".join(missing))
    return HistoricalSourceInventoryEntry(
        source_path=str(path),
        source_family=source_family,
        classification=classification,
        row_count=row_count,
        columns=columns,
        required_fields_present=present,
        required_fields_missing=missing,
        manual_review_required=manual_review_required,
        notes=" ".join(notes) or "Inspected.",
    )


def _source_family(path: Path, columns: Sequence[str]) -> str:
    haystack = _normalize(" ".join([str(path), *columns]))
    for token in FORBIDDEN_SOURCE_TOKENS:
        if _normalize(token) in haystack:
            return token
    for token, family in ALLOWED_SOURCE_HINTS.items():
        if _normalize(token) in haystack:
            return family
    return "unknown"


def _classification(path: Path, columns: Sequence[str], source_family: str) -> str:
    haystack = _normalize(" ".join([str(path), *columns]))
    if any(_normalize(token) in haystack for token in FORBIDDEN_SOURCE_TOKENS):
        return "blocked"
    if any(_normalize(token) in haystack for token in DISPLAY_ONLY_TOKENS):
        return "display_only"
    if source_family == "unknown":
        return "unknown"
    return "allowed"


def _feature_vector(
    feature_snapshots: Sequence[FeatureSnapshot],
    optional_feature_names: Sequence[str],
) -> dict[str, Any]:
    vector = {feature.feature_name: feature.value for feature in feature_snapshots}
    for feature_name in optional_feature_names:
        vector.setdefault(feature_name, None)
    return vector


def _source_max_timestamp(
    feature_snapshots: Sequence[FeatureSnapshot],
    fallback: str,
) -> str:
    timestamps = [
        feature.source_max_timestamp
        for feature in feature_snapshots
        if feature.source_max_timestamp
    ]
    return max(timestamps) if timestamps else fallback


def _blocked_candidate(
    *,
    row_type: str,
    player_record: Mapping[str, Any],
    snapshot: PredictionSnapshot,
    feature_snapshots: tuple[FeatureSnapshot, ...],
    issue_type: str,
    message: str,
) -> CandidateRowEmission:
    audit = FeatureLegalityAudit(
        valid=False,
        issues=(FeatureLegalityIssue("", issue_type, "error", message),),
    )
    feature_vector = _feature_vector(feature_snapshots, DEFAULT_OPTIONAL_FEATURES)
    return CandidateRowEmission(
        row_type=row_type,
        row_id=None,
        snapshot_hash=None,
        player_id=str(player_record.get("player_id") or ""),
        player_name=str(player_record.get("player_name") or ""),
        position=str(player_record.get("position") or "").upper(),
        prediction_snapshot=snapshot,
        feature_snapshots=feature_snapshots,
        feature_vector=feature_vector,
        missingness_mask=missingness_mask(feature_vector),
        legality_audit=audit,
        training_row=None,
        blocked_reason=issue_type,
    )


def _reject_stale_prior_row(player_record: Mapping[str, Any], snapshot: PredictionSnapshot) -> None:
    if _bool(player_record.get("stale_prior_row")):
        raise ValueError("Stale prior-row reuse is blocked.")
    prior_cutoff = str(player_record.get("prior_row_cutoff_id") or "")
    if prior_cutoff and prior_cutoff != snapshot.cutoff_id:
        raise ValueError("Stale prior-row reuse is blocked.")


def _require_supported_row_type(row_type: str) -> None:
    if row_type not in SUPPORTED_HISTORICAL_ROW_TYPES:
        raise ValueError(
            f"Unsupported row_type {row_type!r}; supported row types are "
            f"{', '.join(SUPPORTED_HISTORICAL_ROW_TYPES)}."
        )


def _candidate_export_row(candidate: CandidateRowEmission) -> dict[str, Any]:
    return {
        "row_type": candidate.row_type,
        "row_id": candidate.row_id or "",
        "snapshot_hash": candidate.snapshot_hash or "",
        "player_id": candidate.player_id,
        "player_name": candidate.player_name,
        "position": candidate.position,
        "feature_count": len(candidate.feature_vector),
        "missing_feature_count": sum(candidate.missingness_mask.values()),
        "legality_valid": candidate.legality_audit.valid,
        "training_row_materialized": candidate.training_row is not None,
        "blocked_reason": candidate.blocked_reason,
    }


def _write_dict_rows(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = tuple(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _optional_float(value: Any) -> float | None:
    if _missing(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    if _missing(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _missing(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _normalize(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())
