"""Canonical redraft pick-legality authority.

This module answers one question only: can this team add this position to
its roster at this draft state?  It consumes league-configured position
maxima, the roster already drafted, flexible-slot semantics, and the number
of picks left to preserve a path to every mandatory starter slot.

It deliberately does not contain strategy heuristics (for example, an
assumed two-QB cap in a 1QB league).  A platform maximum is a league rule and
must be represented in ``DraftContext.roster_limits``; an unknown rule is
not silently invented.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass

from src.services.redraft_engine_v1_service import LeagueProfile, SUPPORTED_POSITIONS


@dataclass(frozen=True)
class DraftPickLegality:
    allowed: bool
    code: str
    reason: str
    position: str
    position_count: int
    position_maximum: int | None
    picks_remaining_after: int
    mandatory_slots_open_after: int


def _normalized_position(value: object) -> str:
    position = str(value or "").strip().upper()
    return "DST" if position in {"D/ST", "DEF"} else position


def _normalized_roster(roster: Mapping[str, int]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for raw_position, raw_count in roster.items():
        position = _normalized_position(raw_position)
        if position:
            counts[position] += max(0, int(raw_count))
    return counts


def _configured_maximum(profile: LeagueProfile, position: str) -> int | None:
    for configured_position, maximum in profile.draft.roster_limits.items():
        if _normalized_position(configured_position) == position:
            return int(maximum)
    return None


def _mandatory_slots_open(profile: LeagueProfile, roster: Mapping[str, int]) -> int:
    counts = _normalized_roster(roster)
    fixed_requirements = {
        "QB": profile.roster.qb,
        "RB": profile.roster.rb,
        "WR": profile.roster.wr,
        "TE": profile.roster.te,
        "K": profile.roster.k,
        "DST": profile.roster.dst,
    }
    fixed_open = sum(
        max(0, required - counts[position])
        for position, required in fixed_requirements.items()
    )
    leftovers = {
        position: max(0, counts[position] - fixed_requirements[position])
        for position in ("QB", "RB", "WR", "TE")
    }
    flex_eligible_left = sum(leftovers[position] for position in ("RB", "WR", "TE"))
    flex_filled = min(profile.roster.flex, flex_eligible_left)
    flex_open = profile.roster.flex - flex_filled
    flex_eligible_left -= flex_filled
    superflex_eligible_left = flex_eligible_left + leftovers["QB"]
    superflex_filled = min(profile.roster.superflex, superflex_eligible_left)
    superflex_open = profile.roster.superflex - superflex_filled
    return fixed_open + flex_open + superflex_open


def _configured_mandatory_slot_count(profile: LeagueProfile) -> int:
    return (
        profile.roster.qb
        + profile.roster.rb
        + profile.roster.wr
        + profile.roster.te
        + profile.roster.flex
        + profile.roster.superflex
        + profile.roster.k
        + profile.roster.dst
    )


def evaluate_draft_pick_legality(
    profile: LeagueProfile,
    roster: Mapping[str, int],
    candidate_position: object,
) -> DraftPickLegality:
    """Return the canonical legality result for one prospective roster add.

    ``roster`` is the team's current position-count mapping.  The team's
    remaining draft capacity is derived from the league's configured round
    count, so every caller (Suggestions, search-adjacent payloads, CPU
    simulation, and pick recording) receives identical mandatory-slot
    protection without passing a second, potentially inconsistent clock.
    """
    position = _normalized_position(candidate_position)
    counts = _normalized_roster(roster)
    position_count = counts[position]
    maximum = _configured_maximum(profile, position)
    roster_size = sum(counts.values())
    picks_remaining_after = profile.draft.rounds - roster_size - 1

    def result(
        allowed: bool,
        code: str,
        reason: str,
        mandatory_open: int = _mandatory_slots_open(profile, counts),
    ) -> DraftPickLegality:
        return DraftPickLegality(
            allowed=allowed,
            code=code,
            reason=reason,
            position=position,
            position_count=position_count,
            position_maximum=maximum,
            picks_remaining_after=picks_remaining_after,
            mandatory_slots_open_after=mandatory_open,
        )

    if position not in SUPPORTED_POSITIONS:
        return result(False, "UNSUPPORTED_POSITION", f"{position or 'Unknown'} is not a supported roster position.")
    if roster_size >= profile.draft.rounds:
        return result(False, "ROSTER_FULL", "This team's draft roster is already full.")
    if maximum is not None and position_count >= maximum:
        return result(
            False,
            "POSITION_MAXIMUM_REACHED",
            f"Drafting this {position} would exceed the league position maximum of {maximum}.",
        )

    after = counts.copy()
    after[position] += 1
    mandatory_open = _mandatory_slots_open(profile, after)
    # A few historical/test profiles predate roster-capacity validation and
    # configure more mandatory starters than draft rounds.  Such a profile
    # has no valid completion path before this candidate is considered, so
    # it must be surfaced by profile validation rather than making every
    # player falsely illegal here.  Feasible profiles receive the strict
    # remaining-slot guard.
    profile_has_feasible_mandatory_shape = (
        _configured_mandatory_slot_count(profile) <= profile.draft.rounds
    )
    if profile_has_feasible_mandatory_shape and mandatory_open > picks_remaining_after:
        return result(
            False,
            "MANDATORY_SLOTS_WOULD_BE_UNFILLABLE",
            (
                f"Drafting this {position} would leave {mandatory_open} mandatory roster "
                f"slot(s) but only {max(0, picks_remaining_after)} pick(s) to fill them."
            ),
            mandatory_open,
        )
    return result(True, "LEGAL", "This player can be drafted for the team.", mandatory_open)
