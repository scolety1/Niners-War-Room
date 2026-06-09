from __future__ import annotations

import csv
import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.data.validators import validate_data_pack
from src.services.veteran_model_service import (
    generated_model_output_rows,
    run_veteran_model_from_dir,
)

DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "real_data_inputs"
    / "public_sources"
)
DEFAULT_PUBLIC_SOURCE_SNAPSHOT_ROOT = (
    Path(__file__).resolve().parents[2]
    / "local_exports"
    / "public_source_snapshots"
)
DEFAULT_PUBLIC_SOURCE_WORKLIST_ROOT = (
    Path(__file__).resolve().parents[2]
    / "local_exports"
    / "public_source_normalization_worklists"
)
DEFAULT_PUBLIC_SOURCE_MODEL_INPUT_ROOT = (
    Path(__file__).resolve().parents[2]
    / "local_exports"
    / "public_source_model_input_candidates"
)
DEFAULT_PUBLIC_SOURCE_MODEL_PREVIEW_ROOT = (
    Path(__file__).resolve().parents[2]
    / "local_exports"
    / "public_source_model_previews"
)
DEFAULT_PUBLIC_SOURCE_MODEL_PROMOTION_ROOT = (
    Path(__file__).resolve().parents[2]
    / "local_exports"
    / "public_source_model_promotion_candidates"
)
DEFAULT_PUBLIC_SOURCE_MODEL_APPLIED_PACK_ROOT = (
    Path(__file__).resolve().parents[2] / "local_exports" / "data_packs"
)
DEFAULT_VETERAN_FEATURE_REGISTRY_PATH = (
    Path(__file__).resolve().parents[2]
    / "sample_data"
    / "veteran_model_v1"
    / "veteran_feature_registry.csv"
)
SNAPSHOT_MANIFEST_FILE = "source_snapshot_manifest.json"
NORMALIZATION_WORKLIST_MANIFEST_FILE = "normalization_worklist_manifest.json"
NORMALIZATION_WORKLIST_FILE = "veteran_feature_normalization_worklist.csv"
MODEL_INPUT_CANDIDATE_MANIFEST_FILE = "model_input_candidate_manifest.json"
MODEL_INPUT_CANDIDATE_FILE = "veteran_feature_scores_candidate.csv"
MODEL_PREVIEW_MANIFEST_FILE = "model_preview_manifest.json"
MODEL_PREVIEW_OUTPUT_FILE = "veteran_model_preview_outputs.csv"
MODEL_PREVIEW_INPUT_DIR = "model_input"
MODEL_PROMOTION_MANIFEST_FILE = "model_promotion_candidate_manifest.json"
MODEL_PROMOTION_FILE = "model_outputs_promotion_candidate.csv"
MODEL_APPLIED_PACK_MANIFEST_FILE = "model_applied_pack_manifest.json"
PUBLIC_SOURCE_BACKFILL_SOURCE_KEY = "public_source_backfill_candidate"

LVE_PROJECTION_SCORING = {
    "pass_yard": LVE_SCORING["passing_yard"],
    "pass_td": LVE_SCORING["passing_td"],
    "interception": LVE_SCORING["interception"],
    "rush_yard": LVE_SCORING["rushing_yard"],
    "rush_td": LVE_SCORING["rushing_td"],
    "rec_yard": LVE_SCORING["receiving_yard"],
    "rec_td": LVE_SCORING["receiving_td"],
    "return_yard": LVE_SCORING["return_yard"],
    "return_td": LVE_SCORING["return_td"],
    "rush_rec_first_down": LVE_SCORING["rushing_receiving_first_down"],
    "fumble_lost": LVE_SCORING["fumble_lost"],
}

FIRST_DOWN_ESTIMATION_RATES = {
    "QB": {"rush": 0.25, "target": 0.0},
    "RB": {"rush": 0.23, "target": 0.30},
    "WR": {"rush": 0.10, "target": 0.40},
    "TE": {"rush": 0.05, "target": 0.36},
}

PUBLIC_SOURCE_TEMPLATE_HEADERS: dict[str, tuple[str, ...]] = {
    "public_source_catalog.csv": (
        "source_id",
        "source_name",
        "source_url",
        "source_role",
        "access_method",
        "access_artifact",
        "export_format",
        "requires_scrape",
        "license_or_terms_summary",
        "legal_risk_level",
        "maintenance_burden",
        "update_frequency_text",
        "coverage_qb",
        "coverage_rb",
        "coverage_wr",
        "coverage_te",
        "base_confidence",
        "last_refresh_utc",
        "notes",
    ),
    "player_projection_inputs.csv": (
        "player_key",
        "player_name",
        "position",
        "team",
        "season",
        "asof_date",
        "projection_source_id",
        "source_player_id",
        "scoring_profile_id",
        "proj_pass_attempts",
        "proj_completions",
        "proj_pass_yards",
        "proj_pass_tds",
        "proj_pass_ints",
        "proj_rush_attempts",
        "proj_rush_yards",
        "proj_rush_tds",
        "proj_targets",
        "proj_receptions",
        "proj_rec_yards",
        "proj_rec_tds",
        "proj_fumbles_lost",
        "proj_rush_first_downs",
        "proj_rec_first_downs",
        "proj_fantasy_points_source",
        "proj_fantasy_points_lve_rescored",
        "projection_confidence",
        "staleness_days",
        "missing_projection_flags",
        "notes",
    ),
    "player_market_inputs.csv": (
        "player_key",
        "player_name",
        "position",
        "team",
        "season",
        "asof_date",
        "market_source_id",
        "source_player_id",
        "value_1qb",
        "ecr_1qb",
        "ecr_pos",
        "value_2qb",
        "ecr_2qb",
        "market_rank",
        "market_delta",
        "market_scrape_date",
        "liquidity_score",
        "liquidity_proxy_type",
        "market_confidence",
        "staleness_days",
        "format_assumption_flags",
        "notes",
    ),
    "player_role_inputs.csv": (
        "player_key",
        "player_name",
        "position",
        "team",
        "season",
        "asof_date",
        "role_source_id",
        "source_player_id",
        "depth_timestamp_utc",
        "depth_pos_group",
        "depth_pos_slot",
        "depth_pos_rank",
        "starter_flag",
        "offense_snaps",
        "offense_snap_pct",
        "games_sampled",
        "targets",
        "target_share",
        "air_yards_share",
        "wopr",
        "carries",
        "rush_attempt_share",
        "route_participation_pct",
        "role_confidence",
        "staleness_days",
        "role_conflict_flags",
        "notes",
    ),
    "player_injury_inputs.csv": (
        "player_key",
        "player_name",
        "position",
        "team",
        "season",
        "asof_date",
        "injury_source_id",
        "source_player_id",
        "latest_report_week",
        "report_primary_injury",
        "report_secondary_injury",
        "report_status",
        "practice_primary_injury",
        "practice_secondary_injury",
        "practice_status",
        "date_modified_utc",
        "injury_events_rolling_1y",
        "injury_events_rolling_2y",
        "games_missed_proxy",
        "days_since_last_report",
        "injury_confidence",
        "staleness_days",
        "injury_conflict_flags",
        "notes",
    ),
    "player_bio_inputs.csv": (
        "player_key",
        "player_name",
        "position",
        "team",
        "season",
        "asof_date",
        "bio_source_id",
        "source_player_id",
        "sleeper_id",
        "gsis_id",
        "nfl_id",
        "espn_id",
        "fantasypros_id",
        "birthdate",
        "age",
        "years_exp",
        "draft_year",
        "draft_round",
        "draft_pick",
        "draft_ovr",
        "height_in",
        "weight_lb",
        "college",
        "bio_confidence",
        "staleness_days",
        "bio_conflict_flags",
        "notes",
    ),
    "normalized_veteran_feature_backfill.csv": (
        "player_key",
        "player_name",
        "position",
        "team",
        "season",
        "asof_date",
        "lve_projection_value",
        "role_security",
        "age_curve",
        "market_liquidity",
        "position_replaceability",
        "first_down_td_fit",
        "target_earning_stability",
        "route_share_stability",
        "injury_durability",
        "projection_confidence",
        "market_confidence",
        "role_confidence",
        "injury_confidence",
        "bio_confidence",
        "overall_feature_confidence",
        "missing_feature_flags",
        "source_snapshot_id",
        "manual_review_required",
        "notes",
    ),
}

LEGACY_PUBLIC_SOURCE_TEMPLATE_HEADERS: dict[str, tuple[str, ...]] = {
    "public_source_catalog.csv": (
        "source_key",
        "source_name",
        "source_type",
        "source_url",
        "local_path",
        "source_date",
        "retrieved_at",
        "source_format",
        "scoring_context",
        "access_method",
        "terms_risk",
        "reliability_score",
        "freshness_window_hours",
        "is_active",
        "notes",
    ),
}

LEGACY_ROW_COLUMNS: dict[str, tuple[str, ...]] = {
    "player_projection_inputs.csv": (
        "source_key",
        "season",
        "player_id",
        "source_player_id",
        "player_name",
        "position",
        "team",
        "projected_points",
        "projected_games",
        "projected_rank",
        "projected_tds",
        "projected_rush_rec_first_downs",
        "raw_payload_ref",
        "source_confidence",
        "notes",
    ),
    "player_market_inputs.csv": (
        "source_key",
        "season",
        "player_id",
        "source_player_id",
        "player_name",
        "position",
        "team",
        "market_rank",
        "market_value",
        "market_format",
        "trade_liquidity_hint",
        "raw_payload_ref",
        "source_confidence",
        "notes",
    ),
    "player_role_inputs.csv": (
        "source_key",
        "season",
        "player_id",
        "source_player_id",
        "player_name",
        "position",
        "team",
        "depth_chart_role",
        "projected_starter",
        "role_security_hint",
        "route_or_touch_role",
        "raw_payload_ref",
        "source_confidence",
        "notes",
    ),
    "player_injury_inputs.csv": (
        "source_key",
        "season",
        "player_id",
        "source_player_id",
        "player_name",
        "position",
        "team",
        "injury_status",
        "injury_detail",
        "missed_time_risk",
        "durability_hint",
        "raw_payload_ref",
        "source_confidence",
        "notes",
    ),
    "player_bio_inputs.csv": (
        "source_key",
        "season",
        "player_id",
        "source_player_id",
        "player_name",
        "position",
        "team",
        "birth_date",
        "age",
        "years_exp",
        "rookie_year",
        "raw_payload_ref",
        "source_confidence",
        "notes",
    ),
    "normalized_veteran_feature_backfill.csv": (
        "season",
        "snapshot_date",
        "player_id",
        "player_name",
        "position",
        "feature_name",
        "normalized_score",
        "source_key",
        "source_confidence",
        "normalization_method",
        "is_missing",
        "missing_reason",
        "notes",
    ),
}

SOURCE_INPUT_FILES = (
    "player_projection_inputs.csv",
    "player_market_inputs.csv",
    "player_role_inputs.csv",
    "player_injury_inputs.csv",
    "player_bio_inputs.csv",
)

SOURCE_DOMAIN_LABELS = {
    "projection": "Projection source",
    "market": "Market/liquidity source",
    "role": "Role/depth-chart source",
    "injury": "Injury/availability source",
    "bio": "Age/experience source",
}

SUPPORTED_POSITIONS = {"QB", "RB", "WR", "TE"}
MODEL_INPUT_SOURCE_CONFIDENCE_VALUES = {
    "verified",
    "derived",
    "manual",
    "estimated",
    "unknown",
}

SOURCE_POLICY: dict[str, dict[str, object]] = {
    "sleeper": {
        "status": "approved",
        "source_family": "league_state",
        "allowed_uses": "identity|league_state|roster_state|status_fallback",
        "forbidden_uses": "player_value",
        "note": "Canonical roster, pick, league, and platform identity source.",
    },
    "ffa": {
        "status": "approved",
        "source_family": "projection",
        "allowed_uses": "projection_stat_lines|lve_projection_rescoring",
        "forbidden_uses": "dynasty_market|direct_first_down_projection_if_absent",
        "note": "Projection stat lines must be rescored locally to LVE settings.",
    },
    "dynastyprocess": {
        "status": "approved_with_haircut",
        "source_family": "market_prior",
        "allowed_uses": "market_prior|trade_liquidity_context",
        "forbidden_uses": "private_lve_value|direct_keeper_score",
        "note": "Generic 1QB market prior only; shrink toward neutral for LVE.",
    },
    "ff_playerids": {
        "status": "approved",
        "source_family": "bio_id_bridge",
        "allowed_uses": "identity_bridge|age|bio|draft_metadata",
        "forbidden_uses": "player_value",
        "note": "Primary cross-platform ID and bio bridge.",
    },
    "injuries": {
        "status": "approved",
        "source_family": "injury",
        "allowed_uses": "injury_status|durability_confidence",
        "forbidden_uses": "unsupported_medical_guess",
        "note": "Use documented injury status; missing data neutralizes with confidence penalty.",
    },
    "depth": {
        "status": "approved",
        "source_family": "role",
        "allowed_uses": "depth_rank|role_security",
        "forbidden_uses": "talent_score",
        "note": "Depth chart rows are role inputs, not talent truth.",
    },
    "snaps": {
        "status": "approved",
        "source_family": "role",
        "allowed_uses": "snap_share|role_stability",
        "forbidden_uses": "talent_score",
        "note": "Snap data supports role stability and route/touch proxies.",
    },
    "player_stats": {
        "status": "approved",
        "source_family": "advanced_stats",
        "allowed_uses": "first_down_td_fit|target_earning|usage_history",
        "forbidden_uses": "source_fantasy_points_without_lve_rescore",
        "note": "Use stat components; rescore fantasy value locally.",
    },
    "ff_opportunity": {
        "status": "approved",
        "source_family": "advanced_stats",
        "allowed_uses": "expected_points|opportunity_context",
        "forbidden_uses": "uncalibrated_final_value",
        "note": "Expected opportunity supports features, not final score overrides.",
    },
    "ngs": {
        "status": "approved",
        "source_family": "advanced_stats",
        "allowed_uses": "position_context|efficiency_context",
        "forbidden_uses": "low_sample_direct_score",
        "note": "Respect sample thresholds and confidence haircuts.",
    },
    "fn_api": {
        "status": "optional_paid",
        "source_family": "licensed_upgrade",
        "allowed_uses": "projection|market_prior|injury|depth",
        "forbidden_uses": "runtime_api_call",
        "note": "Optional licensed refresh source; never expose API key in the app.",
    },
    "sportsdataio": {
        "status": "optional_paid",
        "source_family": "licensed_premium",
        "allowed_uses": "projection|injury|depth|stats",
        "forbidden_uses": "runtime_api_call",
        "note": "Optional premium vendor source; not required for v1.",
    },
    "league_rank_pdf": {
        "status": "approved_limited",
        "source_family": "league_rank",
        "allowed_uses": "forced_release_exposure",
        "forbidden_uses": "player_value|keeper_score|drop_score|market_value",
        "note": "League rank is a summer/declaration rule input only.",
    },
    "ktc": {
        "status": "rejected",
        "source_family": "market",
        "allowed_uses": "manual_human_context_only",
        "forbidden_uses": "machine_ingestion|required_dependency|scraping",
        "note": "No clean API/CSV and scraping is forbidden.",
    },
    "keeptradecut": {
        "status": "rejected",
        "source_family": "market",
        "allowed_uses": "manual_human_context_only",
        "forbidden_uses": "machine_ingestion|required_dependency|scraping",
        "note": "No clean API/CSV and scraping is forbidden.",
    },
    "fantasypros_scrape": {
        "status": "rejected",
        "source_family": "market",
        "allowed_uses": "none",
        "forbidden_uses": "automated_page_extraction|required_dependency",
        "note": "Use only allowed exports or downstream materialized datasets.",
    },
    "fantasycalc": {
        "status": "rejected_for_v1",
        "source_family": "market",
        "allowed_uses": "manual_human_context_only",
        "forbidden_uses": "required_automated_dependency",
        "note": "No stable public automated export/API was accepted for v1.",
    },
}

REJECTED_SOURCE_STATUSES = {"rejected", "rejected_for_v1"}


@dataclass(frozen=True)
class PublicSourceIssue:
    severity: str
    file_name: str
    row_number: int | None
    entity: str
    issue: str
    suggested_fix: str


@dataclass(frozen=True)
class PublicSourceValidationReport:
    root: Path
    status: str
    row_counts: dict[str, int]
    issues: tuple[PublicSourceIssue, ...]


