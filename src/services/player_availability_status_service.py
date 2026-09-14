"""PlayerAvailabilityStatus authority (NWR pre-UI architecture pass, 2026-09-10).

Directive section 5: a canonical, BROAD current-player-status authority,
kept DISTINCT from `current_player_status_overrides_service.StatusOverride`
(the manual, individually-sourced, verified-override MECHANISM) and from
any `PlayerNewsItem` concept.

Real finding from this pass's own research (grep across the entire repo):
there is no live/automated in-season injury-news ingestion system anywhere
in this codebase. Every "injury"-named module under `src/services`
(`injury_availability_context_service.py`, `injury_context_flags_service.py`,
`injury_context_source_gate_service.py`, `rotowire_local_team_status_
service.py`) reads a STATIC, historical, offline CSV export used for
model-training/backtest context -- none of them is a live feed. The ONLY
real, current-season status source this app has is the manual override
mechanism above.

This module is therefore an honest WRAPPER, not a new data source: it
reads the same overrides and re-expresses them in the broader schema the
directive asks for (injury designation, practice state, IR/PUP/NFI,
suspension, administrative/exempt, released, current team, source,
freshness) -- leaving every field the manual overrides don't actually
cover as `None`, never fabricated. `DATA_AUTHORITY.md` discloses this gap
explicitly. If a real live feed is ever added, it plugs in here (a second
source composed into `load_player_availability_statuses`) without any
consumer needing to change -- the same "wrap, don't fork" instruction this
whole pass follows for `current_player_status_overrides_service.py`.

--- Work Unit 4 (Live Player Intelligence V1, 2026-09-13/14) --------------

EXTENDS this same `PlayerAvailabilityStatus` shape (does not fork a
parallel dataclass/schema) with the normalized FACTUAL fields a future
automated source (e.g. the shadow-only nflverse/Sleeper candidates
characterized under `docs/codex/live_player_intelligence_v1/`) would need
to populate, per Gate 1 of `LIVE_PLAYER_INTELLIGENCE_ADMISSION_CONTRACT.md`
("a field NWR cannot currently populate from any admitted source must
render as absent/unknown, never defaulted to a guessed, healthy, or
otherwise assumed value"). Every new field below defaults to `None`
(unknown) and today's ONLY real source -- the manual override wrapper
above -- leaves every one of them `None`, exactly as before this pass:
this is a pure additive schema change, not a behavior change. Nothing
here is wired to any automated source yet; that is a later, separate
promotion decision (see the admission contract and
`docs/codex/live_player_intelligence_v1/SOURCE_QUALITY_EVALUATION_V1.md`).

New fields, and why each is distinct from what already existed:
  * `game_status` -- the actual game-day inactive/active-for-this-game
    determination (Gate 5's separate, tighter "game-day inactive
    authority" 10-minute freshness bar). Deliberately kept SEPARATE from
    `injury_designation`, which is the ordinary weekly practice-report
    designation (Out/Doubtful/Questionable) -- Gate 5 evaluates these two
    use cases independently, so the schema does not conflate them.
  * `on_injured_reserve` / `on_pup` / `on_nfi` -- distinct boolean facts,
    broken out from the existing combined `ir_pup_nfi` free-text field
    (kept unchanged, still populated exactly as before) so a consumer can
    check one specific list membership without parsing a string.
  * `active_inactive` -- a roster active/inactive read, populated ONLY
    when a source is authoritative for it (Gate 1's per-field discipline).
  * `depth_chart_position` / `depth_chart_context` -- role/depth-chart
    signal (e.g. nflverse depth charts' `pos_rank`), a genuinely different
    concept from an injury designation.
  * `fetched_at` -- when NWR itself retrieved the value (Gate 1).
  * `freshness_seconds` -- the freshness figure Gate 1 requires, derived
    from `source_as_of` and `fetched_at` via `compute_freshness_seconds`
    below; `None` (not a guess) whenever either timestamp is missing or
    unparseable.

Explicitly and deliberately OUT of this factual schema (a different,
not-yet-built concern per this pass's own directive): news prose, analyst
commentary, projected return date, role speculation. None of those
concepts has a field here, and none should be added to this dataclass
without a separate, deliberate design pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.services.current_player_status_overrides_service import (
    StatusOverride,
    load_status_overrides,
)

# Only SEASON_OUT maps to a real, disclosed injury designation ("OUT" --
# the override kind literally means season-ending). The other three kinds
# are not injuries and must never be relabeled as one.
_KIND_TO_STATUS_CATEGORY: dict[str, str] = {
    "SEASON_OUT": "OUT_FOR_SEASON",
    "NOT_WITH_TEAM": "NOT_WITH_TEAM",
    "ADMINISTRATIVE_EXEMPT": "ADMINISTRATIVE_EXEMPT",
    "TEAM_CORRECTION": "TEAM_CORRECTION",
}

AUTHORITY_LABEL = (
    "current_player_status_overrides_service (manual, individually-sourced, "
    "verified overrides -- no automated injury/news feed exists in this repository)"
)


@dataclass(frozen=True)
class PlayerAvailabilityStatus:
    player_id: str
    player_name: str
    status_category: str
    injury_designation: str | None
    practice_state: str | None
    ir_pup_nfi: str | None
    suspension: bool
    administrative_exempt: bool
    released: bool
    current_team: str | None
    reason: str
    source: str
    source_as_of: str
    override_kind: str
    # --- Work Unit 4 additive normalized factual fields (see module
    # docstring). All default to None -- "unknown", never guessed -- and
    # today's only real source (the manual-override wrapper) leaves every
    # one of them None, unchanged from before this pass.
    game_status: str | None = None
    on_injured_reserve: bool | None = None
    on_pup: bool | None = None
    on_nfi: bool | None = None
    active_inactive: str | None = None
    depth_chart_position: str | None = None
    depth_chart_context: str | None = None
    fetched_at: str | None = None
    freshness_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "playerId": self.player_id,
            "playerName": self.player_name,
            "statusCategory": self.status_category,
            "injuryDesignation": self.injury_designation,
            "practiceState": self.practice_state,
            "irPupNfi": self.ir_pup_nfi,
            "suspension": self.suspension,
            "administrativeExempt": self.administrative_exempt,
            "released": self.released,
            "currentTeam": self.current_team,
            "reason": self.reason,
            "source": self.source,
            "sourceAsOf": self.source_as_of,
            "overrideKind": self.override_kind,
            "gameStatus": self.game_status,
            "onInjuredReserve": self.on_injured_reserve,
            "onPup": self.on_pup,
            "onNfi": self.on_nfi,
            "activeInactive": self.active_inactive,
            "depthChartPosition": self.depth_chart_position,
            "depthChartContext": self.depth_chart_context,
            "fetchedAt": self.fetched_at,
            "freshnessSeconds": self.freshness_seconds,
        }


def compute_freshness_seconds(source_as_of_iso: str | None, fetched_at_iso: str | None) -> float | None:
    """Gate 1's 'freshness figure derivable from the two timestamps'.
    Pure, no I/O. Returns `None` (never a guess) whenever either timestamp
    is missing, empty, or not a real parseable ISO-8601 timestamp -- e.g.
    a week-granularity label like `2026-REG-week1` (nflverse injuries'
    real `source_as_of` shape) is honestly NOT a timestamp and must not be
    silently treated as one."""

    if not source_as_of_iso or not fetched_at_iso:
        return None
    try:
        source_dt = datetime.fromisoformat(str(source_as_of_iso).replace("Z", "+00:00"))
        fetched_dt = datetime.fromisoformat(str(fetched_at_iso).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (fetched_dt - source_dt).total_seconds()


def _from_override(override: StatusOverride) -> PlayerAvailabilityStatus:
    category = _KIND_TO_STATUS_CATEGORY.get(override.kind, override.kind)
    return PlayerAvailabilityStatus(
        player_id=override.player_id,
        player_name=override.player_name,
        status_category=category,
        injury_designation="OUT" if override.kind == "SEASON_OUT" else None,
        practice_state=None,
        ir_pup_nfi=None,
        suspension=False,
        administrative_exempt=override.kind == "ADMINISTRATIVE_EXEMPT",
        released=override.kind == "NOT_WITH_TEAM",
        current_team=override.corrected_team or None,
        reason=override.reason,
        source="MANUAL_VERIFIED_OVERRIDE",
        source_as_of=override.effective_date,
        override_kind=override.kind,
    )


def load_player_availability_statuses(
    repo_root: str | Path,
) -> tuple[PlayerAvailabilityStatus, ...]:
    """The one product-facing authority every Draft/Lineup/Waivers/Trades
    surface should eventually read player status from, instead of each
    surface separately re-deriving its own status heuristic (which is what
    happens today -- see `weekly-shared.tsx`'s `statusTone`, a UI-only
    heuristic with no shared backend authority behind it)."""

    return tuple(_from_override(override) for override in load_status_overrides(repo_root))


def player_availability_authority_health(repo_root: str | Path) -> dict[str, Any]:
    statuses = load_player_availability_statuses(repo_root)
    return {
        "authority": AUTHORITY_LABEL,
        "automatedFeed": False,
        "entryCount": len(statuses),
        "issues": [
            "No automated injury/practice-report feed exists in this repository; "
            "only manually verified, individually sourced overrides are reflected here."
        ],
    }
