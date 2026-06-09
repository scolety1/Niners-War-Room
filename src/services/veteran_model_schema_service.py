from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

VETERAN_SOURCE_TABLES = (
    "veteran_player_inputs.csv",
    "veteran_feature_registry.csv",
    "veteran_feature_scores.csv",
    "veteran_source_catalog.csv",
    "veteran_audit_notes.csv",
)
VETERAN_OPTIONAL_SOURCE_TABLES = ("veteran_manual_overrides.csv",)

PLAYER_FILE = "veteran_player_inputs.csv"
REGISTRY_FILE = "veteran_feature_registry.csv"
FEATURE_SCORE_FILE = "veteran_feature_scores.csv"
SOURCE_CATALOG_FILE = "veteran_source_catalog.csv"
AUDIT_NOTES_FILE = "veteran_audit_notes.csv"
MANUAL_OVERRIDES_FILE = "veteran_manual_overrides.csv"

PLAYER_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")
POSITION_VALUES = {"QB", "RB", "WR", "TE"}
FEATURE_CATEGORY_VALUES = {
    "core",
    "secondary",
    "league_overlay",
    "post_draft",
    "confidence_modifier",
    "risk_flag",
    "upside_flag",
    "floor_flag",
    "display_only",
    "rejected",
}
PARENT_COMPONENT_VALUES = {
    "veteran_base_value",
    "keeper_score",
    "drop_candidate_score",
    "trade_value",
    "confidence_score",
    "display_only",
}
EVIDENCE_STRENGTH_VALUES = {"high", "medium", "low", "speculative"}
EXPECTED_DIRECTION_VALUES = {
    "higher_better",
    "lower_better_after_transform",
    "contextual_overlay",
    "display_only",
}
LVE_IMPORTANCE_VALUES = {
    "very_high",
    "high",
    "medium_high",
    "medium",
    "low_medium",
    "low",
    "display_only",
}
COEFFICIENT_POLICY_VALUES = {
    "evidence_backed_direction",
    "model_design_heuristic",
    "heuristic_calibration_required",
    "display_only_no_score",
    "rejected_no_score",
}
SCORING_STATUS_VALUES = {"active_v1", "future_candidate", "display_only", "rejected"}
SOURCE_CONFIDENCE_VALUES = {"verified", "derived", "manual", "estimated", "unknown"}
SOURCE_TYPE_VALUES = {
    "sleeper_api",
    "league_pdf",
    "market_rank",
    "market_proxy",
    "player_identity",
    "player_stats",
    "projection",
    "injury",
    "role_usage",
    "snap_counts",
    "depth_chart",
    "contract",
    "manual_note",
    "handwritten_history",
    "fixture",
}
SOURCE_FAMILY_VALUES = {
    "league_platform",
    "league_rank_doc",
    "market_rank",
    "market_proxy",
    "football_stats",
    "player_identity",
    "projection",
    "injury_report",
    "role_usage",
    "transaction_wire",
    "depth_chart",
    "contract_db",
    "manual_note",
    "handwritten_history",
}
SOURCE_DOMAIN_VALUES = {
    "league_state",
    "league_rank",
    "market",
    "identity",
    "production",
    "projection",
    "injury",
    "role_usage",
    "transaction",
    "depth_chart",
    "contract",
    "note",
    "history",
}
AUTHORITY_TIER_VALUES = {
    "tier_a_local_canonical",
    "tier_b_official_public",
    "tier_c_structured_market",
    "tier_d_editorial_estimate",
    "tier_e_manual_unverified",
}
RUN_MODE_VALUES = {
    "rookie_board",
    "veteran_board",
    "draft_room",
    "forced_release",
    "trade_review",
    "keeper_review",
    "historical_audit",
    "manual_override",
}
SOURCE_FORMAT_VALUES = {"csv", "json", "pdf", "txt", "md", "xlsx", "jpg", "png"}
DATA_QUALITY_VALUES = {"verified", "partial", "estimated", "hand_entered"}
NOTE_SCOPE_VALUES = {"player", "feature", "source", "override", "validation", "league_rule"}
OVERRIDE_TARGET_FIELD_VALUES = {"normalized_score"}
OVERRIDE_STATUS_VALUES = {"active", "inactive"}
OVERRIDE_REVIEW_STATUS_VALUES = {"pending", "approved", "rejected", "expired"}
OVERRIDE_TYPE_VALUES = {
    "data_correction",
    "source_resolution",
    "manual_entry",
    "transcription_fix",
    "league_rule_fix",
    "parser_fix",
}
OVERRIDE_REASON_CODE_VALUES = {
    "official_error",
    "parser_error",
    "transcription_error",
    "commissioner_ruling",
    "ownership_reconciliation",
    "injury_clarification",
    "other",
}


@dataclass(frozen=True)
class VeteranSchemaIssue:
    severity: str
    file_name: str
    entity_id: str
    field_name: str
    issue: str
    suggested_fix: str


@dataclass(frozen=True)
class VeteranPlayerRow:
    season: int
    snapshot_date: str
    player_id: str
    player_name: str
    position: str
    nfl_team: str
    age: float
    team_id: str
    team_name: str
    league_rank: int | None
    is_league_rank_top5: bool
    source_snapshot_id: str
    source_name: str
    source_date: str
    data_quality_tier: str


@dataclass(frozen=True)
class VeteranFeatureDefinition:
    position: str
    feature_name: str
    feature_category: str
    parent_component: str
    default_weight: float
    min_weight: float
    max_weight: float
    evidence_strength: str
    expected_direction: str
    lve_importance: str
    coefficient_policy: str
    scoring_status: str
    is_core: bool
    missing_data_penalty: float
    requires_source_type: str
    confidence_impact: str
    risk_flag_hint: str
    upside_flag_hint: str
    floor_flag_hint: str
    failure_modes: str
    source_summary: str
    implementation_notes: str


@dataclass(frozen=True)
class VeteranFeatureScore:
    season: int
    snapshot_date: str
    player_id: str
    position: str
    feature_name: str
    normalized_score: float | None
    source_key: str
    source_confidence: str
    is_missing: bool
    missing_reason: str
    is_user_override: bool
    override_reason: str


