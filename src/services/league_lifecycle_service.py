"""League lifecycle resolution (NWR pre-UI architecture pass, 2026-09-10;
provider-evidence fix, dogfood v1 Worker 2, 2026-09-17).

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

2026-09-17 fix (owner report: a league with a real completed draft showed
PRE_DRAFT/"Draft Board Ready"): the original version above derived lifecycle
ONLY from local draft-board pick counts. Two real, distinct provider-evidence
gaps were found against real recovered league data (KHA High Stakes, 403 N
18th and friends -- both real, complete ESPN-imported drafts; Fantasy
Gamers -- a real Sleeper league drafted on Sleeper itself, never inside this
app's own Draft Room):

  1. A league whose real draft happened entirely on the provider's own
     platform (e.g. Sleeper) never has ANY local draft-board activity here,
     so it fell into the very first PRE_DRAFT branch forever, even deep
     in-season with real standings/matchups. Sleeper's own `GET
     /league/{id}` response already carries a real, provider-native
     `status` field (`pre_draft` / `drafting` / `in_season` / `complete`)
     that `desktop_facade.py` already fetches for the playoff-context read
     (`sleeper_league_context_service.build_playoff_context`'s
     `leagueStatus`) -- it was simply never plumbed into lifecycle
     resolution. `provider_status` below is that real, already-fetched
     value, now used as the authoritative signal whenever it is available
     (it can only ever be more informed than a local pick count, since it
     comes directly from the platform that ran the real draft).
  2. A real, complete, one-time ESPN-imported draft can legitimately finish
     with fewer local picks than `team_count * draft.rounds` (K/DST rounds
     are commonly resolved outside the live pick stream for these
     `practical_mode` leagues -- see NWR_OWNER_MOCK_QA_V1 -- and real draft
     nights can end with a slightly asymmetric final round). This app has
     no live re-sync path for ESPN at all (confirmed by search: no ESPN
     service exists anywhere in `src/services`, `provider_league_id` is
     always `null` for these profiles) -- once such a draft has recorded
     REAL, SUBSTANTIAL completion evidence (see the 2026-09-18 fix below)
     and gone quiet for longer than any realistic single draft session, no
     further picks are ever coming, so it is treated as the final state of
     a completed draft instead of being stuck in LIVE_DRAFT indefinitely.
     `draft_last_activity_utc` + `live_sync_capable` below implement this,
     gated so a genuinely still-live, actively-being-recorded draft (very
     recent activity) is correctly left as LIVE_DRAFT.

2026-09-18 fix (NWR Sunday Readiness overnight cycle, Worker 4, brief
finding D2): the staleness fallback above originally fired for ANY
`drafted_count >= 1`, so a genuinely still-open, barely-started draft
(e.g. one real pick, then 24+ quiet hours) would be wrongly declared
complete -- age alone was never completion evidence, it only ever meant
"no new pick has landed recently." Real KHA High Stakes (157 of a
configured 192) and 403 N 18th and friends (118 of a configured 128) --
the two real leagues this exact fallback exists for -- both already clear
a large majority of their configured pick count (81.8% and 92.2%
respectively), so requiring a real minimum completion ratio alongside
staleness closes the "just one pick" gap without touching either real
league's own correct resolution. `STALE_DRAFT_MIN_COMPLETION_RATIO` below
is that real, disclosed, still-heuristic bound (not a claim of certainty
-- ESPN genuinely offers no better provider-native completion signal in
this codebase, confirmed by search: no ESPN client exists anywhere in
`src/services`) -- chosen conservatively below both real leagues' own
ratios so neither regresses, while a single- or few-pick draft going
stale no longer silently resolves as done.

Neither fix manufactures picks or hardcodes any league to IN_SEASON: a
genuinely PRE_DRAFT league (no provider status, no local picks) still
resolves PRE_DRAFT, and a genuinely fresh/active LIVE_DRAFT (whether
because it is recent, or because it is stale but still barely started)
still resolves LIVE_DRAFT.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

LIFECYCLE_STATES: tuple[str, ...] = ("PRE_DRAFT", "LIVE_DRAFT", "IN_SEASON", "OFFSEASON")

# Sleeper's own real `league.status` values (https://docs.sleeper.com),
# each mapped to the one LIFECYCLE_STATES entry describing the same real
# state. Unknown/absent values simply fall through to the local
# draft-board-derived logic below -- never a hard failure.
_PROVIDER_STATUS_LIFECYCLE: dict[str, str] = {
    "pre_draft": "PRE_DRAFT",
    "drafting": "LIVE_DRAFT",
    "in_season": "IN_SEASON",
    "complete": "OFFSEASON",
}

# No realistic single real fantasy draft session runs anywhere near this
# long. A provider with no live re-sync path (see module docstring, fix 2)
# whose draft board has gone quiet for at least this long, AND has cleared
# STALE_DRAFT_MIN_COMPLETION_RATIO of its configured picks (see below), is
# being read as a finished historical import, not an active draft.
STALE_DRAFT_THRESHOLD = timedelta(hours=24)

# 2026-09-18 fix (D2): age alone is not completion evidence -- a draft that
# genuinely stalled after only a handful of picks must not be declared
# complete just because nobody touched it for a day. Real KHA (157/192 =
# 81.8%) and real 403 N 18th (118/128 = 92.2%) -- the two real leagues this
# fallback exists to resolve -- both clear this bound comfortably; a
# synthetic "just one pick" draft (well under 1%) does not, and correctly
# stays LIVE_DRAFT even once stale.
STALE_DRAFT_MIN_COMPLETION_RATIO = 0.5


@dataclass(frozen=True)
class LifecycleResolution:
    lifecycle: str
    basis: str


def _staleness(last_activity_utc: str, now_utc: datetime | None) -> timedelta | None:
    try:
        parsed = datetime.fromisoformat(last_activity_utc.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    now = now_utc if now_utc is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now - parsed


def resolve_league_lifecycle(
    *,
    archived: bool,
    draft_configured: bool,
    drafted_count: int,
    total_draft_picks: int,
    current_pick: int | None,
    provider_status: str | None = None,
    live_sync_capable: bool = False,
    draft_last_activity_utc: str | None = None,
    now_utc: datetime | None = None,
) -> LifecycleResolution:
    """Resolve one of `LIFECYCLE_STATES` from real, already-computed draft
    board signals -- and, when available, real provider-native evidence that
    is strictly more informed than a local pick count. Never guesses from
    data this repo doesn't have (e.g. no calendar/week inference) -- every
    branch cites the concrete signal it used, returned in `basis` for the
    owner-facing honesty this pass requires everywhere else.

    `provider_status`: a raw provider-native league status string (e.g.
    Sleeper's `league.status`), when the caller already has one. Takes
    priority over local draft-board signals when recognized, since it can
    reflect a real draft that happened entirely outside this app.

    `live_sync_capable`: True only when this profile's provider can still
    receive new picks through this app going forward (Sleeper with a real
    `provider_league_id`, as of this repo). False for a one-time historical
    import (e.g. ESPN) with no live re-sync path.

    `draft_last_activity_utc` / `now_utc`: the draft board's own real last-
    updated timestamp, and (for tests) an injectable "now". Only consulted
    when `live_sync_capable` is False, the exact-count completion check
    above did not already resolve IN_SEASON, and `drafted_count` has
    already reached `STALE_DRAFT_MIN_COMPLETION_RATIO` of `total_draft_
    picks` -- age alone is never sufficient; see the 2026-09-18 fix (D2)
    in the module docstring.
    """

    if archived:
        return LifecycleResolution("OFFSEASON", "The league profile is archived.")

    normalized_status = (provider_status or "").strip().lower()
    if normalized_status in _PROVIDER_STATUS_LIFECYCLE:
        return LifecycleResolution(
            _PROVIDER_STATUS_LIFECYCLE[normalized_status],
            f"The league provider reports real league status '{normalized_status}', which "
            "takes priority over local draft-board activity (the real draft may have "
            "happened entirely on the provider's own platform, never inside this app).",
        )

    if not draft_configured or drafted_count <= 0:
        return LifecycleResolution(
            "PRE_DRAFT", "No draft board activity has been recorded for this league yet."
        )
    if total_draft_picks > 0 and drafted_count >= total_draft_picks:
        return LifecycleResolution(
            "IN_SEASON",
            f"The draft board shows all {total_draft_picks} of {total_draft_picks} picks recorded.",
        )
    if not live_sync_capable and draft_last_activity_utc and total_draft_picks > 0:
        completion_ratio = drafted_count / total_draft_picks
        if completion_ratio >= STALE_DRAFT_MIN_COMPLETION_RATIO:
            staleness = _staleness(draft_last_activity_utc, now_utc)
            if staleness is not None and staleness >= STALE_DRAFT_THRESHOLD:
                return LifecycleResolution(
                    "IN_SEASON",
                    f"The draft board shows {drafted_count} of {total_draft_picks} picks "
                    f"recorded ({completion_ratio:.0%}, at least "
                    f"{STALE_DRAFT_MIN_COMPLETION_RATIO:.0%} of the configured draft), this "
                    "league's provider has no live draft-sync path in this app, and no new "
                    f"pick has been recorded since {draft_last_activity_utc}; treated as the "
                    "final state of a completed draft (e.g. K/DST rounds resolved outside the "
                    "live pick stream) rather than still in progress.",
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
