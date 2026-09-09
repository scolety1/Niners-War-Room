"""Authorized FantasyPros ECR boundary and Sleeper roster availability.

FantasyPros access remains intentionally limited to K/DST and is external
consensus context, never an NWR model score.  Sleeper roster membership is a
separate, position-agnostic concern used by the Redraft free-agent surfaces.
No credentials are stored and no HTML is scraped.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen


FANTASYPROS_AUTHORITY = "EXTERNAL CONSENSUS — FANTASYPROS"
FANTASYPROS_API_BASE = "https://api.fantasypros.com/public/v2/json"
SUPPORTED_POSITIONS = frozenset({"K", "DST"})
SLEEPER_FANTASY_POSITIONS = frozenset({"QB", "RB", "WR", "TE", "K", "DST"})


class FantasyProsProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class FantasyProsProviderStatus:
    configured: bool
    authority: str
    message: str


@dataclass(frozen=True)
class ConsensusRow:
    provider_player_id: str
    player_name: str
    position: str
    team: str
    ecr: int
    tier: int | None
    week: int
    season: int
    authority: str = FANTASYPROS_AUTHORITY


def provider_status(*, environ: Mapping[str, str] | None = None) -> FantasyProsProviderStatus:
    values = os.environ if environ is None else environ
    if str(values.get("NWR_FANTASYPROS_API_KEY") or "").strip():
        return FantasyProsProviderStatus(True, FANTASYPROS_AUTHORITY, "Authorized FantasyPros API key configured locally.")
    return FantasyProsProviderStatus(False, FANTASYPROS_AUTHORITY, "FantasyPros API key is not configured. No provider request was attempted; the existing K/DST manual-draft fallback is not yet admitted.")


class FantasyProsConsensusClient:
    """Minimal official-API client; use only with owner-authorized credentials."""

    def __init__(self, *, api_key: str | None = None, api_base: str = FANTASYPROS_API_BASE) -> None:
        self.api_key = str(api_key if api_key is not None else os.environ.get("NWR_FANTASYPROS_API_KEY", "")).strip()
        self.api_base = api_base.rstrip("/")

    def consensus_rankings(self, *, season: int, position: str, week: int = 0, scoring: str = "PPR") -> tuple[ConsensusRow, ...]:
        normalized_position = str(position).upper()
        if normalized_position not in SUPPORTED_POSITIONS:
            raise FantasyProsProviderError("FantasyPros boundary is limited to K and DST.")
        if not self.api_key:
            raise FantasyProsProviderError("FantasyPros API key is required before requesting consensus rankings.")
        if not 2012 <= season <= 2100 or week < 0:
            raise FantasyProsProviderError("FantasyPros season or week is invalid.")
        query = urlencode({"position": normalized_position, "scoring": scoring.upper(), "week": week})
        request = Request(
            f"{self.api_base}/nfl/{season}/consensus-rankings?{query}",
            headers={"Accept": "application/json", "x-api-key": self.api_key},
            method="GET",
        )
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # transport errors must not create a synthetic ranking
            raise FantasyProsProviderError("FantasyPros consensus request failed.") from exc
        return _parse_consensus(payload, season=season, week=week, position=normalized_position)


def streamer_actions(
    rows: tuple[ConsensusRow, ...],
    *,
    rostered_provider_ids: set[str],
    owner_provider_ids: set[str],
    owner_starter_provider_ids: set[str] | None = None,
) -> tuple[dict[str, str | int | None], ...]:
    """Explain availability from ECR order without calculating an NWR K/DST score."""

    output: list[dict[str, str | int | None]] = []
    starter_ids = owner_starter_provider_ids or set()
    first_available_id = next(
        (
            row.provider_player_id
            for row in sorted(rows, key=lambda value: value.ecr)
            if row.provider_player_id not in rostered_provider_ids
        ),
        None,
    )
    for row in sorted(rows, key=lambda value: value.ecr):
        if row.provider_player_id in starter_ids:
            action = "START"
            roster_status = "YOUR_STARTER"
        elif row.provider_player_id in owner_provider_ids:
            action = "HOLD"
            roster_status = "YOUR_ROSTER"
        elif row.provider_player_id in rostered_provider_ids:
            action = "ROSTERED_ELSEWHERE"
            roster_status = "ROSTERED"
        else:
            action = "ADD" if row.provider_player_id == first_available_id else "ALTERNATIVE"
            roster_status = "AVAILABLE"
        output.append({
            "playerName": row.player_name,
            "position": row.position,
            "team": row.team,
            "ecr": row.ecr,
            "tier": row.tier,
            "week": row.week,
            "authority": row.authority,
            "rosterStatus": roster_status,
            "recommendation": action,
        })
    return tuple(output)


def sleeper_streamer_actions(
    rows: tuple[ConsensusRow, ...],
    *,
    rosters: object,
    players: object,
    owner_user_id: str,
) -> tuple[tuple[dict[str, str | int | None], ...], tuple[str, ...]]:
    """Resolve Sleeper roster availability with exact normalized name/position/team keys.

    FantasyPros and Sleeper use unrelated player identifiers.  This deliberately
    does not guess across names: a K/DST must match all three public identity
    fields before the consensus row is treated as rostered.
    """

    if not isinstance(rosters, list) or not all(isinstance(value, Mapping) for value in rosters):
        raise FantasyProsProviderError("Sleeper roster response is malformed.")
    if not isinstance(players, Mapping):
        raise FantasyProsProviderError("Sleeper player response is malformed.")
    provider_ids = {_identity(row.player_name, row.position, row.team): row.provider_player_id for row in rows}
    rostered: set[str] = set()
    owner: set[str] = set()
    starters: set[str] = set()
    unmatched: set[str] = set()
    for roster in rosters:
        is_owner = str(roster.get("owner_id") or "") == str(owner_user_id)
        starter_ids = {str(value) for value in roster.get("starters") or []} if is_owner else set()
        for sleeper_id in roster.get("players") or []:
            player = players.get(str(sleeper_id))
            if not isinstance(player, Mapping):
                continue
            position = _sleeper_position(player.get("position"))
            if position not in SUPPORTED_POSITIONS:
                continue
            key = _identity(player.get("full_name") or player.get("search_full_name"), position, player.get("team"))
            provider_id = provider_ids.get(key)
            if provider_id is None:
                unmatched.add(str(sleeper_id))
                continue
            rostered.add(provider_id)
            if is_owner:
                owner.add(provider_id)
                if str(sleeper_id) in starter_ids:
                    starters.add(provider_id)
    return (
        streamer_actions(
            rows,
            rostered_provider_ids=rostered,
            owner_provider_ids=owner,
            owner_starter_provider_ids=starters,
        ),
        tuple(sorted(unmatched)),
    )


def sleeper_rostered_player_ids(rosters: object) -> set[str]:
    """Return every rostered Sleeper player ID across fantasy positions.

    This deliberately uses Sleeper's shared identifiers instead of fuzzy
    cross-provider matching.  It is the general rostered-set primitive used by
    free agents; K/DST consensus continues to perform its stricter identity
    bridge above because FantasyPros IDs are unrelated to Sleeper IDs.
    """

    if not isinstance(rosters, list) or not all(isinstance(value, Mapping) for value in rosters):
        raise FantasyProsProviderError("Sleeper roster response is malformed.")
    return {
        str(sleeper_id)
        for roster in rosters
        for sleeper_id in (roster.get("players") or [])
        if str(sleeper_id).strip()
    }


def sleeper_free_agent_pool(
    *,
    rosters: object,
    players: object,
    rankings: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Build the live unrostered pool and attach only existing NWR values."""

    rostered = sleeper_rostered_player_ids(rosters)
    if not isinstance(players, Mapping):
        raise FantasyProsProviderError("Sleeper player response is malformed.")
    ranking_by_identity = {
        _identity(row.get("playerName"), row.get("position"), row.get("team"),
                  allowed_positions=SLEEPER_FANTASY_POSITIONS): row
        for row in rankings
    }
    ranking_by_identity.pop(("", "", ""), None)
    output: list[dict[str, Any]] = []
    for raw_id, raw in players.items():
        sleeper_id = str(raw_id).strip()
        if not sleeper_id or sleeper_id in rostered or not isinstance(raw, Mapping):
            continue
        position = _sleeper_position(raw.get("position"))
        if position not in SLEEPER_FANTASY_POSITIONS or raw.get("active") is False:
            continue
        team = str(raw.get("team") or "").upper().strip()
        name = str(raw.get("full_name") or raw.get("search_full_name") or "").strip()
        if position == "DST" and not name and team:
            name = f"{team} D/ST"
        if not name or not team:
            continue
        ranking = ranking_by_identity.get(
            _identity(name, position, team, allowed_positions=SLEEPER_FANTASY_POSITIONS)
        )
        output.append(
            {
                "sleeperPlayerId": sleeper_id,
                "playerId": str(ranking.get("playerId") or "") if ranking else "",
                "playerName": name,
                "position": position,
                "team": team,
                "overallRank": ranking.get("overallRank") if ranking else None,
                "positionRank": ranking.get("positionRank") if ranking else None,
                "projectedPoints": ranking.get("projectedPoints") if ranking else None,
                "replacementAdjustedValue": (
                    ranking.get("replacementAdjustedValue") if ranking else None
                ),
                "valueLabel": str(ranking.get("valueLabel") or "") if ranking else "",
                "rankingAuthority": "NWR REDRAFT RANKING" if ranking else "UNRANKED",
                "rosterStatus": "AVAILABLE",
            }
        )
    return tuple(
        sorted(
            output,
            key=lambda row: (
                row["overallRank"] is None,
                row["overallRank"] if row["overallRank"] is not None else 10**9,
                row["position"],
                row["playerName"].casefold(),
                row["sleeperPlayerId"],
            ),
        )
    )


