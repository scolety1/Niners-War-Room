from __future__ import annotations

import csv
import json
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from src.config.api_settings import ApiSettings, get_api_settings
from src.services.draft_day_app_v1_service import (
    EXPECTED_DYNASTY_ROW_COUNT,
    EXPECTED_PINNED_MANIFEST_HASH,
    EXPECTED_ROW_COUNT,
    LOCAL_DYNASTY_RANKINGS_PATH,
    OUTCOME_NUMERIC_DISPLAY_PATH,
    PDF_FREE_AGENT_DRAFTABLE_POOL_PATH,
    PINNED_SNAPSHOT_MANIFEST,
    REPO_SAFE_FROZEN_BOARD_PATH,
    file_sha256,
    pinned_manifest_hash,
)
from src.services.draft_day_runtime_state_service import (
    DEFAULT_DRAFT_ID,
    runtime_state_path,
)
from src.services.lve_refresh_service import run_sleeper_refresh

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATUS_ROOT = REPO_ROOT / "local_exports" / "refresh_data"
DEFAULT_STATUS_PATH = DEFAULT_STATUS_ROOT / "latest_refresh_status.json"
DEFAULT_SHARED_ROOT = Path(r"C:\NWR_SHARED_DATA")
CFBD_CACHE_ROOT = DEFAULT_SHARED_ROOT / "public_sources" / "cfbd"

QUICK_REFRESH = "QUICK_REFRESH"
FULL_SAFE_REFRESH = "FULL_SAFE_REFRESH"
CHECK_PROTECTED_ARTIFACTS = "CHECK_PROTECTED_ARTIFACTS"
MANUAL_SOURCES_CHECKLIST = "MANUAL_SOURCES_CHECKLIST"
LOADER_MODES = (
    QUICK_REFRESH,
    FULL_SAFE_REFRESH,
    CHECK_PROTECTED_ARTIFACTS,
    MANUAL_SOURCES_CHECKLIST,
)

AUTO_QUICK = "AUTO_QUICK"
AUTO_SLOW = "AUTO_SLOW"
CHECK_ONLY = "CHECK_ONLY"
MANUAL_BLOCKED = "MANUAL_BLOCKED"
NOT_CONFIGURED = "NOT_CONFIGURED"

REFRESHED = "REFRESHED"
ACTION_CHECK_ONLY = "CHECK_ONLY"
SKIPPED_BY_POLICY = "SKIPPED_BY_POLICY"
ACTION_NOT_CONFIGURED = "NOT_CONFIGURED"
BLOCKED_MANUAL = "BLOCKED_MANUAL"
FAILED = "FAILED"

QUICK_PROTECTED_CHECKS = {
    "frozen_baseline_board",
    "pinned_manifest_hash",
    "latest_candidate_latest_approved",
}

RESULT_SCHEMA = (
    "run_id",
    "run_timestamp",
    "loader_mode",
    "source_id",
    "source_name",
    "source_kind",
    "loader_category",
    "action_type",
    "refreshed",
    "configured",
    "freshness",
    "expected_artifacts",
    "found_artifacts",
    "user_explanation",
    "model_use_warning",
    "requires_api_key",
    "required_env_vars",
    "runner_exists",
    "safe_to_pull",
    "protected_artifact",
    "writes_raw_cache",
    "raw_cache_location",
    "writes_tracked_artifact",
    "default_action",
    "failure_mode",
    "status",
    "timestamp",
    "duration_seconds",
    "artifact_updated",
    "source_type",
    "safe_to_run",
    "refresh_method",
    "command_or_function",
    "output_artifacts",
    "expected_runtime",
    "last_result",
    "last_success_timestamp",
    "user_message",
    "caveat",
)


@dataclass(frozen=True)
class RefreshSourceEntry:
    source_id: str
    source_name: str
    source_kind: str
    loader_category: str
    enabled_in_quick_refresh: bool
    enabled_in_full_safe_refresh: bool
    requires_api_key: bool
    required_env_vars: tuple[str, ...]
    runner_exists: bool
    configured: bool
    safe_to_pull: bool
    protected_artifact: bool
    writes_raw_cache: bool
    raw_cache_location: str
    writes_tracked_artifact: bool
    expected_artifacts: tuple[str, ...]
    freshness_policy: str
    model_use_allowed: bool
    model_use_warning: str
    default_action: str
    failure_mode: str
    user_explanation: str
    command_or_function: str = ""
    expected_runtime: str = ""

    @property
    def source_type(self) -> str:
        return self.source_kind

    @property
    def safe_to_run(self) -> bool:
        return self.safe_to_pull

    @property
    def refresh_method(self) -> str:
        if self.default_action == REFRESHED:
            return "source_handler"
        if self.default_action == ACTION_CHECK_ONLY:
            return "status_check"
        if self.default_action == BLOCKED_MANUAL:
            return "manual_only"
        return "policy_skip"

    @property
    def output_artifacts(self) -> tuple[str, ...]:
        return self.expected_artifacts


