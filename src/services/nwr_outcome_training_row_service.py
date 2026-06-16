from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

SUPPORTED_ROW_TYPES = ("rookie_post_draft", "all_player_pre_week1", "offseason_carryover")

APP_PROBABILITY_STATUSES = (
    "ready",
    "in_development",
    "needs_data",
    "model_unavailable",
    "insufficient_evidence",
    "not_applicable",
    "leakage_audit_failed",
    "source_stale",
    "manual_review_pending",
)

IDENTITY_FIELDS_BLOCKED_AS_FEATURES = ("player_id", "player_name")

FORBIDDEN_FEATURE_FRAGMENTS = (
    "adp",
    "fantasypros",
    "public_rank",
    "public_projection",
    "public_consensus",
    "consensus",
    "startup",
    "startup_rank",
    "dynasty_rank",
    "trade_calculator",
    "trade_value",
    "market_rank",
    "league_rank",
    "rotowire_projection",
    "rotowire_ranking",
    "rotowire_outlook",
    "rotowire_value",
    "prior_nwr_private_score",
    "legacy_private_score",
    "private_score",
    "prior_model_output",
    "prior_nwr_model_output",
    "prior_fantasy_draft_history",
    "fantasy_acquisition_cost",
    "acquisition_cost",
    "same_season_final_stats",
    "hindsight_note",
    "post_cutoff_update",
)

DEFAULT_ALLOWED_SOURCE_FAMILIES = (
    "nwr_scoring_rules",
    "nwr_player_dim",
    "nwr_historical_week_scores",
    "nwr_historical_season_labels",
    "nflverse_raw_stats",
    "rotowire_raw_stats",
    "rotowire_role_usage",
    "rotowire_workouts",
    "official_draft_capital",
    "injury_status_source",
    "manual_private_scouting_notes",
)

DEFAULT_BLOCKED_SOURCE_FAMILIES = (
    "adp",
    "fantasypros",
    "public_rankings",
    "public_projections",
    "public_consensus",
    "startup_rankings",
    "trade_calculators",
    "market_rank",
    "league_rank",
    "rotowire_projections",
    "rotowire_rankings",
    "rotowire_outlooks",
    "rotowire_values",
    "prior_fantasy_draft_history",
    "legacy_private_score",
    "prior_nwr_model_outputs",
    "hindsight_notes",
)


@dataclass(frozen=True)
class SourceAllowlistRule:
    source_family: str
    allowed_for_features: bool
    allowed_fields: tuple[str, ...] = ()
    blocked_fields: tuple[str, ...] = ()
    allowed_use: str = "training_feature_input"
    blocked_use: str = ""
    notes: str = ""


@dataclass(frozen=True)
class PredictionSnapshot:
    cutoff_id: str
    row_type: str
    prediction_date: str
    input_snapshot_date: str
    label_available_date: str
    target_season: int
    target_horizon: str
    parser_version: str
    source_manifest: str


@dataclass(frozen=True)
class FeatureSnapshot:
    feature_name: str
    value: Any
    source_family: str
    source_field: str
    source_available_at: str
    source_max_timestamp: str
    lineage: tuple[str, ...] = ()
    future_data_flag: bool = False
    target_window_start: str = ""
    target_window_end: str = ""


@dataclass(frozen=True)
class TrainingRow:
    row_id: str
    player_id: str
    player_name: str
    position: str
    row_type: str
    cutoff_id: str
    prediction_date: str
    input_snapshot_date: str
    source_max_timestamp: str
    label_available_date: str
    target_season: int
    target_horizon: str
    team_at_snapshot: str
    age_at_snapshot: float | None
    experience_at_snapshot: int | None
    feature_vector: dict[str, Any]
    missingness_mask: dict[str, bool]
    outcome_window: str
    label_schema_version: str
    source_manifest: str
    parser_version: str
    snapshot_hash: str
    manual_review_status: str
    probability_status: str = "in_development"