@dataclass(frozen=True)
class PublicSourceMatchRow:
    player_id: str
    player_name: str
    position: str
    team_name: str
    projection_match: bool
    market_match: bool
    role_match: bool
    injury_match: bool
    bio_match: bool
    matched_sources: int
    missing_sources: str


@dataclass(frozen=True)
class PublicSourcePlayerMatchRow:
    file_name: str
    row_number: int
    source_key: str
    source_player_key: str
    source_player_id: str
    source_player_name: str
    source_position: str
    match_status: str
    match_method: str
    matched_player_id: str
    matched_player_name: str
    candidate_player_ids: str
    issue: str
    suggested_fix: str


@dataclass(frozen=True)
class PublicSourceFeatureReadinessRow:
    player_id: str
    player_name: str
    position: str
    feature_name: str
    required_source_type: str
    source_domain: str
    status: str
    source_evidence: str
    normalized_score: str
    confidence: str
    next_action: str
    decision_effect: str


@dataclass(frozen=True)
class UnscoredPlayerRow:
    player_id: str
    player_name: str
    position: str
    team_name: str
    league_rank: str
    model_output_status: str
    missing_feature_rows: int
    next_action: str


@dataclass(frozen=True)
class PublicSourceSnapshotResult:
    snapshot_id: str
    snapshot_path: Path
    status: str
    created: bool
    message: str
    manifest_path: Path | None


@dataclass(frozen=True)
class PublicSourceNormalizationWorklistResult:
    worklist_id: str
    worklist_path: Path
    status: str
    created: bool
    message: str
    csv_path: Path | None
    manifest_path: Path | None


@dataclass(frozen=True)
class PublicSourceModelInputCandidateResult:
    candidate_id: str
    candidate_path: Path
    status: str
    created: bool
    message: str
    csv_path: Path | None
    manifest_path: Path | None


@dataclass(frozen=True)
class PublicSourceModelPreviewResult:
    preview_id: str
    preview_path: Path
    status: str
    created: bool
    message: str
    output_path: Path | None
    manifest_path: Path | None
    model_input_path: Path | None


@dataclass(frozen=True)
class PublicSourceModelPromotionCandidateResult:
    promotion_id: str
    promotion_path: Path
    status: str
    created: bool
    message: str
    csv_path: Path | None
    manifest_path: Path | None


@dataclass(frozen=True)
class PublicSourceModelAppliedPackResult:
    applied_pack_id: str
    applied_pack_path: Path
    status: str
    created: bool
    message: str
    manifest_path: Path | None


def expected_public_source_headers() -> dict[str, tuple[str, ...]]:
    return PUBLIC_SOURCE_TEMPLATE_HEADERS


def public_source_policy_rows() -> list[dict[str, object]]:
    return [
        {
            "source_key": source_key,
            "status": str(policy["status"]),
            "source_family": str(policy["source_family"]),
            "allowed_uses": str(policy["allowed_uses"]),
            "forbidden_uses": str(policy["forbidden_uses"]),
            "note": str(policy["note"]),
        }
        for source_key, policy in SOURCE_POLICY.items()
    ]


def create_public_source_snapshot(
    source_root: str | Path = DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT,
    snapshot_root: str | Path = DEFAULT_PUBLIC_SOURCE_SNAPSHOT_ROOT,
    snapshot_id: str | None = None,
    created_at_utc: datetime | None = None,
) -> PublicSourceSnapshotResult:
    source_root_path = Path(source_root)
    snapshot_root_path = Path(snapshot_root)
    created_at = created_at_utc or datetime.now(UTC)
    resolved_snapshot_id = _snapshot_id(snapshot_id, created_at)
    target = snapshot_root_path / resolved_snapshot_id
    report = validate_public_source_inputs(source_root_path)
    if report.status == "blocked":
        return PublicSourceSnapshotResult(
            snapshot_id=resolved_snapshot_id,
            snapshot_path=target,
            status="blocked",
            created=False,
            message="Source inputs are blocked; fix validation errors before snapshotting.",
            manifest_path=None,
        )
    if target.exists():
        return PublicSourceSnapshotResult(
            snapshot_id=resolved_snapshot_id,
            snapshot_path=target,
            status="blocked",
            created=False,
            message="Snapshot already exists; choose a new snapshot id.",
            manifest_path=None,
        )
    target.mkdir(parents=True, exist_ok=False)
    copied_files: list[dict[str, object]] = []
    for file_name in PUBLIC_SOURCE_TEMPLATE_HEADERS:
        source_file = source_root_path / file_name
        target_file = target / file_name
        shutil.copy2(source_file, target_file)
        copied_files.append(
            {
                "file": file_name,
                "rows": report.row_counts.get(file_name, 0),
                "sha256": _file_sha256(target_file),
            }
        )
    manifest = {
        "snapshot_id": resolved_snapshot_id,
        "created_at_utc": created_at.isoformat(),
        "source_root": str(source_root_path.resolve()),
        "validation_status": report.status,
        "issue_count": len(report.issues),
        "row_counts": report.row_counts,
        "files": copied_files,
        "scoring_effect": "none; raw source snapshot only",
    }
    manifest_path = target / SNAPSHOT_MANIFEST_FILE
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PublicSourceSnapshotResult(
        snapshot_id=resolved_snapshot_id,
        snapshot_path=target.resolve(),
        status=report.status,
        created=True,
        message="Public source snapshot created. It does not change model scores.",
        manifest_path=manifest_path.resolve(),
    )


