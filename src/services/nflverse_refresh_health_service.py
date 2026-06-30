from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

NOT_ENOUGH_INFORMATION = "Not enough information"
NOT_CONFIGURED = "NOT_CONFIGURED"
GREEN = "GREEN"
YELLOW = "YELLOW"
RED = "RED"
BLOCKED = "BLOCKED"

EXECUTION_SUCCEEDED = "succeeded"
EXECUTION_FAILED = "failed"
EXECUTION_BLOCKED_POLICY = "blocked_policy"
EXECUTION_BLOCKED_CONFIG = "blocked_config"
EXECUTION_SKIPPED = "skipped"

AXIS_PASS = "pass"
AXIS_REVIEW = "review"
AXIS_FAIL = "fail"
AXIS_UNKNOWN = "unknown"
AXIS_NOT_APPLICABLE = "not_applicable"

DEFAULT_SHARED_ROOT = Path(r"C:\NWR_SHARED_DATA")
DEFAULT_STATUS_ROOT = Path(__file__).resolve().parents[2] / "local_exports" / "refresh_data"
NFLVERSE_SNAPSHOT_ROOT_PARTS = ("scheduled_ingest", "nflverse")
METADATA_FILE_NAME = "snapshot_metadata.json"

SAFE_REFRESH = "safe_refresh"
FULL_SAFE_REFRESH = "full_safe_refresh"
BLOCKED_MODE = "blocked"


@dataclass(frozen=True)
class NflverseDatasetSpec:
    dataset_id: str
    source_family: str
    display_name: str
    loader_name_canonical: str
    loader_name_local_candidates: tuple[str, ...]
    runner_dataset_names: tuple[str, ...]
    file_names: tuple[str, ...]
    default_mode: str
    policy_status: str
    grain: str
    required_columns: tuple[str, ...]
    monitored_columns: tuple[str, ...]
    expected_scope_rule: str
    freshness_rule: str
    row_count_rule: str
    coverage_rule: str
    missingness_rule: str
    attribution_or_license_note: str
    review_reason_default: str
    blocked_reason_default: str

    @property
    def loader_names(self) -> tuple[str, ...]:
        return (self.loader_name_canonical, *self.loader_name_local_candidates)

    @property
    def file_name(self) -> str:
        return self.file_names[0]

    @property
    def configured_in_runner(self) -> bool:
        return self.default_mode != BLOCKED_MODE

    @property
    def freshness_policy(self) -> str:
        return self.freshness_rule

    @property
    def source_policy_status(self) -> str:
        return self.policy_status


@dataclass(frozen=True)
class NflverseDatasetHealth:
    source_id: str
    dataset_id: str
    source_family: str
    display_name: str
    loader_name_canonical: str
    loader_names: tuple[str, ...]
    default_mode: str
    configured_in_runner: bool
    runner_exists: bool
    safe_to_pull: bool
    status: str
    headline_status: str
    execution_status: str
    freshness_status: str
    schema_status: str
    coverage_status: str
    row_count_status: str
    missingness_status: str
    source_policy_status: str
    row_count: str
    column_count: str
    season_coverage: str
    key_column_coverage: str
    schema_fingerprint: str
    raw_cache_path: str
    tracked_summary_path: str
    metadata_path: str
    data_path: str
    found_artifacts: tuple[str, ...]
    safe_refresh_health: str
    full_safe_refresh_health: str
    model_use_allowed: str
    training_allowed: str
    rank_logic_allowed: str
    user_explanation: str
    model_use_warning: str
    caveat: str
    last_attempt_at: str
    last_success_at: str
    package_version: str


def _spec(
    dataset_id: str,
    loader: str,
    aliases: tuple[str, ...],
    mode: str,
    policy: str,
    grain: str,
    required: tuple[str, ...],
    monitored: tuple[str, ...] = (),
    *,
    files: tuple[str, ...] | None = None,
    scope: str = "current configured seasons",
    freshness: str = "latest local-only nflverse snapshot",
    row_count: str = "non-empty row count expected when source covers scope",
    coverage: str = "required grain keys and configured season scope",
    missingness: str = "required keys must not be wholly missing",
    note: str = "nflverse/nflreadpy public dataset; refresh-health visibility only",
    review: str = "Review-only until a separate source-policy lane approves use",
    blocked: str = "No model, rank, source-truth, hidden-sort, candidate, or approval mutation",
) -> NflverseDatasetSpec:
    file_names = files or (f"{dataset_id}.csv",)
    return NflverseDatasetSpec(
        dataset_id=dataset_id,
        source_family="nflverse",
        display_name=f"nflverse {dataset_id.replace('_', ' ')}",
        loader_name_canonical=loader,
        loader_name_local_candidates=aliases,
        runner_dataset_names=(dataset_id, *aliases),
        file_names=file_names,
        default_mode=mode,
        policy_status=policy,
        grain=grain,
        required_columns=required,
        monitored_columns=monitored,
        expected_scope_rule=scope,
        freshness_rule=freshness,
        row_count_rule=row_count,
        coverage_rule=coverage,
        missingness_rule=missingness,
        attribution_or_license_note=note,
        review_reason_default=review,
        blocked_reason_default=blocked,
    )


