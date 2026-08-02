"""Truthful post-release freshness, save-state, and decision follow-up helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from src.services.governed_asset_registry_service import (
    BLOCKED_ROOKIES_SHA256,
    CURRENT_BOARD_SHA256,
    ROOKIE_BOARD_SHA256,
)

SCHEDULED_REFRESH_STATE = "DISABLED_PENDING_OWNER_APPROVAL"
SAVE_STATES = {
    "Saved",
    "Saving",
    "Unsaved changes",
    "Save failed",
    "Read-only",
    "Recovery required",
}


@dataclass(frozen=True)
class SourceFreshness:
    source_name: str
    source_version: str
    snapshot_date: str
    last_verified_date: str
    state: str
    refresh_status: str
    authority: str
    detail: str = ""


@dataclass(frozen=True)
class SaveStatus:
    state: str
    message: str
    result: Any = None

    def __post_init__(self) -> None:
        if self.state not in SAVE_STATES:
            raise ValueError(f"Unsupported save state: {self.state}")


@dataclass(frozen=True)
class FollowupDashboard:
    due_today: tuple[dict[str, Any], ...]
    overdue: tuple[dict[str, Any], ...]
    upcoming: tuple[dict[str, Any], ...]
    recent: tuple[dict[str, Any], ...]
    archived: tuple[dict[str, Any], ...]
    missing_date: tuple[dict[str, Any], ...]


def governed_source_freshness(
    *, repo_root: str | Path | None = None
) -> tuple[SourceFreshness, ...]:
    """Return explicit governed metadata; never derive authority dates from mtimes."""

    _ = repo_root  # Reserved for future manifest validation; mtimes are intentionally unused.
    return (
        SourceFreshness(
            "Finished V1",
            f"sha256:{CURRENT_BOARD_SHA256}",
            "2026-05-05",
            "2026-08-01",
            "STALE",
            "Manual refresh only; scheduled refresh disabled",
            "Production",
            "Snapshot date comes from the governed active-pack identifier, not file metadata.",
        ),
        SourceFreshness(
            "Outcome V3",
            "NWR_OUTCOME_COLUMNS_V3_RC1",
            "2026-07-29",
            "2026-08-01",
            "FROZEN",
            "No automatic refresh",
            "Governed context with blocked fields",
        ),
        SourceFreshness(
            "Model V4 2026 Rookie Review",
            f"sha256:{ROOKIE_BOARD_SHA256}",
            "Not documented",
            "2026-07-30",
            "REVIEW_ONLY",
            "No automatic refresh",
            "Review-Only",
            f"Blocked-rookie receipt sha256:{BLOCKED_ROOKIES_SHA256}",
        ),
        SourceFreshness(
            "Frozen 2026 Draft Context",
            "FINAL_BOARD_V1_20260622",
            "2026-06-22",
            "2026-08-01",
            "FROZEN",
            "No automatic refresh",
            "Frozen context",
        ),
        SourceFreshness(
            "Personal Workspace V1",
            "schema:1",
            "Not applicable",
            "Verified after each atomic write",
            "PERSONAL",
            "User save only",
            "Personal local data",
        ),
    )


def freshness_for_sources(source_names: Iterable[str]) -> tuple[SourceFreshness, ...]:
    wanted = {str(value) for value in source_names}
    return tuple(row for row in governed_source_freshness() if row.source_name in wanted)


def initial_save_status(store_status: str, updated_at_utc: str = "") -> SaveStatus:
    if store_status == "CORRUPT":
        return SaveStatus(
            "Recovery required",
            "Checksum or schema validation failed. Restore or retry explicitly.",
        )
    if store_status == "READ_ONLY":
        return SaveStatus("Read-only", "This workspace cannot accept writes.")
    if store_status == "LOADED":
        detail = (
            f"Last verified write: {updated_at_utc}"
            if updated_at_utc
            else "Verified local data loaded."
        )
        return SaveStatus("Saved", detail)
    return SaveStatus("Unsaved changes", "No local record exists. Nothing is written on page open.")


def perform_workspace_write[T](
    write: Callable[[], T], *, observer: Callable[[SaveStatus], None] | None = None
) -> SaveStatus:
    """Expose truthful state ordering around an owning atomic write."""

    saving = SaveStatus("Saving", "Atomic local write in progress.")
    if observer:
        observer(saving)
    try:
        result = write()
    except Exception as exc:  # The UI must surface the owning failure without false success.
        failed = SaveStatus("Save failed", str(exc))
        if observer:
            observer(failed)
        return failed
    result_status = str(getattr(result, "status", ""))
    if result_status.startswith("BLOCKED"):
        blocked = SaveStatus(
            "Unsaved changes",
            str(getattr(result, "message", "")) or f"Write blocked: {result_status}",
            result,
        )
        if observer:
            observer(blocked)
        return blocked
    saved = SaveStatus("Saved", "Atomic write and checksum verification completed.", result)
    if observer:
        observer(saved)
    return saved


def build_followup_dashboard(
    decisions: Iterable[Mapping[str, Any]],
    *,
    today: date | None = None,
    statuses: Iterable[str] | None = None,
    decision_types: Iterable[str] | None = None,
    asset_query: str = "",
    team_windows: Iterable[str] | None = None,
) -> FollowupDashboard:
    current = today or datetime.now(UTC).date()
    status_set = set(statuses or ())
    type_set = set(decision_types or ())
    team_set = set(team_windows or ())
    needle = asset_query.casefold().strip()
    rows = []
    for raw in decisions:
        row = dict(raw)
        if status_set and row.get("status") not in status_set:
            continue
        if type_set and row.get("decision_type") not in type_set:
            continue
        if team_set and row.get("team_window") not in team_set:
            continue
        if needle and needle not in " ".join(map(str, row.get("assets", ()))).casefold():
            continue
        rows.append(row)

    def created_key(row: Mapping[str, Any]) -> str:
        return str(row.get("created_at_utc", ""))

    active = [row for row in rows if row.get("status") != "Archived"]
    archived = sorted(
        (row for row in rows if row.get("status") == "Archived"), key=created_key, reverse=True
    )
    dated: list[tuple[date, dict[str, Any]]] = []
    missing: list[dict[str, Any]] = []
    for row in active:
        raw_date = str(row.get("follow_up_date", "")).strip()
        if not raw_date:
            missing.append(row)
            continue
        try:
            dated.append((date.fromisoformat(raw_date), row))
        except ValueError:
            missing.append(row)
    due = [row for when, row in dated if when == current]
    overdue = [row for when, row in dated if when < current]
    upcoming = [row for when, row in dated if when > current]
    return FollowupDashboard(
        tuple(sorted(due, key=created_key, reverse=True)),
        tuple(sorted(overdue, key=lambda row: str(row.get("follow_up_date", "")))),
        tuple(sorted(upcoming, key=lambda row: str(row.get("follow_up_date", "")))),
        tuple(sorted(active, key=created_key, reverse=True)[:10]),
        tuple(archived),
        tuple(sorted(missing, key=created_key, reverse=True)),
    )