@dataclass(frozen=True)
class RefreshSourceResult:
    run_id: str
    run_timestamp: str
    loader_mode: str
    source_id: str
    source_name: str
    source_kind: str
    loader_category: str
    action_type: str
    refreshed: bool
    configured: bool
    freshness: str
    expected_artifacts: tuple[str, ...]
    found_artifacts: tuple[str, ...]
    user_explanation: str
    model_use_warning: str
    requires_api_key: bool
    required_env_vars: tuple[str, ...]
    runner_exists: bool
    safe_to_pull: bool
    protected_artifact: bool
    writes_raw_cache: bool
    raw_cache_location: str
    writes_tracked_artifact: bool
    default_action: str
    failure_mode: str
    status: str
    timestamp: str
    duration_seconds: float
    artifact_updated: str
    source_type: str
    safe_to_run: bool
    refresh_method: str
    command_or_function: str
    output_artifacts: tuple[str, ...]
    expected_runtime: str
    last_result: str
    last_success_timestamp: str
    user_message: str
    caveat: str


@dataclass(frozen=True)
class RefreshRunResult:
    run_id: str
    started_at_utc: str
    finished_at_utc: str
    loader_mode: str
    overall_status: str
    status_path: str
    results: tuple[RefreshSourceResult, ...]


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class RefreshContext:
    run_id: str
    run_timestamp: str
    loader_mode: str
    repo_root: Path
    status_root: Path
    shared_root: Path
    settings: ApiSettings
    python_executable: str
    command_runner: Callable[[list[str], Path, int], CommandResult]


SourceHandler = Callable[[RefreshSourceEntry, RefreshContext], RefreshSourceResult]


def build_refresh_registry(
    *,
    repo_root: Path = REPO_ROOT,
    status_root: Path = DEFAULT_STATUS_ROOT,
    settings: ApiSettings | None = None,
    shared_root: Path = DEFAULT_SHARED_ROOT,
    include_slow_sources: bool | None = None,
) -> tuple[RefreshSourceEntry, ...]:
    del include_slow_sources
    settings = settings or get_api_settings()
    scripts = repo_root / "scripts"
    dynasty_script = scripts / "refresh_dynastyprocess_market_baseline_v1.py"
    sleeper_script = scripts / "run_sleeper_refresh_v0.ps1"
    nflverse_script = scripts / "run_nflverse_refresh_v0.ps1"
    cfbd_configured = bool(settings.cfbd_api_key)
    cfbd_category = AUTO_SLOW if cfbd_configured else NOT_CONFIGURED

    return (
        RefreshSourceEntry(
            source_id="sleeper_league_state",
            source_name="Sleeper league data",
            source_kind="public_api_league_state",
            loader_category=AUTO_QUICK,
            enabled_in_quick_refresh=True,
            enabled_in_full_safe_refresh=True,
            requires_api_key=False,
            required_env_vars=("NINERS_SLEEPER_LEAGUE_ID",),
            runner_exists=sleeper_script.exists(),
            configured=bool(settings.sleeper_league_id) and sleeper_script.exists(),
            safe_to_pull=bool(settings.sleeper_league_id) and sleeper_script.exists(),
            protected_artifact=False,
            writes_raw_cache=True,
            raw_cache_location=str(status_root / "sleeper"),
            writes_tracked_artifact=False,
            expected_artifacts=("sleeper_league_settings.csv", "sleeper_rosters.csv"),
            freshness_policy="Current league state when explicitly refreshed.",
            model_use_allowed=False,
            model_use_warning=(
                "Sleeper refresh is league state only; it does not rebuild candidate packs "
                "or change model/rank outputs."
            ),
            default_action=REFRESHED,
            failure_mode="Report FAILED for Sleeper only; continue other sources.",
            user_explanation=(
                "Pulls current Sleeper league state snapshots only. It does not rebuild "
                "candidate/model packs."
            ),
            command_or_function="src.services.lve_refresh_service.run_sleeper_refresh",
            expected_runtime="< 1 minute",
        ),
        RefreshSourceEntry(
            source_id="dynastyprocess_market_baseline",
            source_name="DynastyProcess market baseline",
            source_kind="public_market_display",
            loader_category=AUTO_QUICK,
            enabled_in_quick_refresh=True,
            enabled_in_full_safe_refresh=True,
            requires_api_key=False,
            required_env_vars=(),
            runner_exists=dynasty_script.exists(),
            configured=dynasty_script.exists(),
            safe_to_pull=dynasty_script.exists(),
            protected_artifact=False,
            writes_raw_cache=True,
            raw_cache_location=str(status_root / "dynastyprocess_market_baseline"),
            writes_tracked_artifact=False,
            expected_artifacts=("dp_freshness_report.csv", "dp_market_baseline_context.csv"),
            freshness_policy="Fresh if upstream scrape date is recent enough for display.",
            model_use_allowed=False,
            model_use_warning=(
                "DynastyProcess is display-only market context; never model, rank, "
                "candidate, or source truth input."
            ),
            default_action=REFRESHED,
            failure_mode="Report FAILED for DynastyProcess only; continue other sources.",
            user_explanation=(
                "Refreshes display-only public market baseline into ignored local artifacts."
            ),
            command_or_function=str(dynasty_script),
            expected_runtime="< 2 minutes",
        ),
        RefreshSourceEntry(
            source_id="nflverse_public_data",
            source_name="nflverse public data",
            source_kind="public_structured_nfl",
            loader_category=AUTO_SLOW,
            enabled_in_quick_refresh=False,
            enabled_in_full_safe_refresh=True,
            requires_api_key=False,
            required_env_vars=(),
            runner_exists=nflverse_script.exists(),
            configured=nflverse_script.exists(),
            safe_to_pull=nflverse_script.exists(),
            protected_artifact=False,
            writes_raw_cache=True,
            raw_cache_location=str(shared_root / "scheduled_ingest" / "nflverse"),
            writes_tracked_artifact=False,
            expected_artifacts=("nflverse snapshot folder", "nflverse refresh log"),
            freshness_policy="Slow public NFL refresh only in Full Safe Refresh.",
            model_use_allowed=False,
            model_use_warning=(
                "nflverse refresh does not write candidates or model/rank outputs in this loader."
            ),
            default_action=REFRESHED,
            failure_mode="Report FAILED for nflverse only; do not write candidates.",
            user_explanation=(
                "Uses scripts/run_nflverse_refresh_v0.ps1 in Full Safe Refresh only. "
                "Raw/cache outputs stay outside git."
            ),
            command_or_function=str(nflverse_script),
            expected_runtime="several minutes",
        ),
        RefreshSourceEntry(
            source_id="cfbd_college_football_data",
            source_name="CollegeFootballData",
            source_kind="keyed_college_api",
            loader_category=cfbd_category,
            enabled_in_quick_refresh=False,
            enabled_in_full_safe_refresh=True,
            requires_api_key=True,
            required_env_vars=("CFBD_API_KEY",),
            runner_exists=True,
            configured=cfbd_configured,
            safe_to_pull=cfbd_configured,
            protected_artifact=False,
            writes_raw_cache=True,
            raw_cache_location=str(shared_root / "public_sources" / "cfbd"),
            writes_tracked_artifact=False,
            expected_artifacts=("cfbd_refresh_manifest.json", "raw CFBD probe JSON outside git"),
            freshness_policy="Available only when CFBD_API_KEY is configured.",
            model_use_allowed=False,
            model_use_warning=(
                "CFBD identities must be reviewed before model use; this task does not "
                "make CFBD model input."
            ),
            default_action=REFRESHED if cfbd_configured else ACTION_NOT_CONFIGURED,
            failure_mode="Without CFBD_API_KEY report NOT_CONFIGURED; with key isolate failures.",
            user_explanation=(
                "CFBD is only pulled in Full Safe Refresh when CFBD_API_KEY exists. "
                "Without a key it is reported as NOT_CONFIGURED."
            ),
            command_or_function="internal_cfbd_safe_probe",
            expected_runtime="< 1 minute",
        ),
        *_check_only_entries(repo_root, shared_root),
        *_manual_blocked_entries(repo_root),
    )