@dataclass(frozen=True)
class VeteranSourceRow:
    source_key: str
    source_name: str
    source_type: str
    source_family: str
    source_domain: str
    authority_tier: str
    priority_rank: int
    required_for_modes: str
    freshness_window_hours: int | None
    source_format: str
    local_path: str
    source_url: str
    source_path_or_url: str
    source_date: str
    retrieved_at: str
    captured_at_local: str
    effective_date: str
    season: int | None
    scoring_context: str
    checksum_sha256: str
    parser_version: str
    source_notes: str
    is_active: bool
    reliability_score: float
    notes: str


@dataclass(frozen=True)
class VeteranAuditNote:
    note_id: str
    season: int
    player_id: str
    feature_name: str
    note_scope: str
    note_text: str
    source_key: str
    affects_score: bool
    created_at: str


@dataclass(frozen=True)
class VeteranManualOverride:
    override_id: str
    season: int
    player_id: str
    position: str
    feature_name: str
    target_field: str
    old_value: str
    override_value: float
    override_type: str
    reason_code: str
    source_key: str
    override_reason: str
    provenance: str
    requested_by: str
    approved_by: str
    self_approved: bool
    review_status: str
    status: str
    created_at: str


@dataclass(frozen=True)
class VeteranSchemaReport:
    data_dir: Path
    players: tuple[VeteranPlayerRow, ...]
    registry: tuple[VeteranFeatureDefinition, ...]
    feature_scores: tuple[VeteranFeatureScore, ...]
    sources: tuple[VeteranSourceRow, ...]
    audit_notes: tuple[VeteranAuditNote, ...]
    manual_overrides: tuple[VeteranManualOverride, ...]
    issues: tuple[VeteranSchemaIssue, ...]
    required_files: tuple[str, ...] = VETERAN_SOURCE_TABLES

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")


def build_veteran_schema_report(data_dir: str | Path) -> VeteranSchemaReport:
    root = Path(data_dir)
    file_issues = _validate_required_files(root)
    if file_issues:
        return VeteranSchemaReport(root, (), (), (), (), (), (), tuple(file_issues))

    player_rows = _read_csv(root / PLAYER_FILE)
    registry_rows = _read_csv(root / REGISTRY_FILE)
    feature_rows = _read_csv(root / FEATURE_SCORE_FILE)
    source_rows = _read_csv(root / SOURCE_CATALOG_FILE)
    audit_rows = _read_csv(root / AUDIT_NOTES_FILE)
    override_path = root / MANUAL_OVERRIDES_FILE
    override_rows = _read_csv(override_path) if override_path.exists() else []

    issues: list[VeteranSchemaIssue] = []
    issues.extend(_validate_required_columns(PLAYER_FILE, player_rows, _player_columns()))
    issues.extend(_validate_required_columns(REGISTRY_FILE, registry_rows, _registry_columns()))
    issues.extend(
        _validate_required_columns(FEATURE_SCORE_FILE, feature_rows, _feature_score_columns())
    )
    issues.extend(_validate_required_columns(SOURCE_CATALOG_FILE, source_rows, _source_columns()))
    issues.extend(_validate_required_columns(AUDIT_NOTES_FILE, audit_rows, _audit_columns()))
    if override_rows:
        issues.extend(
            _validate_required_columns(
                MANUAL_OVERRIDES_FILE,
                override_rows,
                _manual_override_columns(),
            )
        )
    if any(issue.severity == "error" for issue in issues):
        return VeteranSchemaReport(root, (), (), (), (), (), (), tuple(issues))

    players = _parse_players(player_rows, issues)
    registry = _parse_registry(registry_rows, issues)
    sources = _parse_sources(source_rows, issues)
    feature_scores = _parse_feature_scores(feature_rows, issues)
    audit_notes = _parse_audit_notes(audit_rows, issues)
    manual_overrides = _parse_manual_overrides(override_rows, issues)

    issues.extend(
        _validate_cross_table_rules(
            players,
            registry,
            feature_scores,
            sources,
            audit_notes,
            manual_overrides,
        )
    )
    feature_scores = _apply_manual_overrides(feature_scores, manual_overrides, issues)

    return VeteranSchemaReport(
        data_dir=root,
        players=tuple(players),
        registry=tuple(registry),
        feature_scores=tuple(feature_scores),
        sources=tuple(sources),
        audit_notes=tuple(audit_notes),
        manual_overrides=tuple(manual_overrides),
        issues=tuple(issues),
    )


def _validate_required_files(root: Path) -> list[VeteranSchemaIssue]:
    issues: list[VeteranSchemaIssue] = []
    for file_name in VETERAN_SOURCE_TABLES:
        if not (root / file_name).exists():
            issues.append(
                _issue(
                    "error",
                    file_name,
                    "",
                    file_name,
                    "Required veteran source file is missing.",
                    f"Add {file_name} to the veteran model data directory.",
                )
            )
    return issues


def _validate_required_columns(
    file_name: str,
    rows: list[dict[str, str]],
    required_columns: tuple[str, ...],
) -> list[VeteranSchemaIssue]:
    if not rows:
        return [
            _issue(
                "error",
                file_name,
                "",
                file_name,
                "CSV file has no data rows.",
                "Keep the header and add at least one fixture row.",
            )
        ]
    columns = set(rows[0])
    return [
        _issue(
            "error",
            file_name,
            "",
            column,
            f"Missing required column: {column}.",
            f"Add {column} to {file_name}.",
        )
        for column in required_columns
        if column not in columns
    ]