NFLVERSE_DATASET_SPECS: tuple[NflverseDatasetSpec, ...] = (
    _spec(
        "player_stats_weekly",
        'load_player_stats(summary_level="week")',
        ("weekly_stats", "import_weekly_data", "load_player_stats"),
        SAFE_REFRESH,
        "safe_review",
        "player-season-week",
        ("season", "week"),
        ("player_id", "player_name", "player_display_name", "recent_team", "position"),
        files=("player_stats_weekly.csv", "weekly_stats.csv"),
    ),
    _spec(
        "player_stats_seasonal",
        'load_player_stats(summary_level="reg")',
        ("season_stats", "import_seasonal_data", "load_seasonal_data"),
        FULL_SAFE_REFRESH,
        "safe_review",
        "player-season",
        ("season",),
        ("player_id", "player_name", "player_display_name", "recent_team", "position"),
        files=("player_stats_seasonal.csv", "season_stats.csv"),
    ),
    _spec(
        "play_by_play",
        "load_pbp()",
        ("pbp", "import_pbp_data", "load_pbp"),
        FULL_SAFE_REFRESH,
        "derived_only",
        "game-play",
        ("season", "week"),
        ("game_id", "play_id", "old_game_id", "posteam", "defteam"),
        files=("play_by_play.csv", "pbp.csv"),
        note="Raw play-level rows stay local-only; tracked outputs are summary/status only",
    ),
    _spec(
        "team_stats",
        "load_team_stats()",
        ("team_stats", "import_team_stats"),
        FULL_SAFE_REFRESH,
        "leakage_gated",
        "team-season or team-week/team-game",
        ("season",),
        ("team", "recent_team", "club_code", "week", "game_id"),
    ),
    _spec(
        "schedules",
        "load_schedules()",
        ("schedules", "games", "import_schedules"),
        SAFE_REFRESH,
        "display_only",
        "game",
        ("season", "week"),
        ("game_id", "home_team", "away_team", "game_type"),
    ),
    _spec(
        "players",
        "load_players()",
        ("players", "import_players"),
        SAFE_REFRESH,
        "identity_only",
        "player identity/profile",
        (),
        ("gsis_id", "player_id", "display_name", "full_name", "pfr_id", "espn_id"),
        freshness="identity file freshness by latest local snapshot",
    ),
    _spec(
        "rosters",
        "load_rosters()",
        ("rosters", "import_rosters"),
        SAFE_REFRESH,
        "identity_only",
        "player-team-season roster row",
        ("season",),
        ("team", "recent_team", "position", "player_id", "gsis_id", "full_name"),
    ),
    _spec(
        "weekly_rosters",
        "load_rosters_weekly()",
        ("weekly_rosters", "import_weekly_rosters", "load_weekly_rosters"),
        SAFE_REFRESH,
        "identity_only",
        "player-team-week roster row",
        ("season", "week"),
        ("team", "recent_team", "position", "player_id", "gsis_id", "full_name"),
    ),
    _spec(
        "ff_playerids",
        "load_ff_playerids()",
        ("ff_playerids", "import_ff_playerids"),
        SAFE_REFRESH,
        "identity_only",
        "player identity crosswalk",
        (),
        ("gsis_id", "sleeper_id", "espn_id", "pfr_id", "name", "player_name"),
    ),
    _spec(
        "depth_charts",
        "load_depth_charts()",
        ("depth_charts", "import_depth_charts"),
        SAFE_REFRESH,
        "review_only",
        "team-week-player-depth slot",
        ("season", "week"),
        ("team", "club_code", "depth_team", "position", "depth_position", "player_name"),
        blocked="No missing-as-no-role default; no rank/model/source-truth use",
    ),
    _spec(
        "injuries",
        "load_injuries()",
        ("injuries", "import_injuries"),
        SAFE_REFRESH,
        "transparency_only",
        "player-week injury report row",
        ("season", "week"),
        ("team", "player_name", "status", "report_status", "injury"),
        blocked="No missing-as-healthy default; no injury-risk score or model/rank use",
    ),
    _spec(
        "snap_counts",
        "load_snap_counts()",
        ("snap_counts", "import_snap_counts"),
        SAFE_REFRESH,
        "safe_review",
        "player-game",
        ("season", "week"),
        ("player", "player_name", "position", "team", "offense_snaps", "offense_pct"),
        blocked="No missing-as-zero-snaps default without source proof",
    ),
    _spec(
        "participation",
        "load_participation()",
        ("participation", "import_participation"),
        FULL_SAFE_REFRESH,
        "review_only",
        "player-play or participation row",
        (),
        ("season", "week", "game_id", "nflverse_game_id", "play_id", "offense_players"),
    ),
    _spec(
        "ftn_charting",
        "load_ftn_charting()",
        ("ftn_charting", "import_ftn_charting"),
        FULL_SAFE_REFRESH,
        "review_only",
        "play-level manual charting",
        (),
        ("season", "week", "game_id", "nflverse_game_id", "play_id"),
        note="FTN charting source caveats must remain visible",
    ),
    _spec(
        "pfr_advstats",
        "load_pfr_advstats(stat_type=pass/rush/rec)",
        ("pfr_advstats", "pfr_advstats_pass", "pfr_advstats_rush", "pfr_advstats_rec"),
        FULL_SAFE_REFRESH,
        "review_only",
        "player-week or player-season by subtype",
        ("season",),
        ("player", "player_name", "team", "recent_team", "week", "stat_type"),
    ),
    _spec(
        "nextgen_stats",
        "load_nextgen_stats(stat_type=passing/rushing/receiving)",
        ("nextgen_stats", "nextgen_passing", "nextgen_rushing", "nextgen_receiving"),
        FULL_SAFE_REFRESH,
        "review_only",
        "player-week plus season summary by subtype",
        ("season",),
        ("player_display_name", "player_name", "team", "week", "stat_type"),
        blocked=(
            "Threshold-limited missing rows are Not enough information, "
            "not bad/zero performance"
        ),
    ),
    _spec(
        "draft_picks",
        "load_draft_picks()",
        ("draft_picks", "import_draft_picks"),
        FULL_SAFE_REFRESH,
        "safe_review",
        "draft-year/pick/player",
        (),
        ("season", "draft_year", "round", "pick", "team", "player_name", "gsis_id"),
        blocked="Missing draft row is not confirmed UDFA",
    ),
    _spec(
        "combine",
        "load_combine()",
        ("combine", "import_combine"),
        FULL_SAFE_REFRESH,
        "safe_review",
        "prospect/draft-class",
        (),
        ("season", "draft_year", "player_name", "pos", "height", "weight", "forty"),
        blocked="Missing drills stay missing, not zero/bad athlete",
    ),
    _spec(
        "contracts",
        "load_contracts()",
        ("contracts", "import_contracts"),
        FULL_SAFE_REFRESH,
        "display_only",
        "player-contract row",
        (),
        ("player", "player_name", "team", "year_signed", "contract_years"),
        blocked="Display/inventory only; no valuation, trade value, or rank/model use",
    ),
    _spec(
        "trades",
        "load_trades()",
        ("trades", "import_trades"),
        SAFE_REFRESH,
        "display_only",
        "NFL trade transaction",
        (),
        ("season", "date", "team", "trade_id", "player_name", "draft_pick"),
        blocked="Never feed Trading Lab valuation, pick value, model, or rank logic",
    ),
    _spec(
        "teams",
        "load_teams()",
        ("teams", "import_teams"),
        SAFE_REFRESH,
        "display_only",
        "team metadata",
        (),
        ("team_abbr", "team_name", "team_id", "team_nick"),
    ),
    _spec(
        "officials",
        "load_officials()",
        ("officials", "import_officials"),
        FULL_SAFE_REFRESH,
        "display_only",
        "game-official assignment",
        (),
        ("season", "week", "game_id", "official_name"),
    ),
    _spec(
        "espn_qbr",
        "load_espn_qbr()",
        ("espn_qbr", "import_espn_qbr"),
        FULL_SAFE_REFRESH,
        "review_only",
        "QB-season/week depending output",
        ("season",),
        ("player_id", "player_name", "team", "qbr", "week"),
        note="Vendor-derived ESPN metric; source-policy inventory only",
    ),
    _spec(
        "ff_opportunity",
        "load_ff_opportunity(stat_type=weekly/pbp_pass/pbp_rush)",
        ("opportunity", "ff_opportunity", "load_opportunity", "import_opportunity"),
        FULL_SAFE_REFRESH,
        "review_only",
        "player-week or play-level external model row",
        ("season",),
        ("week", "player_id", "player_name", "full_name", "position", "team", "posteam"),
        files=("ff_opportunity.csv", "opportunity.csv"),
        note="External model-derived source visibility only",
    ),
    _spec(
        "ff_rankings",
        "load_ff_rankings()",
        ("ff_rankings", "fantasypros_rankings"),
        BLOCKED_MODE,
        "blocked_policy",
        "vendor/analyst ranking row",
        (),
        (),
        scope="blocked policy inventory only",
        freshness="not applicable; no auto-refresh",
        row_count="not applicable",
        coverage="not applicable",
        missingness="not applicable",
        note="FantasyPros/vendor-like rankings remain blocked unless source policy changes",
        review="Visible as blocked/review-status inventory only",
        blocked="No auto-refresh; no model input; no rank logic; no source truth; no hidden sort",
    ),
)