def run_quick_refresh(**kwargs: Any) -> RefreshRunResult:
    return run_data_loader(loader_mode=QUICK_REFRESH, **kwargs)


def run_full_safe_refresh(**kwargs: Any) -> RefreshRunResult:
    return run_data_loader(loader_mode=FULL_SAFE_REFRESH, **kwargs)


def run_check_protected_artifacts(**kwargs: Any) -> RefreshRunResult:
    return run_data_loader(loader_mode=CHECK_PROTECTED_ARTIFACTS, **kwargs)


def run_manual_sources_checklist(**kwargs: Any) -> RefreshRunResult:
    return run_data_loader(loader_mode=MANUAL_SOURCES_CHECKLIST, **kwargs)


def run_data_refresh(
    *,
    include_slow_sources: bool = False,
    **kwargs: Any,
) -> RefreshRunResult:
    loader_mode = FULL_SAFE_REFRESH if include_slow_sources else QUICK_REFRESH
    return run_data_loader(loader_mode=loader_mode, **kwargs)


def run_data_loader(
    *,
    loader_mode: str,
    repo_root: Path = REPO_ROOT,
    status_root: Path = DEFAULT_STATUS_ROOT,
    shared_root: Path = DEFAULT_SHARED_ROOT,
    source_ids: Iterable[str] | None = None,
    settings: ApiSettings | None = None,
    command_runner: Callable[[list[str], Path, int], CommandResult] | None = None,
    handlers: dict[str, SourceHandler] | None = None,
    write_status: bool = True,
) -> RefreshRunResult:
    if loader_mode not in LOADER_MODES:
        raise ValueError(f"Unknown loader mode: {loader_mode}")
    started = _utc_now()
    run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    registry = build_refresh_registry(
        repo_root=repo_root,
        status_root=status_root,
        settings=settings,
        shared_root=shared_root,
    )
    selected_ids = set(source_ids) if source_ids is not None else None
    context = RefreshContext(
        run_id=run_id,
        run_timestamp=started,
        loader_mode=loader_mode,
        repo_root=repo_root,
        status_root=status_root,
        shared_root=shared_root,
        settings=settings or get_api_settings(),
        python_executable=sys.executable,
        command_runner=command_runner or _run_command,
    )
    source_handlers = _default_handlers() | (handlers or {})

    results: list[RefreshSourceResult] = []
    for entry in registry:
        selected = _entry_selected(entry, loader_mode, selected_ids)
        if not selected:
            results.append(
                _policy_result(
                    entry,
                    context,
                    action_type=SKIPPED_BY_POLICY,
                    status="SKIPPED",
                    explanation=f"{entry.source_name} is not selected for {loader_mode}.",
                )
            )
            continue
        if entry.loader_category == MANUAL_BLOCKED:
            results.append(
                _policy_result(
                    entry,
                    context,
                    action_type=BLOCKED_MANUAL,
                    status="BLOCKED",
                    explanation=entry.user_explanation,
                )
            )
            continue
        if entry.loader_category == CHECK_ONLY:
            handler = source_handlers.get(entry.source_id, _check_artifact_source)
            results.append(_run_handler(entry, context, handler))
            continue
        if not entry.configured:
            results.append(
                _policy_result(
                    entry,
                    context,
                    action_type=ACTION_NOT_CONFIGURED,
                    status="NOT_CONFIGURED",
                    explanation=entry.user_explanation,
                )
            )
            continue
        if not entry.safe_to_pull:
            results.append(
                _policy_result(
                    entry,
                    context,
                    action_type=SKIPPED_BY_POLICY,
                    status="SKIPPED",
                    explanation=entry.user_explanation,
                )
            )
            continue
        handler = source_handlers.get(entry.source_id, _check_artifact_source)
        results.append(_run_handler(entry, context, handler))

    finished = _utc_now()
    status_path = status_root / "latest_refresh_status.json"
    run = RefreshRunResult(
        run_id=run_id,
        started_at_utc=started,
        finished_at_utc=finished,
        loader_mode=loader_mode,
        overall_status=_overall_status(results),
        status_path=str(status_path),
        results=tuple(results),
    )
    if write_status:
        write_refresh_status(run, status_root=status_root)
    return run