@dataclass(frozen=True)
class FeatureLegalityIssue:
    feature_name: str
    issue_type: str
    severity: str
    message: str


@dataclass(frozen=True)
class FeatureLegalityAudit:
    valid: bool
    issues: tuple[FeatureLegalityIssue, ...]


@dataclass(frozen=True)
class ModelSplitSpec:
    split_id: str
    split_type: str = "walk_forward"
    train_start_season: int | None = None
    train_end_season: int | None = None
    validation_season: int | None = None
    test_season: int | None = None
    notes: str = "Skeleton only; no model training in Sprint 2."


@dataclass(frozen=True)
class PointInTimeContracts:
    prediction_snapshots: tuple[str, ...] = (
        "cutoff_id",
        "row_type",
        "prediction_date",
        "input_snapshot_date",
        "label_available_date",
        "target_season",
        "target_horizon",
        "parser_version",
        "source_manifest",
    )
    feature_snapshots: tuple[str, ...] = (
        "feature_name",
        "value",
        "source_family",
        "source_field",
        "source_available_at",
        "source_max_timestamp",
        "lineage",
        "future_data_flag",
        "target_window_start",
        "target_window_end",
    )
    training_rows: tuple[str, ...] = (
        "row_id",
        "player_id",
        "player_name",
        "position",
        "row_type",
        "cutoff_id",
        "prediction_date",
        "input_snapshot_date",
        "source_max_timestamp",
        "label_available_date",
        "target_season",
        "target_horizon",
        "team_at_snapshot",
        "age_at_snapshot",
        "experience_at_snapshot",
        "feature_vector",
        "missingness_mask",
        "outcome_window",
        "label_schema_version",
        "source_manifest",
        "parser_version",
        "snapshot_hash",
        "manual_review_status",
    )
    feature_legality_audit: tuple[str, ...] = (
        "feature_name",
        "issue_type",
        "severity",
        "message",
    )
    model_split_registry: tuple[str, ...] = (
        "split_id",
        "split_type",
        "train_start_season",
        "train_end_season",
        "validation_season",
        "test_season",
        "notes",
    )


def default_source_allowlist() -> dict[str, SourceAllowlistRule]:
    rules: dict[str, SourceAllowlistRule] = {}
    for source in DEFAULT_ALLOWED_SOURCE_FAMILIES:
        rules[source] = SourceAllowlistRule(
            source_family=source,
            allowed_for_features=True,
            blocked_fields=FORBIDDEN_FEATURE_FRAGMENTS,
            notes="Allowed only when timestamp and lineage checks pass.",
        )
    for source in DEFAULT_BLOCKED_SOURCE_FAMILIES:
        rules[source] = SourceAllowlistRule(
            source_family=source,
            allowed_for_features=False,
            blocked_use="predictive_training_feature",
            notes="Blocked by anti-leakage policy.",
        )
    return rules


def generate_row_id(
    *,
    row_type: str,
    player_id: str,
    position: str,
    cutoff_id: str,
    input_snapshot_date: str,
    target_season: int,
    target_horizon: str,
) -> str:
    _require_supported_row_type(row_type)
    payload = {
        "row_type": row_type,
        "player_id": player_id,
        "position": position.upper(),
        "cutoff_id": cutoff_id,
        "input_snapshot_date": input_snapshot_date,
        "target_season": target_season,
        "target_horizon": target_horizon,
    }
    return "nwr_tr_" + _sha256(payload)[:24]


def snapshot_hash(row_payload: Mapping[str, Any]) -> str:
    return _sha256(row_payload)


def missingness_mask(feature_vector: Mapping[str, Any]) -> dict[str, bool]:
    return {key: _is_missing(value) for key, value in feature_vector.items()}


