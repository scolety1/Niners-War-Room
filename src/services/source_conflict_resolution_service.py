"""Source conflict resolution (directive section 20).

Structured handling for when two sources disagree about the same fact
(e.g. Source A says a player is active, Source B says IR). The AI layer
never silently picks a winner here -- `resolve_source_conflict` returns an
explicit status (CONFIRMED / PROVISIONAL / CONFLICTED / STALE / UNKNOWN)
and a `resolved_value` that is populated ONLY for CONFIRMED/PROVISIONAL/
STALE. A CONFLICTED or UNKNOWN result always carries `resolved_value =
None` -- the caller (a decision engine, per the directive) is the one
that decides whether to block or discount an uncertain fact, per its own
explicit policy; this module never fabricates a resolution to avoid
surfacing the disagreement.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

CONFIRMED = "CONFIRMED"
PROVISIONAL = "PROVISIONAL"
CONFLICTED = "CONFLICTED"
STALE = "STALE"
UNKNOWN = "UNKNOWN"
CONFLICT_STATUSES = frozenset({CONFIRMED, PROVISIONAL, CONFLICTED, STALE, UNKNOWN})

# e.g. the platform of record (Sleeper roster status, NFL injury report).
HIGH_AUTHORITY = "HIGH_AUTHORITY"
MEDIUM_AUTHORITY = "MEDIUM_AUTHORITY"  # e.g. a licensed aggregator (FantasyPros consensus)
LOW_AUTHORITY = "LOW_AUTHORITY"  # e.g. an unverified news scout event
AUTHORITY_TYPES = frozenset({HIGH_AUTHORITY, MEDIUM_AUTHORITY, LOW_AUTHORITY})

DEFAULT_STALE_AFTER_HOURS = 72.0


class SourceConflictError(ValueError):
    pass


@dataclass(frozen=True)
class SourceObservation:
    source: str
    timestamp_utc: str
    authority_type: str
    confidence: str  # HIGH / MEDIUM / LOW -- the source's own stated confidence
    value: str  # the asserted fact, e.g. "ACTIVE" / "IR" / "QUESTIONABLE"

    def __post_init__(self) -> None:
        if self.authority_type not in AUTHORITY_TYPES:
            raise SourceConflictError(f"Unknown authority_type: {self.authority_type!r}")


@dataclass(frozen=True)
class ConflictResolution:
    status: str
    resolved_value: str | None
    observations: tuple[SourceObservation, ...]
    note: str

    def __post_init__(self) -> None:
        if self.status not in CONFLICT_STATUSES:
            raise SourceConflictError(f"Unknown status: {self.status!r}")
        if self.status in (CONFLICTED, UNKNOWN) and self.resolved_value is not None:
            raise SourceConflictError(
                f"{self.status} must never carry a resolved_value -- "
                "the AI layer does not silently choose a winner."
            )
        if self.status in (CONFIRMED, PROVISIONAL, STALE) and self.resolved_value is None:
            raise SourceConflictError(f"{self.status} requires a resolved_value.")


def _hours_since(timestamp_utc: str, now: datetime) -> float | None:
    try:
        observed = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
    except ValueError:
        return None
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=UTC)
    return (now - observed).total_seconds() / 3600.0


def resolve_source_conflict(
    observations: Sequence[SourceObservation],
    *,
    now_utc: str | None = None,
    stale_after_hours: float = DEFAULT_STALE_AFTER_HOURS,
) -> ConflictResolution:
    """The single entry point. `now_utc` defaults to the real current time
    (UTC) when omitted -- pass it explicitly for a deterministic,
    reproducible resolution (e.g. in a historical replay)."""
    if not observations:
        return ConflictResolution(
            status=UNKNOWN, resolved_value=None, observations=(),
            note="No observations supplied.",
        )
    now = (
        datetime.fromisoformat(now_utc.replace("Z", "+00:00")).astimezone(UTC)
        if now_utc is not None
        else datetime.now(UTC)
    )
    ordered = sorted(observations, key=lambda o: o.timestamp_utc)
    ages = {obs: _hours_since(obs.timestamp_utc, now) for obs in ordered}
    fresh = [obs for obs in ordered if (ages[obs] is None) or (ages[obs] <= stale_after_hours)]

    if not fresh:
        latest = ordered[-1]
        return ConflictResolution(
            status=STALE, resolved_value=latest.value, observations=tuple(ordered),
            note=(
                f"Newest observation ({latest.source}, {latest.timestamp_utc}) is older than "
                f"the {stale_after_hours}h freshness window; using it as the last-known value, "
                "not a current confirmed fact."
            ),
        )

    distinct_values = {obs.value for obs in fresh}
    if len(distinct_values) > 1:
        return ConflictResolution(
            status=CONFLICTED, resolved_value=None, observations=tuple(ordered),
            note=(
                "Fresh sources disagree: "
                + "; ".join(f"{obs.source}={obs.value!r}" for obs in fresh)
                + ". Not resolved automatically -- the calling decision engine must "
                "apply its own explicit policy (block or discount)."
            ),
        )

    resolved_value = fresh[0].value
    has_high_authority = any(obs.authority_type == HIGH_AUTHORITY for obs in fresh)
    status = CONFIRMED if has_high_authority else PROVISIONAL
    authority_note = (
        " (includes a HIGH_AUTHORITY source)."
        if has_high_authority
        else " (no HIGH_AUTHORITY source yet)."
    )
    note = f"{len(fresh)} fresh source(s) agree on {resolved_value!r}" + authority_note
    return ConflictResolution(
        status=status, resolved_value=resolved_value, observations=tuple(ordered), note=note,
    )