def write_refresh_status(run: RefreshRunResult, *, status_root: Path = DEFAULT_STATUS_ROOT) -> Path:
    status_root.mkdir(parents=True, exist_ok=True)
    latest_path = status_root / "latest_refresh_status.json"
    archive_path = status_root / f"{run.run_id}_{run.loader_mode.lower()}_status.json"
    payload = _run_payload(run, latest_path)
    latest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    archive_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return latest_path


def load_latest_refresh_status(
    *, status_path: Path = DEFAULT_STATUS_PATH
) -> dict[str, Any] | None:
    if not status_path.exists():
        return None
    try:
        return json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def refresh_results_table(run: RefreshRunResult) -> list[dict[str, Any]]:
    return [_result_payload(result) for result in run.results]


def export_results_csv(run: RefreshRunResult) -> str:
    rows = refresh_results_table(run)
    output = []
    output.append(",".join(RESULT_SCHEMA))
    for row in rows:
        output.append(
            ",".join(_csv_cell(row.get(column, "")) for column in RESULT_SCHEMA)
        )
    return "\n".join(output) + "\n"


def validate_refresh_result_schema(rows: Iterable[dict[str, Any]]) -> None:
    expected = set(RESULT_SCHEMA)
    for row in rows:
        missing = expected - set(row)
        if missing:
            raise ValueError(f"Refresh result row missing columns: {sorted(missing)}")


def _default_handlers() -> dict[str, SourceHandler]:
    return {
        "sleeper_league_state": _refresh_sleeper,
        "dynastyprocess_market_baseline": _refresh_dynastyprocess,
        "nflverse_public_data": _refresh_nflverse,
        "cfbd_college_football_data": _refresh_cfbd,
        "frozen_baseline_board": _check_frozen_board,
        "pinned_manifest_hash": _check_pinned_manifest,
        "latest_candidate_latest_approved": _check_artifact_source,
        "full_dynasty_model_v4_output": _check_full_dynasty,
        "outcome_artifacts": _check_artifact_source,
        "lve_pdf_free_agent_extract": _check_artifact_source,
        "runtime_draft_state": _check_runtime_state,
        "model_evaluation_harness": _check_artifact_source,
        "sleeper_adp_display_context": _check_artifact_source,
    }


def _refresh_sleeper(entry: RefreshSourceEntry, context: RefreshContext) -> RefreshSourceResult:
    started = perf_counter()
    result = run_sleeper_refresh(
        league_id=context.settings.sleeper_league_id,
        output_root=context.status_root / "sleeper",
        snapshot_name=context.run_id,
    )
    rows = result.counts.get("rosters", 0)
    return _result(
        entry,
        context,
        started=started,
        action_type=REFRESHED,
        status="GREEN",
        refreshed=True,
        freshness=f"refreshed {context.run_timestamp}; roster rows={rows}",
        found_artifacts=tuple(str(path) for path in result.files.values()),
        explanation=f"Sleeper league state refreshed with {rows} roster rows.",
        artifact=str(result.output_dir),
    )


