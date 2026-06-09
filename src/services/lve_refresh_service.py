from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.services.lve_rank_merge_service import (
    RANK_PROVENANCE,
    RankMergeResult,
    merge_lve_roster_ranks,
)
from src.services.sleeper_import_service import (
    DEFAULT_LEAGUE_ID,
    SleeperHttpClient,
    SleeperSnapshotResult,
    export_sleeper_snapshot,
)

DEFAULT_RANK_TEXT_PATH = Path("local_exports/pdf_extracts/LVE_Rosters_033126_2.txt")
DEFAULT_SLEEPER_OUTPUT_ROOT = Path("local_exports/sleeper")
DEFAULT_MERGED_OUTPUT_ROOT = Path("local_exports/merged")


@dataclass(frozen=True)
class RefreshStep:
    step_name: str
    status: str
    output_path: Path | None
    row_count: int | None
    message: str


@dataclass(frozen=True)
class RefreshWorkflowResult:
    league_id: str
    generated_at: str
    sleeper_result: SleeperSnapshotResult | None
    rank_merge_result: RankMergeResult | None
    steps: tuple[RefreshStep, ...]
    warnings: tuple[str, ...]


def run_sleeper_refresh(
    *,
    league_id: str = DEFAULT_LEAGUE_ID,
    output_root: str | Path = DEFAULT_SLEEPER_OUTPUT_ROOT,
    client: SleeperHttpClient | None = None,
    snapshot_name: str | None = None,
) -> SleeperSnapshotResult:
    return export_sleeper_snapshot(
        league_id=league_id,
        output_root=output_root,
        client=client,
        snapshot_name=snapshot_name,
    )


def run_rank_merge_for_snapshot(
    *,
    sleeper_output_dir: str | Path,
    rank_text_path: str | Path = DEFAULT_RANK_TEXT_PATH,
    output_root: str | Path = DEFAULT_MERGED_OUTPUT_ROOT,
) -> RankMergeResult:
    snapshot_dir = Path(sleeper_output_dir)
    rosters_csv = snapshot_dir / "sleeper_rosters.csv"
    output_dir = Path(output_root) / f"{snapshot_dir.name}_pdf_ranks"
    return merge_lve_roster_ranks(
        sleeper_rosters_csv=rosters_csv,
        rank_text_path=rank_text_path,
        output_dir=output_dir,
    )


def run_full_refresh(
    *,
    league_id: str = DEFAULT_LEAGUE_ID,
    rank_text_path: str | Path = DEFAULT_RANK_TEXT_PATH,
    sleeper_output_root: str | Path = DEFAULT_SLEEPER_OUTPUT_ROOT,
    merged_output_root: str | Path = DEFAULT_MERGED_OUTPUT_ROOT,
    client: SleeperHttpClient | None = None,
    snapshot_name: str | None = None,
) -> RefreshWorkflowResult:
    steps: list[RefreshStep] = []
    warnings = _static_refresh_warnings(rank_text_path)
    sleeper_result: SleeperSnapshotResult | None = None
    rank_result: RankMergeResult | None = None

    try:
        sleeper_result = run_sleeper_refresh(
            league_id=league_id,
            output_root=sleeper_output_root,
            client=client,
            snapshot_name=snapshot_name,
        )
        steps.extend(_steps_from_sleeper(sleeper_result))
    except Exception as exc:
        steps.append(
            RefreshStep(
                step_name="sleeper_snapshot",
                status="error",
                output_path=None,
                row_count=None,
                message=f"Sleeper snapshot failed: {exc}",
            )
        )
        return _workflow_result(league_id, sleeper_result, rank_result, steps, warnings)

    rank_path = Path(rank_text_path)
    if not rank_path.exists():
        steps.append(
            RefreshStep(
                step_name="league_rank_merge",
                status="skipped",
                output_path=None,
                row_count=None,
                message="Rank merge skipped because the local PDF text file is missing.",
            )
        )
        return _workflow_result(league_id, sleeper_result, rank_result, steps, warnings)

    try:
        rank_result = run_rank_merge_for_snapshot(
            sleeper_output_dir=sleeper_result.output_dir,
            rank_text_path=rank_path,
            output_root=merged_output_root,
        )
        steps.extend(_steps_from_rank_merge(rank_result))
    except Exception as exc:
        steps.append(
            RefreshStep(
                step_name="league_rank_merge",
                status="error",
                output_path=None,
                row_count=None,
                message=f"League-rank merge failed: {exc}",
            )
        )

    return _workflow_result(league_id, sleeper_result, rank_result, steps, warnings)


def find_latest_sleeper_snapshot(
    *,
    league_id: str = DEFAULT_LEAGUE_ID,
    output_root: str | Path = DEFAULT_SLEEPER_OUTPUT_ROOT,
) -> Path | None:
    root = Path(output_root)
    if not root.exists():
        return None
    candidates = [
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name.startswith(f"{league_id}_")
        and (path / "sleeper_rosters.csv").exists()
    ]
    return max(candidates, key=lambda path: path.name) if candidates else None


def refresh_status_rows(result: RefreshWorkflowResult) -> list[dict[str, object]]:
    return [
        {
            "step": step.step_name,
            "status": step.status,
            "rows": step.row_count if step.row_count is not None else "",
            "output_path": str(step.output_path) if step.output_path else "",
            "message": step.message,
        }
        for step in result.steps
    ]


def _steps_from_sleeper(result: SleeperSnapshotResult) -> list[RefreshStep]:
    return [
        RefreshStep(
            step_name=f"sleeper_{name}",
            status="ok",
            output_path=path,
            row_count=result.counts.get(name, 0),
            message="Local Sleeper snapshot file refreshed.",
        )
        for name, path in result.files.items()
    ]


def _steps_from_rank_merge(result: RankMergeResult) -> list[RefreshStep]:
    return [
        RefreshStep(
            step_name=f"league_rank_{name}",
            status="ok",
            output_path=path,
            row_count=result.counts.get(name, 0),
            message="League-rank merge output refreshed.",
        )
        for name, path in result.files.items()
    ]


def _workflow_result(
    league_id: str,
    sleeper_result: SleeperSnapshotResult | None,
    rank_result: RankMergeResult | None,
    steps: list[RefreshStep],
    warnings: list[str],
) -> RefreshWorkflowResult:
    return RefreshWorkflowResult(
        league_id=league_id,
        generated_at=datetime.now(UTC).isoformat(),
        sleeper_result=sleeper_result,
        rank_merge_result=rank_result,
        steps=tuple(steps),
        warnings=tuple(warnings),
    )


def _static_refresh_warnings(rank_text_path: str | Path) -> list[str]:
    warnings = [
        (
            "League rank is a summer/declaration input only. Sleeper roster and pick "
            "state remain the current ownership truth."
        ),
        f"League-rank provenance for this PDF text is {RANK_PROVENANCE}.",
    ]
    if not Path(rank_text_path).exists():
        warnings.append(f"League-rank text file is missing: {rank_text_path}")
    return warnings
