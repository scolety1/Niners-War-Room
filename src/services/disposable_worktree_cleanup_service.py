"""Fail-closed safety assessment for NWR disposable worktree cleanup."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

PROTECTED_WORKTREES = (
    Path(r"C:\NWR\Niners-War-Room-V1"),
    Path(r"C:\NWR\Niners-War-Room"),
)
KNOWN_GENERATED_PATHS = {
    "docs/model_v4/DRAFTABLE_POOL_SOURCE_READINESS_20260609.md",
    "docs/model_v4/DRAFT_PREP_CURRENT_STATE_AUDIT_20260609.md",
    "docs/model_v4/DRAFT_PREP_PAGE_ARCHITECTURE_20260609.md",
    "docs/model_v4/PRIOR_DRAFT_HISTORY_NORMALIZATION_20260609.md",
    "docs/model_v4/PRIOR_LEAGUE_DRAFT_BEHAVIOR_SUMMARY_20260609.md",
    "uv.lock",
}
SOURCE_SUFFIXES = {".py", ".ps1", ".js", ".ts", ".tsx", ".jsx", ".sql", ".yaml", ".yml"}


@dataclass(frozen=True)
class CleanupAssessment:
    safe: bool
    verdict: str
    reasons: tuple[str, ...]


def assess_disposable_worktree_cleanup(
    target: str | Path,
    *,
    registered: bool,
    active_processes: Iterable[int] = (),
    changed_paths: Iterable[str] = (),
    untracked_paths: Iterable[str] = (),
    patch_equivalent_in_hq: bool,
) -> CleanupAssessment:
    path = Path(target)
    reasons: list[str] = []
    if any(_same_path(path, protected) for protected in PROTECTED_WORKTREES):
        reasons.append("Stable and operational worktrees are protected.")
    if not registered:
        reasons.append("Target is not the expected registered worktree.")
    if tuple(active_processes):
        reasons.append("An active process owns the target.")
    all_changes = {str(value).replace("\\", "/") for value in (*changed_paths, *untracked_paths)}
    unique_source = sorted(
        value
        for value in all_changes
        if Path(value).suffix.casefold() in SOURCE_SUFFIXES and value not in KNOWN_GENERATED_PATHS
    )
    unexpected = sorted(all_changes - KNOWN_GENERATED_PATHS)
    if unique_source:
        reasons.append(f"Unique uncommitted source exists: {', '.join(unique_source)}")
    elif unexpected:
        reasons.append(f"Unexpected uncommitted paths exist: {', '.join(unexpected)}")
    if not patch_equivalent_in_hq:
        reasons.append("Canonical adoption is not patch-equivalent in HQ.")
    if reasons:
        return CleanupAssessment(
            False,
            "DISPOSABLE_WORKTREE_PRESERVED_PENDING_OWNER_REVIEW",
            tuple(reasons),
        )
    return CleanupAssessment(True, "SAFE_DISPOSABLE_WORKTREE_REMOVAL_AUTHORIZED", ())


def _same_path(left: Path, right: Path) -> bool:
    return str(left.absolute()).casefold().rstrip("\\/") == str(right.absolute()).casefold().rstrip(
        "\\/"
    )