def _refresh_dynastyprocess(
    entry: RefreshSourceEntry, context: RefreshContext
) -> RefreshSourceResult:
    started = perf_counter()
    artifact_dir = context.status_root / "dynastyprocess_market_baseline" / "latest"
    command = [
        context.python_executable,
        entry.command_or_function,
        "--output-dir",
        str(artifact_dir),
        "--snapshot-label",
        context.run_id,
    ]
    command_result = context.command_runner(command, context.repo_root, 120)
    found = _existing_paths(artifact_dir / name for name in entry.expected_artifacts)
    if command_result.returncode != 0:
        return _result(
            entry,
            context,
            started=started,
            action_type=FAILED,
            status="RED",
            refreshed=False,
            freshness="refresh failed",
            found_artifacts=found,
            explanation=_tail(command_result.stderr) or "DynastyProcess refresh failed.",
            artifact="",
        )
    return _result(
        entry,
        context,
        started=started,
        action_type=REFRESHED,
        status="GREEN",
        refreshed=True,
        freshness=_artifact_freshness(artifact_dir / "dp_freshness_report.csv"),
        found_artifacts=found or (str(artifact_dir),),
        explanation=_tail(command_result.stdout) or "DynastyProcess refresh completed.",
        artifact=str(artifact_dir),
    )


def _refresh_nflverse(entry: RefreshSourceEntry, context: RefreshContext) -> RefreshSourceResult:
    started = perf_counter()
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        entry.command_or_function,
        "-SharedRoot",
        str(context.shared_root),
        "-SnapshotLabel",
        context.run_id,
    ]
    command_result = context.command_runner(command, context.repo_root, 300)
    snapshot_dir = context.shared_root / "scheduled_ingest" / "nflverse" / context.run_id
    log_path = (
        context.shared_root
        / "scheduled_ingest"
        / "logs"
        / f"nflverse_refresh_v0_{context.run_id}.log"
    )
    found = _existing_paths((snapshot_dir, log_path))
    if command_result.returncode != 0:
        return _result(
            entry,
            context,
            started=started,
            action_type=FAILED,
            status="RED",
            refreshed=False,
            freshness="refresh failed",
            found_artifacts=found,
            explanation=_tail(command_result.stderr) or "nflverse refresh failed.",
            artifact="",
        )
    return _result(
        entry,
        context,
        started=started,
        action_type=REFRESHED,
        status="GREEN",
        refreshed=True,
        freshness=f"refreshed {context.run_timestamp}",
        found_artifacts=found or (str(snapshot_dir),),
        explanation="nflverse runner completed without candidate/model writes.",
        artifact=str(snapshot_dir),
    )