def build_training_row(
    *,
    player_id: str,
    player_name: str,
    position: str,
    snapshot: PredictionSnapshot,
    team_at_snapshot: str,
    age_at_snapshot: float | None,
    experience_at_snapshot: int | None,
    feature_vector: Mapping[str, Any],
    outcome_window: str,
    label_schema_version: str,
    source_max_timestamp: str,
    manual_review_status: str = "not_required",
    probability_status: str = "in_development",
) -> TrainingRow:
    _require_supported_row_type(snapshot.row_type)
    _require_probability_status(probability_status)
    if "player_id" in feature_vector or "player_name" in feature_vector:
        raise ValueError("player_id and player_name are identity fields, not model features.")
    row_id = generate_row_id(
        row_type=snapshot.row_type,
        player_id=player_id,
        position=position,
        cutoff_id=snapshot.cutoff_id,
        input_snapshot_date=snapshot.input_snapshot_date,
        target_season=snapshot.target_season,
        target_horizon=snapshot.target_horizon,
    )
    row_payload = {
        "row_id": row_id,
        "player_id": player_id,
        "player_name": player_name,
        "position": position.upper(),
        "row_type": snapshot.row_type,
        "cutoff_id": snapshot.cutoff_id,
        "prediction_date": snapshot.prediction_date,
        "input_snapshot_date": snapshot.input_snapshot_date,
        "source_max_timestamp": source_max_timestamp,
        "label_available_date": snapshot.label_available_date,
        "target_season": snapshot.target_season,
        "target_horizon": snapshot.target_horizon,
        "team_at_snapshot": team_at_snapshot,
        "age_at_snapshot": age_at_snapshot,
        "experience_at_snapshot": experience_at_snapshot,
        "feature_vector": dict(feature_vector),
        "missingness_mask": missingness_mask(feature_vector),
        "outcome_window": outcome_window,
        "label_schema_version": label_schema_version,
        "source_manifest": snapshot.source_manifest,
        "parser_version": snapshot.parser_version,
        "manual_review_status": manual_review_status,
        "probability_status": probability_status,
    }
    return TrainingRow(snapshot_hash=snapshot_hash(row_payload), **row_payload)


def validate_training_row_schema(row: TrainingRow) -> FeatureLegalityAudit:
    issues: list[FeatureLegalityIssue] = []
    try:
        _require_supported_row_type(row.row_type)
    except ValueError as exc:
        issues.append(_issue("", "unsupported_row_type", str(exc)))
    try:
        _require_probability_status(row.probability_status)
    except ValueError as exc:
        issues.append(_issue("", "invalid_probability_status", str(exc)))
    if "player_id" in row.feature_vector or "player_name" in row.feature_vector:
        issues.append(
            _issue(
                "feature_vector",
                "identity_feature_blocked",
                "player_id and player_name cannot be admitted as model features.",
            )
        )
    for field_name in PointInTimeContracts().training_rows:
        if not hasattr(row, field_name):
            issues.append(
                _issue(field_name, "missing_contract_field", "Required row field missing.")
            )
    return FeatureLegalityAudit(valid=not issues, issues=tuple(issues))


