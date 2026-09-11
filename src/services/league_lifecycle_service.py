"""League lifecycle resolution (NWR pre-UI architecture pass, 2026-09-10).

ONE authority for whether a league is PRE_DRAFT / LIVE_DRAFT / IN_SEASON /
OFFSEASON. Before this module, no such concept existed anywhere in the
codebase (confirmed by direct search): every in-season page decided what to
show purely from `profile.provider == "sleeper"`, and the league chooser
(`leagues.tsx`) unconditionally navigated every opened league to the Draft
Room regardless of whether that league had already finished drafting.

This is a pure function over data the facade already has (the draft board's
own `configured`/`drafted`/`currentPick` fields, built by the existing
`build_draft_room_payload`) -- it does not call any new API, fetch any new
data, or change how any existing engine computes anything. It is designed to
be reusable, byte-for-byte in spirit, from both the backend (this module)
and the frontend (`league-context.ts`'s `resolveLeagueLifecycle`, which
mirrors this same logic so a routing decision never needs an extra network
round trip).

Real, disclosed limitation: this repository has no live NFL-calendar/season
signal (no wrapper around Sleeper's `GET /v1/state/nfl` or equivalent
exists anywhere in `src/services`, confirmed by search). OFFSEASON is
therefore only reachable via an archived profile, not via calendar
awareness -- a real gap, not silently hidden (see `DATA_AUTHORITY.md`).
"""

from __future__ import annotations

from dataclasses import dataclass

LIFECYCLE_STATES: tuple[str, ...] = ("PRE_DRAFT", "LIVE_DRAFT", "IN_SEASON", "OFFSEASON")


@dataclass(frozen=True)
class LifecycleResolution:
    lifecycle: str
    basis: str


def resolve_league_lifecycle(
    *,
    archived: bool,
    draft_configured: bool,
    drafted_count: int,
    total_draft_picks: int,
    current_pick: int | None,
) -> LifecycleResolution:
    """Resolve one of `LIFECYCLE_STATES` from real, already-computed draft
    board signals. Never guesses from data this repo doesn't have (e.g. no
    calendar/week inference) -- every branch cites the concrete signal it
    used, returned in `basis` for the owner-facing honesty this pass
    requires everywhere else.
    """

    if archived:
        return LifecycleResolution("OFFSEASON", "The league profile is archived.")
    if not draft_configured or drafted_count <= 0:
        return LifecycleResolution(
            "PRE_DRAFT", "No draft board activity has been recorded for this league yet."
        )
    if total_draft_picks > 0 and drafted_count >= total_draft_picks:
        return LifecycleResolution(
            "IN_SEASON",
            f"The draft board shows all {total_draft_picks} of {total_draft_picks} picks recorded.",
        )
    if current_pick is not None:
        return LifecycleResolution(
            "LIVE_DRAFT",
            "The draft board shows an active current-pick pointer and the draft "
            "is not yet complete.",
        )
    return LifecycleResolution(
        "LIVE_DRAFT",
        f"The draft board shows {drafted_count} of {total_draft_picks} picks recorded with no "
        "confirmed completion signal; treated as still in progress rather than assumed complete.",
    )
