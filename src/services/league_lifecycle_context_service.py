"""Provider-neutral league lifecycle context shared by Redraft and Dynasty.

This is a presentation/read-model synthesis over facts NWR already knows:
provider league status, Sleeper's NFL state, draft completion evidence, league
waiver settings, and the league's configured playoff start.  The existing
``resolve_league_lifecycle`` function remains the single draft-status authority;
this module adds the finer season phase and navigation booleans requested by the
owner without creating a second calendar system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from src.services.league_lifecycle_service import resolve_league_lifecycle

LeagueType = Literal["REDRAFT", "DYNASTY"]
SeasonPhase = Literal[
    "OFFSEASON",
    "ROOKIE_PRE_DRAFT",
    "DRAFT_APPROACHING",
    "DRAFT_DAY",
    "REGULAR_SEASON",
    "PLAYOFF_PUSH",
    "FANTASY_PLAYOFFS",
    "SEASON_COMPLETE",
]
DraftStatus = Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETE", "UNKNOWN"]
WaiverType = Literal["WAIVER_PRIORITY", "FAAB", "FREE_AGENCY", "UNKNOWN"]


@dataclass(frozen=True)
class LeagueLifecycleContext:
    league_type: LeagueType
    season_year: int
    current_week: int | None
    season_phase: SeasonPhase
    draft_status: DraftStatus
    waiver_type: WaiverType
    faab_enabled: bool | None
    playoffs_start: int | None
    is_draft_season: bool
    is_regular_season: bool
    is_playoffs: bool
    is_offseason: bool
    provider_status: str | None
    season_type: str | None
    basis: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "leagueType": self.league_type,
            "seasonYear": self.season_year,
            "currentWeek": self.current_week,
            "seasonPhase": self.season_phase,
            "draftStatus": self.draft_status,
            "waiverType": self.waiver_type,
            "faabEnabled": self.faab_enabled,
            "playoffsStart": self.playoffs_start,
            "isDraftSeason": self.is_draft_season,
            "isRegularSeason": self.is_regular_season,
            "isPlayoffs": self.is_playoffs,
            "isOffseason": self.is_offseason,
            "providerStatus": self.provider_status,
            "seasonType": self.season_type,
            "basis": self.basis,
        }


def _normalized_text(value: object) -> str | None:
    text = str(value or "").strip().lower()
    return text or None


def _waiver_context(raw_waiver_type: object) -> tuple[WaiverType, bool | None]:
    # Sleeper's documented numeric contract, already used by the waiver engine:
    # 0 = free agency, 1 = rolling waiver priority, 2 = FAAB.
    if raw_waiver_type in (2, "2", "faab", "auction"):
        return "FAAB", True
    if raw_waiver_type in (1, "1", "waiver_priority", "waivers"):
        return "WAIVER_PRIORITY", False
    if raw_waiver_type in (0, "0", "free_agency", "free_agent"):
        return "FREE_AGENCY", False
    return "UNKNOWN", None


def build_league_lifecycle_context(
    *,
    league_type: LeagueType,
    season_year: int,
    archived: bool,
    draft_configured: bool,
    drafted_count: int,
    total_draft_picks: int,
    current_pick: int | None,
    provider_status: str | None,
    current_week: int | None,
    season_type: str | None,
    playoffs_start: int | None,
    raw_waiver_type: object = None,
    live_sync_capable: bool = False,
    draft_last_activity_utc: str | None = None,
) -> LeagueLifecycleContext:
    """Compose one lifecycle contract from provider and draft evidence.

    ``PLAYOFF_PUSH`` begins three provider weeks before the configured fantasy
    playoff start.  This is a league-relative threshold, not a calendar-date
    guess.  When a week is unavailable, provider status still resolves the
    broader regular-season phase and the context says exactly which evidence it
    used in ``basis``.
    """

    legacy = resolve_league_lifecycle(
        archived=archived,
        draft_configured=draft_configured,
        drafted_count=drafted_count,
        total_draft_picks=total_draft_picks,
        current_pick=current_pick,
        provider_status=provider_status,
        live_sync_capable=live_sync_capable,
        draft_last_activity_utc=draft_last_activity_utc,
    )
    normalized_status = _normalized_text(provider_status)
    normalized_season_type = _normalized_text(season_type)

    if legacy.lifecycle == "PRE_DRAFT":
        phase: SeasonPhase = (
            "DRAFT_APPROACHING" if normalized_status == "pre_draft" else "ROOKIE_PRE_DRAFT"
        )
        draft_status: DraftStatus = "NOT_STARTED"
    elif legacy.lifecycle == "LIVE_DRAFT":
        phase = "DRAFT_DAY"
        draft_status = "IN_PROGRESS"
    elif legacy.lifecycle == "OFFSEASON":
        phase = "SEASON_COMPLETE" if normalized_status == "complete" else "OFFSEASON"
        draft_status = "COMPLETE" if normalized_status == "complete" else "UNKNOWN"
    else:
        draft_status = "COMPLETE"
        if normalized_status == "complete" or normalized_season_type in {"post", "postseason"}:
            phase = "SEASON_COMPLETE"
        elif (
            current_week is not None
            and playoffs_start is not None
            and current_week >= playoffs_start
        ):
            phase = "FANTASY_PLAYOFFS"
        elif (
            current_week is not None
            and playoffs_start is not None
            and current_week >= max(1, playoffs_start - 3)
        ):
            phase = "PLAYOFF_PUSH"
        else:
            phase = "REGULAR_SEASON"

    waiver_type, faab_enabled = _waiver_context(raw_waiver_type)
    draft_phases = {"ROOKIE_PRE_DRAFT", "DRAFT_APPROACHING", "DRAFT_DAY"}
    regular_phases = {"REGULAR_SEASON", "PLAYOFF_PUSH"}
    return LeagueLifecycleContext(
        league_type=league_type,
        season_year=season_year,
        current_week=current_week,
        season_phase=phase,
        draft_status=draft_status,
        waiver_type=waiver_type,
        faab_enabled=faab_enabled,
        playoffs_start=playoffs_start,
        is_draft_season=phase in draft_phases,
        is_regular_season=phase in regular_phases,
        is_playoffs=phase == "FANTASY_PLAYOFFS",
        is_offseason=phase in {"OFFSEASON", "SEASON_COMPLETE"},
        provider_status=normalized_status,
        season_type=normalized_season_type,
        basis=legacy.basis,
    )