def validate_feature_legality(
    features: list[FeatureSnapshot],
    *,
    input_snapshot_date: str,
    label_available_date: str,
    source_allowlist: Mapping[str, SourceAllowlistRule] | None = None,
) -> FeatureLegalityAudit:
    allowlist = source_allowlist or default_source_allowlist()
    issues: list[FeatureLegalityIssue] = []
    input_dt = _parse_date(input_snapshot_date)
    label_dt = _parse_date(label_available_date)
    for feature in features:
        rule = allowlist.get(feature.source_family)
        if rule is None:
            issues.append(
                _issue(
                    feature.feature_name,
                    "source_not_allowlisted",
                    f"Source family is not allowlisted: {feature.source_family}",
                )
            )
        elif not rule.allowed_for_features:
            issues.append(
                _issue(
                    feature.feature_name,
                    "source_blocked",
                    f"Source family is blocked for predictive features: {feature.source_family}",
                )
            )
        if _contains_forbidden_fragment(feature.feature_name, feature.source_field):
            issues.append(
                _issue(
                    feature.feature_name,
                    "forbidden_feature_family",
                    "Feature or source field references a prohibited input family.",
                )
            )
        if feature.source_available_at and _parse_date(feature.source_available_at) > input_dt:
            issues.append(
                _issue(
                    feature.feature_name,
                    "post_cutoff_source_timestamp",
                    "Feature source availability is after the input snapshot date.",
                )
            )
        if feature.source_max_timestamp and _parse_date(feature.source_max_timestamp) > input_dt:
            issues.append(
                _issue(
                    feature.feature_name,
                    "post_cutoff_source_max_timestamp",
                    "Feature source max timestamp is after the input snapshot date.",
                )
            )
        if feature.future_data_flag:
            issues.append(
                _issue(
                    feature.feature_name,
                    "future_data_flag",
                    "Feature is flagged as future or post-cutoff data.",
                )
            )
        if not feature.lineage:
            issues.append(
                _issue(
                    feature.feature_name,
                    "incomplete_lineage",
                    "Feature must include source lineage receipts.",
                )
            )
        if _target_window_overlaps(
            feature.target_window_start,
            feature.target_window_end,
            input_dt=input_dt,
            label_dt=label_dt,
        ):
            issues.append(
                _issue(
                    feature.feature_name,
                    "target_window_overlap",
                    "Feature source overlaps the target/outcome window.",
                )
            )
    return FeatureLegalityAudit(valid=not issues, issues=tuple(issues))


def materialize_training_row_if_label_available(
    row: TrainingRow,
    *,
    as_of_date: str,
) -> TrainingRow | None:
    return row if _parse_date(as_of_date) >= _parse_date(row.label_available_date) else None


def model_split_registry_skeleton() -> tuple[ModelSplitSpec, ...]:
    return (
        ModelSplitSpec(
            split_id="walk_forward_v1_2021_train_2022_validation_2023_test",
            train_start_season=2021,
            train_end_season=2021,
            validation_season=2022,
            test_season=2023,
        ),
        ModelSplitSpec(
            split_id="walk_forward_v1_2021_2022_train_2023_validation_2024_test",
            train_start_season=2021,
            train_end_season=2022,
            validation_season=2023,
            test_season=2024,
        ),
    )


def contract_field_names() -> PointInTimeContracts:
    return PointInTimeContracts()


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _canonical_json(payload: Any) -> str:
    return json.dumps(_canonicalize(payload), sort_keys=True, separators=(",", ":"), default=str)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, list | tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def _contains_forbidden_fragment(*values: str) -> bool:
    normalized_values = [_normalize_forbidden_token(value) for value in values]
    normalized = "|".join(normalized_values)
    compact = normalized.replace("_", "")
    return any(
        fragment in normalized or fragment.replace("_", "") in compact
        for fragment in FORBIDDEN_FEATURE_FRAGMENTS
    )


def _normalize_forbidden_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _target_window_overlaps(
    start: str,
    end: str,
    *,
    input_dt: datetime,
    label_dt: datetime,
) -> bool:
    if not start and not end:
        return False
    start_dt = _parse_date(start or end)
    end_dt = _parse_date(end or start)
    return end_dt > input_dt and start_dt < label_dt


def _parse_date(value: str) -> datetime:
    if not value:
        raise ValueError("date value is required")
    cleaned = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _require_supported_row_type(row_type: str) -> None:
    if row_type not in SUPPORTED_ROW_TYPES:
        raise ValueError(
            f"Unsupported row_type {row_type!r}; supported types are "
            f"{', '.join(SUPPORTED_ROW_TYPES)}."
        )


def _require_probability_status(status: str) -> None:
    if status not in APP_PROBABILITY_STATUSES:
        raise ValueError(
            f"Unsupported probability status {status!r}; supported statuses are "
            + ", ".join(APP_PROBABILITY_STATUSES)
            + "."
        )


def _issue(feature_name: str, issue_type: str, message: str) -> FeatureLegalityIssue:
    return FeatureLegalityIssue(
        feature_name=feature_name,
        issue_type=issue_type,
        severity="error",
        message=message,
    )
