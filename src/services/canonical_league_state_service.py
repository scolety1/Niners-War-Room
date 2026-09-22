"""Provider-neutral canonical league-state boundary (waiver-night hardening
cycle, Worker 3, 2026-09-22).

Owner's Phase 3 direction, verbatim: "Even with a valid ESPN snapshot, many
decision methods still enter Sleeper-specific second-stage live-fetch
logic. Fix this properly. Do NOT create 11 copy-pasted ESPN special cases
if a provider-neutral boundary is feasible... provider ingestion ->
validated provider snapshot -> provider-neutral canonical league state ->
existing NWR decision engines."

This module is that boundary. It is pure (no I/O, no Sleeper/ESPN/Flaim
calls of its own) and provider-neutral: given already-fetched raw Sleeper
data (rosters/players catalog -- the SAME live-fetch `desktop_facade.py`
already performs, unchanged) OR a real, parsed `EspnFlaimSnapshot`
(`espn_flaim_snapshot_service.py`), it assembles the SAME
`CanonicalLeagueState` shape either way, with honest per-field
completeness where a source genuinely doesn't provide something.

What this module deliberately does NOT do:
  * It does not perform any network I/O. `desktop_facade.py` still owns
    every live Sleeper fetch (via `SleeperHttpClient`) exactly as before --
    this module only assembles the RESULT of that fetch (or of a loaded
    ESPN snapshot) into a shared shape.
  * It does not compute NWR's own ranking-based canonical player identity
    (`resolve_roster_canonical_ids` in `waiver_engine_service.py` still
    owns that -- a downstream NWR concern layered ON TOP of a roster's
    provider-native identity, not a provider-data concept itself). Every
    `CanonicalRosterPlayer` carries the provider's OWN player id/name/
    position/team -- callers that need an NWR canonical id still resolve
    it themselves the same way they already do, just against
    `state.roster` instead of a raw Sleeper roster dict.
  * It does not fabricate FAAB budget, available-player-pool, or
    current-week data a given call site did not actually fetch this
    request -- those fields are honestly `None`/`"NOT_FETCHED_THIS_
    REQUEST"` when the caller didn't supply them, never guessed.
  * Waiver status (pending/on-waivers vs. free agent), waiver-clear-time,
    and recent league transactions are modeled as a real, honestly-null
    `CanonicalAcquisitionState` -- Worker 2's live-verified finding is that
    NONE of these exist for ANY provider today (not Sleeper-specific, not
    an ESPN gap) -- see `docs/codex/waiver_night_hardening_20260922/
    LEDGER.md`. This module does not fake data for Sleeper just to fill
    the schema.

`CanonicalRosterPlayer` deliberately mirrors `EspnRosterPlayer`'s shape
(`espn_flaim_snapshot_service.py`) -- provider_player_id/player_name/
position/team/slot -- rather than inventing a new shape, per the
dispatch directive's instruction to wrap/consume that existing, real,
tested schema rather than redesign it. `CanonicalAvailablePlayer` mirrors
`EspnAvailablePlayer` the same way.

See `docs/codex/waiver_night_hardening_20260922/LEDGER.md` (Worker 3
section) for exactly which `desktop_facade.py` callers consume this
module tonight, which are gate-only touched, and which remain untouched
for a later worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping, Sequence

from src.services.espn_flaim_snapshot_service import EspnFlaimSnapshot
from src.services.league_capability_service import (
    LeagueCapabilities,
    capabilities_from_espn_flaim_snapshot,
)

RosterSlotKind = Literal["STARTER", "BENCH", "RESERVE"]
ScoringCompleteness = Literal["COMPLETE", "PARTIAL", "UNKNOWN"]
PlayerPoolCoverage = Literal["COMPLETE", "BOUNDED", "NONE"]
FaabBudgetSource = Literal["SLEEPER_LIVE", "UNKNOWN", "NOT_FETCHED_THIS_REQUEST"]
CanonicalProvider = Literal["sleeper", "espn"]


class CanonicalLeagueStateError(ValueError):
    """A real, specific failure building a `CanonicalLeagueState` from raw
    provider data -- e.g. a malformed Sleeper rosters response, or no
    roster matching the given owner. `kind` is a short, stable symbolic
    string a caller can branch on to reproduce its OWN pre-existing,
    tool-specific error code/message/status exactly (see
    `desktop_facade.py::_resolve_canonical_league_state` callers), rather
    than this shared module dictating one generic error shape for every
    caller that uses it.
    """

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class CanonicalRosterPlayer:
    """Mirrors `EspnRosterPlayer` exactly (see module docstring)."""

    provider_player_id: str
    player_name: str
    position: str
    team: str
    slot: RosterSlotKind


@dataclass(frozen=True)
class CanonicalTeamRoster:
    """One OTHER team's roster (e.g. for Opponent Rosters). The owner's
    own team uses the top-level `CanonicalLeagueState.roster`/
    `owner_team_id`/`owner_team_name` fields instead of an entry here."""

    team_id: str
    team_name: str
    roster: tuple[CanonicalRosterPlayer, ...]


@dataclass(frozen=True)
class CanonicalScoringState:
    completeness: ScoringCompleteness
    disclosures: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalFaabState:
    """`source == "NOT_FETCHED_THIS_REQUEST"` is the honest default for a
    caller (e.g. My Roster, Start/Sit) that never asked for FAAB/waiver
    league settings this request -- distinct from `"UNKNOWN"` (asked, and
    genuinely could not be determined) and `"SLEEPER_LIVE"` (asked, and
    got a real live answer)."""

    is_faab_league: bool | None
    total_budget_dollars: float | None
    remaining_budget_dollars: float | None
    waiver_position: int | None
    source: FaabBudgetSource


@dataclass(frozen=True)
class CanonicalAcquisitionState:
    """Real, honestly-null for every provider today -- see module
    docstring. Never populate `waiver_status_supported`/
    `recent_transactions_supported` as `True` without a real, live-tested
    data path behind it."""

    waiver_status_supported: bool = False
    waiver_clear_time_utc: str | None = None
    recent_transactions_supported: bool = False
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "Waiver status (pending/on-waivers vs. free agent), waiver-clear "
            "time, and recent league transactions are not modeled by any "
            "provider integration in this codebase yet -- genuinely absent "
            "for Sleeper AND ESPN, not an ESPN-specific gap (see "
            "docs/codex/waiver_night_hardening_20260922/LEDGER.md, Worker 2).",
        )
    )


@dataclass(frozen=True)
class CanonicalAvailablePlayer:
    """Mirrors `EspnAvailablePlayer` exactly (see module docstring). Raw
    provider identity only -- no NWR ranking enrichment (a downstream
    concern, same boundary rule as `CanonicalRosterPlayer`)."""

    provider_player_id: str
    player_name: str
    position: str
    team: str


@dataclass(frozen=True)
class CanonicalLeagueState:
    """One retrieval's worth of a league's real state, in a shape that
    does not care whether it began as a live Sleeper fetch or a real
    `EspnFlaimSnapshot`. See module docstring for the fields this
    deliberately does and does not model."""

    provider: CanonicalProvider
    provider_league_id: str
    league_name: str
    season: int
    team_count: int
    owner_team_id: str
    owner_team_name: str | None
    roster: tuple[CanonicalRosterPlayer, ...]
    # Real extension beyond the owner's original field list (identity/
    # owner-team/roster/scoring/waiver/pool/acquisition/week/provenance):
    # added because a second real converted caller (`redraft_opponent_
    # rosters`, gate-level only tonight -- see the ledger) needed a
    # provider-neutral shape for OTHER teams' rosters too. `None` when a
    # caller didn't fetch/need opponent data this request.
    opponent_rosters: tuple[CanonicalTeamRoster, ...] | None
    scoring: CanonicalScoringState
    faab: CanonicalFaabState
    available_player_pool: tuple[CanonicalAvailablePlayer, ...] | None
    available_player_pool_coverage: PlayerPoolCoverage
    acquisition: CanonicalAcquisitionState
    current_week: int | None
    retrieved_at_utc: str | None
    provider_as_of_utc: str | None
    source: str
    capabilities: LeagueCapabilities


def _sleeper_roster_player(
    provider_player_id: str,
    *,
    players_catalog: Mapping[str, Mapping[str, object]] | None,
    starter_ids: frozenset[str],
    reserve_ids: frozenset[str],
) -> CanonicalRosterPlayer:
    """Byte-identical field derivation to the pre-existing inline logic in
    `desktop_facade.py::redraft_my_roster` (and mirrored in
    `redraft_weekly_lineup`/`redraft_opponent_rosters`) -- a present
    catalog entry's `full_name` (falling back to `search_full_name`, then
    the raw provider id) and raw `position`/upper-stripped `team`; an
    absent catalog entry degrades to empty position/team and the raw
    provider id as the name, matching what those call sites did before
    this module existed. Do not change this fallback order without
    re-verifying every converted caller's regression fixtures -- several
    rely on it producing IDENTICAL rows to the pre-conversion code."""

    catalog_entry = (
        players_catalog.get(provider_player_id)
        if isinstance(players_catalog, Mapping)
        else None
    )
    if isinstance(catalog_entry, Mapping):
        position = str(catalog_entry.get("position") or "")
        team = str(catalog_entry.get("team") or "").upper().strip()
        name = str(
            catalog_entry.get("full_name")
            or catalog_entry.get("search_full_name")
            or provider_player_id
        )
    else:
        position, team, name = "", "", provider_player_id
    if provider_player_id in reserve_ids:
        slot: RosterSlotKind = "RESERVE"
    elif provider_player_id in starter_ids:
        slot = "STARTER"
    else:
        slot = "BENCH"
    return CanonicalRosterPlayer(
        provider_player_id=provider_player_id, player_name=name, position=position,
        team=team, slot=slot,
    )


def build_canonical_league_state_from_sleeper(
    *,
    league_name: str,
    season: int,
    team_count: int,
    league_id: str,
    owner_user_id: str,
    rosters_raw: object,
    players_catalog: Mapping[str, Mapping[str, object]],
    retrieved_at_utc: str,
    capabilities: LeagueCapabilities,
    users_raw: object = None,
    include_opponent_rosters: bool = False,
) -> CanonicalLeagueState:
    """Assembles a `CanonicalLeagueState` from an already-fetched live
    Sleeper `league/{id}/rosters` response (`rosters_raw`) and player
    catalog (`players_catalog`) -- the SAME two live reads
    `desktop_facade.py` already performs for My Roster/Start-Sit/Opponent
    Rosters, unchanged. Performs NO network I/O itself.

    Raises `CanonicalLeagueStateError` (never a bare exception) for a
    malformed `rosters_raw` or a roster that does not match
    `owner_user_id` -- callers translate `exc.kind` into their own
    pre-existing, tool-specific `FacadeError` code/message/status.
    """

    if not isinstance(rosters_raw, Sequence) or not all(
        isinstance(entry, Mapping) for entry in rosters_raw
    ):
        raise CanonicalLeagueStateError(
            "MALFORMED_ROSTERS", "Sleeper roster response is malformed."
        )
    own_roster = next(
        (
            roster
            for roster in rosters_raw
            if str(roster.get("owner_id") or "") == str(owner_user_id)
        ),
        None,
    )
    if own_roster is None:
        raise CanonicalLeagueStateError(
            "OWN_ROSTER_NOT_FOUND", "The owner's Sleeper roster could not be found."
        )
    starter_ids = frozenset(str(v) for v in own_roster.get("starters") or [])
    reserve_ids = frozenset(str(v) for v in own_roster.get("reserve") or [])
    roster_players = tuple(
        _sleeper_roster_player(
            str(raw_id), players_catalog=players_catalog,
            starter_ids=starter_ids, reserve_ids=reserve_ids,
        )
        for raw_id in own_roster.get("players") or []
    )

    opponent_rosters: tuple[CanonicalTeamRoster, ...] | None = None
    if include_opponent_rosters:
        team_names: dict[str, str] = {}
        if isinstance(users_raw, Sequence):
            users_by_id = {
                str(u.get("user_id")): u for u in users_raw if isinstance(u, Mapping)
            }
            for roster in rosters_raw:
                roster_id = str(roster.get("roster_id") or "")
                owner_id = str(roster.get("owner_id") or "")
                user = users_by_id.get(owner_id)
                if roster_id and isinstance(user, Mapping):
                    metadata = user.get("metadata")
                    team_name = (
                        (metadata.get("team_name") if isinstance(metadata, Mapping) else None)
                        or user.get("display_name")
                        or ""
                    )
                    team_names[roster_id] = str(team_name)
        opponent_rosters = tuple(
            CanonicalTeamRoster(
                team_id=str(roster.get("roster_id") or ""),
                team_name=team_names.get(str(roster.get("roster_id") or ""), ""),
                roster=tuple(
                    _sleeper_roster_player(
                        str(raw_id), players_catalog=players_catalog,
                        starter_ids=frozenset(str(v) for v in roster.get("starters") or []),
                        reserve_ids=frozenset(str(v) for v in roster.get("reserve") or []),
                    )
                    for raw_id in roster.get("players") or []
                ),
            )
            for roster in rosters_raw
            if str(roster.get("owner_id") or "") != str(owner_user_id)
        )

    return CanonicalLeagueState(
        provider="sleeper",
        provider_league_id=league_id,
        league_name=league_name,
        season=season,
        team_count=team_count,
        owner_team_id=str(own_roster.get("roster_id") or owner_user_id),
        owner_team_name=None,
        roster=roster_players,
        opponent_rosters=opponent_rosters,
        scoring=CanonicalScoringState(
            completeness=capabilities.has_scoring_settings,
            disclosures=capabilities.disclosures,
        ),
        faab=CanonicalFaabState(
            is_faab_league=None, total_budget_dollars=None, remaining_budget_dollars=None,
            waiver_position=None, source="NOT_FETCHED_THIS_REQUEST",
        ),
        available_player_pool=None,
        available_player_pool_coverage="NONE",
        acquisition=CanonicalAcquisitionState(),
        current_week=None,
        retrieved_at_utc=retrieved_at_utc,
        provider_as_of_utc=None,
        source="Sleeper live API (api.sleeper.app)",
        capabilities=capabilities,
    )


def build_canonical_league_state_from_espn_snapshot(
    snapshot: EspnFlaimSnapshot,
    *,
    capabilities: LeagueCapabilities | None = None,
) -> CanonicalLeagueState:
    """Pure wrap of a real, already-parsed `EspnFlaimSnapshot`
    (`espn_flaim_snapshot_service.py`) -- performs no I/O, no re-
    validation (the snapshot's own `parse_espn_flaim_snapshot` already
    validated it). `capabilities` defaults to computing it from the
    snapshot via `capabilities_from_espn_flaim_snapshot` if not already
    computed by the caller (avoids a redundant recompute when the caller
    -- e.g. `desktop_facade._league_capabilities_for_profile` -- already
    has one).

    The snapshot schema deliberately has no standings and no opponent-
    roster field at all (see `espn_flaim_snapshot_service.py`'s own
    docstring) -- `opponent_rosters` is always `None` here, honestly,
    never fabricated.
    """

    resolved_capabilities = capabilities or capabilities_from_espn_flaim_snapshot(snapshot)
    roster_players = tuple(
        CanonicalRosterPlayer(
            provider_player_id=player.provider_player_id, player_name=player.player_name,
            position=player.position, team=player.team, slot=player.slot,
        )
        for player in snapshot.roster
    )
    available_pool = tuple(
        CanonicalAvailablePlayer(
            provider_player_id=player.provider_player_id, player_name=player.player_name,
            position=player.position, team=player.team,
        )
        for player in snapshot.available_player_pool
    ) or None
    return CanonicalLeagueState(
        provider="espn",
        provider_league_id=snapshot.provider_league_id,
        league_name=snapshot.league_name,
        season=snapshot.season,
        team_count=snapshot.team_count,
        owner_team_id=snapshot.owner_team_id,
        owner_team_name=snapshot.owner_team_name,
        roster=roster_players,
        opponent_rosters=None,
        scoring=CanonicalScoringState(
            completeness=snapshot.scoring_completeness,
            disclosures=resolved_capabilities.disclosures,
        ),
        faab=CanonicalFaabState(
            is_faab_league=None, total_budget_dollars=None, remaining_budget_dollars=None,
            waiver_position=None, source="UNKNOWN",
        ),
        available_player_pool=available_pool,
        available_player_pool_coverage=snapshot.available_player_pool_coverage,
        acquisition=CanonicalAcquisitionState(),
        current_week=None,
        retrieved_at_utc=snapshot.retrieved_at_utc,
        provider_as_of_utc=snapshot.provider_as_of_utc,
        source=snapshot.source,
        capabilities=resolved_capabilities,
    )