def _parse_players(
    rows: list[dict[str, str]],
    issues: list[VeteranSchemaIssue],
) -> list[VeteranPlayerRow]:
    player_id_counts = Counter(row.get("player_id", "") for row in rows)
    players: list[VeteranPlayerRow] = []
    for row in rows:
        player_id = row.get("player_id", "")
        _validate_required_values(PLAYER_FILE, row, _player_columns(), player_id, issues)
        if player_id and not PLAYER_ID_PATTERN.match(player_id):
            issues.append(_bad_slug(PLAYER_FILE, player_id, "player_id"))
        if player_id and player_id_counts[player_id] > 1:
            issues.append(
                _issue(
                    "error",
                    PLAYER_FILE,
                    player_id,
                    "player_id",
                    "Duplicate player_id.",
                    "Keep one veteran_player_inputs.csv row per player_id.",
                )
            )
        if row.get("position") and row["position"] not in POSITION_VALUES:
            issues.append(_bad_enum(PLAYER_FILE, player_id, "position", POSITION_VALUES))
        if row.get("data_quality_tier") and row["data_quality_tier"] not in DATA_QUALITY_VALUES:
            issues.append(
                _bad_enum(PLAYER_FILE, player_id, "data_quality_tier", DATA_QUALITY_VALUES)
            )
        if row.get("age") and not _is_number(row["age"], 18, 45):
            issues.append(_bad_score_range(PLAYER_FILE, player_id, "age", "18-45"))
        if row.get("league_rank") and not _is_int(row["league_rank"], 1, 400):
            issues.append(_bad_score_range(PLAYER_FILE, player_id, "league_rank", "1-400"))
        if row.get("is_league_rank_top5") and not _is_bool(row["is_league_rank_top5"]):
            issues.append(_bad_bool(PLAYER_FILE, player_id, "is_league_rank_top5"))
        if not any(issue.severity == "error" and issue.entity_id == player_id for issue in issues):
            players.append(
                VeteranPlayerRow(
                    season=int(row["season"]),
                    snapshot_date=row["snapshot_date"],
                    player_id=player_id,
                    player_name=row["player_name"],
                    position=row["position"],
                    nfl_team=row["nfl_team"],
                    age=float(row["age"]),
                    team_id=row["team_id"],
                    team_name=row["team_name"],
                    league_rank=_optional_int(row.get("league_rank", "")),
                    is_league_rank_top5=_bool(row["is_league_rank_top5"]),
                    source_snapshot_id=row["source_snapshot_id"],
                    source_name=row["source_name"],
                    source_date=row["source_date"],
                    data_quality_tier=row["data_quality_tier"],
                )
            )
    return players


def _parse_registry(
    rows: list[dict[str, str]],
    issues: list[VeteranSchemaIssue],
) -> list[VeteranFeatureDefinition]:
    registry: list[VeteranFeatureDefinition] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        entity_id = f"{row.get('position', '')}:{row.get('feature_name', '')}"
        _validate_required_values(REGISTRY_FILE, row, _registry_columns(), entity_id, issues)
        key = (row.get("position", ""), row.get("feature_name", ""))
        if key in seen_keys:
            issues.append(
                _issue(
                    "error",
                    REGISTRY_FILE,
                    entity_id,
                    "feature_name",
                    "Duplicate veteran feature definition.",
                    "Keep one registry row per position + feature_name.",
                )
            )
        seen_keys.add(key)
        if row.get("position") and row["position"] not in POSITION_VALUES:
            issues.append(_bad_enum(REGISTRY_FILE, entity_id, "position", POSITION_VALUES))
        if row.get("feature_category") and row["feature_category"] not in FEATURE_CATEGORY_VALUES:
            issues.append(
                _bad_enum(REGISTRY_FILE, entity_id, "feature_category", FEATURE_CATEGORY_VALUES)
            )
        if row.get("parent_component") and row["parent_component"] not in PARENT_COMPONENT_VALUES:
            issues.append(
                _bad_enum(REGISTRY_FILE, entity_id, "parent_component", PARENT_COMPONENT_VALUES)
            )
        if (
            row.get("evidence_strength")
            and row["evidence_strength"] not in EVIDENCE_STRENGTH_VALUES
        ):
            issues.append(
                _bad_enum(REGISTRY_FILE, entity_id, "evidence_strength", EVIDENCE_STRENGTH_VALUES)
            )
        if (
            row.get("expected_direction")
            and row["expected_direction"] not in EXPECTED_DIRECTION_VALUES
        ):
            issues.append(
                _bad_enum(
                    REGISTRY_FILE,
                    entity_id,
                    "expected_direction",
                    EXPECTED_DIRECTION_VALUES,
                )
            )
        if row.get("lve_importance") and row["lve_importance"] not in LVE_IMPORTANCE_VALUES:
            issues.append(
                _bad_enum(REGISTRY_FILE, entity_id, "lve_importance", LVE_IMPORTANCE_VALUES)
            )
        if (
            row.get("coefficient_policy")
            and row["coefficient_policy"] not in COEFFICIENT_POLICY_VALUES
        ):
            issues.append(
                _bad_enum(
                    REGISTRY_FILE,
                    entity_id,
                    "coefficient_policy",
                    COEFFICIENT_POLICY_VALUES,
                )
            )
        if row.get("scoring_status") and row["scoring_status"] not in SCORING_STATUS_VALUES:
            issues.append(
                _bad_enum(REGISTRY_FILE, entity_id, "scoring_status", SCORING_STATUS_VALUES)
            )
        if row.get("is_core") and not _is_bool(row["is_core"]):
            issues.append(_bad_bool(REGISTRY_FILE, entity_id, "is_core"))
        for column in ("default_weight", "min_weight", "max_weight", "missing_data_penalty"):
            if row.get(column) and not _is_number(row[column], 0, 100):
                issues.append(_bad_score_range(REGISTRY_FILE, entity_id, column, "0-100"))
        if all(row.get(column) for column in ("default_weight", "min_weight", "max_weight")):
            min_weight = float(row["min_weight"])
            default_weight = float(row["default_weight"])
            max_weight = float(row["max_weight"])
            if not min_weight <= default_weight <= max_weight:
                issues.append(
                    _issue(
                        "error",
                        REGISTRY_FILE,
                        entity_id,
                        "default_weight",
                        "Feature weight is outside min/max bounds.",
                        "Set min_weight <= default_weight <= max_weight.",
                    )
                )
        is_unscored_feature = row.get("feature_category") in {"display_only", "rejected"}
        has_live_weight = row.get("default_weight") not in {
            "",
            "0",
            "0.0",
        }
        if is_unscored_feature and has_live_weight:
            issues.append(
                _issue(
                    "error",
                    REGISTRY_FILE,
                    entity_id,
                    "default_weight",
                    "Display-only/rejected feature has live weight.",
                    "Set default_weight to 0.0.",
                )
            )
        if row.get("scoring_status") in {"display_only", "rejected"} and has_live_weight:
            issues.append(
                _issue(
                    "error",
                    REGISTRY_FILE,
                    entity_id,
                    "default_weight",
                    "Non-scoring feature has live weight.",
                    "Set default_weight to 0.0 for display_only or rejected scoring_status.",
                )
            )
        if (
            row.get("scoring_status") == "active_v1"
            and row.get("parent_component") == "display_only"
        ):
            issues.append(
                _issue(
                    "error",
                    REGISTRY_FILE,
                    entity_id,
                    "scoring_status",
                    "Active scoring feature points to display_only component.",
                    "Use future_candidate/display_only or assign a scored component.",
                )
            )
        if not any(issue.severity == "error" and issue.entity_id == entity_id for issue in issues):
            registry.append(
                VeteranFeatureDefinition(
                    position=row["position"],
                    feature_name=row["feature_name"],
                    feature_category=row["feature_category"],
                    parent_component=row["parent_component"],
                    default_weight=float(row["default_weight"]),
                    min_weight=float(row["min_weight"]),
                    max_weight=float(row["max_weight"]),
                    evidence_strength=row["evidence_strength"],
                    expected_direction=row["expected_direction"],
                    lve_importance=row["lve_importance"],
                    coefficient_policy=row["coefficient_policy"],
                    scoring_status=row["scoring_status"],
                    is_core=_bool(row["is_core"]),
                    missing_data_penalty=float(row["missing_data_penalty"]),
                    requires_source_type=row["requires_source_type"],
                    confidence_impact=row["confidence_impact"],
                    risk_flag_hint=row["risk_flag_hint"],
                    upside_flag_hint=row["upside_flag_hint"],
                    floor_flag_hint=row["floor_flag_hint"],
                    failure_modes=row["failure_modes"],
                    source_summary=row["source_summary"],
                    implementation_notes=row["implementation_notes"],
                )
            )
    return registry


