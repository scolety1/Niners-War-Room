from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from src.config.api_settings import ApiSettings, get_api_settings
from src.services.draft_day_runtime_state_service import (
    DEFAULT_DRAFT_ID,
    runtime_state_path,
)
from src.services.lve_refresh_service import run_sleeper_refresh

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATUS_ROOT = REPO_ROOT / "local_exports" / "refresh_data"
DEFAULT_STATUS_PATH = DEFAULT_STATUS_ROOT / "latest_refresh_status.json"
DEFAULT_SHARED_ROOT = Path(r"C:\NWR_SHARED_DATA")
DEFAULT_NFLVERSE_PYDEPS = (
    DEFAULT_SHARED_ROOT / "vendor_spikes" / "nflverse" / "scratch" / "pydeps"
)

BLOCKED_SOURCE_TYPES = {"vendor_manual", "email_manual"}
RESULT_SCHEMA = (
    "source_id",
    "source_name",
    "source_type",
    "configured",
    "safe_to_run",
    "refresh_method",
    "command_or_function",
    "output_artifacts",
    "expected_runtime",
    "last_result",
    "last_success_timestamp",
    "status",
    "refreshed",
    "user_message",
    "timestamp",
    "artifact_updated",
    "caveat",
    "duration_seconds",
)


@dataclass(frozen=True)
class RefreshSourceEntry:
    source_id: str
    source_name: str
    source_type: str
    configured: bool
    safe_to_run: bool
    refresh_method: str
    command_or_function: str
    output_artifacts: tuple[str, ...]
    expected_runtime: str
    last_result: str = ""
    last_success_timestamp: str = ""
    status: str = "SKIPPED"
    user_message: str = ""


@dataclass(frozen=True)
class RefreshSourceResult:
    source_id: str
    source_name: str
    source_type: str
    configured: bool
    safe_to_run: bool
    refresh_method: str
    command_or_function: str
    output_artifacts: tuple[str, ...]
    expected_runtime: str
    last_result: str
    last_success_timestamp: str
    status: str
    refreshed: bool
    user_message: str
    timestamp: str
    artifact_updated: str
    caveat: str
    duration_seconds: float


@dataclass(frozen=True)
class RefreshRunResult:
    run_id: str
    started_at_utc: str
    finished_at_utc: str
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
    repo_root: Path
    status_root: Path
    settings: ApiSettings
    python_executable: str
    command_runner: Callable[[list[str], Path, int], CommandResult]


SourceHandler = Callable[[RefreshSourceEntry, RefreshContext], RefreshSourceResult]