CANONICAL_DATASET_IDS = tuple(spec.dataset_id for spec in NFLVERSE_DATASET_SPECS)
SAFE_REFRESH_DATASET_IDS = tuple(
    spec.dataset_id for spec in NFLVERSE_DATASET_SPECS if spec.default_mode == SAFE_REFRESH
)
FULL_SAFE_REFRESH_DATASET_IDS = tuple(
    spec.dataset_id
    for spec in NFLVERSE_DATASET_SPECS
    if spec.default_mode in {SAFE_REFRESH, FULL_SAFE_REFRESH}
)


def nflverse_dataset_source_id(dataset_id: str) -> str:
    return f"nflverse_{dataset_id}"


def configured_dataset_ids() -> set[str]:
    return {spec.dataset_id for spec in NFLVERSE_DATASET_SPECS if spec.configured_in_runner}


def safe_refresh_dataset_ids() -> tuple[str, ...]:
    return SAFE_REFRESH_DATASET_IDS


def full_safe_refresh_dataset_ids() -> tuple[str, ...]:
    return FULL_SAFE_REFRESH_DATASET_IDS


def build_nflverse_dataset_health(
    *,
    shared_root: Path = DEFAULT_SHARED_ROOT,
    status_root: Path = DEFAULT_STATUS_ROOT,
    snapshot_dir: Path | None = None,
) -> tuple[NflverseDatasetHealth, ...]:
    metadata_path = _resolve_metadata_path(
        shared_root=shared_root,
        status_root=status_root,
        snapshot_dir=snapshot_dir,
    )
    metadata = _load_metadata(metadata_path) if metadata_path else {}
    resolved_snapshot_dir = metadata_path.parent if metadata_path else snapshot_dir
    datasets = _metadata_datasets_by_name(metadata)
    return tuple(
        _dataset_health(
            spec,
            _lookup_dataset(spec, datasets),
            metadata,
            metadata_path,
            resolved_snapshot_dir,
            status_root,
        )
        for spec in NFLVERSE_DATASET_SPECS
    )