def _parse_feature_scores(
    rows: list[dict[str, str]],
    issues: list[VeteranSchemaIssue],
) -> list[VeteranFeatureScore]:
    scores: list[VeteranFeatureScore] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        entity_id = f"{row.get('player_id', '')}:{row.get('feature_name', '')}"
        _validate_required_values(
            FEATURE_SCORE_FILE,
            row,
            _feature_score_value_columns(),
            entity_id,
            issues,
        )
        key = (row.get("player_id", ""), row.get("feature_name", ""))
        if key in seen_keys:
            issues.append(
                _issue(
                    "error",
                    FEATURE_SCORE_FILE,
                    entity_id,
                    "feature_name",
                    "Duplicate veteran feature score.",
                    "Keep one feature score row per player_id + feature_name.",
                )
            )
        seen_keys.add(key)
        if row.get("position") and row["position"] not in POSITION_VALUES:
            issues.append(_bad_enum(FEATURE_SCORE_FILE, entity_id, "position", POSITION_VALUES))
        if (
            row.get("source_confidence")
            and row["source_confidence"] not in SOURCE_CONFIDENCE_VALUES
        ):
            issues.append(
                _bad_enum(
                    FEATURE_SCORE_FILE,
                    entity_id,
                    "source_confidence",
                    SOURCE_CONFIDENCE_VALUES,
                )
            )
        for column in ("is_missing", "is_user_override"):
            if row.get(column) and not _is_bool(row[column]):
                issues.append(_bad_bool(FEATURE_SCORE_FILE, entity_id, column))
        is_missing = _bool(row.get("is_missing", "false"))
        is_override = _bool(row.get("is_user_override", "false"))
        normalized = row.get("normalized_score", "")
        if is_missing and not row.get("missing_reason"):
            issues.append(
                _issue(
                    "error",
                    FEATURE_SCORE_FILE,
                    entity_id,
                    "missing_reason",
                    "Missing feature row does not explain missingness.",
                    "Populate missing_reason when is_missing is true.",
                )
            )
        if is_override and not row.get("override_reason"):
            issues.append(
                _issue(
                    "error",
                    FEATURE_SCORE_FILE,
                    entity_id,
                    "override_reason",
                    "User override does not include an override reason.",
                    "Explain why the manual override is active.",
                )
            )
        if not is_missing and not _is_number(normalized, 0, 100):
            issues.append(
                _bad_score_range(FEATURE_SCORE_FILE, entity_id, "normalized_score", "0-100")
            )
        if not row.get("source_key"):
            issues.append(
                _issue(
                    "error",
                    FEATURE_SCORE_FILE,
                    entity_id,
                    "source_key",
                    "Feature score is missing source provenance.",
                    "Populate source_key with a row from veteran_source_catalog.csv.",
                )
            )
        if not any(issue.severity == "error" and issue.entity_id == entity_id for issue in issues):
            scores.append(
                VeteranFeatureScore(
                    season=int(row["season"]),
                    snapshot_date=row["snapshot_date"],
                    player_id=row["player_id"],
                    position=row["position"],
                    feature_name=row["feature_name"],
                    normalized_score=None if is_missing else float(row["normalized_score"]),
                    source_key=row["source_key"],
                    source_confidence=row["source_confidence"],
                    is_missing=is_missing,
                    missing_reason=row.get("missing_reason", ""),
                    is_user_override=is_override,
                    override_reason=row.get("override_reason", ""),
                )
            )
    return scores