def build_refresh_registry(
    *,
    repo_root: Path = REPO_ROOT,
    status_root: Path = DEFAULT_STATUS_ROOT,
    include_slow_sources: bool = False,
    settings: ApiSettings | None = None,
    shared_root: Path = DEFAULT_SHARED_ROOT,
) -> tuple[RefreshSourceEntry, ...]:
    settings = settings or get_api_settings()
    scripts = repo_root / "scripts"
    dynasty_script = scripts / "refresh_dynastyprocess_market_baseline_v1.py"
    sleeper_script = scripts / "run_sleeper_refresh_v0.ps1"
    nflverse_script = scripts / "run_nflverse_refresh_v0.ps1"
    nflverse_pydeps = shared_root / "vendor_spikes" / "nflverse" / "scratch" / "pydeps"

    return (
        RefreshSourceEntry(
            source_id="dynastyprocess_market_baseline",
            source_name="DynastyProcess market baseline",
            source_type="public_market_display",
            configured=dynasty_script.exists(),
            safe_to_run=dynasty_script.exists(),
            refresh_method="python_script",
            command_or_function=str(dynasty_script),
            output_artifacts=(
                str(status_root / "dynastyprocess_market_baseline" / "latest"),
            ),
            expected_runtime="< 2 minutes",
            status="GREEN" if dynasty_script.exists() else "NOT_CONFIGURED",
            user_message=(
                "Refreshes display-only public market baseline into ignored local artifacts."
            ),
        ),
        RefreshSourceEntry(
            source_id="sleeper_league_state",
            source_name="Sleeper league data",
            source_type="public_api_league_state",
            configured=bool(settings.sleeper_league_id) and sleeper_script.exists(),
            safe_to_run=bool(settings.sleeper_league_id) and sleeper_script.exists(),
            refresh_method="python_function",
            command_or_function="src.services.lve_refresh_service.run_sleeper_refresh",
            output_artifacts=(str(status_root / "sleeper"),),
            expected_runtime="< 1 minute",
            status=(
                "GREEN"
                if settings.sleeper_league_id and sleeper_script.exists()
                else "NOT_CONFIGURED"
            ),
            user_message="Refreshes league state snapshots only; does not build candidate packs.",
        ),
        RefreshSourceEntry(
            source_id="nflverse_public_data",
            source_name="nflverse / nfl_data_py public data",
            source_type="public_structured_nfl",
            configured=nflverse_script.exists() and nflverse_pydeps.exists(),
            safe_to_run=(
                include_slow_sources
                and nflverse_script.exists()
                and nflverse_pydeps.exists()
            ),
            refresh_method="powershell_script",
            command_or_function=str(nflverse_script),
            output_artifacts=(str(shared_root / "scheduled_ingest" / "nflverse"),),
            expected_runtime="several minutes",
            status="GREEN"
            if include_slow_sources and nflverse_script.exists() and nflverse_pydeps.exists()
            else "SKIPPED"
            if nflverse_script.exists() and nflverse_pydeps.exists()
            else "NOT_CONFIGURED",
            user_message=(
                "Configured local runner found; skipped unless slow source refresh is "
                "explicitly included."
            ),
        ),
        RefreshSourceEntry(
            source_id="collegefootballdata",
            source_name="CollegeFootballData",
            source_type="keyed_api",
            configured=bool(settings.cfbd_api_key),
            safe_to_run=False,
            refresh_method="skipped",
            command_or_function="",
            output_artifacts=(),
            expected_runtime="manual",
            status="BLOCKED" if settings.cfbd_api_key else "NOT_CONFIGURED",
            user_message="No approved app refresh connector/script is registered for CFBD.",
        ),
        RefreshSourceEntry(
            source_id="rotowire_vendor_exports",
            source_name="RotoWire / vendor exports",
            source_type="vendor_manual",
            configured=True,
            safe_to_run=False,
            refresh_method="manual_export_only",
            command_or_function="",
            output_artifacts=(),
            expected_runtime="manual",
            status="BLOCKED",
            user_message="Vendor/export sources are manual and are never scraped from this button.",
        ),
        RefreshSourceEntry(
            source_id="gmail_league_history",
            source_name="Gmail league-history evidence",
            source_type="email_manual",
            configured=False,
            safe_to_run=False,
            refresh_method="manual_metadata_queue_only",
            command_or_function="",
            output_artifacts=(),
            expected_runtime="manual",
            status="SKIPPED",
            user_message="Email bodies are not pulled by Refresh Data.",
        ),
        RefreshSourceEntry(
            source_id="runtime_draft_state",
            source_name="Local runtime draft state",
            source_type="local_runtime_status",
            configured=True,
            safe_to_run=True,
            refresh_method="status_check",
            command_or_function="src.services.draft_day_runtime_state_service.runtime_state_path",
            output_artifacts=(),
            expected_runtime="< 1 second",
            status="SKIPPED",
            user_message=(
                "Runtime state is checked only; API refresh is not valid for manual "
                "draft state."
            ),
        ),
        RefreshSourceEntry(
            source_id="model_evaluation_harness",
            source_name="Model Evaluation Harness outputs",
            source_type="local_generated_status",
            configured=True,
            safe_to_run=True,
            refresh_method="status_check",
            command_or_function="docs/hq/model/evaluation_v0",
            output_artifacts=(),
            expected_runtime="< 1 second",
            status="SKIPPED",
            user_message=(
                "Harness outputs are checked only; rerun remains a deliberate manual "
                "action."
            ),
        ),
        RefreshSourceEntry(
            source_id="data_health_inputs",
            source_name="Settings / Data Health inputs",
            source_type="local_generated_status",
            configured=True,
            safe_to_run=True,
            refresh_method="status_check",
            command_or_function="src.services.data_health_dashboard_service",
            output_artifacts=(),
            expected_runtime="< 1 second",
            status="SKIPPED",
            user_message="Checks local data-health inputs without mutating source truth.",
        ),
    )