def health_by_source_id(
    *,
    shared_root: Path = DEFAULT_SHARED_ROOT,
    status_root: Path = DEFAULT_STATUS_ROOT,
    snapshot_dir: Path | None = None,
) -> dict[str, NflverseDatasetHealth]:
    return {
        row.source_id: row
        for row in build_nflverse_dataset_health(
            shared_root=shared_root,
            status_root=status_root,
            snapshot_dir=snapshot_dir,
        )
    }


def dataset_health_table(
    *,
    shared_root: Path = DEFAULT_SHARED_ROOT,
    status_root: Path = DEFAULT_STATUS_ROOT,
    snapshot_dir: Path | None = None,
) -> list[dict[str, str]]:
    return [
        _health_row(row)
        for row in build_nflverse_dataset_health(
            shared_root=shared_root,
            status_root=status_root,
            snapshot_dir=snapshot_dir,
        )
    ]


def dataset_registry_rows() -> list[dict[str, str]]:
    return [
        {
            "dataset_id": spec.dataset_id,
            "source_family": spec.source_family,
            "loader_name_canonical": spec.loader_name_canonical,
            "loader_name_local_candidates": "; ".join(spec.loader_name_local_candidates),
            "default_mode": spec.default_mode,
            "policy_status": spec.policy_status,
            "grain": spec.grain,
            "required_columns": "; ".join(spec.required_columns),
            "monitored_columns": "; ".join(spec.monitored_columns),
            "expected_scope_rule": spec.expected_scope_rule,
            "freshness_rule": spec.freshness_rule,
            "row_count_rule": spec.row_count_rule,
            "coverage_rule": spec.coverage_rule,
            "missingness_rule": spec.missingness_rule,
            "attribution_or_license_note": spec.attribution_or_license_note,
            "review_reason_default": spec.review_reason_default,
            "blocked_reason_default": spec.blocked_reason_default,
            "model_use_allowed": "false",
            "training_allowed": "false",
            "rank_logic_allowed": "false",
            "latest_candidate_mutation_allowed": "false",
            "latest_approved_mutation_allowed": "false",
            "last_attempt_status": NOT_ENOUGH_INFORMATION,
            "last_success_status": NOT_ENOUGH_INFORMATION,
            "schema_fingerprint_latest": NOT_ENOUGH_INFORMATION,
            "schema_fingerprint_last_success": NOT_ENOUGH_INFORMATION,
        }
        for spec in NFLVERSE_DATASET_SPECS
    ]


def _health_row(row: NflverseDatasetHealth) -> dict[str, str]:
    return {
        "dataset_id": row.dataset_id,
        "source_family": row.source_family,
        "default_mode": row.default_mode,
        "headline_status": row.headline_status,
        "execution_status": row.execution_status,
        "freshness_status": row.freshness_status,
        "schema_status": row.schema_status,
        "coverage_status": row.coverage_status,
        "row_count_status": row.row_count_status,
        "missingness_status": row.missingness_status,
        "policy_status": row.source_policy_status,
        "last_attempt_at": row.last_attempt_at,
        "last_success_at": row.last_success_at,
        "loader_name_canonical": row.loader_name_canonical,
        "configured": str(row.configured_in_runner).lower(),
        "runner_exists": str(row.runner_exists).lower(),
        "safe_to_pull": str(row.safe_to_pull).lower(),
        "row_count": row.row_count,
        "season_coverage": row.season_coverage,
        "key_column_coverage": row.key_column_coverage,
        "schema_fingerprint": row.schema_fingerprint,
        "raw_cache_path": row.raw_cache_path,
        "tracked_summary_path": row.tracked_summary_path,
        "model_use_allowed": row.model_use_allowed,
        "training_allowed": row.training_allowed,
        "rank_logic_allowed": row.rank_logic_allowed,
        "status": row.status,
        "user_message": row.user_explanation,
    }


