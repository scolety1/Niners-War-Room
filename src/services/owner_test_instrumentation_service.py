"""Owner test instrumentation -- local, non-sensitive product diagnostics
(NWR Draft Upgrade HQ, Owner Test Candidate V1, section 15).

Mirrors `nwr_pure_experiment_service.py`'s own append-only JSONL pattern
(the established precedent this codebase already reuses for
`champion_challenger_registry_service.py` and the decision-receipt
writer itself) rather than inventing a new logging mechanism.

Captures ONLY what section 15 names -- DecisionBundle calc latency,
selected/top candidates, score changes, draft-state-change events,
backend errors, and blocked-calc reasons -- never unrelated telemetry.
This is a LOCAL usability/reliability log for the owner test pass, never
a training or scoring signal: nothing in this module reads these events
back to adjust any weight, threshold, or model parameter, and no
function here is imported by any scoring/calibration code.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

INSTRUMENTATION_SCHEMA_VERSION = 1

OWNER_TEST_EVENT_TYPES = frozenset(
    {
        "DECISION_BUNDLE_CALCULATED",
        "DECISION_BUNDLE_BLOCKED",
        "DECISION_BUNDLE_ERROR",
        "DRAFT_STATE_CHANGED",
    }
)

# The exact draft-state-change vocabulary section 16's acceptance tests
# name (owner pick, correction, Catch-Up, Sleeper sync) plus the CPU
# picks that already happen alongside them in FAST/MOCK auto-advance.
DRAFT_STATE_CHANGE_KINDS = frozenset(
    {
        "OWNER_PICK",
        "CPU_PICK",
        "CORRECTION_REPLACE",
        "CORRECTION_CLEAR",
        "CORRECTION_FILL_GAP",
        "CORRECTION_UNDO",
        "CATCH_UP_APPLIED",
        "SLEEPER_SYNC_APPLIED",
    }
)


class OwnerTestInstrumentationError(ValueError):
    pass


@dataclass(frozen=True)
class OwnerTestDiagnosticEvent:
    profile_id: str
    timestamp_utc: str
    event_type: str
    # DECISION_BUNDLE_* fields -- None/() when not applicable to this event_type.
    latency_seconds: float | None = None
    speed: str | None = None
    top_candidate_player_ids: tuple[str, ...] = ()
    selected_player_id: str | None = None
    team_score_before: float | None = None
    championship_equity_before: float | None = None
    blocked_reason: str | None = None
    error_message: str | None = None
    # DRAFT_STATE_CHANGED fields -- None otherwise.
    draft_state_change_kind: str | None = None
    pick_number: int | None = None
    player_id: str | None = None
    schema_version: int = INSTRUMENTATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.event_type not in OWNER_TEST_EVENT_TYPES:
            raise OwnerTestInstrumentationError(f"Unknown event_type: {self.event_type!r}")
        if self.event_type == "DRAFT_STATE_CHANGED" and (
            self.draft_state_change_kind not in DRAFT_STATE_CHANGE_KINDS
        ):
            raise OwnerTestInstrumentationError(
                f"DRAFT_STATE_CHANGED requires draft_state_change_kind to be one of "
                f"{sorted(DRAFT_STATE_CHANGE_KINDS)}, got {self.draft_state_change_kind!r}"
            )


def _events_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "owner_test_instrumentation" / profile_id / "events.jsonl"


def append_owner_test_event(root: str | Path, event: OwnerTestDiagnosticEvent) -> None:
    """Append-only local write. Callers that treat instrumentation as
    best-effort (never allowed to block a real draft-state mutation)
    should catch any exception this raises -- see
    DesktopBackendFacade's own call sites, which wrap every call here in
    a narrow try/except for exactly that reason."""
    path = _events_path(root, event.profile_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), sort_keys=True, separators=(",", ":")) + "\n")


def read_owner_test_events(root: str | Path, profile_id: str) -> list[dict[str, Any]]:
    path = _events_path(root, profile_id)
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def build_decision_bundle_diagnostic_event(
    *,
    profile_id: str,
    timestamp_utc: str,
    speed: str,
    bundle_available: bool,
    latency_seconds: float | None = None,
    top_candidate_player_ids: tuple[str, ...] = (),
    selected_player_id: str | None = None,
    team_score_before: float | None = None,
    championship_equity_before: float | None = None,
    blocked_reason: str | None = None,
    error_message: str | None = None,
) -> OwnerTestDiagnosticEvent:
    """Builds the right event shape from a real redraft_decision_bundle()
    call outcome -- the caller passes only real, already-computed values
    (or None), never a fabricated placeholder for a field it doesn't
    have."""
    if error_message is not None:
        return OwnerTestDiagnosticEvent(
            profile_id=profile_id, timestamp_utc=timestamp_utc,
            event_type="DECISION_BUNDLE_ERROR", speed=speed, error_message=error_message,
        )
    if not bundle_available:
        return OwnerTestDiagnosticEvent(
            profile_id=profile_id, timestamp_utc=timestamp_utc,
            event_type="DECISION_BUNDLE_BLOCKED", speed=speed, blocked_reason=blocked_reason,
        )
    return OwnerTestDiagnosticEvent(
        profile_id=profile_id, timestamp_utc=timestamp_utc,
        event_type="DECISION_BUNDLE_CALCULATED", speed=speed,
        latency_seconds=latency_seconds,
        top_candidate_player_ids=top_candidate_player_ids,
        selected_player_id=selected_player_id,
        team_score_before=team_score_before,
        championship_equity_before=championship_equity_before,
    )


def build_draft_state_change_event(
    *,
    profile_id: str,
    timestamp_utc: str,
    change_kind: str,
    pick_number: int | None = None,
    player_id: str | None = None,
) -> OwnerTestDiagnosticEvent:
    return OwnerTestDiagnosticEvent(
        profile_id=profile_id, timestamp_utc=timestamp_utc,
        event_type="DRAFT_STATE_CHANGED", draft_state_change_kind=change_kind,
        pick_number=pick_number, player_id=player_id,
    )
