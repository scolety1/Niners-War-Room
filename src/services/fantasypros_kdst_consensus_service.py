"""Authorized FantasyPros ECR boundary for K/DST only.

This is intentionally external consensus context, never an NWR model score.
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


def _identity(name: object, position: object, team: object) -> tuple[str, str, str]:
    normalized_name = "".join(character for character in str(name or "").casefold() if character.isalnum())
    normalized_position = _sleeper_position(position)
    normalized_team = str(team or "").upper().strip()
    if not normalized_name or normalized_position not in SUPPORTED_POSITIONS or not normalized_team:
        return ("", "", "")
    return normalized_name, normalized_position, normalized_team
