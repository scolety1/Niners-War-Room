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
) -> LeagueWorkspaceContext:
    lifecycle_resolution = resolve_league_lifecycle(
        archived=profile.archived,
        draft_configured=draft_configured,
        drafted_count=drafted_count,
        total_draft_picks=total_draft_picks,
        current_pick=current_pick,
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
    )
