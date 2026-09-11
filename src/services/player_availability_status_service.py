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
"""

from __future__ import annotations

from dataclasses import dataclass
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
        }


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
