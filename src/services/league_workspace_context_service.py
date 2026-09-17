"""LeagueWorkspaceContext (NWR pre-UI architecture pass, 2026-09-10).

Makes league identity first-class (directive section 1). Wraps the
EXISTING profile/draft-board/roster data the facade already computes --
this module performs zero new I/O and recomputes nothing an existing
engine already owns; it only identifies and hashes state that already
exists so every consumer can answer "which league, which lifecycle stage,
which decision-relevant state" the same way.

Hashing reuses `provenance_hash` (`point_in_time_feature_store_service`),
the same deterministic sha256-over-canonical-JSON helper already used by
the draft-room DecisionBundle's `roster_state_hash`/`available_player_hash`
provenance fields -- this pass extends that same pattern to the in-season
surface, which had no hash/snapshot-identity field at all before this pass
(confirmed by direct search of `desktop_facade.py`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from src.services.league_lifecycle_service import resolve_league_lifecycle
from src.services.point_in_time_feature_store_service import provenance_hash
from src.services.redraft_engine_v1_service import LeagueProfile


@dataclass(frozen=True)
class LeagueWorkspaceContext:
    profile_id: str
    provider: str
    provider_league_id: str | None
    season: int
    lifecycle: str
    lifecycle_basis: str
    current_week: int | None
    scoring_profile_hash: str
    roster_state_hash: str | None
    league_snapshot_id: str
    sync_status: str
    sync_as_of: str | None
    issues: tuple[str, ...]
    # P1-1 (2026-09-12): additive-only real, directly-sourced Sleeper
    # context -- each is None when unavailable (no provider, read failed,
    # or malformed response), never a fabricated/simulated value. Built by
    # `sleeper_league_context_service.py`; this module only plumbs the
    # already-built dicts through, same "zero new I/O here" contract as
    # every other field on this dataclass.
    matchup: dict[str, Any] | None = None
    standings: dict[str, Any] | None = None
    playoff: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "profileId": self.profile_id,
            "provider": self.provider,
            "providerLeagueId": self.provider_league_id,
            "season": self.season,
            "lifecycle": self.lifecycle,
            "lifecycleBasis": self.lifecycle_basis,
            "currentWeek": self.current_week,
            "scoringProfileHash": self.scoring_profile_hash,
            "rosterStateHash": self.roster_state_hash,
            "leagueSnapshotId": self.league_snapshot_id,
            "syncStatus": self.sync_status,
            "syncAsOf": self.sync_as_of,
            "issues": list(self.issues),
            "matchup": self.matchup,
            "standings": self.standings,
            "playoff": self.playoff,
        }


def compute_scoring_profile_hash(profile: LeagueProfile) -> str:
    """Identity of the league's rules -- roster construction, scoring
    weights, draft context. Two profiles with the same rules (even
    different profile_id/leagueName) hash identically; any rule edit
    changes the hash."""

    return provenance_hash(
        {
            "roster": asdict(profile.roster),
            "scoring": asdict(profile.scoring),
            "draft": asdict(profile.draft),
            "teamCount": profile.team_count,
            "season": profile.season,
        }
    )


def compute_roster_state_hash(player_ids: Sequence[str] | None) -> str | None:
    """None (never a fabricated hash of nothing) when the caller has no
    real roster read for this request -- e.g. a local/non-Sleeper profile,
    or a live read that failed."""

    if player_ids is None:
        return None
    return provenance_hash({"rosterPlayerIds": sorted(str(pid) for pid in player_ids)})


def compute_league_snapshot_id(
    *,
    scoring_profile_hash: str,
    roster_state_hash: str | None,
    week: int | None,
    extra: Mapping[str, Any] | None = None,
) -> str:
    """One id identifying "this consistent decision state" -- directive
    section 3's LeagueSnapshot. Two calls with the same rules, the same
    roster read, and the same week always produce the same id; any of
    those changing (a roster move, a rules edit, a different week)
    produces a different id, so two recommendations computed from
    different underlying state are never silently shown as if they agreed.
    """

    return provenance_hash(
        {
            "scoringProfileHash": scoring_profile_hash,
            "rosterStateHash": roster_state_hash,
            "week": week,
            "extra": dict(extra or {}),
        }
    )


def build_league_workspace_context(
    *,
    profile: LeagueProfile,
    draft_configured: bool,
    drafted_count: int,
    total_draft_picks: int,
    current_pick: int | None,
    current_week: int | None,
    roster_player_ids: Sequence[str] | None,
    sync_status: str,
    sync_as_of: str | None,
    issues: Sequence[str] = (),
    matchup: Mapping[str, Any] | None = None,
    standings: Mapping[str, Any] | None = None,
    playoff: Mapping[str, Any] | None = None,
    draft_last_activity_utc: str | None = None,
) -> LeagueWorkspaceContext:
    # Real, already-fetched provider-native league status (Sleeper's own
    # `league.status`), when the caller obtained one for the playoff-context
    # read -- see league_lifecycle_service's module docstring for why this
    # takes priority over local draft-board activity. `playoff` is only ever
    # a real dict built by `sleeper_league_context_service.build_playoff_context`
    # (or None); no new I/O happens here.
    provider_status: str | None = None
    if playoff is not None:
        raw_status = playoff.get("leagueStatus")
        if isinstance(raw_status, str) and raw_status.strip():
            provider_status = raw_status
    lifecycle_resolution = resolve_league_lifecycle(
        archived=profile.archived,
        draft_configured=draft_configured,
        drafted_count=drafted_count,
        total_draft_picks=total_draft_picks,
        current_pick=current_pick,
        provider_status=provider_status,
        live_sync_capable=profile.provider == "sleeper" and bool(profile.provider_league_id),
        draft_last_activity_utc=draft_last_activity_utc,
    )
    scoring_hash = compute_scoring_profile_hash(profile)
    roster_hash = compute_roster_state_hash(roster_player_ids)
    snapshot_id = compute_league_snapshot_id(
        scoring_profile_hash=scoring_hash,
        roster_state_hash=roster_hash,
        week=current_week,
        extra={"lifecycle": lifecycle_resolution.lifecycle},
    )
    return LeagueWorkspaceContext(
        profile_id=profile.profile_id,
        provider=profile.provider,
        provider_league_id=profile.provider_league_id,
        season=profile.season,
        lifecycle=lifecycle_resolution.lifecycle,
        lifecycle_basis=lifecycle_resolution.basis,
        current_week=current_week,
        scoring_profile_hash=scoring_hash,
        roster_state_hash=roster_hash,
        league_snapshot_id=snapshot_id,
        sync_status=sync_status,
        sync_as_of=sync_as_of,
        issues=tuple(issues),
        matchup=dict(matchup) if matchup is not None else None,
        standings=dict(standings) if standings is not None else None,
        playoff=dict(playoff) if playoff is not None else None,
    )