def _parse_sources(
    rows: list[dict[str, str]],
    issues: list[VeteranSchemaIssue],
) -> list[VeteranSourceRow]:
    sources: list[VeteranSourceRow] = []
    seen_keys: set[str] = set()
    active_priorities: set[tuple[str, int]] = set()
    for row in rows:
        source_key = row.get("source_key", "")
        _validate_required_values(
            SOURCE_CATALOG_FILE,
            row,
            _source_value_columns(),
            source_key,
            issues,
        )
        if source_key and source_key in seen_keys:
            issues.append(
                _issue(
                    "error",
                    SOURCE_CATALOG_FILE,
                    source_key,
                    "source_key",
                    "Duplicate source_key.",
                    "Keep source_key unique in veteran_source_catalog.csv.",
                )
            )
        seen_keys.add(source_key)
        if source_key and not PLAYER_ID_PATTERN.match(source_key):
            issues.append(_bad_slug(SOURCE_CATALOG_FILE, source_key, "source_key"))
        if row.get("source_type") and row["source_type"] not in SOURCE_TYPE_VALUES:
            issues.append(
                _bad_enum(SOURCE_CATALOG_FILE, source_key, "source_type", SOURCE_TYPE_VALUES)
            )
        if row.get("source_family") and row["source_family"] not in SOURCE_FAMILY_VALUES:
            issues.append(
                _bad_enum(SOURCE_CATALOG_FILE, source_key, "source_family", SOURCE_FAMILY_VALUES)
            )
        if row.get("source_domain") and row["source_domain"] not in SOURCE_DOMAIN_VALUES:
            issues.append(
                _bad_enum(SOURCE_CATALOG_FILE, source_key, "source_domain", SOURCE_DOMAIN_VALUES)
            )
        if row.get("authority_tier") and row["authority_tier"] not in AUTHORITY_TIER_VALUES:
            issues.append(
                _bad_enum(SOURCE_CATALOG_FILE, source_key, "authority_tier", AUTHORITY_TIER_VALUES)
            )
        if row.get("source_format") and row["source_format"] not in SOURCE_FORMAT_VALUES:
            issues.append(
                _bad_enum(SOURCE_CATALOG_FILE, source_key, "source_format", SOURCE_FORMAT_VALUES)
            )
        if row.get("priority_rank") and not _is_int(row["priority_rank"], 1, 1000):
            issues.append(
                _bad_score_range(
                    SOURCE_CATALOG_FILE,
                    source_key,
                    "priority_rank",
                    "1-1000",
                )
            )
        if (
            row.get("freshness_window_hours")
            and not _is_int(row["freshness_window_hours"], 1, 87600)
        ):
            issues.append(
                _bad_score_range(
                    SOURCE_CATALOG_FILE,
                    source_key,
                    "freshness_window_hours",
                    "1-87600",
                )
            )
        if row.get("season") and not _is_int(row["season"], 2000, 2100):
            issues.append(_bad_score_range(SOURCE_CATALOG_FILE, source_key, "season", "2000-2100"))
        if row.get("is_active") and not _is_bool(row["is_active"]):
            issues.append(_bad_bool(SOURCE_CATALOG_FILE, source_key, "is_active"))
        if row.get("required_for_modes"):
            for mode in _split_pipe(row["required_for_modes"]):
                if mode not in RUN_MODE_VALUES:
                    issues.append(
                        _bad_enum(
                            SOURCE_CATALOG_FILE,
                            source_key,
                            "required_for_modes",
                            RUN_MODE_VALUES,
                        )
                    )
                    break
        if (
            row.get("is_active") == "true"
            and row.get("source_domain")
            and row.get("priority_rank")
            and _is_int(row["priority_rank"], 1, 1000)
        ):
            priority_key = (row["source_domain"], int(row["priority_rank"]))
            if priority_key in active_priorities:
                issues.append(
                    _issue(
                        "error",
                        SOURCE_CATALOG_FILE,
                        source_key,
                        "priority_rank",
                        "Active source priority is duplicated within a source domain.",
                        "Keep priority_rank unique per active source_domain.",
                    )
                )
            active_priorities.add(priority_key)
        if row.get("source_family") in {"market_rank", "projection"} and not row.get(
            "scoring_context"
        ):
            issues.append(
                _issue(
                    "error",
                    SOURCE_CATALOG_FILE,
                    source_key,
                    "scoring_context",
                    "Market/projection source is missing scoring context.",
                    "Set scoring_context so generic market inputs cannot masquerade as LVE truth.",
                )
            )
        if row.get("reliability_score") and not _is_number(row["reliability_score"], 0, 100):
            issues.append(
                _bad_score_range(
                    SOURCE_CATALOG_FILE,
                    source_key,
                    "reliability_score",
                    "0-100",
                )
            )
        if not any(issue.severity == "error" and issue.entity_id == source_key for issue in issues):
            sources.append(
                VeteranSourceRow(
                    source_key=source_key,
                    source_name=row["source_name"],
                    source_type=row["source_type"],
                    source_family=row["source_family"],
                    source_domain=row["source_domain"],
                    authority_tier=row["authority_tier"],
                    priority_rank=int(row["priority_rank"]),
                    required_for_modes=row["required_for_modes"],
                    freshness_window_hours=_optional_int(row.get("freshness_window_hours", "")),
                    source_format=row["source_format"],
                    local_path=row["local_path"],
                    source_url=row.get("source_url", ""),
                    source_path_or_url=row["source_path_or_url"],
                    source_date=row["source_date"],
                    retrieved_at=row["retrieved_at"],
                    captured_at_local=row["captured_at_local"],
                    effective_date=row.get("effective_date", ""),
                    season=_optional_int(row.get("season", "")),
                    scoring_context=row.get("scoring_context", ""),
                    checksum_sha256=row.get("checksum_sha256", ""),
                    parser_version=row.get("parser_version", ""),
                    source_notes=row.get("source_notes", ""),
                    is_active=_bool(row["is_active"]),
                    reliability_score=float(row["reliability_score"]),
                    notes=row.get("notes", ""),
                )
            )
    return sources


def _parse_audit_notes(
    rows: list[dict[str, str]],
    issues: list[VeteranSchemaIssue],
) -> list[VeteranAuditNote]:
    notes: list[VeteranAuditNote] = []
    seen_ids: set[str] = set()
    for row in rows:
        note_id = row.get("note_id", "")
        _validate_required_values(AUDIT_NOTES_FILE, row, _audit_columns(), note_id, issues)
        if note_id and note_id in seen_ids:
            issues.append(
                _issue(
                    "error",
                    AUDIT_NOTES_FILE,
                    note_id,
                    "note_id",
                    "Duplicate note_id.",
                    "Keep note_id unique in veteran_audit_notes.csv.",
                )
            )
        seen_ids.add(note_id)
        if note_id and not PLAYER_ID_PATTERN.match(note_id):
            issues.append(_bad_slug(AUDIT_NOTES_FILE, note_id, "note_id"))
        if row.get("note_scope") and row["note_scope"] not in NOTE_SCOPE_VALUES:
            issues.append(_bad_enum(AUDIT_NOTES_FILE, note_id, "note_scope", NOTE_SCOPE_VALUES))
        if row.get("affects_score") and not _is_bool(row["affects_score"]):
            issues.append(_bad_bool(AUDIT_NOTES_FILE, note_id, "affects_score"))
        if _bool(row.get("affects_score", "false")) and not row.get("feature_name"):
            issues.append(
                _issue(
                    "error",
                    AUDIT_NOTES_FILE,
                    note_id,
                    "feature_name",
                    "Score-affecting note is not tied to a feature.",
                    "Populate feature_name for notes that affect score.",
                )
            )
        if not any(issue.severity == "error" and issue.entity_id == note_id for issue in issues):
            notes.append(
                VeteranAuditNote(
                    note_id=note_id,
                    season=int(row["season"]),
                    player_id=row["player_id"],
                    feature_name=row.get("feature_name", ""),
                    note_scope=row["note_scope"],
                    note_text=row["note_text"],
                    source_key=row["source_key"],
                    affects_score=_bool(row["affects_score"]),
                    created_at=row["created_at"],
                )
            )
    return notes


