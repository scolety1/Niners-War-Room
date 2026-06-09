from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.data_pack_admission_service import (
    DataPackAdmissionReport,
    build_data_pack_admission_report,
)
from src.services.data_pack_build_service import (
    DEFAULT_DATA_PACK_OUTPUT_ROOT,
    DataPackBuildResult,
    build_data_pack_from_refresh,
)
from src.services.data_pack_health_service import (
    DataPackHealthReport,
    build_data_pack_health_report,
)
from src.services.lve_refresh_service import (
    DEFAULT_MERGED_OUTPUT_ROOT,
    DEFAULT_RANK_TEXT_PATH,
    DEFAULT_SLEEPER_OUTPUT_ROOT,
    find_latest_sleeper_snapshot,
    run_rank_merge_for_snapshot,
    run_sleeper_refresh,
)
from src.services.sleeper_import_service import DEFAULT_LEAGUE_ID, SleeperHttpClient
from src.services.veteran_model_schema_service import VETERAN_SOURCE_TABLES

DEFAULT_ROUTINE_VETERAN_MODEL_INPUT_DIR = Path(
    "local_exports/active_veteran_model_public_sources"
)
PROTECTED_OUTPUT_MARKERS = {"draft_freezes", "freeze", "frozen", "final"}


@dataclass(frozen=True)
class RoutineRefreshStep:
    step: str
    status: str
    mutated: bool
    output_path: str
    rows: int | str
    message: str


@dataclass(frozen=True)
class RoutineRefreshResult:
    run_id: str
    dry_run: bool
    status: str
    readiness: str
    active_candidate_pack: Path | None
    steps: tuple[RoutineRefreshStep, ...]
    warnings: tuple[str, ...]
    health: DataPackHealthReport | None
    admission: DataPackAdmissionReport | None
    data_pack_result: DataPackBuildResult | None