def _dataset_health(
    spec: NflverseDatasetSpec,
    dataset: dict[str, Any] | None,
    metadata: dict[str, Any],
    metadata_path: Path | None,
    snapshot_dir: Path | None,
    status_root: Path,
) -> NflverseDatasetHealth:
    source_id = nflverse_dataset_source_id(spec.dataset_id)
    summary_path = status_root / "nflverse" / "latest" / "nflverse_refresh_manifest.json"
    model_warning = (
        "NFLVerse dataset health is refresh visibility only; it is not model input, "
        "rank logic, source truth, hidden sort, trade value, pick value, latest_candidate, "
        "or latest_approved."
    )
    package_version = str(metadata.get("package_version") or NOT_ENOUGH_INFORMATION)
    last_attempt = str(metadata.get("created_at") or "")

    if spec.policy_status == "blocked_policy":
        return _health(
            spec=spec,
            source_id=source_id,
            status=BLOCKED,
            headline_status="blocked_policy",
            execution_status=EXECUTION_BLOCKED_POLICY,
            freshness_status=AXIS_NOT_APPLICABLE,
            schema_status=AXIS_NOT_APPLICABLE,
            coverage_status=AXIS_NOT_APPLICABLE,
            row_count_status=AXIS_NOT_APPLICABLE,
            missingness_status=AXIS_NOT_APPLICABLE,
            row_count=NOT_ENOUGH_INFORMATION,
            column_count=NOT_ENOUGH_INFORMATION,
            season_coverage=NOT_ENOUGH_INFORMATION,
            key_column_coverage=NOT_ENOUGH_INFORMATION,
            schema_fingerprint=NOT_ENOUGH_INFORMATION,
            raw_cache_path="",
            tracked_summary_path=str(summary_path),
            metadata_path=str(metadata_path or ""),
            data_path="",
            found_artifacts=(str(metadata_path),) if metadata_path else (),
            safe_refresh_health=BLOCKED,
            full_safe_refresh_health=BLOCKED,
            explanation=(
                "ff_rankings is blocked/review-status-only. It is not auto-refreshed "
                "and cannot feed rankings, model input, hidden sort, source truth, "
                "or app decisions."
            ),
            model_warning=model_warning,
            last_attempt_at=last_attempt,
            last_success_at="",
            package_version=package_version,
        )

    if not metadata_path or not metadata:
        explanation = (
            f"No local nflverse snapshot metadata found for {spec.dataset_id}. "
            f"Report {NOT_ENOUGH_INFORMATION}; do not default missing usage, injury, role, "
            "depth, draft, or performance context to zero/false/healthy/clean."
        )
        return _health(
            spec=spec,
            source_id=source_id,
            status=YELLOW,
            headline_status="unknown",
            execution_status=EXECUTION_SKIPPED,
            freshness_status=AXIS_UNKNOWN,
            schema_status=AXIS_UNKNOWN,
            coverage_status=AXIS_UNKNOWN,
            row_count_status=AXIS_UNKNOWN,
            missingness_status=AXIS_UNKNOWN,
            row_count=NOT_ENOUGH_INFORMATION,
            column_count=NOT_ENOUGH_INFORMATION,
            season_coverage=NOT_ENOUGH_INFORMATION,
            key_column_coverage=NOT_ENOUGH_INFORMATION,
            schema_fingerprint=NOT_ENOUGH_INFORMATION,
            raw_cache_path="",
            tracked_summary_path=str(summary_path),
            metadata_path="",
            data_path="",
            found_artifacts=(),
            safe_refresh_health=YELLOW,
            full_safe_refresh_health=YELLOW,
            explanation=explanation,
            model_warning=model_warning,
            last_attempt_at="",
            last_success_at="",
            package_version=package_version,
        )

    if not dataset:
        data_path = _first_data_path(spec, snapshot_dir or metadata_path.parent)
        explanation = (
            f"{spec.dataset_id} is in the canonical registry but absent from {metadata_path}. "
            f"Treat as {NOT_ENOUGH_INFORMATION}; do not infer an empty clean dataset."
        )
        return _health(
            spec=spec,
            source_id=source_id,
            status=YELLOW,
            headline_status="unknown",
            execution_status=EXECUTION_SKIPPED,
            freshness_status=_freshness_status(metadata, metadata_path),
            schema_status=AXIS_UNKNOWN,
            coverage_status=AXIS_UNKNOWN,
            row_count_status=AXIS_UNKNOWN,
            missingness_status=AXIS_UNKNOWN,
            row_count=NOT_ENOUGH_INFORMATION,
            column_count=NOT_ENOUGH_INFORMATION,
            season_coverage=NOT_ENOUGH_INFORMATION,
            key_column_coverage=NOT_ENOUGH_INFORMATION,
            schema_fingerprint=NOT_ENOUGH_INFORMATION,
            raw_cache_path=str(data_path),
            tracked_summary_path=str(summary_path),
            metadata_path=str(metadata_path),
            data_path=str(data_path) if data_path.exists() else "",
            found_artifacts=tuple(
                str(path) for path in (metadata_path, data_path) if path.exists()
            ),
            safe_refresh_health=YELLOW,
            full_safe_refresh_health=YELLOW,
            explanation=explanation,
            model_warning=model_warning,
            last_attempt_at=last_attempt,
            last_success_at="",
            package_version=package_version,
        )

    return _present_dataset_health(
        spec=spec,
        dataset=dataset,
        metadata=metadata,
        metadata_path=metadata_path,
        snapshot_dir=snapshot_dir or metadata_path.parent,
        summary_path=summary_path,
        model_warning=model_warning,
        package_version=package_version,
    )


