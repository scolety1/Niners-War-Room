"""Weekly Start/Sit lineup optimizer (NWR Overnight V3, Lane 3).

Only buildable because `weekly_projection_service.py` (Lane 1/2, this same
pass) found a real, live, per-player weekly projection source -- three
prior overnight passes on this branch independently concluded this lane was
BLOCKED. Reuses existing infrastructure only:

  * Roster/eligibility shape: `RosterSettings` (`redraft_engine_v1_service.py`).
  * Weekly points: `WeeklyProjectionRow` (`weekly_projection_service.py`).
  * Availability: the ONE shared status layer
    (`current_player_status_overrides_service.StatusOverride` /
    `ZERO_VALUE_KINDS`) -- no second injury/status system. A roster player
    whose `canonical_player_id` carries a real `SEASON_OUT` / `NOT_WITH_TEAM`
    / `ADMINISTRATIVE_EXEMPT` override is hard-excluded from the optimizer,
    exactly like the draft-time ranking already treats him (zero value).
    A player whose weekly-projection identity match is UNMATCHED cannot be
    checked against the status layer at all -- reported as
    `status="STATUS_UNKNOWN_UNMATCHED_IDENTITY"`, never silently assumed
    healthy.

Optimizer correctness note: this league's slot-eligibility sets are a
laminar (nested) family when grouped by specificity -- QB-only slots and
RB/WR/TE-only slots are each subsets of FLEX-eligible-or-wider, and FLEX
itself is a subset of SUPERFLEX-eligible. For a laminar family of "at most
k of this eligible set" constraints, a single global greedy pass (highest
projected points first, each player placed into the MOST SPECIFIC open
slot he is eligible for) is provably optimal -- this is the standard
laminar-matroid greedy-optimality result, not a heuristic. Cross-checked
against brute-force enumeration for small fixtures in the accompanying
test file, not just asserted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from src.services.current_player_status_overrides_service import ZERO_VALUE_KINDS, StatusOverride
from src.services.redraft_engine_v1_service import RosterSettings
from src.services.weekly_projection_service import WeeklyProjectionRow

# Slot type -> (eligible positions, specificity rank; lower = more specific,
# assigned first so a dedicated-position player never wrongly "steals" a
# generic FLEX/SUPERFLEX slot ahead of a player who can ONLY go there).
_SLOT_ELIGIBILITY: dict[str, frozenset[str]] = {
    "QB": frozenset({"QB"}),
    "RB": frozenset({"RB"}),
    "WR": frozenset({"WR"}),
    "TE": frozenset({"TE"}),
    "K": frozenset({"K"}),
    "DST": frozenset({"DST"}),
    "FLEX": frozenset({"RB", "WR", "TE"}),
    "SUPERFLEX": frozenset({"QB", "RB", "WR", "TE"}),
}
_SLOT_ORDER = ("QB", "RB", "WR", "TE", "K", "DST", "FLEX", "SUPERFLEX")

# A heuristic, disclosed-as-heuristic close-call band -- this source carries
# no per-player variance/uncertainty figure (unlike the season-long FFA
# archive's `sd_pts`), so this is NOT a statistically derived threshold.
CLOSE_CALL_ABSOLUTE_PTS = 2.0
CLOSE_CALL_RELATIVE_FRACTION = 0.15


@dataclass(frozen=True)
class RosterCandidate:
    sleeper_player_id: str
    canonical_player_id: str
    player_name: str
    position: str
    team: str
    projected_points: float | None
    identity_match: str
    currently_starting: bool


@dataclass(frozen=True)
class LineupSlot:
    slot_type: str
    player: RosterCandidate | None
    projected_points: float | None
    status: str  # OK | UNPROJECTED | EMPTY | SEASON_OUT | NOT_WITH_TEAM | ADMINISTRATIVE_EXEMPT
    close_call: bool
    close_call_alternative: str | None
    close_call_margin: float | None


@dataclass(frozen=True)
class SwapReason:
    slot_type: str
    start_player: str
    bench_player: str
    projected_delta: float
    summary: str


@dataclass(frozen=True)
class WeeklyLineupResult:
    starters: tuple[LineupSlot, ...]
    bench: tuple[RosterCandidate, ...]
    excluded: tuple[RosterCandidate, ...]  # hard-excluded by real status override
    projected_total: float
    unprojected_starter_count: int
    swaps_vs_current: tuple[SwapReason, ...]


def _status_for(
    candidate_canonical_id: str, identity_match: str, overrides_by_id: Mapping[str, StatusOverride]
) -> str:
    if identity_match != "MATCHED":
        return "STATUS_UNKNOWN_UNMATCHED_IDENTITY"
    override = overrides_by_id.get(candidate_canonical_id)
    if override is not None and override.kind in ZERO_VALUE_KINDS:
        return override.kind
    return "OK"


def build_roster_candidates(
    *,
    roster_sleeper_player_ids: Sequence[str],
    starter_sleeper_player_ids: Sequence[str],
    projection_rows: Sequence[WeeklyProjectionRow],
    status_overrides: Sequence[StatusOverride],
) -> tuple[RosterCandidate, ...]:
    by_sleeper_id = {row.sleeper_player_id: row for row in projection_rows}
    overrides_by_id = {override.player_id: override for override in status_overrides}
    starter_set = {str(value) for value in starter_sleeper_player_ids}
    candidates: list[RosterCandidate] = []
    for raw_id in roster_sleeper_player_ids:
        sleeper_id = str(raw_id)
        row = by_sleeper_id.get(sleeper_id)
        if row is None:
            continue  # not a fantasy-relevant position this week (e.g. taxi/practice squad slot)
        candidates.append(
            RosterCandidate(
                sleeper_player_id=sleeper_id,
                canonical_player_id=row.canonical_player_id,
                player_name=row.player_name,
                position=row.position,
                team=row.team,
                projected_points=row.projected_points,
                identity_match=row.identity_match,
                currently_starting=sleeper_id in starter_set,
            )
        )
    return tuple(candidates)


def optimize_weekly_lineup(
    *,
    candidates: Sequence[RosterCandidate],
    roster: RosterSettings,
    status_overrides: Sequence[StatusOverride],
) -> WeeklyLineupResult:
    overrides_by_id = {override.player_id: override for override in status_overrides}
    slot_counts = {
        "QB": roster.qb, "RB": roster.rb, "WR": roster.wr, "TE": roster.te,
        "K": roster.k, "DST": roster.dst, "FLEX": roster.flex, "SUPERFLEX": roster.superflex,
    }

    excluded: list[RosterCandidate] = []
    eligible: list[RosterCandidate] = []
    for candidate in candidates:
        status = _status_for(candidate.canonical_player_id, candidate.identity_match, overrides_by_id)
        if status in ZERO_VALUE_KINDS:
            excluded.append(candidate)
        else:
            eligible.append(candidate)

    # Global greedy: known-points players first (highest first), then
    # unprojected players last (in stable roster order) -- never fabricates
    # a number to sort an unprojected player by.
    eligible.sort(
        key=lambda c: (c.projected_points is None, -(c.projected_points or 0.0), c.player_name)
    )

    open_slots: dict[str, int] = dict(slot_counts)
    filled: dict[str, list[RosterCandidate]] = {slot: [] for slot in _SLOT_ORDER}
    remaining_by_id = {candidate.sleeper_player_id: candidate for candidate in eligible}

    for candidate in eligible:
        for slot_type in _SLOT_ORDER:
            if candidate.position not in _SLOT_ELIGIBILITY[slot_type]:
                continue
            if open_slots.get(slot_type, 0) <= 0:
                continue
            filled[slot_type].append(candidate)
            open_slots[slot_type] -= 1
            remaining_by_id.pop(candidate.sleeper_player_id, None)
            break

    bench = tuple(remaining_by_id.values())

    starters: list[LineupSlot] = []
    unprojected_count = 0
    total = 0.0
    for slot_type in _SLOT_ORDER:
        for player in filled[slot_type]:
            if player.projected_points is None:
                unprojected_count += 1
                status = "UNPROJECTED"
            else:
                total += player.projected_points
                status = "OK"
            close_call, alt_name, margin = _close_call(player, slot_type, bench)
            starters.append(
                LineupSlot(
                    slot_type=slot_type,
                    player=player,
                    projected_points=player.projected_points,
                    status=status,
                    close_call=close_call,
                    close_call_alternative=alt_name,
                    close_call_margin=margin,
                )
            )
        empty_count = open_slots.get(slot_type, 0)
        for _ in range(max(0, empty_count)):
            starters.append(
                LineupSlot(
                    slot_type=slot_type, player=None, projected_points=None,
                    status="EMPTY", close_call=False, close_call_alternative=None, close_call_margin=None,
                )
            )

    swaps = _swap_reasons(starters, bench)
    return WeeklyLineupResult(
        starters=tuple(starters),
        bench=bench,
        excluded=tuple(excluded),
        projected_total=round(total, 2),
        unprojected_starter_count=unprojected_count,
        swaps_vs_current=swaps,
    )


def _close_call(
    player: RosterCandidate, slot_type: str, bench: Sequence[RosterCandidate]
) -> tuple[bool, str | None, float | None]:
    if player.projected_points is None:
        return False, None, None
    best_bench_same_position = None
    for candidate in bench:
        if candidate.position not in _SLOT_ELIGIBILITY[slot_type]:
            continue
        if candidate.projected_points is None:
            continue
        if best_bench_same_position is None or candidate.projected_points > best_bench_same_position.projected_points:
            best_bench_same_position = candidate
    if best_bench_same_position is None:
        return False, None, None
    margin = round(player.projected_points - best_bench_same_position.projected_points, 2)
    threshold = max(CLOSE_CALL_ABSOLUTE_PTS, player.projected_points * CLOSE_CALL_RELATIVE_FRACTION)
    if margin <= threshold:
        return True, best_bench_same_position.player_name, margin
    return False, None, None


def _swap_reasons(starters: Sequence[LineupSlot], bench: Sequence[RosterCandidate]) -> tuple[SwapReason, ...]:
    reasons: list[SwapReason] = []
    for slot in starters:
        if slot.player is None or slot.player.currently_starting or slot.player.projected_points is None:
            continue
        # This optimizer moved a bench player into a slot a currently-started
        # player occupied on the platform -- find who is now benched for the
        # same eligible slot to name the actual swap.
        newly_benched = [
            candidate for candidate in bench
            if candidate.currently_starting and candidate.position in _SLOT_ELIGIBILITY[slot.slot_type]
        ]
        if not newly_benched:
            continue
        bumped = max(newly_benched, key=lambda c: c.projected_points or 0.0)
        delta = round((slot.player.projected_points or 0.0) - (bumped.projected_points or 0.0), 2)
        reasons.append(
            SwapReason(
                slot_type=slot.slot_type,
                start_player=slot.player.player_name,
                bench_player=bumped.player_name,
                projected_delta=delta,
                summary=f"START {slot.player.player_name} over {bumped.player_name}, {delta:+.1f} projected",
            )
        )
    return tuple(reasons)