def run_data_refresh(
    *,
    repo_root: Path = REPO_ROOT,
    status_root: Path = DEFAULT_STATUS_ROOT,
    source_ids: Iterable[str] | None = None,
    include_slow_sources: bool = False,
    settings: ApiSettings | None = None,
    command_runner: Callable[[list[str], Path, int], CommandResult] | None = None,
    handlers: dict[str, SourceHandler] | None = None,
    write_status: bool = True,
) -> RefreshRunResult:
    started = _utc_now()
    run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    registry = build_refresh_registry(
        repo_root=repo_root,
        status_root=status_root,
        include_slow_sources=include_slow_sources,
        settings=settings,
    )
    selected = set(source_ids or [entry.source_id for entry in registry])
    context = RefreshContext(
        run_id=run_id,
        repo_root=repo_root,
        status_root=status_root,
        settings=settings or get_api_settings(),
        python_executable=sys.executable,
        command_runner=command_runner or _run_command,
    )
    source_handlers = _default_handlers() | (handlers or {})

    results: list[RefreshSourceResult] = []
    for entry in registry:
        if entry.source_id not in selected:
            results.append(_skipped_result(entry, "SKIPPED", "Source not selected for this run."))
            continue
        if not entry.configured:
            results.append(
                _skipped_result(
                    entry,
                    "NOT_CONFIGURED",
                    entry.user_message or "Source is not configured.",
                )
            )
            continue
        if not entry.safe_to_run:
            status = (
                "BLOCKED"
                if entry.source_type in BLOCKED_SOURCE_TYPES or entry.status == "BLOCKED"
                else "SKIPPED"
            )
            results.append(_skipped_result(entry, status, entry.user_message))
            continue
        handler = source_handlers.get(entry.source_id, _status_check_source)
        started_source = perf_counter()
        try:
            result = handler(entry, context)
        except Exception as exc:
            result = _failure_result(entry, exc, started_source)
        results.append(result)

    finished = _utc_now()
    run = RefreshRunResult(
        run_id=run_id,
        started_at_utc=started,
        finished_at_utc=finished,
        overall_status=_overall_status(results),
        status_path=str(
            DEFAULT_STATUS_PATH
            if status_root == DEFAULT_STATUS_ROOT
            else status_root / "latest_refresh_status.json"
        ),
        results=tuple(results),
    )
    if write_status:
        write_refresh_status(run, status_root=status_root)
    return run


def write_refresh_status(run: RefreshRunResult, *, status_root: Path = DEFAULT_STATUS_ROOT) -> Path:
    status_root.mkdir(parents=True, exist_ok=True)
    latest_path = status_root / "latest_refresh_status.json"
    archive_path = status_root / f"{run.run_id}_refresh_status.json"
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


def validate_refresh_result_schema(rows: Iterable[dict[str, Any]]) -> None:
    expected = set(RESULT_SCHEMA)
    for row in rows:
        missing = expected - set(row)
        if missing:
            raise ValueError(f"Refresh result row missing columns: {sorted(missing)}")


def _default_handlers() -> dict[str, SourceHandler]:
    return {
        "dynastyprocess_market_baseline": _refresh_dynastyprocess,
        "sleeper_league_state": _refresh_sleeper,
        "nflverse_public_data": _refresh_nflverse,
        "runtime_draft_state": _check_runtime_state,
        "model_evaluation_harness": _check_model_evaluation,
        "data_health_inputs": _status_check_source,
    }


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
    result = context.command_runner(command, context.repo_root, 120)
    freshness_path = artifact_dir / "dp_freshness_report.csv"
    status = "GREEN" if result.returncode == 0 else "RED"
    message = _tail(result.stdout) or "DynastyProcess refresh completed."
    if result.returncode != 0:
        message = _tail(result.stderr) or _tail(result.stdout) or "DynastyProcess refresh failed."
    return _result(
        entry,
        status=status,
        refreshed=result.returncode == 0,
        message=message,
        artifact=str(artifact_dir if freshness_path.exists() or result.returncode == 0 else ""),
        caveat="Display-only market context; not a model/rank/source-truth input.",
        started=started,
    )


def _refresh_sleeper(entry: RefreshSourceEntry, context: RefreshContext) -> RefreshSourceResult:
    started = perf_counter()
    output_root = context.status_root / "sleeper"
    result = run_sleeper_refresh(
        league_id=context.settings.sleeper_league_id,
        output_root=output_root,
        snapshot_name=context.run_id,
    )
    rows = result.counts.get("rosters", 0)
    return _result(
        entry,
        status="GREEN",
        refreshed=True,
        message=f"Sleeper snapshot refreshed with {rows} roster rows.",
        artifact=str(result.output_dir),
        caveat="League state only; candidate data packs and ranks are not rebuilt.",
        started=started,
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
        "-SnapshotLabel",
        context.run_id,
    ]
    result = context.command_runner(command, context.repo_root, 300)
    return _result(
        entry,
        status="GREEN" if result.returncode == 0 else "RED",
        refreshed=result.returncode == 0,
        message=_tail(result.stdout)
        if result.returncode == 0
        else _tail(result.stderr) or "nflverse refresh failed.",
        artifact=str(DEFAULT_SHARED_ROOT / "scheduled_ingest" / "nflverse" / context.run_id),
        caveat="Public structured NFL data; normalizer/candidate writes remain opt-in.",
        started=started,
    )