def _present_dataset_health(
    *,
    spec: NflverseDatasetSpec,
    dataset: dict[str, Any],
    metadata: dict[str, Any],
    metadata_path: Path,
    snapshot_dir: Path,
    summary_path: Path,
    model_warning: str,
    package_version: str,
) -> NflverseDatasetHealth:
    source_id = nflverse_dataset_source_id(spec.dataset_id)
    data_path = _first_data_path(spec, snapshot_dir)
    field_names = [str(value) for value in dataset.get("field_names", [])]
    if not field_names and data_path.exists():
        field_names = _csv_header(data_path)
    row_count_value = dataset.get("row_count")
    row_count = _nullable_count(row_count_value)
    column_count = _nullable_count(dataset.get("column_count") if dataset else len(field_names))
    dataset_status = str(dataset.get("status") or "").lower()
    health_summary = (
        dataset.get("health_summary")
        if isinstance(dataset.get("health_summary"), dict)
        else {}
    )

    execution_status = _execution_status(dataset_status)
    freshness_status = _freshness_status(metadata, metadata_path)
    schema_status = _schema_status(spec, field_names, execution_status)
    row_count_status = _row_count_status(row_count_value, execution_status)
    missingness_status = _missingness_status(data_path, spec.required_columns, execution_status)
    coverage_status = _coverage_status(
        spec=spec,
        row_count_value=row_count_value,
        schema_status=schema_status,
        health_summary=health_summary,
        execution_status=execution_status,
    )
    headline_status = _headline_status(
        execution_status=execution_status,
        freshness_status=freshness_status,
        schema_status=schema_status,
        coverage_status=coverage_status,
        row_count_status=row_count_status,
        missingness_status=missingness_status,
        policy_status=spec.policy_status,
    )
    status = _ui_status(headline_status)
    found = tuple(str(path) for path in (metadata_path, data_path) if path.exists())
    caveat = _dataset_caveat(
        spec=spec,
        dataset=dataset,
        metadata_path=metadata_path,
        execution_status=execution_status,
        row_count=row_count,
    )
    last_success = (
        str(metadata.get("created_at") or "")
        if execution_status == EXECUTION_SUCCEEDED
        else ""
    )
    return _health(
        spec=spec,
        source_id=source_id,
        status=status,
        headline_status=headline_status,
        execution_status=execution_status,
        freshness_status=freshness_status,
        schema_status=schema_status,
        coverage_status=coverage_status,
        row_count_status=row_count_status,
        missingness_status=missingness_status,
        row_count=row_count,
        column_count=column_count,
        season_coverage=str(
            health_summary.get("season_coverage")
            or _season_coverage_from_file(data_path)
            or NOT_ENOUGH_INFORMATION
        ),
        key_column_coverage=str(
            health_summary.get("key_column_coverage")
            or _key_column_coverage(field_names, spec.required_columns)
        ),
        schema_fingerprint=str(
            dataset.get("schema_fingerprint") or _schema_fingerprint(field_names)
        ),
        raw_cache_path=str(data_path),
        tracked_summary_path=str(summary_path),
        metadata_path=str(metadata_path),
        data_path=str(data_path) if data_path.exists() else "",
        found_artifacts=found,
        safe_refresh_health=status,
        full_safe_refresh_health=status,
        explanation=caveat,
        model_warning=model_warning,
        last_attempt_at=str(metadata.get("created_at") or ""),
        last_success_at=last_success,
        package_version=package_version,
    )


def _health(
    *,
    spec: NflverseDatasetSpec,
    source_id: str,
    status: str,
    headline_status: str,
    execution_status: str,
    freshness_status: str,
    schema_status: str,
    coverage_status: str,
    row_count_status: str,
    missingness_status: str,
    row_count: str,
    column_count: str,
    season_coverage: str,
    key_column_coverage: str,
    schema_fingerprint: str,
    raw_cache_path: str,
    tracked_summary_path: str,
    metadata_path: str,
    data_path: str,
    found_artifacts: tuple[str, ...],
    safe_refresh_health: str,
    full_safe_refresh_health: str,
    explanation: str,
    model_warning: str,
    last_attempt_at: str,
    last_success_at: str,
    package_version: str,
) -> NflverseDatasetHealth:
    return NflverseDatasetHealth(
        source_id=source_id,
        dataset_id=spec.dataset_id,
        source_family=spec.source_family,
        display_name=spec.display_name,
        loader_name_canonical=spec.loader_name_canonical,
        loader_names=spec.loader_names,
        default_mode=spec.default_mode,
        configured_in_runner=spec.configured_in_runner,
        runner_exists=spec.configured_in_runner,
        safe_to_pull=spec.configured_in_runner,
        status=status,
        headline_status=headline_status,
        execution_status=execution_status,
        freshness_status=freshness_status,
        schema_status=schema_status,
        coverage_status=coverage_status,
        row_count_status=row_count_status,
        missingness_status=missingness_status,
        source_policy_status=spec.policy_status,
        row_count=row_count,
        column_count=column_count,
        season_coverage=season_coverage,
        key_column_coverage=key_column_coverage,
        schema_fingerprint=schema_fingerprint,
        raw_cache_path=raw_cache_path,
        tracked_summary_path=tracked_summary_path,
        metadata_path=metadata_path,
        data_path=data_path,
        found_artifacts=found_artifacts,
        safe_refresh_health=safe_refresh_health,
        full_safe_refresh_health=full_safe_refresh_health,
        model_use_allowed="false",
        training_allowed="false",
        rank_logic_allowed="false",
        user_explanation=explanation,
        model_use_warning=model_warning,
        caveat=explanation,
        last_attempt_at=last_attempt_at,
        last_success_at=last_success_at,
        package_version=package_version,
    )


