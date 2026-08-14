"""Deterministic practical mock QA for manual K/DST assets.

This is draft simulation, not an NWR player valuation.  Only QB/RB/WR/TE rows
come from the Redraft ranking result; K/DST are selected from an unranked
manual asset pool at late roster-completion picks.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Sequence

from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult


@dataclass(frozen=True)
class PracticalMockResult:
    owner_slot: int
    picks: tuple[dict[str, Any], ...]
    rosters: dict[int, dict[str, int]]
    errors: tuple[str, ...]


def run_practical_mock(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[dict[str, str]],
    *,
    owner_slot: int,
) -> PracticalMockResult:
    if not profile.practical_mode:
        raise ValueError("Practical Mock requires an owner-authorized practical profile.")
    if profile.draft.draft_type != "snake" or not 1 <= owner_slot <= profile.team_count:
        raise ValueError("Practical Mock requires a valid snake draft slot.")
    model_pool = [
        {"player_id": row.player_id, "player_name": row.player_name, "position": row.position, "team": row.team, "kind": "NWR_RANKED"}
        for row in ranking.rows
        if row.position in {"QB", "RB", "WR", "TE"}
    ]
    manual_pool = [
        {**row, "kind": "MANUAL_UNMODELED"}
        for row in manual_assets
        if row.get("position") in {"K", "DST"}
    ]
    if not model_pool or not any(row["position"] == "K" for row in manual_pool) or not any(row["position"] == "DST" for row in manual_pool):
        raise ValueError("Practical Mock requires ranked QB/RB/WR/TE plus manual K and DST assets.")
    available = {row["player_id"]: row for row in [*model_pool, *manual_pool]}
    rosters: dict[int, Counter[str]] = {slot: Counter() for slot in range(1, profile.team_count + 1)}
    picks: list[dict[str, Any]] = []
    for round_number in range(1, profile.draft.rounds + 1):
        slots = range(1, profile.team_count + 1) if round_number % 2 else range(profile.team_count, 0, -1)
        for slot in slots:
            asset = _select_asset(
                profile,
                round_number=round_number,
                roster=rosters[slot],
                available=available,
            )
            if asset is None:
                return PracticalMockResult(owner_slot, tuple(picks), {key: dict(value) for key, value in rosters.items()}, ("No valid asset remained for a required mock pick.",))
            available.pop(asset["player_id"], None)
            rosters[slot][asset["position"]] += 1
            picks.append(
                {
                    "pick_number": len(picks) + 1,
                    "round": round_number,
                    "slot": slot,
                    "owner_pick": slot == owner_slot,
                    "player_id": asset["player_id"],
                    "player_name": asset["player_name"],
                    "position": asset["position"],
                    "selection_behavior": asset["kind"],
                }
            )
    errors = tuple(
        f"Slot {slot} is missing {position}."
        for slot, roster in rosters.items()
        for position, required in (("QB", profile.roster.qb), ("RB", profile.roster.rb), ("WR", profile.roster.wr), ("TE", profile.roster.te), ("K", profile.roster.k), ("DST", profile.roster.dst))
        if roster[position] < required
    )
    return PracticalMockResult(owner_slot, tuple(picks), {key: dict(value) for key, value in rosters.items()}, errors)


def _select_asset(profile: LeagueProfile, *, round_number: int, roster: Counter[str], available: dict[str, dict[str, str]]) -> dict[str, str] | None:
    # K/DST are deterministic completion behavior, deliberately unranked.
    if round_number >= max(1, profile.draft.rounds - 1):
        for position in ("K", "DST"):
            if roster[position] < getattr(profile.roster, position.lower()):
                return _first(available, position, kind="MANUAL_UNMODELED")
    # Make fundamental starters legal before late manual completion.
    deadlines = {"QB": 8, "RB": 12, "WR": 12, "TE": 11}
    for position, deadline in deadlines.items():
        if round_number >= deadline and roster[position] < getattr(profile.roster, position.lower()):
            candidate = _first(available, position, kind="NWR_RANKED")
            if candidate is not None:
                return candidate
    # Do not exhaust draft capital with duplicate QBs/TEs before required starters.
    for asset in available.values():
        if asset["kind"] != "NWR_RANKED":
            continue
        position = asset["position"]
        if position == "QB" and roster[position] >= max(profile.roster.qb + 1, 2):
            continue
        if position == "TE" and roster[position] >= max(profile.roster.te + 1, 2):
            continue
        return asset
    return _first(available, "K", kind="MANUAL_UNMODELED") or _first(available, "DST", kind="MANUAL_UNMODELED")


def _first(available: dict[str, dict[str, str]], position: str, *, kind: str) -> dict[str, str] | None:
    return next((row for row in available.values() if row["position"] == position and row["kind"] == kind), None)