def _refresh_cfbd(entry: RefreshSourceEntry, context: RefreshContext) -> RefreshSourceResult:
    started = perf_counter()
    raw_dir = context.shared_root / "public_sources" / "cfbd" / context.run_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = context.status_root / "cfbd" / "latest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "teams_fbs_probe.json"
    manifest_path = manifest_dir / "cfbd_refresh_manifest.json"
    year = str(datetime.now(UTC).year)
    url = f"{context.settings.cfbd_api_base}/teams/fbs?year={year}"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {context.settings.cfbd_api_key}",
            "User-Agent": "NinersWarRoom-CFBD-SafeLoader/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=context.settings.api_timeout_seconds) as resp:
            body = resp.read().decode("utf-8")
    except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        manifest = {
            "source_id": entry.source_id,
            "run_id": context.run_id,
            "status": "FAILED",
            "url": url,
            "raw_cache_location": str(raw_dir),
            "error": str(exc),
            "model_use_warning": entry.model_use_warning,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        return _result(
            entry,
            context,
            started=started,
            action_type=FAILED,
            status="RED",
            refreshed=False,
            freshness="CFBD probe failed",
            found_artifacts=_existing_paths((manifest_path,)),
            explanation=f"CFBD configured but safe probe failed: {exc}",
            artifact=str(manifest_path),
        )
    raw_path.write_text(body, encoding="utf-8")
    row_count = _json_row_count(body)
    manifest = {
        "source_id": entry.source_id,
        "run_id": context.run_id,
        "status": "REFRESHED",
        "url": url,
        "raw_cache_location": str(raw_dir),
        "raw_file": str(raw_path),
        "row_count": row_count,
        "identity_gate": "CFBD identities must be reviewed before model use.",
        "model_use_allowed": False,
        "model_use_warning": entry.model_use_warning,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return _result(
        entry,
        context,
        started=started,
        action_type=REFRESHED,
        status="GREEN",
        refreshed=True,
        freshness=f"refreshed {context.run_timestamp}; rows={row_count}",
        found_artifacts=(str(raw_path), str(manifest_path)),
        explanation=(
            "CFBD safe probe refreshed to outside-git raw cache with a local manifest. "
            "No college identities became model input."
        ),
        artifact=str(manifest_path),
    )


def _check_frozen_board(entry: RefreshSourceEntry, context: RefreshContext) -> RefreshSourceResult:
    started = perf_counter()
    found = _existing_paths(Path(path) for path in entry.expected_artifacts)
    path = Path(found[0]) if found else REPO_SAFE_FROZEN_BOARD_PATH
    row_count = _csv_row_count(path) if path.exists() else 0
    status = "GREEN" if row_count == EXPECTED_ROW_COUNT else "RED"
    return _result(
        entry,
        context,
        started=started,
        action_type=ACTION_CHECK_ONLY,
        status=status,
        refreshed=False,
        freshness=f"row_count={row_count}; expected={EXPECTED_ROW_COUNT}",
        found_artifacts=found,
        explanation=(
            "Frozen Final Draft Board V1 checked only; baseline/checkpoint artifact was not "
            "refreshed or mutated."
        ),
        artifact="",
    )


def _check_pinned_manifest(
    entry: RefreshSourceEntry, context: RefreshContext
) -> RefreshSourceResult:
    started = perf_counter()
    found = _existing_paths(Path(path) for path in entry.expected_artifacts)
    current_hash = pinned_manifest_hash() or ""
    status = "GREEN" if current_hash == EXPECTED_PINNED_MANIFEST_HASH else "RED"
    return _result(
        entry,
        context,
        started=started,
        action_type=ACTION_CHECK_ONLY,
        status=status,
        refreshed=False,
        freshness=current_hash or "missing",
        found_artifacts=found,
        explanation="Pinned manifest hash checked only; pinned snapshot was not refreshed.",
        artifact="",
    )


def _check_full_dynasty(entry: RefreshSourceEntry, context: RefreshContext) -> RefreshSourceResult:
    started = perf_counter()
    found = _existing_paths(Path(path) for path in entry.expected_artifacts)
    path = Path(found[0]) if found else LOCAL_DYNASTY_RANKINGS_PATH
    row_count = _csv_row_count(path) if path.exists() else 0
    status = "GREEN" if row_count == EXPECTED_DYNASTY_ROW_COUNT else "YELLOW"
    return _result(
        entry,
        context,
        started=started,
        action_type=ACTION_CHECK_ONLY,
        status=status,
        refreshed=False,
        freshness=f"row_count={row_count}; expected={EXPECTED_DYNASTY_ROW_COUNT}",
        found_artifacts=found,
        explanation="Full dynasty/model_v4 output checked only; no model/rank output was rebuilt.",
        artifact="",
    )


def _check_runtime_state(
    entry: RefreshSourceEntry, context: RefreshContext
) -> RefreshSourceResult:
    started = perf_counter()
    path = runtime_state_path(mode="live", draft_id=DEFAULT_DRAFT_ID)
    found = (str(path),) if path.exists() else ()
    return _result(
        entry,
        context,
        started=started,
        action_type=ACTION_CHECK_ONLY,
        status="GREEN" if path.exists() else "YELLOW",
        refreshed=False,
        freshness=_artifact_freshness(path),
        found_artifacts=found,
        explanation=(
            "Runtime draft state checked only; no manual draft state was created or changed."
        ),
        artifact="",
    )


def _check_artifact_source(
    entry: RefreshSourceEntry, context: RefreshContext
) -> RefreshSourceResult:
    started = perf_counter()
    paths = [Path(path) for path in entry.expected_artifacts]
    found = _existing_paths(paths)
    status = "GREEN" if found else "YELLOW"
    freshness = "; ".join(_artifact_freshness(Path(path)) for path in found) or "not found"
    return _result(
        entry,
        context,
        started=started,
        action_type=ACTION_CHECK_ONLY,
        status=status,
        refreshed=False,
        freshness=freshness,
        found_artifacts=found,
        explanation=entry.user_explanation,
        artifact="",
    )


def _run_command(command: list[str], cwd: Path, timeout_seconds: int) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _run_handler(
    entry: RefreshSourceEntry,
    context: RefreshContext,
    handler: SourceHandler,
) -> RefreshSourceResult:
    started = perf_counter()
    try:
        return handler(entry, context)
    except Exception as exc:
        return _result(
            entry,
            context,
            started=started,
            action_type=FAILED,
            status="RED",
            refreshed=False,
            freshness="failed",
            found_artifacts=(),
            explanation=f"{entry.source_name} failed: {exc}",
            artifact="",
        )


def _result(
    entry: RefreshSourceEntry,
    context: RefreshContext,
    *,
    started: float,
    action_type: str,
    status: str,
    refreshed: bool,
    freshness: str,
    found_artifacts: tuple[str, ...],
    explanation: str,
    artifact: str,
) -> RefreshSourceResult:
    timestamp = _utc_now()
    return RefreshSourceResult(
        run_id=context.run_id,
        run_timestamp=context.run_timestamp,
        loader_mode=context.loader_mode,
        source_id=entry.source_id,
        source_name=entry.source_name,
        source_kind=entry.source_kind,
        loader_category=entry.loader_category,
        action_type=action_type,
        refreshed=refreshed,
        configured=entry.configured,
        freshness=freshness,
        expected_artifacts=entry.expected_artifacts,
        found_artifacts=found_artifacts,
        user_explanation=explanation,
        model_use_warning=entry.model_use_warning,
        requires_api_key=entry.requires_api_key,
        required_env_vars=entry.required_env_vars,
        runner_exists=entry.runner_exists,
        safe_to_pull=entry.safe_to_pull,
        protected_artifact=entry.protected_artifact,
        writes_raw_cache=entry.writes_raw_cache,
        raw_cache_location=entry.raw_cache_location,
        writes_tracked_artifact=entry.writes_tracked_artifact,
        default_action=entry.default_action,
        failure_mode=entry.failure_mode,
        status=status,
        timestamp=timestamp,
        duration_seconds=round(perf_counter() - started, 3),
        artifact_updated=artifact,
        source_type=entry.source_type,
        safe_to_run=entry.safe_to_run,
        refresh_method=entry.refresh_method,
        command_or_function=entry.command_or_function,
        output_artifacts=entry.output_artifacts,
        expected_runtime=entry.expected_runtime,
        last_result=status,
        last_success_timestamp=timestamp if refreshed and status == "GREEN" else "",
        user_message=explanation,
        caveat=entry.model_use_warning,
    )


def _policy_result(
    entry: RefreshSourceEntry,
    context: RefreshContext,
    *,
    action_type: str,
    status: str,
    explanation: str,
) -> RefreshSourceResult:
    return _result(
        entry,
        context,
        started=perf_counter(),
        action_type=action_type,
        status=status,
        refreshed=False,
        freshness="not refreshed",
        found_artifacts=(),
        explanation=explanation,
        artifact="",
    )


def _entry_selected(
    entry: RefreshSourceEntry,
    loader_mode: str,
    source_ids: set[str] | None,
) -> bool:
    if source_ids is not None:
        return entry.source_id in source_ids
    if loader_mode == QUICK_REFRESH:
        return entry.enabled_in_quick_refresh or entry.source_id in QUICK_PROTECTED_CHECKS
    if loader_mode == FULL_SAFE_REFRESH:
        return (
            entry.enabled_in_full_safe_refresh
            or entry.loader_category in {CHECK_ONLY, MANUAL_BLOCKED, NOT_CONFIGURED}
        )
    if loader_mode == CHECK_PROTECTED_ARTIFACTS:
        return entry.loader_category == CHECK_ONLY
    if loader_mode == MANUAL_SOURCES_CHECKLIST:
        return entry.loader_category == MANUAL_BLOCKED
    return False


def _check_only_entries(repo_root: Path, shared_root: Path) -> tuple[RefreshSourceEntry, ...]:
    latest_root = shared_root / "lane_exchange"
    model_evaluation_root = repo_root / "docs" / "hq" / "model" / "evaluation_v0"
    adp_root = shared_root / "lane_exchange" / "market_behavior" / "sleeper_adp_display_context"
    return (
        _check_entry(
            "frozen_baseline_board",
            "Frozen Final Draft Board V1",
            (str(REPO_SAFE_FROZEN_BOARD_PATH),),
            "Frozen baseline/checkpoint only; never refreshed or source truth.",
            "Expected 66 rows; checked only.",
        ),
        _check_entry(
            "pinned_manifest_hash",
            "Pinned manifest/hash",
            (str(PINNED_SNAPSHOT_MANIFEST),),
            "Pinned snapshot is protected and never refreshed.",
            "Hash must remain unchanged.",
        ),
        _check_entry(
            "latest_candidate_latest_approved",
            "latest_candidate/latest_approved",
            (
                str(latest_root / "latest_candidate"),
                str(latest_root / "latest_approved"),
            ),
            "latest_candidate/latest_approved are protected; this loader never updates them.",
            "Presence/status only.",
        ),
        _check_entry(
            "full_dynasty_model_v4_output",
            "Full dynasty/model_v4 output",
            (str(LOCAL_DYNASTY_RANKINGS_PATH),),
            "Full dynasty/model_v4 outputs are checked only; rank logic is not run.",
            "Expected 240 rows if local output is present.",
        ),
        _check_entry(
            "outcome_artifacts",
            "Outcome artifacts",
            (str(OUTCOME_NUMERIC_DISPLAY_PATH),),
            "Outcome artifacts are status-only in this loader.",
            "No outcome output rebuild.",
        ),
        _check_entry(
            "lve_pdf_free_agent_extract",
            "LVE PDF/free-agent extract",
            (str(PDF_FREE_AGENT_DRAFTABLE_POOL_PATH),),
            "LVE PDF/free-agent extract is checked only.",
            "Manual evidence extract remains protected.",
        ),
        _check_entry(
            "runtime_draft_state",
            "Runtime draft state",
            (str(runtime_state_path(mode="live", draft_id=DEFAULT_DRAFT_ID)),),
            "Runtime draft state is manual/local state; checked only.",
            "No runtime mutation.",
        ),
        _check_entry(
            "model_evaluation_harness",
            "Model evaluation harness outputs",
            (str(model_evaluation_root),),
            "Model evaluation harness outputs are checked only; no harness run.",
            "No model evaluation output mutation.",
        ),
        _check_entry(
            "sleeper_adp_display_context",
            "Sleeper ADP display context",
            (str(adp_root),),
            "Sleeper ADP context is display-only if present; never model input.",
            "Status only.",
        ),
    )


def _check_entry(
    source_id: str,
    source_name: str,
    expected_artifacts: tuple[str, ...],
    explanation: str,
    freshness_policy: str,
) -> RefreshSourceEntry:
    return RefreshSourceEntry(
        source_id=source_id,
        source_name=source_name,
        source_kind="protected_artifact_status",
        loader_category=CHECK_ONLY,
        enabled_in_quick_refresh=False,
        enabled_in_full_safe_refresh=True,
        requires_api_key=False,
        required_env_vars=(),
        runner_exists=False,
        configured=True,
        safe_to_pull=False,
        protected_artifact=True,
        writes_raw_cache=False,
        raw_cache_location="",
        writes_tracked_artifact=False,
        expected_artifacts=expected_artifacts,
        freshness_policy=freshness_policy,
        model_use_allowed=False,
        model_use_warning="Checked only; this loader does not make it model input.",
        default_action=ACTION_CHECK_ONLY,
        failure_mode="Report missing/stale status without mutation.",
        user_explanation=explanation,
        command_or_function="status_check",
        expected_runtime="< 1 second",
    )


def _manual_blocked_entries(repo_root: Path) -> tuple[RefreshSourceEntry, ...]:
    manual_root = repo_root / "templates" / "real_data_inputs"
    return (
        _manual_entry(
            "gmail_league_history",
            "Gmail league-history evidence",
            "email_privacy_gated",
            "Gmail evidence intake is manual/privacy-gated. This loader never pulls raw "
            "email bodies.",
        ),
        _manual_entry(
            "rotowire_vendor_exports",
            "RotoWire/vendor exports",
            "vendor_manual_export",
            "RotoWire/vendor sources require manual export/review and are never scraped.",
        ),
        _manual_entry(
            "fantasypros_vendor_exports",
            "FantasyPros/vendor/projection exports",
            "vendor_manual_export",
            "FantasyPros/vendor projection sources are manual/keyed exports only; no scraping.",
        ),
        _manual_entry(
            "pdf_manual_evidence_files",
            "PDFs/manual evidence files",
            "manual_evidence_file",
            "PDF/manual evidence files must be provided and reviewed by the user; no auto-pull.",
            expected_artifacts=(str(manual_root),),
        ),
    )


def _manual_entry(
    source_id: str,
    source_name: str,
    source_kind: str,
    explanation: str,
    *,
    expected_artifacts: tuple[str, ...] = (),
) -> RefreshSourceEntry:
    return RefreshSourceEntry(
        source_id=source_id,
        source_name=source_name,
        source_kind=source_kind,
        loader_category=MANUAL_BLOCKED,
        enabled_in_quick_refresh=False,
        enabled_in_full_safe_refresh=False,
        requires_api_key=False,
        required_env_vars=(),
        runner_exists=False,
        configured=False,
        safe_to_pull=False,
        protected_artifact=False,
        writes_raw_cache=False,
        raw_cache_location="",
        writes_tracked_artifact=False,
        expected_artifacts=expected_artifacts,
        freshness_policy="Manual checklist only.",
        model_use_allowed=False,
        model_use_warning="Manual/blocked source; not pulled and not model input by this loader.",
        default_action=BLOCKED_MANUAL,
        failure_mode="Always report BLOCKED_MANUAL; never pull automatically.",
        user_explanation=explanation,
        command_or_function="",
        expected_runtime="manual",
    )


def _overall_status(results: Iterable[RefreshSourceResult]) -> str:
    statuses = {result.status for result in results}
    if "RED" in statuses:
        return "RED"
    if statuses - {"GREEN", "SKIPPED", "BLOCKED"}:
        return "YELLOW"
    return "GREEN"


def _run_payload(run: RefreshRunResult, latest_path: Path) -> dict[str, Any]:
    payload = asdict(run)
    payload["status_path"] = str(latest_path)
    payload["results"] = [_result_payload(result) for result in run.results]
    return payload


def _result_payload(result: RefreshSourceResult) -> dict[str, Any]:
    payload = asdict(result)
    for key in ("expected_artifacts", "found_artifacts", "required_env_vars", "output_artifacts"):
        payload[key] = "; ".join(str(value) for value in payload.get(key, ()))
    for key in RESULT_SCHEMA:
        payload.setdefault(key, "")
    return payload


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _tail(value: str, *, max_lines: int = 4) -> str:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    return " | ".join(lines[-max_lines:])


def _existing_paths(paths: Iterable[Path]) -> tuple[str, ...]:
    return tuple(str(path) for path in paths if path.exists())


def _artifact_freshness(path: Path) -> str:
    if not path.exists():
        return "missing"
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).replace(microsecond=0)
    if path.is_dir():
        return f"found directory; modified {modified.isoformat()}"
    try:
        sha = file_sha256(path)
    except OSError:
        sha = "unreadable"
    return f"found file; modified {modified.isoformat()}; sha256={sha}"


def _csv_row_count(path: Path) -> int:
    if not path.exists() or path.is_dir():
        return 0
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            next(reader, None)
            return sum(1 for _row in reader)
    except OSError:
        return 0


def _json_row_count(body: str) -> int:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return 0
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                return len(value)
    return 1 if payload else 0


def _csv_cell(value: object) -> str:
    text = str(value).replace('"', '""')
    if any(token in text for token in (",", "\n", '"')):
        return f'"{text}"'
    return text