def _parse_manual_overrides(
    rows: list[dict[str, str]],
    issues: list[VeteranSchemaIssue],
) -> list[VeteranManualOverride]:
    overrides: list[VeteranManualOverride] = []
    seen_ids: set[str] = set()
    seen_targets: set[tuple[str, str, str]] = set()
    for row in rows:
        override_id = row.get("override_id", "")
        _validate_required_values(
            MANUAL_OVERRIDES_FILE,
            row,
            _manual_override_columns(),
            override_id,
            issues,
        )
        if override_id and override_id in seen_ids:
            issues.append(
                _issue(
                    "error",
                    MANUAL_OVERRIDES_FILE,
                    override_id,
                    "override_id",
                    "Duplicate override_id.",
                    "Keep override_id unique in veteran_manual_overrides.csv.",
                )
            )
        seen_ids.add(override_id)
        if override_id and not PLAYER_ID_PATTERN.match(override_id):
            issues.append(_bad_slug(MANUAL_OVERRIDES_FILE, override_id, "override_id"))
        target = (
            row.get("player_id", ""),
            row.get("feature_name", ""),
            row.get("target_field", ""),
        )
        is_active_approved = (
            row.get("status") == "active"
            and row.get("review_status", "approved") == "approved"
        )
        if is_active_approved and target in seen_targets:
            issues.append(
                _issue(
                    "error",
                    MANUAL_OVERRIDES_FILE,
                    override_id,
                    "feature_name",
                    "Multiple active overrides target the same feature field.",
                    "Keep one override per player_id + feature_name + target_field.",
                )
            )
        if is_active_approved:
            seen_targets.add(target)
        if row.get("position") and row["position"] not in POSITION_VALUES:
            issues.append(
                _bad_enum(MANUAL_OVERRIDES_FILE, override_id, "position", POSITION_VALUES)
            )
        if row.get("target_field") and row["target_field"] not in OVERRIDE_TARGET_FIELD_VALUES:
            issues.append(
                _bad_enum(
                    MANUAL_OVERRIDES_FILE,
                    override_id,
                    "target_field",
                    OVERRIDE_TARGET_FIELD_VALUES,
                )
            )
        if row.get("status") and row["status"] not in OVERRIDE_STATUS_VALUES:
            issues.append(
                _bad_enum(MANUAL_OVERRIDES_FILE, override_id, "status", OVERRIDE_STATUS_VALUES)
            )
        if (
            row.get("review_status")
            and row["review_status"] not in OVERRIDE_REVIEW_STATUS_VALUES
        ):
            issues.append(
                _bad_enum(
                    MANUAL_OVERRIDES_FILE,
                    override_id,
                    "review_status",
                    OVERRIDE_REVIEW_STATUS_VALUES,
                )
            )
        if row.get("override_type") and row["override_type"] not in OVERRIDE_TYPE_VALUES:
            issues.append(
                _bad_enum(
                    MANUAL_OVERRIDES_FILE,
                    override_id,
                    "override_type",
                    OVERRIDE_TYPE_VALUES,
                )
            )
        if row.get("reason_code") and row["reason_code"] not in OVERRIDE_REASON_CODE_VALUES:
            issues.append(
                _bad_enum(
                    MANUAL_OVERRIDES_FILE,
                    override_id,
                    "reason_code",
                    OVERRIDE_REASON_CODE_VALUES,
                )
            )
        if row.get("self_approved") and not _is_bool(row["self_approved"]):
            issues.append(_bad_bool(MANUAL_OVERRIDES_FILE, override_id, "self_approved"))
        if row.get("override_value") and not _is_number(row["override_value"], 0, 100):
            issues.append(
                _bad_score_range(
                    MANUAL_OVERRIDES_FILE,
                    override_id,
                    "override_value",
                    "0-100",
                )
            )
        for column in (
            "old_value",
            "override_reason",
            "provenance",
            "requested_by",
            "approved_by",
            "source_key",
            "review_status",
        ):
            if row.get(column, "") == "":
                issues.append(
                    _issue(
                        "error",
                        MANUAL_OVERRIDES_FILE,
                        override_id,
                        column,
                        "Manual override is missing required audit provenance.",
                        f"Populate {column}; overrides may only target feature scores.",
                    )
                )
        if row.get("requested_by") == row.get("approved_by") and row.get(
            "self_approved"
        ) != "true":
            issues.append(
                _issue(
                    "error",
                    MANUAL_OVERRIDES_FILE,
                    override_id,
                    "self_approved",
                    "Self-approved override is not explicitly marked.",
                    "Set self_approved=true when requested_by and approved_by match.",
                )
            )
        if row.get("status") == "active" and row.get("review_status") != "approved":
            issues.append(
                _issue(
                    "error",
                    MANUAL_OVERRIDES_FILE,
                    override_id,
                    "review_status",
                    "Active override is not approved.",
                    "Only approved overrides may be active.",
                )
            )
        has_override_error = any(
            issue.severity == "error" and issue.entity_id == override_id
            for issue in issues
        )
        if not has_override_error:
            overrides.append(
                VeteranManualOverride(
                    override_id=override_id,
                    season=int(row["season"]),
                    player_id=row["player_id"],
                    position=row["position"],
                    feature_name=row["feature_name"],
                    target_field=row["target_field"],
                    old_value=row["old_value"],
                    override_value=float(row["override_value"]),
                    override_type=row["override_type"],
                    reason_code=row["reason_code"],
                    source_key=row["source_key"],
                    override_reason=row["override_reason"],
                    provenance=row["provenance"],
                    requested_by=row["requested_by"],
                    approved_by=row["approved_by"],
                    self_approved=_bool(row["self_approved"]),
                    review_status=row["review_status"],
                    status=row["status"],
                    created_at=row["created_at"],
                )
            )
    return overrides