def public_source_snapshot_rows(
    snapshot_root: str | Path = DEFAULT_PUBLIC_SOURCE_SNAPSHOT_ROOT,
) -> list[dict[str, object]]:
    root = Path(snapshot_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for snapshot_path in sorted(root.iterdir(), reverse=True):
        if not snapshot_path.is_dir():
            continue
        manifest_path = snapshot_path / SNAPSHOT_MANIFEST_FILE
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                manifest = {}
        else:
            manifest = {}
        rows.append(
            {
                "snapshot_id": manifest.get("snapshot_id", snapshot_path.name),
                "created_at_utc": manifest.get("created_at_utc", ""),
                "validation_status": manifest.get("validation_status", "unknown"),
                "issue_count": manifest.get("issue_count", ""),
                "path": str(snapshot_path),
            }
        )
    return rows


def create_public_source_normalization_worklist(
    data_pack_path: str | Path,
    source_root: str | Path = DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT,
    registry_path: str | Path = DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_WORKLIST_ROOT,
    worklist_id: str | None = None,
    created_at_utc: datetime | None = None,
) -> PublicSourceNormalizationWorklistResult:
    created_at = created_at_utc or datetime.now(UTC)
    resolved_worklist_id = _snapshot_id(worklist_id, created_at)
    output_root_path = Path(output_root)
    target = output_root_path / resolved_worklist_id
    if target.exists():
        return PublicSourceNormalizationWorklistResult(
            worklist_id=resolved_worklist_id,
            worklist_path=target,
            status="blocked",
            created=False,
            message="Normalization worklist already exists; choose a new id.",
            csv_path=None,
            manifest_path=None,
        )
    readiness_rows = build_public_source_feature_readiness_rows(
        data_pack_path,
        source_root,
        registry_path,
    )
    worklist_rows = public_source_normalization_worklist_rows(readiness_rows)
    target.mkdir(parents=True, exist_ok=False)
    csv_path = target / NORMALIZATION_WORKLIST_FILE
    _write_csv(
        csv_path,
        _normalization_worklist_header(),
        worklist_rows,
    )
    manifest = {
        "worklist_id": resolved_worklist_id,
        "created_at_utc": created_at.isoformat(),
        "data_pack_path": str(Path(data_pack_path).resolve()),
        "source_root": str(Path(source_root).resolve()),
        "registry_path": str(Path(registry_path).resolve()),
        "row_count": len(worklist_rows),
        "status_counts": _count_by_key(worklist_rows, "status"),
        "priority_counts": _count_by_key(worklist_rows, "priority"),
        "scoring_effect": "none; normalization worklist only",
        "csv_file": NORMALIZATION_WORKLIST_FILE,
        "csv_sha256": _file_sha256(csv_path),
    }
    manifest_path = target / NORMALIZATION_WORKLIST_MANIFEST_FILE
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PublicSourceNormalizationWorklistResult(
        worklist_id=resolved_worklist_id,
        worklist_path=target.resolve(),
        status="created",
        created=True,
        message="Normalization worklist created. It does not change model scores.",
        csv_path=csv_path.resolve(),
        manifest_path=manifest_path.resolve(),
    )


def public_source_normalization_worklist_rows(
    readiness_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    included_statuses = {
        "review",
        "source_available",
        "manual_required",
        "missing_source",
    }
    rows: list[dict[str, object]] = []
    for row in readiness_rows:
        status = str(row.get("status") or "")
        if status not in included_statuses:
            continue
        rows.append(
            {
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "team_id": row.get("team_id", ""),
                "team_name": row.get("team_name", ""),
                "league_rank": row.get("league_rank", ""),
                "feature_name": row.get("feature_name", ""),
                "required_source_type": row.get("required_source_type", ""),
                "source_domain": row.get("source_domain", ""),
                "status": status,
                "priority": _normalization_worklist_priority(row),
                "source_evidence": row.get("source_evidence", ""),
                "normalized_score": row.get("normalized_score", ""),
                "confidence": row.get("confidence", ""),
                "normalization_task": _normalization_task_for_status(status),
                "task_reason": _normalization_task_reason(row),
                "next_action": row.get("next_action", ""),
                "scoring_effect": "none",
            }
        )
    return rows


def public_source_normalization_worklist_snapshot_rows(
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_WORKLIST_ROOT,
) -> list[dict[str, object]]:
    root = Path(output_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for worklist_path in sorted(root.iterdir(), reverse=True):
        if not worklist_path.is_dir():
            continue
        manifest_path = worklist_path / NORMALIZATION_WORKLIST_MANIFEST_FILE
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                manifest = {}
        else:
            manifest = {}
        rows.append(
            {
                "worklist_id": manifest.get("worklist_id", worklist_path.name),
                "created_at_utc": manifest.get("created_at_utc", ""),
                "row_count": manifest.get("row_count", ""),
                "status_counts": json.dumps(
                    manifest.get("status_counts", {}),
                    sort_keys=True,
                ),
                "priority_counts": json.dumps(
                    manifest.get("priority_counts", {}),
                    sort_keys=True,
                ),
                "path": str(worklist_path),
            }
        )
    return rows


def public_source_backfill_acceptance_rows(
    readiness_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in readiness_rows:
        status = str(row.get("status") or "")
        normalized_score = str(row.get("normalized_score") or "")
        confidence = str(row.get("confidence") or "")
        acceptance_status = _backfill_acceptance_status(
            status,
            normalized_score,
            confidence,
        )
        rows.append(
            {
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "team_id": row.get("team_id", ""),
                "team_name": row.get("team_name", ""),
                "league_rank": row.get("league_rank", ""),
                "feature_name": row.get("feature_name", ""),
                "required_source_type": row.get("required_source_type", ""),
                "source_domain": row.get("source_domain", ""),
                "readiness_status": status,
                "acceptance_status": acceptance_status,
                "priority": _backfill_acceptance_priority(row, acceptance_status),
                "source_evidence": row.get("source_evidence", ""),
                "normalized_score": normalized_score,
                "confidence": confidence,
                "blocking": acceptance_status == "blocked",
                "reason": _backfill_acceptance_reason(
                    acceptance_status,
                    status,
                    normalized_score,
                    confidence,
                ),
                "next_action": _backfill_acceptance_next_action(acceptance_status),
                "decision_effect": "review only; no score impact",
            }
        )
    return rows


def public_source_backfill_acceptance_summary_rows(
    acceptance_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = ("accepted", "review", "blocked")
    return [
        {
            "acceptance_status": status,
            "rows": sum(
                1
                for row in acceptance_rows
                if row.get("acceptance_status") == status
            ),
            "high_priority_rows": sum(
                1
                for row in acceptance_rows
                if row.get("acceptance_status") == status
                and row.get("priority") == "high"
            ),
            "decision_effect": "review only; no score impact",
            "next_action": _backfill_acceptance_summary_next_action(status),
        }
        for status in statuses
    ]


def create_public_source_model_input_candidate(
    data_pack_path: str | Path,
    source_root: str | Path = DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT,
    registry_path: str | Path = DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_INPUT_ROOT,
    candidate_id: str | None = None,
    created_at_utc: datetime | None = None,
) -> PublicSourceModelInputCandidateResult:
    created_at = created_at_utc or datetime.now(UTC)
    resolved_candidate_id = _snapshot_id(candidate_id, created_at)
    output_root_path = Path(output_root)
    target = output_root_path / resolved_candidate_id
    if target.exists():
        return PublicSourceModelInputCandidateResult(
            candidate_id=resolved_candidate_id,
            candidate_path=target,
            status="blocked",
            created=False,
            message="Model-input candidate already exists; choose a new id.",
            csv_path=None,
            manifest_path=None,
        )
    readiness_rows = build_public_source_feature_readiness_rows(
        data_pack_path,
        source_root,
        registry_path,
    )
    acceptance_rows = public_source_backfill_acceptance_rows(readiness_rows)
    candidate_rows = public_source_model_input_candidate_rows(
        data_pack_path,
        acceptance_rows,
    )
    if not candidate_rows:
        return PublicSourceModelInputCandidateResult(
            candidate_id=resolved_candidate_id,
            candidate_path=target,
            status="blocked",
            created=False,
            message="No accepted normalized backfill rows are available for export.",
            csv_path=None,
            manifest_path=None,
        )
    target.mkdir(parents=True, exist_ok=False)
    csv_path = target / MODEL_INPUT_CANDIDATE_FILE
    _write_csv(csv_path, _model_input_candidate_header(), candidate_rows)
    manifest = {
        "candidate_id": resolved_candidate_id,
        "created_at_utc": created_at.isoformat(),
        "data_pack_path": str(Path(data_pack_path).resolve()),
        "source_root": str(Path(source_root).resolve()),
        "registry_path": str(Path(registry_path).resolve()),
        "row_count": len(candidate_rows),
        "player_count": len({str(row.get("player_id") or "") for row in candidate_rows}),
        "feature_count": len({str(row.get("feature_name") or "") for row in candidate_rows}),
        "accepted_input_count": sum(
            1 for row in acceptance_rows if row.get("acceptance_status") == "accepted"
        ),
        "excluded_review_count": sum(
            1 for row in acceptance_rows if row.get("acceptance_status") == "review"
        ),
        "excluded_blocked_count": sum(
            1 for row in acceptance_rows if row.get("acceptance_status") == "blocked"
        ),
        "acceptance_status_counts": _count_by_key(
            acceptance_rows,
            "acceptance_status",
        ),
        "candidate_schema": "veteran_feature_scores",
        "scoring_effect": "none; model input candidate only",
        "live_mutation": False,
        "csv_file": MODEL_INPUT_CANDIDATE_FILE,
        "csv_sha256": _file_sha256(csv_path),
    }
    manifest_path = target / MODEL_INPUT_CANDIDATE_MANIFEST_FILE
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PublicSourceModelInputCandidateResult(
        candidate_id=resolved_candidate_id,
        candidate_path=target.resolve(),
        status="created",
        created=True,
        message="Model-input candidate created. It does not change model scores.",
        csv_path=csv_path.resolve(),
        manifest_path=manifest_path.resolve(),
    )


def public_source_model_input_candidate_rows(
    data_pack_path: str | Path,
    acceptance_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    season, snapshot_date = _data_pack_season_snapshot(data_pack_path)
    rows: list[dict[str, object]] = []
    for row in acceptance_rows:
        if row.get("acceptance_status") != "accepted":
            continue
        rows.append(
            {
                "season": season,
                "snapshot_date": snapshot_date,
                "player_id": row.get("player_id", ""),
                "position": row.get("position", ""),
                "feature_name": row.get("feature_name", ""),
                "normalized_score": row.get("normalized_score", ""),
                "source_key": PUBLIC_SOURCE_BACKFILL_SOURCE_KEY,
                "source_confidence": "derived",
                "is_missing": "false",
                "missing_reason": "",
                "is_user_override": "false",
                "override_reason": "",
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("player_id") or ""),
            str(row.get("feature_name") or ""),
        ),
    )


def public_source_model_input_candidate_snapshot_rows(
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_INPUT_ROOT,
) -> list[dict[str, object]]:
    root = Path(output_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for candidate_path in sorted(root.iterdir(), reverse=True):
        if not candidate_path.is_dir():
            continue
        manifest_path = candidate_path / MODEL_INPUT_CANDIDATE_MANIFEST_FILE
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                manifest = {}
        else:
            manifest = {}
        rows.append(
            {
                "candidate_id": manifest.get("candidate_id", candidate_path.name),
                "created_at_utc": manifest.get("created_at_utc", ""),
                "row_count": manifest.get("row_count", ""),
                "player_count": manifest.get("player_count", ""),
                "feature_count": manifest.get("feature_count", ""),
                "accepted_input_count": manifest.get("accepted_input_count", ""),
                "excluded_review_count": manifest.get("excluded_review_count", ""),
                "excluded_blocked_count": manifest.get("excluded_blocked_count", ""),
                "acceptance_status_counts": json.dumps(
                    manifest.get("acceptance_status_counts", {}),
                    sort_keys=True,
                ),
                "live_mutation": manifest.get("live_mutation", ""),
                "path": str(candidate_path),
            }
        )
    return rows


def public_source_model_input_candidate_validation_rows(
    data_pack_path: str | Path,
    candidate_rows: list[dict[str, object]],
    registry_path: str | Path = DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
) -> list[dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    player_positions = _player_positions_from_data_pack(validated.rows_by_table)
    active_features = _active_feature_registry_rows(registry_path)
    active_feature_keys = {
        (position, feature["feature_name"])
        for position, features in active_features.items()
        for feature in features
    }
    key_counts = _candidate_key_counts(candidate_rows)
    rows: list[dict[str, object]] = []
    for row in candidate_rows:
        player_id = str(row.get("player_id") or "")
        position = str(row.get("position") or "")
        feature_name = str(row.get("feature_name") or "")
        normalized_score = str(row.get("normalized_score") or "")
        status, reason = _model_input_candidate_validation_status(
            row,
            player_positions,
            active_feature_keys,
            key_counts,
        )
        rows.append(
            {
                "player_id": player_id,
                "position": position,
                "feature_name": feature_name,
                "normalized_score": normalized_score,
                "validation_status": status,
                "blocking": status == "blocked",
                "reason": reason,
                "next_action": _model_input_candidate_validation_next_action(status),
                "decision_effect": "review only; no score impact",
            }
        )
    return rows


def public_source_model_input_candidate_validation_summary_rows(
    validation_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = ("accepted", "review", "blocked")
    return [
        {
            "validation_status": status,
            "rows": sum(
                1 for row in validation_rows if row.get("validation_status") == status
            ),
            "decision_effect": "review only; no score impact",
            "next_action": _model_input_candidate_validation_summary_next_action(status),
        }
        for status in statuses
    ]


def public_source_model_input_candidate_coverage_rows(
    data_pack_path: str | Path,
    candidate_rows: list[dict[str, object]],
    validation_rows: list[dict[str, object]],
    registry_path: str | Path = DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
) -> list[dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    active_features = _active_feature_registry_rows(registry_path)
    accepted_feature_keys = {
        (str(row.get("player_id") or ""), str(row.get("feature_name") or ""))
        for row in candidate_rows
        if _candidate_row_validation_status(row, validation_rows) == "accepted"
    }
    rows: list[dict[str, object]] = []
    for roster_row in validated.rows_by_table.get("rosters", []):
        position = str(roster_row.get("position") or "")
        if position not in SUPPORTED_POSITIONS:
            continue
        player_id = str(roster_row.get("player_id") or "")
        player_name = str(roster_row.get("player_name") or "")
        required_features = [
            feature["feature_name"] for feature in active_features.get(position, [])
        ]
        present_features = [
            feature_name
            for feature_name in required_features
            if (player_id, feature_name) in accepted_feature_keys
        ]
        missing_features = [
            feature_name
            for feature_name in required_features
            if feature_name not in present_features
        ]
        status = _candidate_coverage_status(
            len(present_features),
            len(required_features),
        )
        rows.append(
            {
                "player_id": player_id,
                "player_name": player_name,
                "position": position,
                "accepted_features": len(present_features),
                "required_features": len(required_features),
                "coverage_pct": _coverage_pct(
                    len(present_features),
                    len(required_features),
                ),
                "coverage_status": status,
                "missing_features": "|".join(missing_features),
                "next_action": _candidate_coverage_next_action(status),
                "decision_effect": "review only; no score impact",
            }
        )
    return rows


def public_source_model_input_candidate_coverage_summary_rows(
    coverage_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = ("complete", "partial", "empty")
    return [
        {
            "coverage_status": status,
            "players": sum(
                1 for row in coverage_rows if row.get("coverage_status") == status
            ),
            "decision_effect": "review only; no score impact",
            "next_action": _candidate_coverage_summary_next_action(status),
        }
        for status in statuses
    ]


def create_public_source_model_preview(
    data_pack_path: str | Path,
    source_root: str | Path = DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT,
    registry_path: str | Path = DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PREVIEW_ROOT,
    preview_id: str | None = None,
    created_at_utc: datetime | None = None,
) -> PublicSourceModelPreviewResult:
    created_at = created_at_utc or datetime.now(UTC)
    resolved_preview_id = _snapshot_id(preview_id, created_at)
    output_root_path = Path(output_root)
    target = output_root_path / resolved_preview_id
    if target.exists():
        return PublicSourceModelPreviewResult(
            preview_id=resolved_preview_id,
            preview_path=target,
            status="blocked",
            created=False,
            message="Model preview already exists; choose a new id.",
            output_path=None,
            manifest_path=None,
            model_input_path=None,
        )

    readiness_rows = build_public_source_feature_readiness_rows(
        data_pack_path,
        source_root,
        registry_path,
    )
    acceptance_rows = public_source_backfill_acceptance_rows(readiness_rows)
    candidate_rows = public_source_model_input_candidate_rows(
        data_pack_path,
        acceptance_rows,
    )
    validation_rows = public_source_model_input_candidate_validation_rows(
        data_pack_path,
        candidate_rows,
        registry_path,
    )
    coverage_rows = public_source_model_input_candidate_coverage_rows(
        data_pack_path,
        candidate_rows,
        validation_rows,
        registry_path,
    )
    complete_player_ids = {
        str(row.get("player_id") or "")
        for row in coverage_rows
        if row.get("coverage_status") == "complete"
    }
    preview_feature_rows = [
        row
        for row in candidate_rows
        if str(row.get("player_id") or "") in complete_player_ids
        and _candidate_row_validation_status(row, validation_rows) == "accepted"
    ]
    if not complete_player_ids or not preview_feature_rows:
        return PublicSourceModelPreviewResult(
            preview_id=resolved_preview_id,
            preview_path=target,
            status="blocked",
            created=False,
            message="No complete-coverage players are available for isolated preview.",
            output_path=None,
            manifest_path=None,
            model_input_path=None,
        )

    target.mkdir(parents=True, exist_ok=False)
    model_input_path = target / MODEL_PREVIEW_INPUT_DIR
    model_input_path.mkdir(parents=True, exist_ok=False)
    _write_model_preview_inputs(
        data_pack_path,
        registry_path,
        model_input_path,
        preview_feature_rows,
        complete_player_ids,
        source_root,
        created_at,
    )
    run = run_veteran_model_from_dir(model_input_path)
    season, snapshot_date = _data_pack_season_snapshot(data_pack_path)
    output_rows = generated_model_output_rows(
        run.scores,
        snapshot_date=snapshot_date,
        computed_at=created_at.isoformat(),
    )
    output_path = target / MODEL_PREVIEW_OUTPUT_FILE
    _write_csv(output_path, tuple(output_rows[0].keys()), output_rows)
    manifest = {
        "preview_id": resolved_preview_id,
        "created_at_utc": created_at.isoformat(),
        "data_pack_path": str(Path(data_pack_path).resolve()),
        "source_root": str(Path(source_root).resolve()),
        "registry_path": str(Path(registry_path).resolve()),
        "season": season,
        "snapshot_date": snapshot_date,
        "complete_player_count": len(complete_player_ids),
        "feature_row_count": len(preview_feature_rows),
        "output_row_count": len(output_rows),
        "schema_warning_count": len(
            [
                issue
                for issue in run.schema_report.issues
                if issue.severity == "warning"
            ]
        ),
        "scoring_effect": (
            "isolated preview only; no live model inputs, selected pack, or "
            "recommendations were changed"
        ),
        "model_input_dir": MODEL_PREVIEW_INPUT_DIR,
        "output_file": MODEL_PREVIEW_OUTPUT_FILE,
        "output_sha256": _file_sha256(output_path),
    }
    manifest_path = target / MODEL_PREVIEW_MANIFEST_FILE
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PublicSourceModelPreviewResult(
        preview_id=resolved_preview_id,
        preview_path=target.resolve(),
        status="created",
        created=True,
        message="Isolated model preview created. Live model outputs were not changed.",
        output_path=output_path.resolve(),
        manifest_path=manifest_path.resolve(),
        model_input_path=model_input_path.resolve(),
    )


def public_source_model_preview_snapshot_rows(
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PREVIEW_ROOT,
) -> list[dict[str, object]]:
    root = Path(output_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for preview_path in sorted(root.iterdir(), reverse=True):
        if not preview_path.is_dir():
            continue
        manifest_path = preview_path / MODEL_PREVIEW_MANIFEST_FILE
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                manifest = {}
        else:
            manifest = {}
        rows.append(
            {
                "preview_id": manifest.get("preview_id", preview_path.name),
                "created_at_utc": manifest.get("created_at_utc", ""),
                "complete_player_count": manifest.get("complete_player_count", ""),
                "feature_row_count": manifest.get("feature_row_count", ""),
                "output_row_count": manifest.get("output_row_count", ""),
                "schema_warning_count": manifest.get("schema_warning_count", ""),
                "scoring_effect": manifest.get("scoring_effect", ""),
                "path": str(preview_path),
            }
        )
    return rows


def public_source_model_preview_review_rows(
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PREVIEW_ROOT,
) -> list[dict[str, object]]:
    root = Path(output_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for preview_path in sorted(root.iterdir(), reverse=True):
        if not preview_path.is_dir():
            continue
        manifest = _read_json_manifest(preview_path / MODEL_PREVIEW_MANIFEST_FILE)
        preview_id = str(manifest.get("preview_id") or preview_path.name)
        output_path = preview_path / str(
            manifest.get("output_file") or MODEL_PREVIEW_OUTPUT_FILE
        )
        schema_warning_count = _int_or_zero(manifest.get("schema_warning_count", 0))
        if not output_path.exists():
            rows.append(
                {
                    "preview_id": preview_id,
                    "player_id": "",
                    "player_name": "",
                    "position": "",
                    "keeper_score": "",
                    "drop_candidate_score": "",
                    "confidence_score": "",
                    "warning_status": "missing_output",
                    "risk_level": "",
                    "missing_data_penalty": "",
                    "schema_warning_count": schema_warning_count,
                    "preview_review_status": "blocked",
                    "blocking": True,
                    "reason": "Preview manifest exists, but output CSV is missing.",
                    "next_action": "Regenerate the isolated model preview.",
                    "decision_effect": "review only; no live score impact",
                }
            )
            continue
        _, output_rows = _read_csv(output_path)
        for output_row in output_rows:
            status, reason, next_action = _model_preview_review_status(
                output_row,
                schema_warning_count,
            )
            rows.append(
                {
                    "preview_id": preview_id,
                    "player_id": output_row.get("player_id", ""),
                    "player_name": output_row.get("player_name", ""),
                    "position": output_row.get("position", ""),
                    "keeper_score": output_row.get("keeper_score", ""),
                    "drop_candidate_score": output_row.get(
                        "drop_candidate_score",
                        "",
                    ),
                    "confidence_score": output_row.get("confidence_score", ""),
                    "warning_status": output_row.get("warning_status", ""),
                    "risk_level": output_row.get("risk_level", ""),
                    "missing_data_penalty": output_row.get(
                        "missing_data_penalty",
                        "",
                    ),
                    "schema_warning_count": schema_warning_count,
                    "preview_review_status": status,
                    "blocking": status == "blocked",
                    "reason": reason,
                    "next_action": next_action,
                    "decision_effect": "review only; no live score impact",
                }
            )
    return rows


def public_source_model_preview_review_summary_rows(
    review_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = ("ready", "review", "blocked")
    return [
        {
            "preview_review_status": status,
            "rows": sum(
                1
                for row in review_rows
                if row.get("preview_review_status") == status
            ),
            "decision_effect": "review only; no live score impact",
            "next_action": _model_preview_review_summary_next_action(status),
        }
        for status in statuses
    ]


def public_source_model_preview_comparison_rows(
    data_pack_path: str | Path,
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PREVIEW_ROOT,
) -> list[dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    live_outputs = {
        str(row.get("player_id") or ""): row
        for row in validated.rows_by_table.get("model_outputs", [])
    }
    rows: list[dict[str, object]] = []
    for preview_row in public_source_model_preview_review_rows(output_root):
        player_id = str(preview_row.get("player_id") or "")
        live_row = live_outputs.get(player_id, {})
        status, reason, next_action = _model_preview_comparison_status(
            preview_row,
            live_row,
        )
        live_keeper = str(live_row.get("keeper_score") or "")
        preview_keeper = str(preview_row.get("keeper_score") or "")
        live_drop = str(live_row.get("drop_candidate_score") or "")
        preview_drop = str(preview_row.get("drop_candidate_score") or "")
        live_confidence = str(live_row.get("confidence_score") or "")
        preview_confidence = str(preview_row.get("confidence_score") or "")
        rows.append(
            {
                "preview_id": preview_row.get("preview_id", ""),
                "player_id": player_id,
                "player_name": preview_row.get("player_name", ""),
                "position": preview_row.get("position", ""),
                "live_keeper_score": live_keeper,
                "preview_keeper_score": preview_keeper,
                "keeper_delta": _score_delta(preview_keeper, live_keeper),
                "live_drop_candidate_score": live_drop,
                "preview_drop_candidate_score": preview_drop,
                "drop_delta": _score_delta(preview_drop, live_drop),
                "live_confidence_score": live_confidence,
                "preview_confidence_score": preview_confidence,
                "confidence_delta": _score_delta(
                    preview_confidence,
                    live_confidence,
                    confidence=True,
                ),
                "live_recommendation": live_row.get("recommendation", ""),
                "preview_review_status": preview_row.get(
                    "preview_review_status",
                    "",
                ),
                "comparison_status": status,
                "blocking": status == "blocked",
                "reason": reason,
                "next_action": next_action,
                "decision_effect": "comparison only; no live score impact",
            }
        )
    return rows


def public_source_model_preview_comparison_summary_rows(
    comparison_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = ("ready", "review", "blocked")
    return [
        {
            "comparison_status": status,
            "rows": sum(
                1 for row in comparison_rows if row.get("comparison_status") == status
            ),
            "decision_effect": "comparison only; no live score impact",
            "next_action": _model_preview_comparison_summary_next_action(status),
        }
        for status in statuses
    ]


def create_public_source_model_promotion_candidate(
    data_pack_path: str | Path,
    preview_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PREVIEW_ROOT,
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PROMOTION_ROOT,
    promotion_id: str | None = None,
    created_at_utc: datetime | None = None,
) -> PublicSourceModelPromotionCandidateResult:
    created_at = created_at_utc or datetime.now(UTC)
    resolved_promotion_id = _snapshot_id(promotion_id, created_at)
    output_root_path = Path(output_root)
    target = output_root_path / resolved_promotion_id
    if target.exists():
        return PublicSourceModelPromotionCandidateResult(
            promotion_id=resolved_promotion_id,
            promotion_path=target,
            status="blocked",
            created=False,
            message="Promotion candidate already exists; choose a new id.",
            csv_path=None,
            manifest_path=None,
        )

    comparison_rows = public_source_model_preview_comparison_rows(
        data_pack_path,
        preview_root,
    )
    ready_keys = {
        (str(row.get("preview_id") or ""), str(row.get("player_id") or ""))
        for row in comparison_rows
        if row.get("comparison_status") == "ready"
    }
    promotion_rows = _model_promotion_candidate_rows(preview_root, ready_keys)
    if not promotion_rows:
        return PublicSourceModelPromotionCandidateResult(
            promotion_id=resolved_promotion_id,
            promotion_path=target,
            status="blocked",
            created=False,
            message="No ready preview-vs-live rows are available for promotion candidate export.",
            csv_path=None,
            manifest_path=None,
        )

    target.mkdir(parents=True, exist_ok=False)
    csv_path = target / MODEL_PROMOTION_FILE
    _write_csv(csv_path, tuple(promotion_rows[0].keys()), promotion_rows)
    manifest = {
        "promotion_id": resolved_promotion_id,
        "created_at_utc": created_at.isoformat(),
        "data_pack_path": str(Path(data_pack_path).resolve()),
        "preview_root": str(Path(preview_root).resolve()),
        "row_count": len(promotion_rows),
        "comparison_status_counts": _count_by_key(
            comparison_rows,
            "comparison_status",
        ),
        "scoring_effect": (
            "promotion candidate only; live model_outputs.csv was not changed"
        ),
        "csv_file": MODEL_PROMOTION_FILE,
        "csv_sha256": _file_sha256(csv_path),
    }
    manifest_path = target / MODEL_PROMOTION_MANIFEST_FILE
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PublicSourceModelPromotionCandidateResult(
        promotion_id=resolved_promotion_id,
        promotion_path=target.resolve(),
        status="created",
        created=True,
        message="Promotion candidate exported. Live model outputs were not changed.",
        csv_path=csv_path.resolve(),
        manifest_path=manifest_path.resolve(),
    )


def public_source_model_promotion_candidate_snapshot_rows(
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PROMOTION_ROOT,
) -> list[dict[str, object]]:
    root = Path(output_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for promotion_path in sorted(root.iterdir(), reverse=True):
        if not promotion_path.is_dir():
            continue
        manifest = _read_json_manifest(
            promotion_path / MODEL_PROMOTION_MANIFEST_FILE
        )
        rows.append(
            {
                "promotion_id": manifest.get("promotion_id", promotion_path.name),
                "created_at_utc": manifest.get("created_at_utc", ""),
                "row_count": manifest.get("row_count", ""),
                "comparison_status_counts": json.dumps(
                    manifest.get("comparison_status_counts", {}),
                    sort_keys=True,
                ),
                "scoring_effect": manifest.get("scoring_effect", ""),
                "path": str(promotion_path),
            }
        )
    return rows


def public_source_model_promotion_candidate_review_rows(
    data_pack_path: str | Path,
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PROMOTION_ROOT,
) -> list[dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    live_outputs = {
        str(row.get("player_id") or ""): row
        for row in validated.rows_by_table.get("model_outputs", [])
    }
    root = Path(output_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for promotion_path in sorted(root.iterdir(), reverse=True):
        if not promotion_path.is_dir():
            continue
        manifest = _read_json_manifest(
            promotion_path / MODEL_PROMOTION_MANIFEST_FILE
        )
        promotion_id = str(manifest.get("promotion_id") or promotion_path.name)
        csv_path = promotion_path / str(
            manifest.get("csv_file") or MODEL_PROMOTION_FILE
        )
        if not csv_path.exists():
            rows.append(
                {
                    "promotion_id": promotion_id,
                    "player_id": "",
                    "player_name": "",
                    "position": "",
                    "keeper_delta": "",
                    "drop_delta": "",
                    "confidence_delta": "",
                    "promotion_review_status": "blocked",
                    "blocking": True,
                    "reason": "Promotion candidate manifest exists, but CSV is missing.",
                    "next_action": "Regenerate the promotion candidate.",
                    "decision_effect": "review only; no live score impact",
                }
            )
            continue
        _, candidate_rows = _read_csv(csv_path)
        for candidate_row in candidate_rows:
            player_id = str(candidate_row.get("player_id") or "")
            live_row = live_outputs.get(player_id, {})
            status, reason, next_action = _model_promotion_candidate_review_status(
                candidate_row,
                live_row,
            )
            rows.append(
                {
                    "promotion_id": promotion_id,
                    "player_id": player_id,
                    "player_name": candidate_row.get("player_name", ""),
                    "position": candidate_row.get("position", ""),
                    "keeper_delta": _score_delta(
                        str(candidate_row.get("keeper_score") or ""),
                        str(live_row.get("keeper_score") or ""),
                    ),
                    "drop_delta": _score_delta(
                        str(candidate_row.get("drop_candidate_score") or ""),
                        str(live_row.get("drop_candidate_score") or ""),
                    ),
                    "confidence_delta": _score_delta(
                        str(candidate_row.get("confidence_score") or ""),
                        str(live_row.get("confidence_score") or ""),
                        confidence=True,
                    ),
                    "candidate_status": candidate_row.get("promotion_status", ""),
                    "source_preview_id": candidate_row.get(
                        "promotion_source_preview_id",
                        "",
                    ),
                    "promotion_review_status": status,
                    "blocking": status == "blocked",
                    "reason": reason,
                    "next_action": next_action,
                    "decision_effect": "review only; no live score impact",
                }
            )
    return rows


def public_source_model_promotion_candidate_review_summary_rows(
    review_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = ("ready", "review", "blocked")
    return [
        {
            "promotion_review_status": status,
            "rows": sum(
                1
                for row in review_rows
                if row.get("promotion_review_status") == status
            ),
            "decision_effect": "review only; no live score impact",
            "next_action": _model_promotion_candidate_review_summary_next_action(
                status
            ),
        }
        for status in statuses
    ]


def create_public_source_model_applied_pack(
    data_pack_path: str | Path,
    promotion_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PROMOTION_ROOT,
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_APPLIED_PACK_ROOT,
    applied_pack_id: str | None = None,
    created_at_utc: datetime | None = None,
) -> PublicSourceModelAppliedPackResult:
    created_at = created_at_utc or datetime.now(UTC)
    resolved_applied_pack_id = _snapshot_id(applied_pack_id, created_at)
    output_root_path = Path(output_root)
    target = output_root_path / resolved_applied_pack_id
    if target.exists():
        return PublicSourceModelAppliedPackResult(
            applied_pack_id=resolved_applied_pack_id,
            applied_pack_path=target,
            status="blocked",
            created=False,
            message="Applied data pack already exists; choose a new id.",
            manifest_path=None,
        )

    review_rows = public_source_model_promotion_candidate_review_rows(
        data_pack_path,
        promotion_root,
    )
    ready_rows = [
        row for row in review_rows if row.get("promotion_review_status") == "ready"
    ]
    ready_player_counts = _count_by_key(ready_rows, "player_id")
    duplicate_ready_players = [
        player_id
        for player_id, count in ready_player_counts.items()
        if player_id and count > 1
    ]
    if duplicate_ready_players:
        return PublicSourceModelAppliedPackResult(
            applied_pack_id=resolved_applied_pack_id,
            applied_pack_path=target,
            status="blocked",
            created=False,
            message=(
                "Multiple ready promotion candidates exist for the same player; "
                "review duplicates before applying."
            ),
            manifest_path=None,
        )
    ready_keys = {
        (str(row.get("promotion_id") or ""), str(row.get("player_id") or ""))
        for row in ready_rows
    }
    promotion_rows = _ready_promotion_candidate_rows(promotion_root, ready_keys)
    if not promotion_rows:
        return PublicSourceModelAppliedPackResult(
            applied_pack_id=resolved_applied_pack_id,
            applied_pack_path=target,
            status="blocked",
            created=False,
            message="No ready promotion candidates are available to apply.",
            manifest_path=None,
        )

    shutil.copytree(data_pack_path, target)
    applied_count = _apply_model_output_rows(target / "model_outputs.csv", promotion_rows)
    validated = validate_data_pack(target)
    manifest = {
        "applied_pack_id": resolved_applied_pack_id,
        "created_at_utc": created_at.isoformat(),
        "source_data_pack_path": str(Path(data_pack_path).resolve()),
        "promotion_root": str(Path(promotion_root).resolve()),
        "applied_row_count": applied_count,
        "promotion_candidate_count": len(promotion_rows),
        "validation_error_count": sum(
            1 for issue in validated.issues if issue.severity == "error"
        ),
        "validation_warning_count": sum(
            1 for issue in validated.issues if issue.severity == "warning"
        ),
        "scoring_effect": (
            "new generated data pack copy only; selected source pack was not changed"
        ),
    }
    manifest_path = target / MODEL_APPLIED_PACK_MANIFEST_FILE
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PublicSourceModelAppliedPackResult(
        applied_pack_id=resolved_applied_pack_id,
        applied_pack_path=target.resolve(),
        status="created",
        created=True,
        message="Applied data pack copy created. The selected pack was not changed.",
        manifest_path=manifest_path.resolve(),
    )


def public_source_model_applied_pack_snapshot_rows(
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_APPLIED_PACK_ROOT,
) -> list[dict[str, object]]:
    root = Path(output_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for pack_path in sorted(root.iterdir(), reverse=True):
        if not pack_path.is_dir():
            continue
        manifest = _read_json_manifest(pack_path / MODEL_APPLIED_PACK_MANIFEST_FILE)
        if not manifest:
            continue
        rows.append(
            {
                "applied_pack_id": manifest.get("applied_pack_id", pack_path.name),
                "created_at_utc": manifest.get("created_at_utc", ""),
                "applied_row_count": manifest.get("applied_row_count", ""),
                "promotion_candidate_count": manifest.get(
                    "promotion_candidate_count",
                    "",
                ),
                "validation_errors": manifest.get("validation_error_count", ""),
                "validation_warnings": manifest.get("validation_warning_count", ""),
                "scoring_effect": manifest.get("scoring_effect", ""),
                "path": str(pack_path),
            }
        )
    return rows


def public_source_model_applied_pack_review_rows(
    output_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_APPLIED_PACK_ROOT,
) -> list[dict[str, object]]:
    root = Path(output_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for pack_path in sorted(root.iterdir(), reverse=True):
        if not pack_path.is_dir():
            continue
        manifest = _read_json_manifest(pack_path / MODEL_APPLIED_PACK_MANIFEST_FILE)
        if not manifest:
            continue
        try:
            validated = validate_data_pack(pack_path)
            error_count = sum(
                1 for issue in validated.issues if issue.severity == "error"
            )
            warning_count = sum(
                1 for issue in validated.issues if issue.severity == "warning"
            )
            roster_count = len(validated.rows_by_table.get("rosters", []))
            output_count = len(validated.rows_by_table.get("model_outputs", []))
            validation_exception = ""
        except Exception as exc:
            error_count = 1
            warning_count = 0
            roster_count = 0
            output_count = 0
            validation_exception = str(exc)
        status, reason, next_action = _model_applied_pack_review_status(
            manifest,
            error_count,
            warning_count,
            output_count,
            validation_exception,
        )
        rows.append(
            {
                "applied_pack_id": manifest.get("applied_pack_id", pack_path.name),
                "created_at_utc": manifest.get("created_at_utc", ""),
                "applied_row_count": manifest.get("applied_row_count", ""),
                "promotion_candidate_count": manifest.get(
                    "promotion_candidate_count",
                    "",
                ),
                "roster_count": roster_count,
                "model_output_count": output_count,
                "validation_errors": error_count,
                "validation_warnings": warning_count,
                "applied_pack_review_status": status,
                "blocking": status == "blocked",
                "reason": reason,
                "next_action": next_action,
                "decision_effect": "pack admission only; no live score impact",
                "path": str(pack_path),
            }
        )
    return rows


def public_source_model_applied_pack_review_summary_rows(
    review_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = ("ready", "review", "blocked")
    return [
        {
            "applied_pack_review_status": status,
            "rows": sum(
                1
                for row in review_rows
                if row.get("applied_pack_review_status") == status
            ),
            "decision_effect": "pack admission only; no live score impact",
            "next_action": _model_applied_pack_review_summary_next_action(status),
        }
        for status in statuses
    ]


def validate_public_source_inputs(
    root: str | Path = DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT,
) -> PublicSourceValidationReport:
    root_path = Path(root)
    issues: list[PublicSourceIssue] = []
    row_counts: dict[str, int] = {}
    catalog_rows: list[dict[str, str]] = []
    for file_name, expected_header in PUBLIC_SOURCE_TEMPLATE_HEADERS.items():
        path = root_path / file_name
        if not path.exists():
            issues.append(
                PublicSourceIssue(
                    "error",
                    file_name,
                    None,
                    "",
                    "Public source input file is missing.",
                    f"Create {file_name} from the template.",
                )
            )
            row_counts[file_name] = 0
            continue
        header, rows = _read_csv(path)
        row_counts[file_name] = len(rows)
        accepted_headers = (expected_header, LEGACY_ROW_COLUMNS.get(file_name, ()))
        if file_name in LEGACY_PUBLIC_SOURCE_TEMPLATE_HEADERS:
            accepted_headers = (
                expected_header,
                LEGACY_PUBLIC_SOURCE_TEMPLATE_HEADERS[file_name],
            )
        missing_columns = []
        if not any(
            all(column in header for column in accepted_header)
            for accepted_header in accepted_headers
            if accepted_header
        ):
            missing_columns = [
                column for column in expected_header if column not in header
            ]
        if missing_columns:
            issues.append(
                PublicSourceIssue(
                    "error",
                    file_name,
                    None,
                    "",
                    "Missing required columns: " + ", ".join(missing_columns) + ".",
                    "Use the committed public source template header.",
                )
            )
        issues.extend(_validate_rows(file_name, rows))
        if file_name == "public_source_catalog.csv":
            catalog_rows = rows
    catalog_keys = {_row_source_key(row) for row in catalog_rows}
    issues.extend(_validate_source_policy(catalog_rows))
    issues.extend(_validate_source_references(root_path, catalog_keys))
    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    return PublicSourceValidationReport(
        root=root_path.resolve(),
        status="blocked" if error_count else "review" if warning_count else "ready",
        row_counts=row_counts,
        issues=tuple(issues),
    )


def public_source_issue_rows(
    report: PublicSourceValidationReport,
) -> list[dict[str, object]]:
    return [
        {
            "severity": issue.severity,
            "file": issue.file_name,
            "row": issue.row_number or "",
            "entity": issue.entity,
            "issue": issue.issue,
            "fix": issue.suggested_fix,
        }
        for issue in report.issues
    ]


def public_source_count_rows(
    report: PublicSourceValidationReport,
) -> list[dict[str, object]]:
    return [
        {"file": file_name, "rows": report.row_counts.get(file_name, 0)}
        for file_name in PUBLIC_SOURCE_TEMPLATE_HEADERS
    ]


def public_source_domain_rows(
    match_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rostered_count = len(match_rows)
    rows: list[dict[str, object]] = []
    for domain, label in SOURCE_DOMAIN_LABELS.items():
        column = f"{domain}_match"
        matched = sum(1 for row in match_rows if row.get(column) is True)
        missing = rostered_count - matched
        status = (
            "empty"
            if matched == 0
            else "partial"
            if missing
            else "complete"
        )
        rows.append(
            {
                "domain": domain,
                "label": label,
                "matched_players": matched,
                "rostered_players": rostered_count,
                "missing_players": missing,
                "status": status,
                "next_action": _source_domain_next_action(domain, status),
            }
        )
    return rows


def public_source_projection_rescore_rows(
    source_root: str | Path,
) -> list[dict[str, object]]:
    """Rescore staged projection stat lines to LVE settings.

    This scaffold is intentionally side-effect free. It lets free/public or
    future paid projection exports be converted to local LVE points before any
    normalized model feature is accepted.
    """

    root = Path(source_root)
    _, projection_rows = _read_csv(root / "player_projection_inputs.csv")
    rescored_rows: list[dict[str, object]] = []
    for row in projection_rows:
        position = str(row.get("position") or "")
        if position not in SUPPORTED_POSITIONS:
            continue
        scored = _rescore_projection_row_lve(row)
        rescored_rows.append(
            {
                "player_key": _row_player_key(row),
                "player_name": row.get("player_name", ""),
                "position": position,
                "team": row.get("team", ""),
                "season": row.get("season", ""),
                "asof_date": row.get("asof_date", ""),
                "projection_source_id": row.get("projection_source_id", ""),
                "projected_lve_points": f"{scored['projected_lve_points']:.2f}",
                "projected_rush_first_downs": f"{scored['rush_first_downs']:.2f}",
                "projected_rec_first_downs": f"{scored['rec_first_downs']:.2f}",
                "first_down_source": scored["first_down_source"],
                "missing_projection_flags": "|".join(scored["missing_flags"]),
                "projection_confidence": row.get("projection_confidence", ""),
                "scoring_profile_id": "lve_1qb_non_ppr_0_4_fd",
                "scoring_notes": (
                    "No PPR; 3-point passing TD; 4-point rushing/receiving TD; "
                    "0.4 rushing/receiving first down."
                ),
            }
        )
    return rescored_rows


def public_source_projection_rescore_summary_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    total = len(rows)
    direct = sum(1 for row in rows if row["first_down_source"] == "direct")
    estimated = sum(1 for row in rows if row["first_down_source"] == "estimated")
    missing = sum(1 for row in rows if row["first_down_source"] == "missing")
    return [
        {"metric": "projection_rows", "value": total},
        {"metric": "direct_first_down_rows", "value": direct},
        {"metric": "estimated_first_down_rows", "value": estimated},
        {"metric": "missing_first_down_rows", "value": missing},
    ]


def build_public_source_player_match_rows(
    data_pack_path: str | Path,
    source_root: str | Path = DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT,
) -> list[dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    index = _build_player_match_index(validated.rows_by_table)
    rows: list[dict[str, object]] = []
    for file_name in SOURCE_INPUT_FILES + ("normalized_veteran_feature_backfill.csv",):
        path = Path(source_root) / file_name
        if not path.exists():
            continue
        _, source_rows = _read_csv(path)
        for row_number, row in enumerate(source_rows, start=2):
            player_name = (row.get("player_name") or "").strip()
            position = (row.get("position") or "").strip()
            if position and position not in SUPPORTED_POSITIONS:
                continue
            match = _match_source_player(row, index)
            rows.append(
                {
                    "file_name": file_name,
                    "row_number": row_number,
                    "source_key": _row_source_key(row),
                    "source_player_key": _row_player_key(row),
                    "source_player_id": (row.get("source_player_id") or "").strip(),
                    "source_player_name": player_name,
                    "source_position": position,
                    "match_status": match["match_status"],
                    "match_method": match["match_method"],
                    "matched_player_id": match["matched_player_id"],
                    "matched_player_name": match["matched_player_name"],
                    "candidate_player_ids": match["candidate_player_ids"],
                    "issue": match["issue"],
                    "suggested_fix": match["suggested_fix"],
                }
            )
    return rows


def public_source_player_match_summary_rows(
    match_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = ("matched", "ambiguous", "unmatched")
    return [
        {
            "match_status": status,
            "rows": sum(1 for row in match_rows if row.get("match_status") == status),
            "decision_effect": "review only; no score impact",
            "next_action": _match_status_next_action(status),
        }
        for status in statuses
    ]


def build_public_source_feature_readiness_rows(
    data_pack_path: str | Path,
    source_root: str | Path = DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT,
    registry_path: str | Path = DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
) -> list[dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    matched_source_domains = _matched_source_domains_by_player(
        build_public_source_player_match_rows(data_pack_path, source_root)
    )
    backfill_values = _feature_backfill_values(
        Path(source_root) / "normalized_veteran_feature_backfill.csv"
    )
    active_features = _active_feature_registry_rows(registry_path)
    rows: list[dict[str, object]] = []
    for roster_row in validated.rows_by_table.get("rosters", []):
        position = str(roster_row.get("position") or "")
        if position not in SUPPORTED_POSITIONS:
            continue
        player_id = str(roster_row.get("player_id") or "")
        player_name = str(roster_row.get("player_name") or "")
        for feature in active_features.get(position, []):
            feature_name = feature["feature_name"]
            required_source_type = feature["requires_source_type"]
            source_domain = _feature_source_domain(required_source_type)
            evidence_domains = matched_source_domains.get(player_id, set())
            backfill = backfill_values.get((player_id, feature_name), {})
            status = _feature_readiness_status(
                source_domain,
                evidence_domains,
                backfill,
            )
            rows.append(
                {
                    "player_id": player_id,
                    "player_name": player_name,
                    "position": position,
                    "team_id": roster_row.get("team_id", ""),
                    "team_name": roster_row.get("team_name", ""),
                    "league_rank": roster_row.get("league_rank", ""),
                    "feature_name": feature_name,
                    "required_source_type": required_source_type,
                    "source_domain": source_domain,
                    "status": status,
                    "source_evidence": "|".join(sorted(evidence_domains)),
                    "normalized_score": backfill.get("normalized_score", ""),
                    "confidence": backfill.get("confidence", ""),
                    "next_action": _feature_readiness_next_action(
                        status,
                        source_domain,
                    ),
                    "decision_effect": "review only; no score impact",
                }
            )
    return rows


def public_source_feature_readiness_summary_rows(
    readiness_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = (
        "ready",
        "review",
        "source_available",
        "manual_required",
        "missing_source",
    )
    return [
        {
            "status": status,
            "rows": sum(1 for row in readiness_rows if row.get("status") == status),
            "decision_effect": "review only; no score impact",
            "next_action": _feature_readiness_status_next_action(status),
        }
        for status in statuses
    ]


def public_source_readiness_rows(
    report: PublicSourceValidationReport,
    match_rows: list[dict[str, object]],
    unscored_rows: list[dict[str, object]],
    model_input_candidate_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_INPUT_ROOT,
    model_preview_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PREVIEW_ROOT,
    model_promotion_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_PROMOTION_ROOT,
    model_applied_pack_root: str | Path = DEFAULT_PUBLIC_SOURCE_MODEL_APPLIED_PACK_ROOT,
    data_pack_path: str | Path | None = None,
) -> list[dict[str, object]]:
    source_row_count = sum(
        count
        for file_name, count in report.row_counts.items()
        if file_name in SOURCE_INPUT_FILES
    )
    matched_players = sum(
        1 for row in match_rows if int(row.get("matched_sources") or 0) > 0
    )
    placeholder_count = sum(
        1
        for row in unscored_rows
        if row.get("model_output_status") == "placeholder"
    )
    missing_feature_players = sum(
        1 for row in unscored_rows if int(row.get("missing_feature_rows") or 0) > 0
    )
    candidate_snapshots = public_source_model_input_candidate_snapshot_rows(
        model_input_candidate_root
    )
    preview_snapshots = public_source_model_preview_snapshot_rows(model_preview_root)
    preview_review_rows = public_source_model_preview_review_rows(model_preview_root)
    preview_comparison_rows = (
        public_source_model_preview_comparison_rows(data_pack_path, model_preview_root)
        if data_pack_path is not None
        else []
    )
    promotion_snapshots = public_source_model_promotion_candidate_snapshot_rows(
        model_promotion_root
    )
    applied_pack_rows = public_source_model_applied_pack_review_rows(
        model_applied_pack_root
    )

    latest_candidate = _latest_pipeline_row(candidate_snapshots)
    latest_preview = _latest_pipeline_row(preview_snapshots)
    latest_promotion = _latest_pipeline_row(promotion_snapshots)

    return [
        {
            "step": "1. Collect raw source exports",
            "status": "ready" if source_row_count else "not_started",
            "detail": f"{source_row_count} staged raw source rows.",
            "next_action": (
                "Review source matches."
                if source_row_count
                else "Fill public source templates from approved local exports."
            ),
        },
        {
            "step": "2. Match sources to rostered players",
            "status": "ready" if matched_players else "not_started",
            "detail": f"{matched_players} players have at least one source match.",
            "next_action": (
                "Backfill unmatched players or accept lower confidence later."
                if matched_players
                else "Use player_id where possible; player_name fallback is available."
            ),
        },
        {
            "step": "3. Normalize veteran features",
            "status": "ready" if missing_feature_players == 0 and unscored_rows else "needed",
            "detail": f"{missing_feature_players} players still have missing feature rows.",
            "next_action": (
                "Run the veteran model once normalized features are complete."
                if missing_feature_players == 0 and unscored_rows
                else "Translate raw sources into normalized 0-100 veteran features."
            ),
        },
        {
            "step": "4. Generate real model outputs",
            "status": "ready" if placeholder_count == 0 and unscored_rows else "blocked",
            "detail": f"{placeholder_count} players still have placeholder model outputs.",
            "next_action": (
                "Review confidence and warnings."
                if placeholder_count == 0 and unscored_rows
                else "Do not use keeper/drop/trade recommendations yet."
            ),
        },
        {
            "step": "5. Export accepted model-input candidates",
            "status": _artifact_step_status(
                candidate_snapshots,
                row_count_key="row_count",
            ),
            "detail": _artifact_step_detail(
                latest_candidate,
                label="candidate rows",
                row_count_key="row_count",
            ),
            "next_action": (
                "Validate candidate rows and check feature coverage."
                if candidate_snapshots
                else "Create a model-input candidate after normalized backfill rows are accepted."
            ),
        },
        {
            "step": "6. Run isolated model preview",
            "status": _artifact_step_status(
                preview_snapshots,
                row_count_key="output_row_count",
            ),
            "detail": _artifact_step_detail(
                latest_preview,
                label="preview output rows",
                row_count_key="output_row_count",
            ),
            "next_action": (
                "Review preview warnings before comparing to live scores."
                if preview_snapshots
                else "Run an isolated preview once candidate coverage is complete."
            ),
        },
        {
            "step": "7. Review preview and compare to live",
            "status": _preview_and_comparison_step_status(
                preview_review_rows,
                preview_comparison_rows,
            ),
            "detail": _preview_and_comparison_step_detail(
                preview_review_rows,
                preview_comparison_rows,
            ),
            "next_action": _preview_and_comparison_step_next_action(
                preview_review_rows,
                preview_comparison_rows,
            ),
        },
        {
            "step": "8. Export promotion candidates",
            "status": _artifact_step_status(
                promotion_snapshots,
                row_count_key="row_count",
            ),
            "detail": _artifact_step_detail(
                latest_promotion,
                label="promotion rows",
                row_count_key="row_count",
            ),
            "next_action": (
                "Review promotion candidates against the active pack."
                if promotion_snapshots
                else "Export promotion candidates from ready preview-vs-live rows."
            ),
        },
        {
            "step": "9. Apply to generated pack copy",
            "status": _review_gate_step_status(
                applied_pack_rows,
                "applied_pack_review_status",
            ),
            "detail": _review_gate_step_detail(
                applied_pack_rows,
                "applied_pack_review_status",
            ),
            "next_action": _review_gate_step_next_action(
                applied_pack_rows,
                "applied_pack_review_status",
                ready_action="Select the generated pack and run Import Review admission.",
                review_action="Review generated-pack warnings before money decisions.",
                empty_action="Apply ready promotion candidates into a generated data-pack copy.",
            ),
        },
    ]


def _latest_pipeline_row(rows: list[dict[str, object]]) -> dict[str, object]:
    return rows[0] if rows else {}


def _artifact_step_status(
    rows: list[dict[str, object]],
    *,
    row_count_key: str,
) -> str:
    if not rows:
        return "needed"
    if any(_int_or_zero(row.get(row_count_key)) > 0 for row in rows):
        return "ready"
    return "blocked"


def _artifact_step_detail(
    row: dict[str, object],
    *,
    label: str,
    row_count_key: str,
) -> str:
    if not row:
        return f"No {label} exported yet."
    row_count = _int_or_zero(row.get(row_count_key))
    created_at = str(row.get("created_at_utc") or "unknown time")
    return f"Latest export has {row_count} {label} from {created_at}."


def _review_gate_step_status(
    rows: list[dict[str, object]],
    status_key: str,
) -> str:
    if not rows:
        return "needed"
    if any(row.get(status_key) == "blocked" for row in rows):
        return "blocked"
    if any(row.get(status_key) == "review" for row in rows):
        return "review"
    if any(row.get(status_key) == "ready" for row in rows):
        return "ready"
    return "needed"


def _review_gate_step_detail(
    rows: list[dict[str, object]],
    status_key: str,
) -> str:
    if not rows:
        return "No review rows yet."
    ready = sum(1 for row in rows if row.get(status_key) == "ready")
    review = sum(1 for row in rows if row.get(status_key) == "review")
    blocked = sum(1 for row in rows if row.get(status_key) == "blocked")
    return f"{ready} ready, {review} review, {blocked} blocked rows."


def _review_gate_step_next_action(
    rows: list[dict[str, object]],
    status_key: str,
    *,
    ready_action: str,
    review_action: str,
    empty_action: str,
) -> str:
    status = _review_gate_step_status(rows, status_key)
    if status == "ready":
        return ready_action
    if status in {"review", "blocked"}:
        return review_action
    return empty_action


def _preview_and_comparison_step_status(
    preview_rows: list[dict[str, object]],
    comparison_rows: list[dict[str, object]],
) -> str:
    preview_status = _review_gate_step_status(preview_rows, "preview_review_status")
    if preview_status in {"needed", "blocked", "review"}:
        return preview_status
    if not comparison_rows:
        return "needed"
    return _review_gate_step_status(comparison_rows, "comparison_status")


def _preview_and_comparison_step_detail(
    preview_rows: list[dict[str, object]],
    comparison_rows: list[dict[str, object]],
) -> str:
    if not preview_rows:
        return "No preview review rows yet."
    if not comparison_rows:
        return (
            f"Preview review: "
            f"{_review_gate_step_detail(preview_rows, 'preview_review_status')}; "
            "no live comparison rows yet."
        )
    return (
        f"Preview review: "
        f"{_review_gate_step_detail(preview_rows, 'preview_review_status')}; "
        f"live comparison: "
        f"{_review_gate_step_detail(comparison_rows, 'comparison_status')}"
    )


def _preview_and_comparison_step_next_action(
    preview_rows: list[dict[str, object]],
    comparison_rows: list[dict[str, object]],
) -> str:
    preview_status = _review_gate_step_status(preview_rows, "preview_review_status")
    if preview_status == "needed":
        return "Create an isolated preview before review."
    if preview_status in {"review", "blocked"}:
        return "Resolve preview review/blocking rows before comparison or promotion."
    comparison_status = _review_gate_step_status(
        comparison_rows,
        "comparison_status",
    )
    if comparison_status == "ready":
        return "Export ready comparison rows as promotion candidates."
    if comparison_status in {"review", "blocked"}:
        return "Resolve preview-vs-live comparison rows before promotion."
    return "Compare ready preview rows against the selected pack's live model outputs."


def build_public_source_match_rows(
    data_pack_path: str | Path,
    source_root: str | Path = DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT,
) -> list[dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    source_maps = _source_match_maps(source_root)
    rows: list[dict[str, object]] = []
    for roster_row in validated.rows_by_table.get("rosters", []):
        position = str(roster_row.get("position") or "")
        if position not in SUPPORTED_POSITIONS:
            continue
        player_id = str(roster_row.get("player_id") or "")
        player_name = str(roster_row.get("player_name") or "")
        match = PublicSourceMatchRow(
            player_id=player_id,
            player_name=player_name,
            position=position,
            team_name=str(roster_row.get("team_name") or ""),
            projection_match=_has_source_match(source_maps["projection"], player_id, player_name),
            market_match=_has_source_match(source_maps["market"], player_id, player_name),
            role_match=_has_source_match(source_maps["role"], player_id, player_name),
            injury_match=_has_source_match(source_maps["injury"], player_id, player_name),
            bio_match=_has_source_match(source_maps["bio"], player_id, player_name),
            matched_sources=0,
            missing_sources="",
        )
        source_flags = {
            "projection": match.projection_match,
            "market": match.market_match,
            "role": match.role_match,
            "injury": match.injury_match,
            "bio": match.bio_match,
        }
        missing = [name for name, present in source_flags.items() if not present]
        rows.append(
            {
                **match.__dict__,
                "matched_sources": len(source_flags) - len(missing),
                "missing_sources": "|".join(missing),
            }
        )
    return rows


def build_unscored_player_rows(
    data_pack_path: str | Path,
    feature_backfill_path: str | Path | None = None,
) -> list[dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    model_rows_by_player = {
        str(row.get("player_id") or ""): row
        for row in validated.rows_by_table.get("model_outputs", [])
    }
    missing_feature_counts = _missing_feature_counts(feature_backfill_path)
    rows: list[dict[str, object]] = []
    for roster_row in validated.rows_by_table.get("rosters", []):
        position = str(roster_row.get("position") or "")
        if position not in SUPPORTED_POSITIONS:
            continue
        player_id = str(roster_row.get("player_id") or "")
        model_row = model_rows_by_player.get(player_id, {})
        placeholder = (
            model_row.get("risk_level") == "needs_model"
            or "Neutral placeholder" in str(model_row.get("notes") or "")
        )
        missing_count = missing_feature_counts.get(player_id, 0)
        rows.append(
            {
                "player_id": player_id,
                "player_name": str(roster_row.get("player_name") or ""),
                "position": position,
                "team_name": str(roster_row.get("team_name") or ""),
                "league_rank": str(
                    roster_row.get("league_rank")
                    or roster_row.get("official_rank")
                    or ""
                ),
                "model_output_status": "placeholder" if placeholder else "scored",
                "missing_feature_rows": missing_count,
                "next_action": _unscored_next_action(placeholder, missing_count),
            }
        )
    return rows


def _validate_rows(file_name: str, rows: list[dict[str, str]]) -> list[PublicSourceIssue]:
    issues: list[PublicSourceIssue] = []
    for row_number, row in enumerate(rows, start=2):
        entity = (
            _row_player_key(row)
            or row.get("player_name")
            or _row_source_key(row)
            or ""
        )
        position = row.get("position", "")
        if position and position not in SUPPORTED_POSITIONS:
            issues.append(
                PublicSourceIssue(
                    "error",
                    file_name,
                    row_number,
                    entity,
                    "Unsupported position.",
                    "Use QB, RB, WR, or TE. Kickers are roster inventory only.",
                )
            )
        for column in (
            "base_confidence",
            "proj_pass_attempts",
            "proj_completions",
            "proj_pass_yards",
            "proj_pass_tds",
            "proj_pass_ints",
            "proj_rush_attempts",
            "proj_rush_yards",
            "proj_rush_tds",
            "proj_targets",
            "proj_receptions",
            "proj_rec_yards",
            "proj_rec_tds",
            "proj_fumbles_lost",
            "proj_rush_first_downs",
            "proj_rec_first_downs",
            "proj_fantasy_points_source",
            "proj_fantasy_points_lve_rescored",
            "projection_confidence",
            "projected_points",
            "projected_games",
            "projected_rank",
            "projected_tds",
            "projected_rush_rec_first_downs",
            "value_1qb",
            "ecr_1qb",
            "ecr_pos",
            "value_2qb",
            "ecr_2qb",
            "market_rank",
            "market_delta",
            "liquidity_score",
            "market_confidence",
            "market_value",
            "trade_liquidity_hint",
            "depth_pos_rank",
            "offense_snaps",
            "offense_snap_pct",
            "games_sampled",
            "targets",
            "target_share",
            "air_yards_share",
            "wopr",
            "carries",
            "rush_attempt_share",
            "route_participation_pct",
            "role_confidence",
            "role_security_hint",
            "latest_report_week",
            "injury_events_rolling_1y",
            "injury_events_rolling_2y",
            "games_missed_proxy",
            "days_since_last_report",
            "injury_confidence",
            "missed_time_risk",
            "durability_hint",
            "age",
            "years_exp",
            "draft_year",
            "draft_round",
            "draft_pick",
            "draft_ovr",
            "height_in",
            "weight_lb",
            "bio_confidence",
            "rookie_year",
            "normalized_score",
            "lve_projection_value",
            "role_security",
            "age_curve",
            "market_liquidity",
            "position_replaceability",
            "first_down_td_fit",
            "target_earning_stability",
            "route_share_stability",
            "injury_durability",
            "overall_feature_confidence",
            "staleness_days",
            "reliability_score",
            "freshness_window_hours",
        ):
            value = row.get(column, "")
            if value and not _is_float(value):
                issues.append(
                    PublicSourceIssue(
                        "error",
                        file_name,
                        row_number,
                        entity,
                        f"{column} must be numeric.",
                        "Replace with a number or leave blank until sourced.",
                    )
                )
        normalized = row.get("normalized_score", "")
        if normalized and not _in_range(normalized, 0, 100):
            issues.append(
                PublicSourceIssue(
                    "error",
                    file_name,
                    row_number,
                    entity,
                    "normalized_score must be 0-100.",
                    "Normalize feature scores before backfill.",
                )
            )
        for column in (
            "is_active",
            "is_missing",
            "requires_scrape",
            "coverage_qb",
            "coverage_rb",
            "coverage_wr",
            "coverage_te",
            "starter_flag",
            "manual_review_required",
        ):
            value = row.get(column, "")
            if value and value not in {"true", "false"}:
                issues.append(
                    PublicSourceIssue(
                        "error",
                        file_name,
                        row_number,
                        entity,
                        f"{column} must be true or false.",
                        "Use lowercase true or false.",
                    )
                )
    return issues


def _rescore_projection_row_lve(row: dict[str, str]) -> dict[str, object]:
    position = str(row.get("position") or "")
    rush_first_downs = _projection_first_down_value(
        row,
        "proj_rush_first_downs",
        "proj_rush_attempts",
        position,
        "rush",
    )
    rec_first_downs = _projection_first_down_value(
        row,
        "proj_rec_first_downs",
        "proj_targets",
        position,
        "target",
    )
    missing_flags: list[str] = []
    first_down_sources = {rush_first_downs["source"], rec_first_downs["source"]}
    if "estimated" in first_down_sources:
        missing_flags.append("first_downs_estimated")
    if first_down_sources == {"missing"}:
        missing_flags.append("first_downs_missing")
    projected_lve_points = (
        (_float_value(row.get("proj_pass_yards")) * LVE_PROJECTION_SCORING["pass_yard"])
        + (_float_value(row.get("proj_pass_tds")) * LVE_PROJECTION_SCORING["pass_td"])
        + (_float_value(row.get("proj_pass_ints")) * LVE_PROJECTION_SCORING["interception"])
        + (_float_value(row.get("proj_rush_yards")) * LVE_PROJECTION_SCORING["rush_yard"])
        + (_float_value(row.get("proj_rush_tds")) * LVE_PROJECTION_SCORING["rush_td"])
        + (_float_value(row.get("proj_rec_yards")) * LVE_PROJECTION_SCORING["rec_yard"])
        + (_float_value(row.get("proj_rec_tds")) * LVE_PROJECTION_SCORING["rec_td"])
        + (
            (float(rush_first_downs["value"]) + float(rec_first_downs["value"]))
            * LVE_PROJECTION_SCORING["rush_rec_first_down"]
        )
        + (_float_value(row.get("proj_fumbles_lost")) * LVE_PROJECTION_SCORING["fumble_lost"])
    )
    return {
        "projected_lve_points": projected_lve_points,
        "rush_first_downs": rush_first_downs["value"],
        "rec_first_downs": rec_first_downs["value"],
        "first_down_source": _combined_first_down_source(
            str(rush_first_downs["source"]),
            str(rec_first_downs["source"]),
        ),
        "missing_flags": tuple(missing_flags),
    }


def _projection_first_down_value(
    row: dict[str, str],
    direct_column: str,
    volume_column: str,
    position: str,
    rate_key: str,
) -> dict[str, object]:
    direct = row.get(direct_column, "")
    if direct:
        return {"value": _float_value(direct), "source": "direct"}
    volume = row.get(volume_column, "")
    if volume:
        rate = FIRST_DOWN_ESTIMATION_RATES.get(position, {}).get(rate_key, 0.0)
        return {"value": _float_value(volume) * rate, "source": "estimated"}
    return {"value": 0.0, "source": "missing"}


def _combined_first_down_source(rush_source: str, rec_source: str) -> str:
    sources = {rush_source, rec_source}
    if sources == {"direct"}:
        return "direct"
    if "estimated" in sources:
        return "estimated"
    if "direct" in sources:
        return "direct_partial"
    return "missing"


def _float_value(value: object) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _validate_source_policy(rows: list[dict[str, str]]) -> list[PublicSourceIssue]:
    issues: list[PublicSourceIssue] = []
    for row_number, row in enumerate(rows, start=2):
        source_key = _row_source_key(row)
        if not source_key:
            continue
        policy_key = _source_policy_key(source_key)
        policy = SOURCE_POLICY.get(policy_key)
        if policy is None:
            issues.append(
                PublicSourceIssue(
                    "warning",
                    "public_source_catalog.csv",
                    row_number,
                    source_key,
                    "Source is not in the v1 source policy.",
                    "Add a policy entry or keep this source out of scoring inputs.",
                )
            )
            continue
        if policy["status"] in REJECTED_SOURCE_STATUSES:
            issues.append(
                PublicSourceIssue(
                    "error",
                    "public_source_catalog.csv",
                    row_number,
                    source_key,
                    "Source is rejected by the v1 source policy.",
                    str(policy["note"]),
                )
            )
        source_type = (
            row.get("source_type")
            or row.get("source_role")
            or ""
        ).strip()
        source_family = str(policy["source_family"])
        if source_type and source_family not in {source_type, _source_policy_key(source_type)}:
            issues.append(
                PublicSourceIssue(
                    "warning",
                    "public_source_catalog.csv",
                    row_number,
                    source_key,
                    "Catalog source_type differs from source policy family.",
                    f"Expected source family `{source_family}` or document the mismatch.",
                )
            )
    return issues


def _validate_source_references(
    root: Path,
    catalog_keys: set[str],
) -> list[PublicSourceIssue]:
    if not catalog_keys:
        return []
    issues: list[PublicSourceIssue] = []
    for file_name in SOURCE_INPUT_FILES + ("normalized_veteran_feature_backfill.csv",):
        path = root / file_name
        if not path.exists():
            continue
        _, rows = _read_csv(path)
        for row_number, row in enumerate(rows, start=2):
            source_key = _row_source_key(row)
            if not source_key:
                continue
            if source_key not in catalog_keys:
                issues.append(
                    PublicSourceIssue(
                        "warning",
                        file_name,
                        row_number,
                        _row_player_key(row) or row.get("player_name") or source_key,
                        "Source key is not listed in public_source_catalog.csv.",
                        "Add the source to the catalog or remove the row from scoring intake.",
                    )
                )
    return issues


def _source_match_maps(source_root: str | Path) -> dict[str, set[str]]:
    root = Path(source_root)
    return {
        "projection": _match_keys(root / "player_projection_inputs.csv"),
        "market": _match_keys(root / "player_market_inputs.csv"),
        "role": _match_keys(root / "player_role_inputs.csv"),
        "injury": _match_keys(root / "player_injury_inputs.csv"),
        "bio": _match_keys(root / "player_bio_inputs.csv"),
    }


def _match_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    _, rows = _read_csv(path)
    keys: set[str] = set()
    for row in rows:
        player_id = _row_player_key(row)
        player_name = (row.get("player_name") or "").strip()
        if player_id:
            keys.add(f"id:{player_id}")
        if player_name:
            keys.add(f"name:{_name_key(player_name)}")
    return keys


def _has_source_match(keys: set[str], player_id: str, player_name: str) -> bool:
    return f"id:{player_id}" in keys or f"name:{_name_key(player_name)}" in keys


def _missing_feature_counts(feature_backfill_path: str | Path | None) -> dict[str, int]:
    if feature_backfill_path is None:
        return {}
    path = Path(feature_backfill_path)
    if not path.exists():
        return {}
    _, rows = _read_csv(path)
    counts: dict[str, int] = {}
    for row in rows:
        player_id = _row_player_key(row)
        if not player_id:
            continue
        if row.get("is_missing") == "true":
            counts[player_id] = counts.get(player_id, 0) + 1
        missing_flags = row.get("missing_feature_flags", "")
        if missing_flags:
            counts[player_id] = counts.get(player_id, 0) + len(
                [flag for flag in missing_flags.split("|") if flag]
            )
    return counts


def _unscored_next_action(placeholder: bool, missing_feature_count: int) -> str:
    if placeholder and missing_feature_count:
        return "Collect sources, normalize features, then regenerate model outputs."
    if placeholder:
        return "Regenerate scored model outputs from completed veteran features."
    if missing_feature_count:
        return "Review missing feature backfill rows before relying on confidence."
    return "Scored output exists; review confidence and source warnings."


def _source_domain_next_action(domain: str, status: str) -> str:
    if status == "complete":
        return "No matching action needed for this source domain."
    if status == "partial":
        return f"Backfill missing {domain} rows for higher confidence."
    return f"Stage approved {domain} rows in the matching public source template."


def _source_policy_key(source_key: str) -> str:
    normalized = source_key.strip().lower()
    if normalized in SOURCE_POLICY:
        return normalized
    for policy_key in SOURCE_POLICY:
        if normalized.startswith(policy_key + "_"):
            return policy_key
    return normalized


def _build_player_match_index(
    rows_by_table: dict[str, list[dict[str, object]]],
) -> dict[str, object]:
    players_by_id: dict[str, dict[str, str]] = {}
    id_index: dict[str, str] = {}
    name_index: dict[tuple[str, str], set[str]] = {}
    name_any_position_index: dict[str, set[str]] = {}
    for row in rows_by_table.get("players", []):
        player_id = str(row.get("player_id") or "").strip()
        if not player_id:
            continue
        player = {key: str(value or "") for key, value in row.items()}
        players_by_id[player_id] = player
        for identifier in _player_identifier_values(player):
            id_index.setdefault(identifier, player_id)
        name_key = _name_key(
            player.get("merge_name") or player.get("player_name") or ""
        )
        position = player.get("position", "")
        if name_key:
            name_index.setdefault((name_key, position), set()).add(player_id)
            name_any_position_index.setdefault(name_key, set()).add(player_id)

    for row in rows_by_table.get("rosters", []):
        player_id = str(row.get("player_id") or "").strip()
        if not player_id:
            continue
        player = players_by_id.setdefault(
            player_id,
            {
                "player_id": player_id,
                "player_name": str(row.get("player_name") or ""),
                "position": str(row.get("position") or ""),
            },
        )
        for key in ("player_name", "position", "nfl_team"):
            if not player.get(key):
                player[key] = str(row.get(key) or "")
        id_index.setdefault(player_id, player_id)
        name_key = _name_key(str(row.get("player_name") or ""))
        position = str(row.get("position") or "")
        if name_key:
            name_index.setdefault((name_key, position), set()).add(player_id)
            name_any_position_index.setdefault(name_key, set()).add(player_id)
    return {
        "players_by_id": players_by_id,
        "id_index": id_index,
        "name_index": name_index,
        "name_any_position_index": name_any_position_index,
    }


def _match_source_player(
    row: dict[str, str],
    index: dict[str, object],
) -> dict[str, str]:
    id_index = index["id_index"]
    players_by_id = index["players_by_id"]
    name_index = index["name_index"]
    name_any_position_index = index["name_any_position_index"]
    assert isinstance(id_index, dict)
    assert isinstance(players_by_id, dict)
    assert isinstance(name_index, dict)
    assert isinstance(name_any_position_index, dict)

    for source_id in _source_player_identifier_values(row):
        player_id = id_index.get(source_id)
        if player_id:
            return _matched_player_row(
                str(player_id),
                players_by_id,
                "matched",
                "id",
                "",
                "",
            )

    player_name = (row.get("player_name") or "").strip()
    position = (row.get("position") or "").strip()
    name_key = _name_key(player_name)
    if name_key:
        candidates = set(name_index.get((name_key, position), set()))
        if not candidates:
            candidates = set(name_any_position_index.get(name_key, set()))
        if len(candidates) == 1:
            return _matched_player_row(
                next(iter(candidates)),
                players_by_id,
                "matched",
                "name_position" if position else "name",
                "",
                "",
            )
        if len(candidates) > 1:
            candidate_text = "|".join(sorted(candidates))
            return {
                "match_status": "ambiguous",
                "match_method": "name",
                "matched_player_id": "",
                "matched_player_name": "",
                "candidate_player_ids": candidate_text,
                "issue": "Multiple roster/player records match this source name.",
                "suggested_fix": "Add player_key or a platform id before normalization.",
            }
    return {
        "match_status": "unmatched",
        "match_method": "none",
        "matched_player_id": "",
        "matched_player_name": "",
        "candidate_player_ids": "",
        "issue": "No roster/player record matches this source row.",
        "suggested_fix": "Add player_key, source_player_id, or a reviewed player alias.",
    }


def _matched_player_row(
    player_id: str,
    players_by_id: dict[str, dict[str, str]],
    status: str,
    method: str,
    issue: str,
    suggested_fix: str,
) -> dict[str, str]:
    player = players_by_id.get(player_id, {})
    return {
        "match_status": status,
        "match_method": method,
        "matched_player_id": player_id,
        "matched_player_name": player.get("player_name", ""),
        "candidate_player_ids": player_id,
        "issue": issue,
        "suggested_fix": suggested_fix,
    }


def _player_identifier_values(row: dict[str, str]) -> set[str]:
    identifiers = {
        row.get("player_id", ""),
        row.get("sleeper_id", ""),
        row.get("fantasypros_id", ""),
        row.get("ktc_id", ""),
        row.get("fantasycalc_id", ""),
        row.get("pfr_id", ""),
        row.get("cfb_id", ""),
    }
    return {value.strip() for value in identifiers if value and value.strip()}


def _source_player_identifier_values(row: dict[str, str]) -> list[str]:
    values = [
        _row_player_key(row),
        row.get("source_player_id", ""),
        row.get("sleeper_id", ""),
        row.get("fantasypros_id", ""),
        row.get("gsis_id", ""),
        row.get("nfl_id", ""),
        row.get("espn_id", ""),
    ]
    return [value.strip() for value in values if value and value.strip()]


def _match_status_next_action(status: str) -> str:
    if status == "matched":
        return "No matching action needed."
    if status == "ambiguous":
        return "Add player_key or platform ID before normalization."
    return "Review source row and add a safe player identifier or alias."


def _active_feature_registry_rows(
    registry_path: str | Path,
) -> dict[str, list[dict[str, str]]]:
    path = Path(registry_path)
    if not path.exists():
        return {}
    _, rows = _read_csv(path)
    features_by_position: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if row.get("scoring_status") != "active_v1":
            continue
        position = (row.get("position") or "").strip()
        feature_name = (row.get("feature_name") or "").strip()
        if position not in SUPPORTED_POSITIONS or not feature_name:
            continue
        features_by_position.setdefault(position, []).append(
            {
                "feature_name": feature_name,
                "requires_source_type": (
                    row.get("requires_source_type") or "manual_note"
                ).strip(),
            }
        )
    return features_by_position


def _matched_source_domains_by_player(
    match_rows: list[dict[str, object]],
) -> dict[str, set[str]]:
    domains_by_player: dict[str, set[str]] = {}
    for row in match_rows:
        if row.get("match_status") != "matched":
            continue
        player_id = str(row.get("matched_player_id") or "")
        source_domain = _source_domain_from_file_name(str(row.get("file_name") or ""))
        if not player_id or not source_domain:
            continue
        domains_by_player.setdefault(player_id, set()).add(source_domain)
    return domains_by_player


def _source_domain_from_file_name(file_name: str) -> str:
    if file_name == "player_projection_inputs.csv":
        return "projection"
    if file_name == "player_market_inputs.csv":
        return "market"
    if file_name == "player_role_inputs.csv":
        return "role"
    if file_name == "player_injury_inputs.csv":
        return "injury"
    if file_name == "player_bio_inputs.csv":
        return "bio"
    if file_name == "normalized_veteran_feature_backfill.csv":
        return "normalized_backfill"
    return ""


def _feature_source_domain(required_source_type: str) -> str:
    source_type = required_source_type.strip()
    if source_type == "projection":
        return "projection"
    if source_type in {"market_rank", "market_prior"}:
        return "market"
    if source_type in {"depth_chart", "role"}:
        return "role"
    if source_type == "injury":
        return "injury"
    if source_type in {"bio", "ff_playerids"}:
        return "bio"
    if source_type in {"manual_note", "league_pdf", "contract"}:
        return "manual_review"
    return "manual_review"


def _feature_backfill_values(
    path: Path,
) -> dict[tuple[str, str], dict[str, str]]:
    if not path.exists():
        return {}
    _, rows = _read_csv(path)
    values: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        player_id = _row_player_key(row)
        if not player_id:
            continue
        if row.get("feature_name"):
            feature_name = (row.get("feature_name") or "").strip()
            values[(player_id, feature_name)] = {
                "normalized_score": (row.get("normalized_score") or "").strip(),
                "confidence": (row.get("source_confidence") or "").strip(),
                "manual_review_required": "true"
                if row.get("is_missing") == "true"
                else "false",
            }
            continue
        confidence = (
            row.get("overall_feature_confidence")
            or row.get("projection_confidence")
            or row.get("market_confidence")
            or row.get("role_confidence")
            or row.get("injury_confidence")
            or row.get("bio_confidence")
            or ""
        ).strip()
        manual_review_required = (
            (row.get("manual_review_required") or "").strip() == "true"
            or bool((row.get("missing_feature_flags") or "").strip())
        )
        for feature_name in (
            "lve_projection_value",
            "role_security",
            "age_curve",
            "market_liquidity",
            "position_replaceability",
            "first_down_td_fit",
            "target_earning_stability",
            "route_share_stability",
            "injury_durability",
        ):
            score = (row.get(feature_name) or "").strip()
            if not score:
                continue
            values[(player_id, feature_name)] = {
                "normalized_score": score,
                "confidence": confidence,
                "manual_review_required": (
                    "true" if manual_review_required else "false"
                ),
            }
    return values


def _feature_readiness_status(
    source_domain: str,
    evidence_domains: set[str],
    backfill: dict[str, str],
) -> str:
    if backfill.get("normalized_score"):
        if backfill.get("manual_review_required") == "true":
            return "review"
        return "ready"
    if source_domain == "manual_review":
        return "manual_required"
    if source_domain in evidence_domains:
        return "source_available"
    return "missing_source"


def _feature_readiness_next_action(status: str, source_domain: str) -> str:
    if status == "ready":
        return "Normalized feature exists; regenerate model when ready."
    if status == "review":
        return "Review backfill flags before regenerating model outputs."
    if status == "source_available":
        return "Normalize matched source rows into a 0-100 feature score."
    if status == "manual_required":
        return "Add a reviewed manual or local baseline feature score."
    return f"Stage and match approved {source_domain} source rows."


def _feature_readiness_status_next_action(status: str) -> str:
    if status == "ready":
        return "Ready for model regeneration once all required features are ready."
    if status == "review":
        return "Resolve manual-review flags before trusting the feature."
    if status == "source_available":
        return "Convert matched raw source rows into normalized feature scores."
    if status == "manual_required":
        return "Fill local/manual baseline features with provenance notes."
    return "Collect and match approved source rows."


def _normalization_worklist_header() -> tuple[str, ...]:
    return (
        "player_id",
        "player_name",
        "position",
        "team_id",
        "team_name",
        "league_rank",
        "feature_name",
        "required_source_type",
        "source_domain",
        "status",
        "priority",
        "source_evidence",
        "normalized_score",
        "confidence",
        "normalization_task",
        "task_reason",
        "next_action",
        "scoring_effect",
    )


def _model_input_candidate_header() -> tuple[str, ...]:
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


def _normalization_task_for_status(status: str) -> str:
    if status == "review":
        return "review_existing_normalized_value"
    if status == "source_available":
        return "derive_normalized_0_100_score"
    if status == "manual_required":
        return "enter_reviewed_local_baseline"
    return "collect_and_match_source_data"


def _normalization_worklist_priority(row: dict[str, object]) -> str:
    status = str(row.get("status") or "")
    feature_name = str(row.get("feature_name") or "")
    position = str(row.get("position") or "")
    league_rank = _safe_int(row.get("league_rank"))
    if status == "review":
        return "high"
    if league_rank is not None and league_rank <= 75:
        return "high"
    if feature_name in {"lve_projection_value", "role_security"}:
        return "high"
    if position in {"RB", "WR"} and feature_name in {
        "first_down_td_fit",
        "target_earning_stability",
    }:
        return "high"
    if status in {"source_available", "manual_required"}:
        return "medium"
    return "low"


def _normalization_task_reason(row: dict[str, object]) -> str:
    status = str(row.get("status") or "")
    source_domain = str(row.get("source_domain") or "")
    league_rank = _safe_int(row.get("league_rank"))
    if status == "review":
        return "Normalized value exists but has a review flag."
    if status == "source_available":
        return f"Matched {source_domain} evidence exists; derive a reviewed 0-100 score."
    if status == "manual_required":
        return "Feature requires a local/manual baseline with provenance."
    if league_rank is not None and league_rank <= 75:
        return "League-rank top asset has no matched source yet; prioritize before money decisions."
    return f"No matched approved {source_domain} source evidence yet."


def _backfill_acceptance_status(
    readiness_status: str,
    normalized_score: str,
    confidence: str,
) -> str:
    if readiness_status in {"source_available", "manual_required", "missing_source"}:
        return "blocked"
    if readiness_status == "review":
        return "review"
    if readiness_status != "ready":
        return "blocked"
    if not _in_range(normalized_score, 0, 100):
        return "blocked"
    if not confidence or not _in_range(confidence, 0, 100):
        return "review"
    if float(confidence) < 65:
        return "review"
    return "accepted"


def _backfill_acceptance_reason(
    acceptance_status: str,
    readiness_status: str,
    normalized_score: str,
    confidence: str,
) -> str:
    if acceptance_status == "accepted":
        return "Normalized 0-100 feature exists and has no review flag."
    if readiness_status == "review":
        return "Normalized feature exists, but the source row is flagged for review."
    if readiness_status == "source_available":
        return "Matched raw source evidence exists, but no normalized feature score exists."
    if readiness_status == "manual_required":
        return "Feature requires a reviewed local/manual baseline."
    if readiness_status == "missing_source":
        return "Required source evidence is missing."
    if readiness_status not in {"ready", "review", "source_available", "manual_required"}:
        return "Readiness status is unknown; rebuild feature readiness first."
    if not _in_range(normalized_score, 0, 100):
        return "Normalized score is missing or outside 0-100."
    if not confidence or not _in_range(confidence, 0, 100):
        return "Normalized score exists, but confidence/provenance is blank or invalid."
    return "Normalized score exists, but confidence is too low for automatic acceptance."


def _backfill_acceptance_priority(
    row: dict[str, object],
    acceptance_status: str,
) -> str:
    if acceptance_status == "review":
        return "high"
    if acceptance_status == "blocked":
        return _normalization_worklist_priority(row)
    feature_name = str(row.get("feature_name") or "")
    league_rank = _safe_int(row.get("league_rank"))
    if league_rank is not None and league_rank <= 75:
        return "high"
    if feature_name in {
        "lve_projection_value",
        "role_security",
        "first_down_td_fit",
        "target_earning_stability",
    }:
        return "high"
    return "medium"


def _backfill_acceptance_next_action(acceptance_status: str) -> str:
    if acceptance_status == "accepted":
        return "Eligible for a later model-run input step."
    if acceptance_status == "review":
        return "Review provenance/confidence before model-run input."
    return "Complete normalization worklist before model-run input."


def _backfill_acceptance_summary_next_action(status: str) -> str:
    if status == "accepted":
        return "These rows can be carried into the next model-run input review."
    if status == "review":
        return "Resolve review flags before money-decision scoring."
    return "These rows are not ready for model input."


def _data_pack_season_snapshot(data_pack_path: str | Path) -> tuple[str, str]:
    validated = validate_data_pack(data_pack_path)
    roster_rows = validated.rows_by_table.get("rosters", [])
    if roster_rows:
        first = roster_rows[0]
        return (
            str(first.get("season") or ""),
            str(first.get("snapshot_date") or ""),
        )
    return "", ""


def _player_positions_from_data_pack(
    rows_by_table: dict[str, list[dict[str, object]]],
) -> dict[str, str]:
    positions: dict[str, str] = {}
    for table_name in ("players", "rosters"):
        for row in rows_by_table.get(table_name, []):
            player_id = str(row.get("player_id") or "")
            position = str(row.get("position") or "")
            if player_id and position:
                positions.setdefault(player_id, position)
    return positions


def _candidate_key_counts(
    candidate_rows: list[dict[str, object]],
) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for row in candidate_rows:
        key = (
            str(row.get("player_id") or ""),
            str(row.get("feature_name") or ""),
        )
        counts[key] = counts.get(key, 0) + 1
    return counts


def _model_input_candidate_validation_status(
    row: dict[str, object],
    player_positions: dict[str, str],
    active_feature_keys: set[tuple[str, str]],
    key_counts: dict[tuple[str, str], int],
) -> tuple[str, str]:
    player_id = str(row.get("player_id") or "")
    position = str(row.get("position") or "")
    feature_name = str(row.get("feature_name") or "")
    normalized_score = str(row.get("normalized_score") or "")
    source_key = str(row.get("source_key") or "")
    source_confidence = str(row.get("source_confidence") or "")
    is_missing = str(row.get("is_missing") or "")
    is_user_override = str(row.get("is_user_override") or "")
    if not player_id or player_id not in player_positions:
        return "blocked", "Candidate player_id is not in the active data pack."
    if player_positions[player_id] != position:
        return "blocked", "Candidate position does not match active data pack."
    if (position, feature_name) not in active_feature_keys:
        return "blocked", "Candidate feature is not an active V1 feature."
    if key_counts.get((player_id, feature_name), 0) > 1:
        return "blocked", "Duplicate player-feature candidate rows."
    if not _in_range(normalized_score, 0, 100):
        return "blocked", "Candidate normalized_score must be 0-100."
    if is_missing != "false":
        return "blocked", "Accepted candidate rows must not be marked missing."
    if is_user_override != "false":
        return "blocked", "Candidate rows cannot be user overrides."
    if not source_key:
        return "review", "Candidate source_key is blank."
    if source_confidence not in MODEL_INPUT_SOURCE_CONFIDENCE_VALUES:
        return "review", "Candidate source_confidence needs review."
    return "accepted", "Candidate row is structurally safe for later model-input review."


def _model_input_candidate_validation_next_action(status: str) -> str:
    if status == "accepted":
        return "Eligible for a later isolated model-run preview."
    if status == "review":
        return "Fix provenance fields before model-run preview."
    return "Fix blocked candidate row before any model-run preview."


def _model_input_candidate_validation_summary_next_action(status: str) -> str:
    if status == "accepted":
        return "These rows can proceed to a later isolated model-run preview."
    if status == "review":
        return "Review provenance fields before using these rows."
    return "Blocked rows must be fixed before model-run preview."


def _candidate_row_validation_status(
    candidate_row: dict[str, object],
    validation_rows: list[dict[str, object]],
) -> str:
    player_id = str(candidate_row.get("player_id") or "")
    feature_name = str(candidate_row.get("feature_name") or "")
    position = str(candidate_row.get("position") or "")
    for row in validation_rows:
        if (
            str(row.get("player_id") or "") == player_id
            and str(row.get("feature_name") or "") == feature_name
            and str(row.get("position") or "") == position
        ):
            return str(row.get("validation_status") or "")
    return "blocked"


def _candidate_coverage_status(
    accepted_features: int,
    required_features: int,
) -> str:
    if required_features == 0 or accepted_features == 0:
        return "empty"
    if accepted_features >= required_features:
        return "complete"
    return "partial"


def _coverage_pct(covered: int, expected: int) -> float:
    if expected <= 0:
        return 0.0
    return round((covered / expected) * 100, 1)


def _candidate_coverage_next_action(status: str) -> str:
    if status == "complete":
        return "Eligible for a later isolated model preview."
    if status == "partial":
        return "Fill missing active features before model preview."
    return "No accepted active feature rows are available for this player."


def _candidate_coverage_summary_next_action(status: str) -> str:
    if status == "complete":
        return "These players have full accepted active-feature coverage."
    if status == "partial":
        return "Complete missing active features before previewing these players."
    return "Collect and accept feature rows before previewing these players."


def _model_preview_review_status(
    output_row: dict[str, str],
    schema_warning_count: int,
) -> tuple[str, str, str]:
    warning_status = (output_row.get("warning_status") or "").strip()
    risk_level = (output_row.get("risk_level") or "").strip()
    confidence = output_row.get("confidence_score") or ""
    missing_penalty = output_row.get("missing_data_penalty") or ""
    if warning_status == "blocking" or _score_below(confidence, 60):
        return (
            "blocked",
            "Preview output has blocking warnings or very low confidence.",
            "Do not promote this row; fix source coverage or model warnings first.",
        )
    if warning_status in {"review_needed", "missing_output"}:
        return (
            "blocked",
            "Preview output explicitly requires review before use.",
            "Inspect the warning reasons and regenerate after fixing inputs.",
        )
    if (
        warning_status not in {"", "ready"}
        or risk_level == "high"
        or _score_above(missing_penalty, 0)
        or schema_warning_count > 0
        or _score_below(confidence, 75)
    ):
        return (
            "review",
            "Preview scored, but warnings, risk, missing data, or confidence need review.",
            "Inspect this preview row before considering any promotion step.",
        )
    return (
        "ready",
        "Preview row has no active warning and clears confidence checks.",
        "Eligible for manual comparison against current live outputs.",
    )


def _model_preview_review_summary_next_action(status: str) -> str:
    if status == "ready":
        return "These preview rows can be compared against current live outputs."
    if status == "review":
        return "Review warnings and confidence before any promotion workflow."
    return "Blocked preview rows must be fixed and regenerated."


def _model_preview_comparison_status(
    preview_row: dict[str, object],
    live_row: dict[str, object],
) -> tuple[str, str, str]:
    preview_review_status = str(preview_row.get("preview_review_status") or "")
    if preview_review_status == "blocked":
        return (
            "blocked",
            "Preview row is blocked by the preview review gate.",
            "Fix and regenerate the isolated preview before comparing.",
        )
    if not live_row:
        return (
            "review",
            "No current live model output exists for this player.",
            "Inspect identity and pack coverage before considering promotion.",
        )
    keeper_delta = abs(
        _numeric_delta(
            preview_row.get("keeper_score"),
            live_row.get("keeper_score"),
        )
    )
    drop_delta = abs(
        _numeric_delta(
            preview_row.get("drop_candidate_score"),
            live_row.get("drop_candidate_score"),
        )
    )
    confidence_delta = _numeric_delta(
        preview_row.get("confidence_score"),
        live_row.get("confidence_score"),
        confidence=True,
    )
    if preview_review_status == "review":
        return (
            "review",
            "Preview row needs review before the live comparison can be trusted.",
            "Resolve preview warnings, then compare score changes again.",
        )
    if keeper_delta >= 10 or drop_delta >= 10:
        return (
            "review",
            "Preview creates a material keeper/drop score movement.",
            "Manually inspect the feature rows and player explanation before promotion.",
        )
    if confidence_delta <= -15:
        return (
            "review",
            "Preview confidence is materially lower than the live output.",
            "Review provenance and missing data before promotion.",
        )
    return (
        "ready",
        "Preview row is review-cleared and does not materially move live scores.",
        "Safe to inspect side by side with current live output.",
    )


def _model_preview_comparison_summary_next_action(status: str) -> str:
    if status == "ready":
        return "These rows are safe to inspect against live outputs."
    if status == "review":
        return "Review material score changes or missing live baselines."
    return "Blocked rows cannot be compared until the preview gate is fixed."


def _model_promotion_candidate_rows(
    preview_root: str | Path,
    ready_keys: set[tuple[str, str]],
) -> list[dict[str, object]]:
    root = Path(preview_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for preview_path in sorted(root.iterdir(), reverse=True):
        if not preview_path.is_dir():
            continue
        manifest = _read_json_manifest(preview_path / MODEL_PREVIEW_MANIFEST_FILE)
        preview_id = str(manifest.get("preview_id") or preview_path.name)
        output_path = preview_path / str(
            manifest.get("output_file") or MODEL_PREVIEW_OUTPUT_FILE
        )
        if not output_path.exists():
            continue
        _, output_rows = _read_csv(output_path)
        for output_row in output_rows:
            player_id = str(output_row.get("player_id") or "")
            if (preview_id, player_id) not in ready_keys:
                continue
            candidate_row = dict(output_row)
            candidate_row["promotion_source_preview_id"] = preview_id
            candidate_row["promotion_status"] = "candidate"
            candidate_row["promotion_note"] = (
                "Exported from ready preview-vs-live comparison; not live."
            )
            rows.append(candidate_row)
    return rows


def _model_promotion_candidate_review_status(
    candidate_row: dict[str, str],
    live_row: dict[str, object],
) -> tuple[str, str, str]:
    player_id = candidate_row.get("player_id") or ""
    if not player_id:
        return (
            "blocked",
            "Promotion candidate row is missing player_id.",
            "Regenerate the promotion candidate from a valid preview comparison.",
        )
    if candidate_row.get("promotion_status") != "candidate":
        return (
            "blocked",
            "Promotion row is not marked as a candidate.",
            "Regenerate the promotion candidate export.",
        )
    if not candidate_row.get("promotion_source_preview_id"):
        return (
            "blocked",
            "Promotion row is missing source preview provenance.",
            "Regenerate the promotion candidate export.",
        )
    if not live_row:
        return (
            "review",
            "No current live output exists for this promotion candidate.",
            "Inspect selected pack and player identity before any apply step.",
        )
    keeper_delta = abs(
        _numeric_delta(
            candidate_row.get("keeper_score"),
            live_row.get("keeper_score"),
        )
    )
    drop_delta = abs(
        _numeric_delta(
            candidate_row.get("drop_candidate_score"),
            live_row.get("drop_candidate_score"),
        )
    )
    confidence_delta = _numeric_delta(
        candidate_row.get("confidence_score"),
        live_row.get("confidence_score"),
        confidence=True,
    )
    if keeper_delta >= 10 or drop_delta >= 10:
        return (
            "review",
            "Promotion candidate now has material movement versus the selected pack.",
            "Re-run preview comparison or inspect live pack changes before applying.",
        )
    if confidence_delta <= -15:
        return (
            "review",
            "Promotion candidate confidence is materially below the selected pack.",
            "Inspect provenance and missing-data reasons before applying.",
        )
    return (
        "ready",
        "Promotion candidate still matches the selected pack safety checks.",
        "Eligible for a later explicit apply workflow.",
    )


def _model_promotion_candidate_review_summary_next_action(status: str) -> str:
    if status == "ready":
        return "These candidates can proceed to a later explicit apply workflow."
    if status == "review":
        return "Review stale or material changes before any apply workflow."
    return "Blocked candidates must be regenerated."


def _model_applied_pack_review_status(
    manifest: dict[str, object],
    error_count: int,
    warning_count: int,
    output_count: int,
    validation_exception: str,
) -> tuple[str, str, str]:
    applied_count = _int_or_zero(manifest.get("applied_row_count", 0))
    if validation_exception:
        return (
            "blocked",
            f"Applied pack could not be validated: {validation_exception}",
            "Regenerate the applied data pack copy.",
        )
    if error_count > 0:
        return (
            "blocked",
            "Applied pack has validation errors.",
            "Open Import Review for this generated pack before using it.",
        )
    if output_count <= 0:
        return (
            "blocked",
            "Applied pack has no model output rows.",
            "Regenerate the applied data pack copy.",
        )
    if applied_count <= 0:
        return (
            "blocked",
            "Applied pack manifest reports zero applied model rows.",
            "Regenerate from a ready promotion candidate.",
        )
    if warning_count > 0:
        return (
            "review",
            "Applied pack validates, but still has data-pack warnings.",
            "Review pack health before selecting it for decisions.",
        )
    return (
        "ready",
        "Applied pack validates and contains promoted model rows.",
        "Eligible to select in the app data-pack selector for final review.",
    )


def _model_applied_pack_review_summary_next_action(status: str) -> str:
    if status == "ready":
        return "These generated packs can be selected for final app review."
    if status == "review":
        return "Review pack health warnings before using these packs."
    return "Blocked packs must be regenerated or fixed."


def _ready_promotion_candidate_rows(
    promotion_root: str | Path,
    ready_keys: set[tuple[str, str]],
) -> list[dict[str, object]]:
    root = Path(promotion_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for promotion_path in sorted(root.iterdir(), reverse=True):
        if not promotion_path.is_dir():
            continue
        manifest = _read_json_manifest(
            promotion_path / MODEL_PROMOTION_MANIFEST_FILE
        )
        promotion_id = str(manifest.get("promotion_id") or promotion_path.name)
        csv_path = promotion_path / str(
            manifest.get("csv_file") or MODEL_PROMOTION_FILE
        )
        if not csv_path.exists():
            continue
        _, candidate_rows = _read_csv(csv_path)
        for candidate_row in candidate_rows:
            player_id = str(candidate_row.get("player_id") or "")
            if (promotion_id, player_id) in ready_keys:
                rows.append(candidate_row)
    return rows


def _apply_model_output_rows(
    model_outputs_path: Path,
    promotion_rows: list[dict[str, object]],
) -> int:
    header, live_rows = _read_csv(model_outputs_path)
    promotion_by_player = {
        str(row.get("player_id") or ""): row for row in promotion_rows
    }
    applied_count = 0
    output_rows: list[dict[str, object]] = []
    for live_row in live_rows:
        player_id = str(live_row.get("player_id") or "")
        promotion_row = promotion_by_player.get(player_id)
        if promotion_row:
            applied_count += 1
            updated_row = dict(live_row)
            for column in header:
                value = promotion_row.get(column)
                if value not in (None, ""):
                    updated_row[column] = value
            output_rows.append(updated_row)
        else:
            output_rows.append(live_row)
    _write_csv(model_outputs_path, header, output_rows)
    return applied_count


def _write_model_preview_inputs(
    data_pack_path: str | Path,
    registry_path: str | Path,
    model_input_path: Path,
    feature_rows: list[dict[str, object]],
    complete_player_ids: set[str],
    source_root: str | Path,
    created_at: datetime,
) -> None:
    validated = validate_data_pack(data_pack_path)
    season, snapshot_date = _data_pack_season_snapshot(data_pack_path)
    _write_csv(
        model_input_path / "veteran_player_inputs.csv",
        _veteran_player_input_header(),
        _model_preview_player_rows(
            validated.rows_by_table,
            complete_player_ids,
            season,
            snapshot_date,
        ),
    )
    shutil.copy2(registry_path, model_input_path / "veteran_feature_registry.csv")
    _write_csv(
        model_input_path / "veteran_feature_scores.csv",
        _model_input_candidate_header(),
        feature_rows,
    )
    _write_csv(
        model_input_path / "veteran_source_catalog.csv",
        _veteran_source_catalog_header(),
        [
            _model_preview_source_row(
                season,
                snapshot_date,
                Path(source_root),
                created_at,
            )
        ],
    )
    _write_csv(
        model_input_path / "veteran_audit_notes.csv",
        _veteran_audit_note_header(),
        [
            {
                "note_id": "public_source_model_preview",
                "season": season,
                "player_id": str(feature_rows[0].get("player_id") or ""),
                "feature_name": str(feature_rows[0].get("feature_name") or ""),
                "note_scope": "source",
                "note_text": (
                    "Isolated public-source preview generated from accepted "
                    "candidate rows. This note does not alter live model scores."
                ),
                "source_key": PUBLIC_SOURCE_BACKFILL_SOURCE_KEY,
                "affects_score": "false",
                "created_at": created_at.isoformat(),
            }
        ],
    )


def _model_preview_player_rows(
    rows_by_table: dict[str, list[dict[str, object]]],
    complete_player_ids: set[str],
    season: str,
    snapshot_date: str,
) -> list[dict[str, object]]:
    players_by_id = {
        str(row.get("player_id") or ""): row
        for row in rows_by_table.get("players", [])
    }
    roster_rows = [
        row
        for row in rows_by_table.get("rosters", [])
        if str(row.get("player_id") or "") in complete_player_ids
        and str(row.get("position") or "") in SUPPORTED_POSITIONS
    ]
    top_five_ids = _team_top_five_player_ids(roster_rows)
    output_rows: list[dict[str, object]] = []
    for row in roster_rows:
        player_id = str(row.get("player_id") or "")
        player_row = players_by_id.get(player_id, {})
        player_name = str(
            row.get("player_name") or player_row.get("player_name") or player_id
        )
        output_rows.append(
            {
                "season": str(row.get("season") or season),
                "snapshot_date": str(row.get("snapshot_date") or snapshot_date),
                "player_id": player_id,
                "player_name": player_name,
                "position": str(row.get("position") or player_row.get("position") or ""),
                "nfl_team": str(row.get("nfl_team") or player_row.get("nfl_team") or ""),
                "age": _model_preview_age(
                    str(player_row.get("birth_date") or ""),
                    str(row.get("snapshot_date") or snapshot_date),
                ),
                "team_id": str(row.get("team_id") or ""),
                "team_name": str(row.get("team_name") or ""),
                "league_rank": str(
                    row.get("league_rank") or row.get("official_rank") or ""
                ),
                "is_league_rank_top5": (
                    "true" if player_id in top_five_ids else "false"
                ),
                "source_snapshot_id": "public_source_model_preview",
                "source_name": "public_source_backfill_candidate",
                "source_date": str(row.get("snapshot_date") or snapshot_date),
                "data_quality_tier": "partial",
            }
        )
    return output_rows


def _team_top_five_player_ids(roster_rows: list[dict[str, object]]) -> set[str]:
    by_team: dict[str, list[tuple[int, str]]] = {}
    for row in roster_rows:
        rank_text = str(row.get("league_rank") or row.get("official_rank") or "")
        if not rank_text.isdigit():
            continue
        by_team.setdefault(str(row.get("team_id") or ""), []).append(
            (int(rank_text), str(row.get("player_id") or ""))
        )
    top_five: set[str] = set()
    for team_rows in by_team.values():
        top_five.update(player_id for _, player_id in sorted(team_rows)[:5])
    return top_five


def _model_preview_age(birth_date: str, snapshot_date: str) -> str:
    try:
        born = date.fromisoformat(birth_date[:10])
        snapshot = date.fromisoformat(snapshot_date[:10])
    except ValueError:
        return "25.0"
    age = snapshot.year - born.year
    if (snapshot.month, snapshot.day) < (born.month, born.day):
        age -= 1
    birthday_year = (
        snapshot.year
        if (snapshot.month, snapshot.day) >= (born.month, born.day)
        else snapshot.year - 1
    )
    days_after_birthday = (snapshot - date(birthday_year, born.month, born.day)).days
    return f"{age + (days_after_birthday / 365.25):.1f}"


def _model_preview_source_row(
    season: str,
    snapshot_date: str,
    source_root: Path,
    created_at: datetime,
) -> dict[str, object]:
    return {
        "source_key": PUBLIC_SOURCE_BACKFILL_SOURCE_KEY,
        "source_name": "Public source backfill candidate",
        "source_type": "manual_note",
        "source_family": "manual_note",
        "source_domain": "note",
        "authority_tier": "tier_e_manual_unverified",
        "priority_rank": "1",
        "required_for_modes": "keeper_review|draft_room",
        "freshness_window_hours": "",
        "source_format": "csv",
        "local_path": str(source_root / "normalized_veteran_feature_backfill.csv"),
        "source_url": "",
        "source_path_or_url": str(source_root / "normalized_veteran_feature_backfill.csv"),
        "source_date": snapshot_date,
        "retrieved_at": created_at.isoformat(),
        "captured_at_local": created_at.isoformat(),
        "effective_date": snapshot_date,
        "season": season,
        "scoring_context": "custom_lve",
        "checksum_sha256": "",
        "parser_version": "public_source_preview_v1",
        "source_notes": "Generated by isolated public-source model preview.",
        "is_active": "true",
        "reliability_score": "70",
        "notes": "Preview-only source row; no live scoring mutation.",
    }


def _veteran_player_input_header() -> tuple[str, ...]:
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


def _veteran_source_catalog_header() -> tuple[str, ...]:
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


def _veteran_audit_note_header() -> tuple[str, ...]:
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


def _count_by_key(
    rows: list[dict[str, object]],
    key: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _read_json_manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _row_source_key(row: dict[str, str]) -> str:
    for column in (
        "source_key",
        "source_id",
        "projection_source_id",
        "market_source_id",
        "role_source_id",
        "injury_source_id",
        "bio_source_id",
        "source_snapshot_id",
    ):
        value = (row.get(column) or "").strip()
        if value:
            return value
    return ""


def _row_player_key(row: dict[str, str]) -> str:
    return (row.get("player_id") or row.get("player_key") or "").strip()


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _name_key(name: str) -> str:
    return "".join(character.lower() for character in name if character.isalnum())


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _safe_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _in_range(value: str, minimum: float, maximum: float) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return minimum <= number <= maximum


def _score_below(value: str, threshold: float) -> bool:
    try:
        return float(value) < threshold
    except ValueError:
        return True


def _score_above(value: str, threshold: float) -> bool:
    try:
        return float(value) > threshold
    except ValueError:
        return False


def _score_delta(
    new_value: str,
    old_value: str,
    *,
    confidence: bool = False,
) -> str:
    delta = _numeric_delta(new_value, old_value, confidence=confidence)
    if delta == 0 and (not _is_float(str(new_value)) or not _is_float(str(old_value))):
        return ""
    return f"{delta:.1f}"


def _numeric_delta(
    new_value: object,
    old_value: object,
    *,
    confidence: bool = False,
) -> float:
    try:
        new_number = float(str(new_value))
        old_number = float(str(old_value))
    except ValueError:
        return 0.0
    if confidence:
        if 0 <= new_number <= 1:
            new_number *= 100
        if 0 <= old_number <= 1:
            old_number *= 100
    return round(new_number - old_number, 1)


def _int_or_zero(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _snapshot_id(snapshot_id: str | None, created_at: datetime) -> str:
    raw = snapshot_id or created_at.strftime("public_sources_%Y%m%d_%H%M%S")
    safe = "".join(
        character.lower() if character.isalnum() else "_"
        for character in raw.strip()
    ).strip("_")
    return safe or created_at.strftime("public_sources_%Y%m%d_%H%M%S")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