def run_routine_refresh(
    *,
    league_id: str = DEFAULT_LEAGUE_ID,
    rank_text_path: str | Path = DEFAULT_RANK_TEXT_PATH,
    sleeper_output_root: str | Path = DEFAULT_SLEEPER_OUTPUT_ROOT,
    merged_output_root: str | Path = DEFAULT_MERGED_OUTPUT_ROOT,
    data_pack_output_root: str | Path = DEFAULT_DATA_PACK_OUTPUT_ROOT,
    veteran_model_input_dir: str | Path = DEFAULT_ROUTINE_VETERAN_MODEL_INPUT_DIR,
    refresh_sleeper: bool = True,
    dry_run: bool = False,
    client: SleeperHttpClient | None = None,
    run_id: str | None = None,
) -> RoutineRefreshResult:
    resolved_run_id = run_id or _run_id()
    warnings: list[str] = []
    steps: list[RoutineRefreshStep] = []
    data_pack_root = Path(data_pack_output_root)
    protected_reason = _protected_output_reason(data_pack_root)
    if protected_reason:
        steps.append(
            _step(
                "output_guard",
                "error",
                False,
                data_pack_root,
                "",
                protected_reason,
            )
        )
        return _result(resolved_run_id, dry_run, "blocked", "blocked", None, steps, warnings)

    planned_pack_name = _pack_name(league_id, resolved_run_id)
    planned_pack_dir = data_pack_root / planned_pack_name
    if planned_pack_dir.exists():
        steps.append(
            _step(
                "output_guard",
                "error",
                False,
                planned_pack_dir,
                "",
                (
                    "Candidate data pack already exists. Choose a new run id; "
                    "no files were overwritten."
                ),
            )
        )
        return _result(resolved_run_id, dry_run, "blocked", "blocked", None, steps, warnings)

    model_input_path = _scoreable_model_input_dir(veteran_model_input_dir)
    if dry_run:
        steps.extend(
            _dry_run_steps(
                league_id=league_id,
                rank_text_path=Path(rank_text_path),
                sleeper_output_root=Path(sleeper_output_root),
                data_pack_dir=planned_pack_dir,
                veteran_model_input_dir=Path(veteran_model_input_dir),
                model_input_path=model_input_path,
                refresh_sleeper=refresh_sleeper,
            )
        )
        return _result(
            resolved_run_id,
            dry_run,
            "planned",
            "dry_run",
            planned_pack_dir,
            steps,
            warnings,
        )

    snapshot_dir: Path | None = None
    if refresh_sleeper:
        try:
            sleeper_result = run_sleeper_refresh(
                league_id=league_id,
                output_root=sleeper_output_root,
                client=client,
                snapshot_name=resolved_run_id,
            )
        except Exception as exc:
            steps.append(
                _step(
                    "sleeper_snapshot",
                    "error",
                    False,
                    "",
                    "",
                    f"Sleeper refresh failed: {exc}",
                )
            )
            return _result(
                resolved_run_id,
                dry_run,
                "blocked",
                "blocked",
                None,
                steps,
                warnings,
            )
        snapshot_dir = sleeper_result.output_dir
        steps.append(
            _step(
                "sleeper_snapshot",
                "ok",
                True,
                snapshot_dir,
                sleeper_result.counts.get("rosters", 0),
                "Sleeper roster, pick, team, draft, and metadata snapshots refreshed.",
            )
        )
    else:
        snapshot_dir = find_latest_sleeper_snapshot(
            league_id=league_id,
            output_root=sleeper_output_root,
        )
        if snapshot_dir is None:
            steps.append(
                _step(
                    "sleeper_snapshot",
                    "error",
                    False,
                    "",
                    "",
                    "No existing Sleeper snapshot found and Sleeper refresh is disabled.",
                )
            )
            return _result(
                resolved_run_id,
                dry_run,
                "blocked",
                "blocked",
                None,
                steps,
                warnings,
            )
        steps.append(
            _step(
                "sleeper_snapshot",
                "reused",
                False,
                snapshot_dir,
                "",
                "Using latest local Sleeper snapshot; no Sleeper API call made.",
            )
        )

    merged_rank_dir: Path | None = None
    rank_path = Path(rank_text_path)
    if rank_path.exists():
        try:
            merge_result = run_rank_merge_for_snapshot(
                sleeper_output_dir=snapshot_dir,
                rank_text_path=rank_path,
                output_root=merged_output_root,
            )
            merged_rank_dir = merge_result.output_dir
            steps.append(
                _step(
                    "league_rank_merge",
                    "ok",
                    True,
                    merged_rank_dir,
                    merge_result.counts.get("sleeper_rosters_with_pdf_ranks", 0),
                    "League-rank PDF/text merged onto Sleeper roster truth.",
                )
            )
        except Exception as exc:
            warnings.append("League-rank merge failed; data pack will use raw Sleeper ranks.")
            steps.append(
                _step(
                    "league_rank_merge",
                    "error",
                    False,
                    "",
                    "",
                    f"League-rank merge failed: {exc}",
                )
            )
    else:
        warnings.append("League-rank text file is missing; data pack will use raw Sleeper ranks.")
        steps.append(
            _step(
                "league_rank_merge",
                "skipped",
                False,
                rank_path,
                "",
                "League-rank text file missing.",
            )
        )

    steps.append(
        _step(
            "model_input_check",
            "ok" if model_input_path is not None else "skipped",
            False,
            model_input_path or veteran_model_input_dir,
            "",
            "Veteran model inputs found; model scoring will run."
            if model_input_path is not None
            else "Required veteran model inputs missing; pack will keep placeholder scores.",
        )
    )

    try:
        data_pack_result = build_data_pack_from_refresh(
            sleeper_output_dir=snapshot_dir,
            merged_rank_output_dir=merged_rank_dir,
            veteran_model_input_dir=model_input_path,
            output_root=data_pack_root,
            data_pack_name=planned_pack_name,
        )
    except Exception as exc:
        steps.append(
            _step(
                "data_pack_build",
                "error",
                False,
                planned_pack_dir,
                "",
                f"Data pack build failed: {exc}",
            )
        )
        return _result(
            resolved_run_id,
            dry_run,
            "blocked",
            "blocked",
            None,
            steps,
            warnings,
        )
    warnings.extend(data_pack_result.warnings)
    steps.append(
        _step(
            "data_pack_build",
            "ok",
            True,
            data_pack_result.output_dir,
            sum(data_pack_result.counts.values()),
            "Candidate data pack built in a new folder.",
        )
    )
    model_warning = next(
        (warning for warning in data_pack_result.warnings if "Veteran model inputs" in warning),
        "",
    )
    if model_warning:
        steps.append(_step("model_scoring", "error", False, "", "", model_warning))
    elif model_input_path is not None:
        steps.append(
            _step(
                "model_scoring",
                "ok",
                True,
                data_pack_result.files.get("model_outputs.csv", ""),
                data_pack_result.counts.get("model_outputs.csv", 0),
                "Veteran model outputs generated from local normalized inputs.",
            )
        )
    else:
        steps.append(
            _step(
                "model_scoring",
                "skipped",
                False,
                data_pack_result.files.get("model_outputs.csv", ""),
                data_pack_result.counts.get("model_outputs.csv", 0),
                "Required model inputs missing; placeholder model outputs remain.",
            )
        )

    validated = validate_data_pack(data_pack_result.output_dir)
    steps.append(
        _step(
            "validate_pack",
            "error" if validated.has_errors else "ok",
            False,
            data_pack_result.output_dir,
            len(validated.issues),
            "Validation found blocking errors."
            if validated.has_errors
            else "Candidate pack passed schema validation.",
        )
    )
    health = build_data_pack_health_report(data_pack_result.output_dir)
    admission = build_data_pack_admission_report(candidate_data_pack=data_pack_result.output_dir)
    readiness = admission.decision
    steps.append(
        _step(
            "readiness_result",
            readiness,
            False,
            data_pack_result.output_dir,
            health.roster_count,
            (
                f"Health={health.readiness}; admission={admission.decision}; "
                f"placeholders={health.placeholder_model_output_count}."
            ),
        )
    )
    status = "ready" if readiness == "ready" else "review" if readiness == "review" else "blocked"
    return RoutineRefreshResult(
        run_id=resolved_run_id,
        dry_run=dry_run,
        status=status,
        readiness=readiness,
        active_candidate_pack=data_pack_result.output_dir,
        steps=tuple(steps),
        warnings=tuple(warnings),
        health=health,
        admission=admission,
        data_pack_result=data_pack_result,
    )