def _check_runtime_state(
    entry: RefreshSourceEntry, context: RefreshContext
) -> RefreshSourceResult:
    started = perf_counter()
    path = runtime_state_path(mode="live", draft_id=DEFAULT_DRAFT_ID)
    exists = path.exists()
    return _result(
        entry,
        status="GREEN" if exists else "YELLOW",
        refreshed=False,
        message="Live runtime state found." if exists else "No live runtime state found.",
        artifact=str(path) if exists else "",
        caveat="Checked only; manual draft state is never refreshed from APIs.",
        started=started,
    )


def _check_model_evaluation(
    entry: RefreshSourceEntry, context: RefreshContext
) -> RefreshSourceResult:
    started = perf_counter()
    root = context.repo_root / "docs" / "hq" / "model" / "evaluation_v0"
    exists = root.exists()
    return _result(
        entry,
        status="GREEN" if exists else "YELLOW",
        refreshed=False,
        message=(
            "Model Evaluation Harness outputs found."
            if exists
            else "Harness outputs not found."
        ),
        artifact=str(root) if exists else "",
        caveat="Status check only; the harness is not rerun by the standard button.",
        started=started,
    )


def _status_check_source(
    entry: RefreshSourceEntry, context: RefreshContext
) -> RefreshSourceResult:
    started = perf_counter()
    return _result(
        entry,
        status="GREEN",
        refreshed=False,
        message=entry.user_message or "Status check completed.",
        artifact="",
        caveat="No source-truth mutation.",
        started=started,
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


def _result(
    entry: RefreshSourceEntry,
    *,
    status: str,
    refreshed: bool,
    message: str,
    artifact: str,
    caveat: str,
    started: float,
) -> RefreshSourceResult:
    timestamp = _utc_now()
    return RefreshSourceResult(
        source_id=entry.source_id,
        source_name=entry.source_name,
        source_type=entry.source_type,
        configured=entry.configured,
        safe_to_run=entry.safe_to_run,
        refresh_method=entry.refresh_method,
        command_or_function=entry.command_or_function,
        output_artifacts=entry.output_artifacts,
        expected_runtime=entry.expected_runtime,
        last_result=status,
        last_success_timestamp=(
            timestamp if status == "GREEN" and refreshed else entry.last_success_timestamp
        ),
        status=status,
        refreshed=refreshed,
        user_message=message,
        timestamp=timestamp,
        artifact_updated=artifact,
        caveat=caveat,
        duration_seconds=round(perf_counter() - started, 3),
    )


def _skipped_result(
    entry: RefreshSourceEntry, status: str, message: str
) -> RefreshSourceResult:
    return RefreshSourceResult(
        source_id=entry.source_id,
        source_name=entry.source_name,
        source_type=entry.source_type,
        configured=entry.configured,
        safe_to_run=entry.safe_to_run,
        refresh_method=entry.refresh_method,
        command_or_function=entry.command_or_function,
        output_artifacts=entry.output_artifacts,
        expected_runtime=entry.expected_runtime,
        last_result=status,
        last_success_timestamp=entry.last_success_timestamp,
        status=status,
        refreshed=False,
        user_message=message,
        timestamp=_utc_now(),
        artifact_updated="",
        caveat=_skip_caveat(status),
        duration_seconds=0.0,
    )


def _failure_result(
    entry: RefreshSourceEntry, exc: Exception, started: float
) -> RefreshSourceResult:
    return _result(
        entry,
        status="RED",
        refreshed=False,
        message=f"{entry.source_name} failed: {exc}",
        artifact="",
        caveat="Failure was isolated; remaining sources still report independently.",
        started=started,
    )


def _skip_caveat(status: str) -> str:
    if status == "NOT_CONFIGURED":
        return "No configured safe connector was found."
    if status == "BLOCKED":
        return "Blocked/manual source; Refresh Data will not scrape or pull it."
    return "Skipped by refresh policy."


def _overall_status(results: Iterable[RefreshSourceResult]) -> str:
    statuses = {result.status for result in results}
    if "RED" in statuses:
        return "RED"
    if statuses - {"GREEN"}:
        return "YELLOW"
    return "GREEN"


def _run_payload(run: RefreshRunResult, latest_path: Path) -> dict[str, Any]:
    payload = asdict(run)
    payload["status_path"] = str(latest_path)
    payload["results"] = [_result_payload(result) for result in run.results]
    return payload


def _result_payload(result: RefreshSourceResult) -> dict[str, Any]:
    payload = asdict(result)
    for key in RESULT_SCHEMA:
        payload.setdefault(key, "")
    return payload


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _tail(value: str, *, max_lines: int = 4) -> str:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    return " | ".join(lines[-max_lines:])