def _validate_cross_table_rules(
    players: list[VeteranPlayerRow],
    registry: list[VeteranFeatureDefinition],
    feature_scores: list[VeteranFeatureScore],
    sources: list[VeteranSourceRow],
    audit_notes: list[VeteranAuditNote],
    manual_overrides: list[VeteranManualOverride],
) -> list[VeteranSchemaIssue]:
    issues: list[VeteranSchemaIssue] = []
    player_by_id = {player.player_id: player for player in players}
    registry_by_key = {
        (feature.position, feature.feature_name): feature for feature in registry
    }
    source_keys = {source.source_key for source in sources}
    scores_by_player_feature = {
        (score.player_id, score.feature_name): score for score in feature_scores
    }
    score_affecting_notes = {
        (note.player_id, note.feature_name)
        for note in audit_notes
        if note.affects_score
    }

    for score in feature_scores:
        player = player_by_id.get(score.player_id)
        if player is None:
            issues.append(
                _issue(
                    "error",
                    FEATURE_SCORE_FILE,
                    score.player_id,
                    "player_id",
                    "Feature score references an unknown player_id.",
                    "Add the player to veteran_player_inputs.csv or remove the feature row.",
                )
            )
            continue
        if score.position != player.position:
            issues.append(
                _issue(
                    "error",
                    FEATURE_SCORE_FILE,
                    score.player_id,
                    "position",
                    "Feature score position does not match player position.",
                    "Make position consistent across veteran player and feature files.",
                )
            )
        if (score.position, score.feature_name) not in registry_by_key:
            issues.append(
                _issue(
                    "error",
                    FEATURE_SCORE_FILE,
                    score.player_id,
                    "feature_name",
                    "Feature score references an unsupported veteran feature.",
                    "Add a matching registry row or remove the feature score.",
                )
            )
        if score.source_key not in source_keys:
            issues.append(
                _issue(
                    "error",
                    FEATURE_SCORE_FILE,
                    score.player_id,
                    "source_key",
                    "Feature score references an unknown source_key.",
                    "Add the source to veteran_source_catalog.csv.",
                )
            )

    for player in players:
        for feature in registry:
            if (
                feature.position != player.position
                or not feature.is_core
                or feature.scoring_status != "active_v1"
            ):
                continue
            score = scores_by_player_feature.get((player.player_id, feature.feature_name))
            if score is None or score.is_missing:
                issues.append(
                    _issue(
                        "warning",
                        FEATURE_SCORE_FILE,
                        player.player_id,
                        feature.feature_name,
                        "Missing core veteran feature.",
                        "Enter a normalized 0-100 score or accept a confidence penalty.",
                    )
                )

    for note in audit_notes:
        if note.player_id and note.player_id not in player_by_id:
            issues.append(
                _issue(
                    "error",
                    AUDIT_NOTES_FILE,
                    note.note_id,
                    "player_id",
                    "Audit note references an unknown player_id.",
                    "Add the player or correct the note player_id.",
                )
            )
        if note.source_key and note.source_key not in source_keys:
            issues.append(
                _issue(
                    "error",
                    AUDIT_NOTES_FILE,
                    note.note_id,
                    "source_key",
                    "Audit note references an unknown source_key.",
                    "Add the source or correct the note source_key.",
                )
            )

    for override in manual_overrides:
        player = player_by_id.get(override.player_id)
        if player is None:
            issues.append(
                _issue(
                    "error",
                    MANUAL_OVERRIDES_FILE,
                    override.override_id,
                    "player_id",
                    "Override references an unknown player_id.",
                    "Add the player or correct the override player_id.",
                )
            )
            continue
        if override.position != player.position:
            issues.append(
                _issue(
                    "error",
                    MANUAL_OVERRIDES_FILE,
                    override.override_id,
                    "position",
                    "Override position does not match player position.",
                    "Make the override position match veteran_player_inputs.csv.",
                )
            )
        if (override.position, override.feature_name) not in registry_by_key:
            issues.append(
                _issue(
                    "error",
                    MANUAL_OVERRIDES_FILE,
                    override.override_id,
                    "feature_name",
                    "Override targets an unsupported feature.",
                    "Override feature scores only; final score overrides are blocked.",
                )
            )
        if override.source_key not in source_keys:
            issues.append(
                _issue(
                    "error",
                    MANUAL_OVERRIDES_FILE,
                    override.override_id,
                    "source_key",
                    "Override references an unknown source_key.",
                    "Add the source to veteran_source_catalog.csv.",
                )
            )
        if (override.player_id, override.feature_name) not in scores_by_player_feature:
            issues.append(
                _issue(
                    "error",
                    MANUAL_OVERRIDES_FILE,
                    override.override_id,
                    "feature_name",
                    "Override target has no existing feature score row.",
                    "Add the feature score row first; overrides must be auditable deltas.",
                )
            )
        if (override.player_id, override.feature_name) not in score_affecting_notes:
            issues.append(
                _issue(
                    "error",
                    MANUAL_OVERRIDES_FILE,
                    override.override_id,
                    "override_id",
                    "Active override has no matching score-affecting audit note.",
                    "Add a veteran_audit_notes.csv row with affects_score=true "
                    "for this player and feature.",
                )
            )

    return issues


def _apply_manual_overrides(
    feature_scores: list[VeteranFeatureScore],
    manual_overrides: list[VeteranManualOverride],
    issues: list[VeteranSchemaIssue],
) -> list[VeteranFeatureScore]:
    if any(issue.severity == "error" for issue in issues):
        return feature_scores
    active_overrides = {
        (override.player_id, override.feature_name): override
        for override in manual_overrides
        if override.status == "active" and override.review_status == "approved"
    }
    updated_scores: list[VeteranFeatureScore] = []
    for score in feature_scores:
        override = active_overrides.get((score.player_id, score.feature_name))
        if override is None:
            updated_scores.append(score)
            continue
        updated_scores.append(
            VeteranFeatureScore(
                season=score.season,
                snapshot_date=score.snapshot_date,
                player_id=score.player_id,
                position=score.position,
                feature_name=score.feature_name,
                normalized_score=override.override_value,
                source_key=override.source_key,
                source_confidence="manual",
                is_missing=False,
                missing_reason="",
                is_user_override=True,
                override_reason=override.override_reason,
            )
        )
    return updated_scores