def sleeper_opponent_rosters(
    *,
    rosters: object,
    users: object,
    players: object,
    owner_user_id: str,
) -> tuple[dict[str, Any], ...]:
    """Return current non-owner Sleeper rosters with public team identity."""

    if not isinstance(rosters, list) or not all(isinstance(value, Mapping) for value in rosters):
        raise FantasyProsProviderError("Sleeper roster response is malformed.")
    if not isinstance(users, list) or not all(isinstance(value, Mapping) for value in users):
        raise FantasyProsProviderError("Sleeper users response is malformed.")
    if not isinstance(players, Mapping):
        raise FantasyProsProviderError("Sleeper player response is malformed.")
    user_by_id = {str(value.get("user_id") or ""): value for value in users}
    output: list[dict[str, Any]] = []
    for roster in rosters:
        roster_owner_id = str(roster.get("owner_id") or "")
        if roster_owner_id == str(owner_user_id):
            continue
        roster_id = str(roster.get("roster_id") or "")
        user = user_by_id.get(roster_owner_id, {})
        metadata = user.get("metadata") if isinstance(user.get("metadata"), Mapping) else {}
        team_name = str(
            metadata.get("team_name")
            or user.get("display_name")
            or user.get("username")
            or f"Roster {roster_id}"
        ).strip()
        starter_ids = {str(value) for value in roster.get("starters") or []}
        roster_players: list[dict[str, Any]] = []
        unresolved: list[str] = []
        for raw_id in roster.get("players") or []:
            sleeper_id = str(raw_id)
            raw = players.get(sleeper_id)
            if not isinstance(raw, Mapping):
                unresolved.append(sleeper_id)
                continue
            position = _sleeper_position(raw.get("position"))
            name = str(raw.get("full_name") or raw.get("search_full_name") or "").strip()
            team = str(raw.get("team") or "").upper().strip()
            if position == "DST" and not name and team:
                name = f"{team} D/ST"
            roster_players.append(
                {
                    "sleeperPlayerId": sleeper_id,
                    "playerName": name or "Unresolved Sleeper player",
                    "position": position or "UNKNOWN",
                    "team": team,
                    "starter": sleeper_id in starter_ids,
                }
            )
        roster_players.sort(
            key=lambda row: (not row["starter"], row["position"], row["playerName"].casefold())
        )
        output.append(
            {
                "rosterId": roster_id,
                "ownerUserId": roster_owner_id,
                "teamName": team_name,
                "players": roster_players,
                "unresolvedSleeperPlayerIds": sorted(unresolved),
            }
        )
    return tuple(sorted(output, key=lambda row: (row["teamName"].casefold(), row["rosterId"])))