def _metadata_datasets_by_name(metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = metadata.get("datasets", [])
    if not isinstance(rows, list):
        return {}
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        names = {
            str(row.get("name") or ""),
            str(row.get("dataset_id") or ""),
        }
        file_name = str(row.get("file_name") or "")
        if file_name.endswith(".csv"):
            names.add(file_name[:-4])
        for name in names:
            if name:
                output[name] = row
    return output


def _lookup_dataset(
    spec: NflverseDatasetSpec, datasets: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    for name in spec.runner_dataset_names:
        if name in datasets:
            return datasets[name]
    for file_name in spec.file_names:
        stem = file_name[:-4] if file_name.endswith(".csv") else file_name
        if stem in datasets:
            return datasets[stem]
    return None


def _resolve_metadata_path(
    *,
    shared_root: Path,
    status_root: Path,
    snapshot_dir: Path | None,
) -> Path | None:
    if snapshot_dir:
        candidate = snapshot_dir / METADATA_FILE_NAME
        return candidate if candidate.exists() else None
    manifest_path = status_root / "nflverse" / "latest" / "nflverse_refresh_manifest.json"
    manifest = _load_json(manifest_path) if manifest_path.exists() else {}
    manifest_snapshot = manifest.get("snapshot_dir") if isinstance(manifest, dict) else None
    if manifest_snapshot:
        candidate = Path(str(manifest_snapshot)) / METADATA_FILE_NAME
        if candidate.exists():
            return candidate
    snapshot_root = shared_root.joinpath(*NFLVERSE_SNAPSHOT_ROOT_PARTS)
    if not snapshot_root.exists():
        return None
    candidates = [
        path / METADATA_FILE_NAME
        for path in snapshot_root.iterdir()
        if path.is_dir() and (path / METADATA_FILE_NAME).exists()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _load_metadata(path: Path | None) -> dict[str, Any]:
    payload = _load_json(path) if path else {}
    return payload if isinstance(payload, dict) else {}


def _load_json(path: Path | None) -> Any:
    if not path or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _first_data_path(spec: NflverseDatasetSpec, snapshot_dir: Path) -> Path:
    for file_name in spec.file_names:
        path = snapshot_dir / file_name
        if path.exists():
            return path
    return snapshot_dir / spec.file_name


def _execution_status(dataset_status: str) -> str:
    if dataset_status == "ok":
        return EXECUTION_SUCCEEDED
    if dataset_status in {"error", "failed", "failure"}:
        return EXECUTION_FAILED
    if dataset_status in {"missing_loader", "not_configured"}:
        return EXECUTION_BLOCKED_CONFIG
    return EXECUTION_SKIPPED


def _headline_status(
    *,
    execution_status: str,
    freshness_status: str,
    schema_status: str,
    coverage_status: str,
    row_count_status: str,
    missingness_status: str,
    policy_status: str,
) -> str:
    if execution_status == EXECUTION_FAILED or AXIS_FAIL in {
        schema_status,
        coverage_status,
        row_count_status,
        missingness_status,
    }:
        return "failed"
    if execution_status == EXECUTION_BLOCKED_POLICY or policy_status == "blocked_policy":
        return "blocked_policy"
    if execution_status == EXECUTION_BLOCKED_CONFIG:
        return "blocked_config"
    if freshness_status == "stale":
        return "stale"
    if policy_status == "review_only":
        return "review_only"
    if policy_status in {"derived_only", "transparency_only", "leakage_gated"}:
        return "review"
    if AXIS_REVIEW in {schema_status, coverage_status, row_count_status, missingness_status}:
        return "review"
    if execution_status == EXECUTION_SKIPPED:
        return "skipped"
    return "succeeded"


def _ui_status(headline_status: str) -> str:
    if headline_status == "failed":
        return RED
    if headline_status == "blocked_policy":
        return BLOCKED
    if headline_status == "blocked_config":
        return NOT_CONFIGURED
    if headline_status in {"stale", "review_only", "review", "skipped", "unknown"}:
        return YELLOW
    return GREEN


def _schema_status(
    spec: NflverseDatasetSpec,
    field_names: list[str],
    execution_status: str,
) -> str:
    if execution_status == EXECUTION_FAILED:
        return AXIS_FAIL
    if execution_status in {EXECUTION_BLOCKED_CONFIG, EXECUTION_SKIPPED}:
        return AXIS_UNKNOWN
    if not spec.required_columns:
        return AXIS_PASS if field_names else AXIS_REVIEW
    fields = {field.lower() for field in field_names}
    missing = [column for column in spec.required_columns if column.lower() not in fields]
    if missing:
        return AXIS_FAIL
    return AXIS_PASS


def _coverage_status(
    *,
    spec: NflverseDatasetSpec,
    row_count_value: Any,
    schema_status: str,
    health_summary: dict[str, Any],
    execution_status: str,
) -> str:
    if execution_status == EXECUTION_FAILED or schema_status == AXIS_FAIL:
        return AXIS_FAIL
    if execution_status in {EXECUTION_BLOCKED_CONFIG, EXECUTION_SKIPPED}:
        return AXIS_UNKNOWN
    row_count = _as_int(row_count_value)
    if row_count is None:
        return AXIS_UNKNOWN
    if row_count == 0:
        return AXIS_REVIEW
    duplicate_count = _as_int(health_summary.get("duplicate_key_count"))
    if duplicate_count and duplicate_count > 0:
        return AXIS_REVIEW
    if spec.required_columns and schema_status != AXIS_PASS:
        return AXIS_FAIL
    return AXIS_PASS


def _row_count_status(row_count_value: Any, execution_status: str) -> str:
    if execution_status == EXECUTION_FAILED:
        return AXIS_FAIL
    if execution_status in {EXECUTION_BLOCKED_CONFIG, EXECUTION_SKIPPED}:
        return AXIS_UNKNOWN
    row_count = _as_int(row_count_value)
    if row_count is None:
        return AXIS_UNKNOWN
    if row_count <= 0:
        return AXIS_REVIEW
    return AXIS_PASS


def _freshness_status(metadata: dict[str, Any], metadata_path: Path) -> str:
    seasons = metadata.get("seasons", [])
    if not seasons:
        return AXIS_UNKNOWN
    try:
        max_season = max(int(season) for season in seasons)
    except (TypeError, ValueError):
        return AXIS_UNKNOWN
    current_year = datetime.now(UTC).year
    if max_season >= current_year - 1:
        return "fresh"
    modified = datetime.fromtimestamp(metadata_path.stat().st_mtime, tz=UTC)
    if modified.year >= current_year - 1:
        return AXIS_REVIEW
    return "stale"


def _missingness_status(
    path: Path,
    required_columns: tuple[str, ...],
    execution_status: str,
) -> str:
    if execution_status == EXECUTION_FAILED:
        return AXIS_FAIL
    if execution_status in {EXECUTION_BLOCKED_CONFIG, EXECUTION_SKIPPED}:
        return AXIS_UNKNOWN
    if not path.exists() or not required_columns:
        return AXIS_UNKNOWN if not path.exists() else AXIS_PASS
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            field_names = {field.lower(): field for field in reader.fieldnames or []}
            resolved = [field_names.get(column.lower(), "") for column in required_columns]
            if any(not column for column in resolved):
                return AXIS_FAIL
            sampled = 0
            blanks = {column: 0 for column in resolved}
            for row in reader:
                sampled += 1
                for column in resolved:
                    if str(row.get(column) or "").strip() == "":
                        blanks[column] += 1
                if sampled >= 5000:
                    break
    except OSError:
        return AXIS_UNKNOWN
    if sampled == 0:
        return AXIS_REVIEW
    if any(value == sampled for value in blanks.values()):
        return AXIS_FAIL
    if any(value > 0 for value in blanks.values()):
        return AXIS_REVIEW
    return AXIS_PASS


def _schema_fingerprint(field_names: list[str]) -> str:
    if not field_names:
        return NOT_ENOUGH_INFORMATION
    body = "\n".join(f"{index}:{field}" for index, field in enumerate(field_names)).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _csv_header(path: Path) -> list[str]:
    if not path.exists() or path.is_dir():
        return []
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            return [str(value) for value in next(reader, [])]
    except OSError:
        return []


def _season_coverage_from_file(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            season_column = _first_matching_column(
                list(reader.fieldnames or []),
                ("season", "draft_year", "year"),
            )
            week_column = _first_matching_column(list(reader.fieldnames or []), ("week",))
            if not season_column:
                return NOT_ENOUGH_INFORMATION
            seasons: set[str] = set()
            weeks: set[str] = set()
            for index, row in enumerate(reader):
                if row.get(season_column):
                    seasons.add(str(row[season_column]))
                if week_column and row.get(week_column):
                    weeks.add(str(row[week_column]))
                if index >= 4999:
                    break
    except OSError:
        return NOT_ENOUGH_INFORMATION
    if not seasons:
        return NOT_ENOUGH_INFORMATION
    season_text = _range_text(seasons)
    return f"seasons={season_text}; weeks={len(weeks)}" if weeks else f"seasons={season_text}"


def _key_column_coverage(field_names: list[str], required_columns: tuple[str, ...]) -> str:
    if not required_columns:
        return "no hard required keys; monitored columns reviewed when present"
    fields = {field.lower() for field in field_names}
    present = [column for column in required_columns if column.lower() in fields]
    missing = [column for column in required_columns if column.lower() not in fields]
    return f"present={len(present)}/{len(required_columns)}; missing={'; '.join(missing) or 'none'}"


def _dataset_caveat(
    *,
    spec: NflverseDatasetSpec,
    dataset: dict[str, Any],
    metadata_path: Path,
    execution_status: str,
    row_count: str,
) -> str:
    warning = str(dataset.get("warning") or "")
    error = str(dataset.get("error") or "")
    parts = [
        (
            f"{spec.dataset_id}: execution_status={execution_status}; "
            f"rows={row_count}; metadata={metadata_path}."
        ),
        f"Policy={spec.policy_status}; allowed use={spec.review_reason_default}.",
        f"Blocked use={spec.blocked_reason_default}.",
        (
            f"Missing values remain {NOT_ENOUGH_INFORMATION}, not zero/false/"
            "healthy/clean/no-role/no-injury/no-usage."
        ),
    ]
    if warning:
        parts.append(f"Dataset warning: {warning}")
    if error:
        parts.append(f"Dataset error: {error}")
    return " ".join(parts)


def _nullable_count(value: Any) -> str:
    count = _as_int(value)
    return NOT_ENOUGH_INFORMATION if count is None else str(count)


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _first_matching_column(field_names: list[str], candidates: tuple[str, ...]) -> str:
    by_lower = {str(field).lower(): str(field) for field in field_names}
    for candidate in candidates:
        match = by_lower.get(candidate.lower())
        if match:
            return match
    return ""


def _range_text(values: set[str]) -> str:
    numeric = sorted(value for value in (_as_int(value) for value in values) if value is not None)
    if numeric and len(numeric) == len(values):
        return f"{numeric[0]}-{numeric[-1]}" if len(numeric) > 1 else str(numeric[0])
    return "; ".join(sorted(values))