def routine_refresh_status_rows(result: RoutineRefreshResult) -> list[dict[str, object]]:
    return [
        {
            "step": step.step,
            "status": step.status,
            "mutated": step.mutated,
            "rows": step.rows,
            "output_path": step.output_path,
            "message": step.message,
        }
        for step in result.steps
    ]


def _dry_run_steps(
    *,
    league_id: str,
    rank_text_path: Path,
    sleeper_output_root: Path,
    data_pack_dir: Path,
    veteran_model_input_dir: Path,
    model_input_path: Path | None,
    refresh_sleeper: bool,
) -> list[RoutineRefreshStep]:
    latest_snapshot = find_latest_sleeper_snapshot(
        league_id=league_id,
        output_root=sleeper_output_root,
    )
    return [
        _step(
            "sleeper_snapshot",
            "planned" if refresh_sleeper else "reused" if latest_snapshot else "error",
            False,
            sleeper_output_root if refresh_sleeper else latest_snapshot or "",
            "",
            "Would refresh Sleeper snapshot."
            if refresh_sleeper
            else "Would reuse latest local Sleeper snapshot."
            if latest_snapshot
            else "No existing Sleeper snapshot found.",
        ),
        _step(
            "league_rank_merge",
            "planned" if rank_text_path.exists() else "skipped",
            False,
            rank_text_path,
            "",
            "Would merge league-rank text onto Sleeper roster truth."
            if rank_text_path.exists()
            else "League-rank text file is missing.",
        ),
        _step(
            "model_input_check",
            "ok" if model_input_path is not None else "skipped",
            False,
            model_input_path or veteran_model_input_dir,
            "",
            "Required veteran model input files exist."
            if model_input_path is not None
            else "Required veteran model input files are missing.",
        ),
        _step(
            "data_pack_build",
            "planned",
            False,
            data_pack_dir,
            "",
            "Would build a new candidate data pack. Dry run does not write files.",
        ),
        _step("validate_pack", "planned", False, data_pack_dir, "", "Would validate pack."),
        _step(
            "readiness_result",
            "planned",
            False,
            data_pack_dir,
            "",
            "Would report health/admission readiness after validation.",
        ),
    ]


def _scoreable_model_input_dir(path: str | Path) -> Path | None:
    root = Path(path)
    if all((root / file_name).exists() for file_name in VETERAN_SOURCE_TABLES):
        return root
    return None


def _protected_output_reason(path: Path) -> str:
    lower_parts = {part.lower() for part in path.parts}
    if lower_parts & PROTECTED_OUTPUT_MARKERS:
        return (
            "Routine refresh cannot write into final/frozen/freeze folders. "
            "Choose a candidate data-pack output root."
        )
    return ""


def _pack_name(league_id: str, run_id: str) -> str:
    return f"{_slug(league_id)}_{_slug(run_id)}_routine_refresh"


def _run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _slug(value: str) -> str:
    return "".join(
        character.lower() if character.isalnum() else "_"
        for character in value
    ).strip("_")


def _step(
    step: str,
    status: str,
    mutated: bool,
    output_path: str | Path | None,
    rows: int | str | None,
    message: str,
) -> RoutineRefreshStep:
    return RoutineRefreshStep(
        step=step,
        status=status,
        mutated=mutated,
        output_path=str(output_path or ""),
        rows="" if rows is None else rows,
        message=message,
    )


def _result(
    run_id: str,
    dry_run: bool,
    status: str,
    readiness: str,
    candidate_pack: Path | None,
    steps: list[RoutineRefreshStep],
    warnings: list[str],
) -> RoutineRefreshResult:
    return RoutineRefreshResult(
        run_id=run_id,
        dry_run=dry_run,
        status=status,
        readiness=readiness,
        active_candidate_pack=candidate_pack,
        steps=tuple(steps),
        warnings=tuple(warnings),
        health=None,
        admission=None,
        data_pack_result=None,
    )