def _parse_consensus(payload: object, *, season: int, week: int, position: str) -> tuple[ConsensusRow, ...]:
    if not isinstance(payload, Mapping) or not isinstance(payload.get("players"), list):
        raise FantasyProsProviderError("FantasyPros consensus response is malformed.")
    rows: list[ConsensusRow] = []
    seen: set[str] = set()
    for value in payload["players"]:
        if not isinstance(value, Mapping):
            raise FantasyProsProviderError("FantasyPros player row is malformed.")
        provider_id = str(value.get("player_id") or "").strip()
        name = str(value.get("player_name") or "").strip()
        row_position = str(value.get("player_position_id") or value.get("player_position") or position).upper()
        try:
            ecr = int(str(value.get("rank_ecr")))
        except (TypeError, ValueError) as exc:
            raise FantasyProsProviderError("FantasyPros player row has no numeric ECR.") from exc
        if not provider_id or not name or provider_id in seen or row_position != position or ecr < 1:
            raise FantasyProsProviderError("FantasyPros consensus identity or position is invalid.")
        seen.add(provider_id)
        tier = _optional_int(value.get("tier"))
        rows.append(ConsensusRow(provider_id, name, row_position, str(value.get("player_team_id") or "").upper(), ecr, tier, week, season))
    return tuple(sorted(rows, key=lambda value: value.ecr))


def _optional_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _sleeper_position(value: object) -> str:
    position = str(value or "").upper()
    return "DST" if position == "DEF" else position


def _identity(
    name: object,
    position: object,
    team: object,
    *,
    allowed_positions: frozenset[str] = SUPPORTED_POSITIONS,
) -> tuple[str, str, str]:
    normalized_name = "".join(character for character in str(name or "").casefold() if character.isalnum())
    normalized_position = _sleeper_position(position)
    normalized_team = str(team or "").upper().strip()
    if not normalized_name or normalized_position not in allowed_positions or not normalized_team:
        return ("", "", "")
    return normalized_name, normalized_position, normalized_team