def _validate_required_values(
    file_name: str,
    row: dict[str, str],
    required_columns: tuple[str, ...],
    entity_id: str,
    issues: list[VeteranSchemaIssue],
) -> None:
    for column in required_columns:
        if row.get(column, "") == "":
            issues.append(
                _issue(
                    "error",
                    file_name,
                    entity_id,
                    column,
                    "Missing required value.",
                    f"Populate {column}.",
                )
            )


def _player_columns() -> tuple[str, ...]:
    return (
        "season",
        "snapshot_date",
        "player_id",
        "player_name",
        "position",
        "nfl_team",
        "age",
        "team_id",
        "team_name",
        "league_rank",
        "is_league_rank_top5",
        "source_snapshot_id",
        "source_name",
        "source_date",
        "data_quality_tier",
    )


def _registry_columns() -> tuple[str, ...]:
    return (
        "position",
        "feature_name",
        "feature_category",
        "parent_component",
        "default_weight",
        "min_weight",
        "max_weight",
        "evidence_strength",
        "expected_direction",
        "lve_importance",
        "coefficient_policy",
        "scoring_status",
        "is_core",
        "missing_data_penalty",
        "requires_source_type",
        "confidence_impact",
        "risk_flag_hint",
        "upside_flag_hint",
        "floor_flag_hint",
        "failure_modes",
        "source_summary",
        "implementation_notes",
    )


def _feature_score_columns() -> tuple[str, ...]:
    return (
        "season",
        "snapshot_date",
        "player_id",
        "position",
        "feature_name",
        "normalized_score",
        "source_key",
        "source_confidence",
        "is_missing",
        "missing_reason",
        "is_user_override",
        "override_reason",
    )


def _feature_score_value_columns() -> tuple[str, ...]:
    return (
        "season",
        "snapshot_date",
        "player_id",
        "position",
        "feature_name",
        "source_key",
        "source_confidence",
        "is_missing",
        "is_user_override",
    )


def _source_columns() -> tuple[str, ...]:
    return (
        "source_key",
        "source_name",
        "source_type",
        "source_family",
        "source_domain",
        "authority_tier",
        "priority_rank",
        "required_for_modes",
        "freshness_window_hours",
        "source_format",
        "local_path",
        "source_url",
        "source_path_or_url",
        "source_date",
        "retrieved_at",
        "captured_at_local",
        "effective_date",
        "season",
        "scoring_context",
        "checksum_sha256",
        "parser_version",
        "source_notes",
        "is_active",
        "reliability_score",
        "notes",
    )


def _source_value_columns() -> tuple[str, ...]:
    return (
        "source_key",
        "source_name",
        "source_type",
        "source_family",
        "source_domain",
        "authority_tier",
        "priority_rank",
        "required_for_modes",
        "source_format",
        "local_path",
        "source_path_or_url",
        "source_date",
        "retrieved_at",
        "captured_at_local",
        "is_active",
        "reliability_score",
    )


def _audit_columns() -> tuple[str, ...]:
    return (
        "note_id",
        "season",
        "player_id",
        "feature_name",
        "note_scope",
        "note_text",
        "source_key",
        "affects_score",
        "created_at",
    )


def _manual_override_columns() -> tuple[str, ...]:
    return (
        "override_id",
        "season",
        "player_id",
        "position",
        "feature_name",
        "target_field",
        "old_value",
        "override_value",
        "override_type",
        "reason_code",
        "source_key",
        "override_reason",
        "provenance",
        "requested_by",
        "approved_by",
        "self_approved",
        "review_status",
        "status",
        "created_at",
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _issue(
    severity: str,
    file_name: str,
    entity_id: str,
    field_name: str,
    issue: str,
    suggested_fix: str,
) -> VeteranSchemaIssue:
    return VeteranSchemaIssue(
        severity=severity,
        file_name=file_name,
        entity_id=entity_id,
        field_name=field_name,
        issue=issue,
        suggested_fix=suggested_fix,
    )


def _bad_slug(file_name: str, entity_id: str, field_name: str) -> VeteranSchemaIssue:
    return _issue(
        "error",
        file_name,
        entity_id,
        field_name,
        f"{field_name} must be a stable lowercase slug.",
        "Use only lowercase letters, numbers, and underscores.",
    )


def _bad_enum(
    file_name: str,
    entity_id: str,
    field_name: str,
    allowed_values: set[str],
) -> VeteranSchemaIssue:
    return _issue(
        "error",
        file_name,
        entity_id,
        field_name,
        f"Unsupported {field_name}.",
        f"Use one of: {', '.join(sorted(allowed_values))}.",
    )


def _bad_bool(file_name: str, entity_id: str, field_name: str) -> VeteranSchemaIssue:
    return _issue(
        "error",
        file_name,
        entity_id,
        field_name,
        f"{field_name} must be true or false.",
        "Use lowercase true or false.",
    )


def _bad_score_range(
    file_name: str,
    entity_id: str,
    field_name: str,
    allowed_range: str,
) -> VeteranSchemaIssue:
    return _issue(
        "error",
        file_name,
        entity_id,
        field_name,
        f"{field_name} must be numeric in range {allowed_range}.",
        f"Replace {field_name} with a value in range {allowed_range}.",
    )


def _is_int(value: str, minimum: int, maximum: int) -> bool:
    try:
        number = int(value)
    except ValueError:
        return False
    return minimum <= number <= maximum


def _is_number(value: str, minimum: float, maximum: float) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return minimum <= number <= maximum


def _is_bool(value: str) -> bool:
    return value in {"true", "false"}


def _bool(value: str) -> bool:
    return value == "true"


def _optional_int(value: str) -> int | None:
    if value == "":
        return None
    return int(value)


def _split_pipe(value: str) -> list[str]:
    return [part for part in value.split("|") if part]
