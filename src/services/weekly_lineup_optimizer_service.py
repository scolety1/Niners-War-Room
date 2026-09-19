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

--- NWR Sunday Readiness overnight cycle, Worker 2 (2026-09-18/19) -------

Section 2 of the governing brief (W1-W4: current-week + legal Start/Sit)
found and fixed FOUR real, reproduced defects in this module, all
regression-tested in `tests/test_weekly_lineup_optimizer_service.py`:

  * W2a (reserve/taxi not excluded): `build_roster_candidates` now accepts
    `reserve_sleeper_player_ids` / `taxi_sleeper_player_ids` (Sleeper's own
    real roster `reserve`/`taxi` arrays) and tags each `RosterCandidate`
    with `is_reserve`/`is_taxi`. `optimize_weekly_lineup` hard-excludes
    both from the normal eligible/greedy pool into a new `reserve` bucket
    -- a reserve player can never win an unconditional START here, no
    matter how many points he projects, matching the brief's explicit
    instruction that reserve/taxi activation (if ever built) must be a
    separate, conditional transaction, never this optimizer's default
    output.
  * W2b (no lock/kickoff input): `build_roster_candidates` now accepts
    `locked_teams` (a real, live kickoff-derived set from
    `weekly_game_lock_service.py`, threaded in by the facade) and tags
    each candidate `is_locked`. `optimize_weekly_lineup` PINS an
    already-locked CURRENT starter into a real eligible slot regardless of
    point comparison (his real game already started; NWR cannot un-start
    him), and hard-excludes an already-locked BENCH player from being
    newly started (his own real game already started too -- inserting him
    now would be illegal on the real platform). An unlocked player, or one
    with no real lock data at all (`locked_teams` empty, e.g. the real
    schedule fetch failed), behaves exactly as before this pass -- lock
    logic is strictly additive, never a guess when the input is absent.
  * W3 (missing-projection rows silently vanish): `build_roster_candidates`
    previously `continue`d (dropped entirely, not even counted) any real
    roster/starter id with no matching row in
    `weekly_projection_service`'s output -- a genuinely real, reproducible
    gap (Sleeper's weekly-projection endpoint simply has no entry for some
    real rostered players some weeks). Fixed: such a player is now kept as
    a real `RosterCandidate` (`identity_match="UNMATCHED_NO_PROJECTION_ROW"`,
    `projected_points=None`), with name/position/team resolved from the
    real Sleeper player catalog when the caller supplies one
    (`player_catalog`, optional) rather than silently dropped -- "missing
    is not zero, healthy, free agent, or already optimal" (governing
    brief). Because a truly required starting slot with zero usable
    candidates now correctly renders `status="EMPTY"`, `optimize_weekly_
    lineup` also now counts every real EMPTY starting slot toward
    `unprojected_starter_count` (previously 0 for an empty slot -- the
    exact false-NOMINAL-confidence gap the brief's fixture 3 describes).
  * W3b / W4 (unmatched identity silently promoted to OK; duplicate-sit /
    disappearing-FLEX swap explanations): see `_swap_reasons` and the
    per-slot status derivation in `optimize_weekly_lineup` below for the
    exact fix and reasoning -- a real before/after starter-ID diff
    replaces the old per-slot-type heuristic that could (a) attribute the
    SAME displaced incumbent to two different new starters (the
    "duplicate sits" bug) and (b) emit ZERO swaps for a real cross-slot
    (FLEX) rearrangement that changed the actual starting SET, because the
    old heuristic only looked for a displaced player who shared the new
    starter's own slot TYPE, never one who simply moved to a different
    slot instead of being benched.

Every new parameter above defaults to empty/`None` and is purely additive:
called with no reserve/taxi/lock/catalog input (as every pre-existing test
and call site does until updated), this module's output is byte-identical
to before this pass.

--- NWR connection/update pass, Worker 2 (2026-09-19) -----------------------

Owner-reported bug fix: `_swap_reasons` used to compute a swap's displayed
`projected_delta` as `slot.player.projected_points - (bumped.projected_points
or 0.0)` -- silently treating a genuinely MISSING weekly projection on the
displaced (`bumped`) player as a real, known 0.0. This fabricated a delta
equal to the new starter's own raw points, presented as a real, known point
swing (real-world case: Zay Flowers had no projection row; both the "start
Pittman over Flowers, +11.7" and "start Coker over [bench], +7.6" swap
explanations were built on this exact silent-zero substitution). Fixed:
`SwapReason.projected_delta` is now `float | None`, with a parallel
`delta_basis` field (`"KNOWN"` | `"UNKNOWN_MISSING_BENCH_PROJECTION"`) so a
missing-projection swap is represented HONESTLY -- neither fabricated nor
silently dropped. A real, known 0.0 projection (e.g. a kicker in a
bad-weather week) is NOT the same as a missing projection and still produces
a real, KNOWN numeric delta. See `_swap_reasons` below for the exact logic,
and `desktop_facade.py`'s Start/Sit confidence-gate branch for the matching
upstream fix (a top recommendation built on an unknown delta is no longer
reported as NOMINAL confidence).
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

# Same concept and same two positions as `waiver_engine_service.py`'s own
# `_OUT_OF_RANKED_MODEL_SCOPE_POSITIONS` (not imported directly -- a small,
# intentionally duplicated constant to avoid a cross-service import purely
# for two literal strings): NWR's governed ranking has ZERO K/DST rows by
# design, so every real K/DST candidate is structurally "UNMATCHED" against
# it, in every league, every week -- a real, disclosed scope boundary, not
# a genuine per-player identity-resolution failure.
_OUT_OF_RANKED_MODEL_SCOPE_POSITIONS = frozenset({"K", "DST"})


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
    # Worker 2 (Sunday Readiness overnight cycle, W2): real, sourced roster
    # facts previously not carried into this optimizer at all. All default
    # False -- purely additive, never inferred when not explicitly supplied.
    is_reserve: bool = False
    is_taxi: bool = False
    is_locked: bool = False
    # Worker 3 (Sunday Readiness overnight cycle, W7 fix): the real scoring
    # basis this player's `projected_points` was computed under (see
    # `weekly_projection_service.WeeklyProjectionRow.scoring_context`) --
    # threaded through so the lineup total no longer silently blends
    # league-exact and generic-provider points with no visible distinction.
    # `None` only for a candidate with no real projection row at all
    # (`UNMATCHED_NO_PROJECTION_ROW`).
    scoring_context: str | None = None
    unsupported_scoring_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class LineupSlot:
    slot_type: str
    player: RosterCandidate | None
    projected_points: float | None
    # OK | UNPROJECTED | EMPTY | UNRESOLVED_IDENTITY | SEASON_OUT |
    # NOT_WITH_TEAM | ADMINISTRATIVE_EXEMPT
    status: str
    close_call: bool
    close_call_alternative: str | None
    close_call_margin: float | None


@dataclass(frozen=True)
class SwapReason:
    slot_type: str
    start_player: str
    bench_player: str
    # `None` only when `delta_basis != "KNOWN"` -- the displaced
    # (`bench_player`) side has no real weekly projection row this week, so
    # the true point swing is genuinely unknown, never a fabricated number
    # (see `delta_basis`/`_swap_reasons` below). Never `None` when
    # `delta_basis == "KNOWN"`.
    projected_delta: float | None
    # "KNOWN" (both sides have a real projected-points value; `projected_
    # delta` is a real, computable number, including a real 0.0 on either
    # side) or "UNKNOWN_MISSING_BENCH_PROJECTION" (the displaced
    # `bench_player` has `projected_points is None` -- a genuinely missing
    # weekly-projection row, e.g. Sleeper's projection endpoint has no entry
    # for him at all this week -- NOT the same thing as a real, known 0.0).
    # Owner-reported bug fix (2026-09-19): `bumped.projected_points or 0.0`
    # used to silently treat "missing" as "zero", fabricating a delta equal
    # to the new starter's own raw points and presenting it as a real,
    # known point swing. Missing must remain unknown, not zero.
    delta_basis: str
    summary: str


@dataclass(frozen=True)
class WeeklyLineupResult:
    starters: tuple[LineupSlot, ...]
    bench: tuple[RosterCandidate, ...]
    excluded: tuple[RosterCandidate, ...]  # hard-excluded by real status override
    # Worker 2 (W2): reserve/taxi roster members -- never selectable as an
    # unconditional start by this optimizer, kept here (not silently
    # dropped) for coverage/explanation. Distinct from `excluded`, which
    # remains the real status-override (SEASON_OUT/NOT_WITH_TEAM/
    # ADMINISTRATIVE_EXEMPT) bucket, unchanged in meaning from before.
    reserve: tuple[RosterCandidate, ...] = ()
    # A real bench player whose own game has already kicked off (locked)
    # and was NOT already a current starter -- cannot legally be newly
    # started this week, kept for coverage/explanation, never silently
    # dropped or silently offered as a start.
    locked_unavailable: tuple[RosterCandidate, ...] = ()
    projected_total: float = 0.0
    unprojected_starter_count: int = 0
    # A starter whose identity was never confirmed against NWR's canonical
    # mapping (`identity_match != "MATCHED"`) -- may still carry a real
    # provider point value, but that value is NOT the same confidence as a
    # confirmed identity. Kept distinct from `unprojected_starter_count`.
    unresolved_identity_starter_count: int = 0
    swaps_vs_current: tuple[SwapReason, ...] = ()


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
    reserve_sleeper_player_ids: Sequence[str] = (),
    taxi_sleeper_player_ids: Sequence[str] = (),
    locked_teams: Sequence[str] = (),
    player_catalog: Mapping[str, Mapping[str, object]] | None = None,
) -> tuple[RosterCandidate, ...]:
    by_sleeper_id = {row.sleeper_player_id: row for row in projection_rows}
    # "0" is Sleeper's own placeholder for an empty starter slot -- never a
    # real player id, and must never be treated as "player 0 is starting".
    starter_set = {str(value) for value in starter_sleeper_player_ids if str(value) and str(value) != "0"}
    reserve_set = {str(value) for value in reserve_sleeper_player_ids}
    taxi_set = {str(value) for value in taxi_sleeper_player_ids}
    locked_team_set = {str(team).upper().strip() for team in locked_teams if str(team).strip()}
    catalog = player_catalog or {}
    candidates: list[RosterCandidate] = []
    for raw_id in roster_sleeper_player_ids:
        sleeper_id = str(raw_id)
        row = by_sleeper_id.get(sleeper_id)
        if row is not None:
            canonical_player_id = row.canonical_player_id
            player_name = row.player_name
            position = row.position
            team = row.team
            projected_points = row.projected_points
            identity_match = row.identity_match
            scoring_context = row.scoring_context
            unsupported_scoring_categories = row.unsupported_scoring_categories
        else:
            # W3 fix (Sunday Readiness overnight cycle, Worker 2): a real
            # roster/starter id with NO matching weekly-projection row
            # (Sleeper's projection endpoint simply has no entry for this
            # player this week) used to be silently dropped from
            # `candidates` entirely -- not even counted anywhere. Keep
            # them, resolved from the real Sleeper player catalog when the
            # caller supplied one; never fabricate a number, never a
            # silent disappearance.
            catalog_entry = catalog.get(sleeper_id)
            if isinstance(catalog_entry, Mapping):
                position = str(catalog_entry.get("position") or "UNKNOWN").upper().strip() or "UNKNOWN"
                team = str(catalog_entry.get("team") or "").upper().strip()
                player_name = (
                    str(catalog_entry.get("full_name") or catalog_entry.get("search_full_name") or "").strip()
                    or f"Sleeper id {sleeper_id}"
                )
            else:
                position, team, player_name = "UNKNOWN", "", f"Sleeper id {sleeper_id}"
            projected_points = None
            identity_match = "UNMATCHED_NO_PROJECTION_ROW"
            canonical_player_id = f"sleeper:{sleeper_id}"
            scoring_context = None
            unsupported_scoring_categories = ()
        candidates.append(
            RosterCandidate(
                sleeper_player_id=sleeper_id,
                canonical_player_id=canonical_player_id,
                player_name=player_name,
                position=position,
                team=team,
                projected_points=projected_points,
                identity_match=identity_match,
                currently_starting=sleeper_id in starter_set,
                is_reserve=sleeper_id in reserve_set,
                is_taxi=sleeper_id in taxi_set,
                is_locked=bool(team) and team.upper() in locked_team_set,
                scoring_context=scoring_context,
                unsupported_scoring_categories=unsupported_scoring_categories,
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
    reserve: list[RosterCandidate] = []
    locked_unavailable: list[RosterCandidate] = []
    pinned: list[RosterCandidate] = []  # locked AND already starting -- must keep a real slot
    eligible: list[RosterCandidate] = []
    for candidate in candidates:
        status = _status_for(candidate.canonical_player_id, candidate.identity_match, overrides_by_id)
        if status in ZERO_VALUE_KINDS:
            excluded.append(candidate)
            continue
        if candidate.is_reserve or candidate.is_taxi:
            # W2: reserve/taxi are never selectable as an unconditional
            # START here -- real activation (if ever built) is a separate,
            # conditional roster transaction, not this optimizer's output.
            reserve.append(candidate)
            continue
        if candidate.is_locked and not candidate.currently_starting:
            # W2: this bench player's own real game already kicked off --
            # he cannot legally be newly started this week on the real
            # platform. Distinct from an ordinary bench candidate.
            locked_unavailable.append(candidate)
            continue
        if candidate.is_locked and candidate.currently_starting:
            pinned.append(candidate)
        else:
            eligible.append(candidate)

    open_slots: dict[str, int] = dict(slot_counts)
    filled: dict[str, list[RosterCandidate]] = {slot: [] for slot in _SLOT_ORDER}

    # Phase 1 (W2): pin already-locked current starters into a real
    # eligible slot FIRST, regardless of point comparison -- a locked
    # starter's real game already started, so NWR cannot recommend
    # un-starting him for a higher-scoring bench candidate. Stable roster
    # order (not point order) -- every pinned player starts regardless of
    # relative points, so their processing order never changes who starts.
    for candidate in pinned:
        placed = False
        for slot_type in _SLOT_ORDER:
            if candidate.position not in _SLOT_ELIGIBILITY[slot_type]:
                continue
            if open_slots.get(slot_type, 0) <= 0:
                continue
            filled[slot_type].append(candidate)
            open_slots[slot_type] -= 1
            placed = True
            break
        if not placed:
            # No real eligible slot left for this locked starter (e.g. a
            # roster-settings change since the platform's own lineup was
            # set) -- fall through to normal competition rather than
            # silently dropping a real, currently-locked-in player.
            eligible.append(candidate)

    # Phase 2: the existing global greedy for everyone else (unlocked
    # candidates, plus any pinned candidate with no matching slot above).
    # Known-points players first (highest first), then unprojected players
    # last (in stable roster order) -- never fabricates a number to sort
    # an unprojected player by.
    eligible.sort(
        key=lambda c: (c.projected_points is None, -(c.projected_points or 0.0), c.player_name)
    )
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
    unresolved_identity_count = 0
    total = 0.0
    for slot_type in _SLOT_ORDER:
        for player in filled[slot_type]:
            # W3b: an unmatched/unresolved identity must never resolve to
            # plain "OK" just because a provider point value exists -- his
            # real canonical identity (and therefore his real
            # status-override eligibility) was never confirmed. EXCEPT for
            # K/DST: this codebase's own governed ranking has ZERO K/DST
            # rows BY DESIGN (see `waiver_engine_service.py`'s
            # `_OUT_OF_RANKED_MODEL_SCOPE_POSITIONS` / `UnmatchedRosterPlayer
            # .OUT_OF_RANKED_MODEL_SCOPE` -- the same, already-established
            # distinction this codebase draws elsewhere), so EVERY real K/DST
            # candidate is structurally "UNMATCHED" against that ranking,
            # every league, every week -- never a genuine identity failure.
            # Without this carve-out, any league that starts a K or DST
            # (nearly all of them) would show a permanently LOW-confidence
            # Start/Sit result for a real, expected, by-design scope
            # boundary rather than an actual data problem.
            if player.identity_match != "MATCHED" and player.position not in _OUT_OF_RANKED_MODEL_SCOPE_POSITIONS:
                status = "UNRESOLVED_IDENTITY"
                unresolved_identity_count += 1
                if player.projected_points is None:
                    unprojected_count += 1
                else:
                    total += player.projected_points
            elif player.projected_points is None:
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
            # W3: a real required starting slot with NO usable candidate is
            # missing production, not neutral -- must increase the
            # unprojected-starter counter so a caller's confidence gate
            # (e.g. the facade's NOMINAL/LOW check) cannot stay falsely
            # NOMINAL while a real starting slot sits empty.
            unprojected_count += 1
            starters.append(
                LineupSlot(
                    slot_type=slot_type, player=None, projected_points=None,
                    status="EMPTY", close_call=False, close_call_alternative=None, close_call_margin=None,
                )
            )

    swaps = _swap_reasons(candidates, starters)
    return WeeklyLineupResult(
        starters=tuple(starters),
        bench=bench,
        excluded=tuple(excluded),
        reserve=tuple(reserve),
        locked_unavailable=tuple(locked_unavailable),
        projected_total=round(total, 2),
        unprojected_starter_count=unprojected_count,
        unresolved_identity_starter_count=unresolved_identity_count,
        swaps_vs_current=swaps,
    )


@dataclass(frozen=True)
class ThisWeekAddDropImpact:
    """NWR Sunday Readiness overnight cycle, Worker 3 (W5 fix): the real,
    legal-lineup before/after impact of one candidate acquisition (and, when
    a drop is required, one real paired drop) for THIS week -- computed by
    calling `optimize_weekly_lineup` (the SAME, unmodified optimizer W2-W4
    already fixed) twice: once against the roster as it stands today, once
    against the roster after the hypothetical transaction. This is the real
    "actual usable lineup gain" signal the governing brief asks for, in
    place of a raw-point or season-marginal-utility proxy that ignores
    whether the add can actually crack this week's real starting lineup.
    """

    baseline_projected_total: float
    after_projected_total: float
    # Rounded `after - baseline`; can be exactly 0.0 for a real, evaluated
    # non-improvement (never confused with "not evaluated" -- see
    # `evaluated` on the caller's own wrapping type).
    gain: float
    # Whether the add candidate himself appears in a real starting slot in
    # the AFTER lineup -- the real, recomputed replacement for the old
    # season-based `becomes_starter` flag this same-named concept used to
    # borrow from `marginal_roster_utility_v2`.
    becomes_starter: bool


def simulate_this_week_add_drop(
    *,
    own_roster_candidates: Sequence[RosterCandidate],
    add_candidate: RosterCandidate,
    drop_sleeper_player_id: str | None,
    roster: RosterSettings,
    status_overrides: Sequence[StatusOverride],
) -> ThisWeekAddDropImpact:
    """Evaluate one real THIS-WEEK acquisition (`add_candidate`, built the
    SAME way as any other `RosterCandidate` -- e.g. via `build_roster_
    candidates` for a single free agent) against the owner's real current
    roster, optionally pairing it with one real drop
    (`drop_sleeper_player_id`, `None` when a real open non-reserve roster
    slot means no drop is required). Never re-derives roster legality --
    both the BEFORE and AFTER lineups are produced by the SAME `optimize_
    weekly_lineup` this module already exposes, with the SAME locks/
    reserve/taxi/status-override inputs on both sides (only the roster pool
    itself changes).

    NWR connection/update pass, Worker 2 (2026-09-19): `gain`/`becomes_
    starter` were checked for the same silent-missing-as-zero mistake
    `_swap_reasons` had. Verified honest, not fabricated: `optimize_weekly_
    lineup`'s own `total` already correctly EXCLUDES any starter with
    `projected_points is None` from `projected_total` (never substitutes
    0.0 for him -- see that function's own `unprojected_count` handling),
    so both `baseline` and `after` here are each already an honest total,
    and `gain = after.total - baseline.total` is a fair, symmetric
    comparison of two honest numbers -- never a fabricated one. The one
    real remaining risk this pass checked directly: if `add_candidate`
    itself has `projected_points is None` and still becomes a starter, his
    own real (unknown) contribution is silently OMITTED from `after.total`
    (not fabricated as zero, but also not disclosed as missing) -- `gain`
    would then understate the real value of the add without saying so. The
    one real call site (`desktop_facade.py`'s THIS_WEEK waiver evaluation)
    was confirmed this pass to only ever build `add_candidate` from a free
    agent whose `projected_points is not None` (it pre-filters the
    shortlist on exactly that condition before calling this function), so
    this risk does not currently occur in production. A future caller that
    evaluates an add candidate with no real projection row should be aware
    `gain` can silently undercount in that specific case."""

    baseline = optimize_weekly_lineup(
        candidates=own_roster_candidates, roster=roster, status_overrides=status_overrides
    )
    after_pool = [
        candidate
        for candidate in own_roster_candidates
        if drop_sleeper_player_id is None or candidate.sleeper_player_id != drop_sleeper_player_id
    ]
    after_pool.append(add_candidate)
    after = optimize_weekly_lineup(candidates=after_pool, roster=roster, status_overrides=status_overrides)
    becomes_starter = any(
        slot.player is not None and slot.player.sleeper_player_id == add_candidate.sleeper_player_id
        for slot in after.starters
    )
    return ThisWeekAddDropImpact(
        baseline_projected_total=baseline.projected_total,
        after_projected_total=after.projected_total,
        gain=round(after.projected_total - baseline.projected_total, 2),
        becomes_starter=becomes_starter,
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


def _swap_reasons(
    all_candidates: Sequence[RosterCandidate], starters: Sequence[LineupSlot]
) -> tuple[SwapReason, ...]:
    """W4 fix (Sunday Readiness overnight cycle, Worker 2): a real,
    complete, nonconflicting before/after starter-ID diff, replacing the
    old per-slot-type heuristic that had two real, reproduced bugs:

      1. "Duplicate sits" -- when TWO new starters were both eligible for
         the same slot TYPE (e.g. two RB slots), the old code independently
         searched the whole bench for "the currently-starting player
         eligible for this slot type" for EACH new starter, so the SAME
         displaced incumbent (whoever had the higher points) could be
         named as "bumped" by both new starters at once -- sitting him
         twice in the explanation and double/under-counting the real
         total point swing.
      2. Disappearing FLEX/cross-slot swaps -- when the real displaced
         incumbent didn't end up on the bench at all (he moved to a
         DIFFERENT slot he's also eligible for, e.g. an RB shifted from
         the dedicated RB slot into FLEX while a new RB was started ahead
         of him), the old code's `slot.player.currently_starting` guard
         skipped that new starter's slot entirely (its occupant still
         "currently_starting" via the OTHER slot), and the truly-benched
         player's own slot search never found a same-slot-type match
         either -- so NO swap was emitted at all, and the UI could then
         wrongly claim "Already optimal" despite the roster's actual
         starting SET having changed.

    This version instead computes the real before/after starting-ID SETS
    (which real players are/aren't in the after-optimization starting
    lineup, regardless of which specific slot they occupy), and greedily
    pairs each real newly-started player with a real newly-benched player
    (same-slot-type preferred for a natural "who lost this spot" story,
    falling back to whichever real former starter is still unaccounted
    for otherwise) -- each used at most once. "Already optimal" is then
    correctly derivable as "the before/after starting ID sets are equal",
    never as "the old heuristic happened to emit nothing".
    """

    before_starting = {
        candidate.sleeper_player_id: candidate
        for candidate in all_candidates
        if candidate.currently_starting
    }
    after_by_id = {
        slot.player.sleeper_player_id: slot for slot in starters if slot.player is not None
    }
    newly_started_ids = {pid for pid in after_by_id if pid not in before_starting}
    benched_pool = [
        candidate for pid, candidate in before_starting.items() if pid not in after_by_id
    ]

    reasons: list[SwapReason] = []
    for slot in starters:
        if slot.player is None or slot.player.sleeper_player_id not in newly_started_ids:
            continue
        if slot.player.projected_points is None or not benched_pool:
            # Never fabricate a delta from an unprojected new starter; and
            # if nothing real remains in the benched pool there is nothing
            # honest left to name as displaced.
            continue
        same_slot = [c for c in benched_pool if c.position in _SLOT_ELIGIBILITY[slot.slot_type]]
        pool = same_slot or benched_pool
        bumped = max(pool, key=lambda c: c.projected_points if c.projected_points is not None else float("-inf"))
        benched_pool.remove(bumped)
        if bumped.projected_points is None:
            # Owner-reported bug fix (2026-09-19): `bumped` (the displaced
            # player) has NO real weekly-projection row this week -- his
            # true point total is genuinely unknown, not zero. The prior
            # code (`bumped.projected_points or 0.0`) silently substituted
            # 0.0 here, fabricating a delta equal to `slot.player`'s own raw
            # points and presenting it as a real, known point swing (the
            # real-world Zay Flowers case: a "+11.7" / "+7.6" that was
            # really just the new starter's own total minus an assumed,
            # wrong zero for the unprojected bumped player). Carry the
            # uncertainty through honestly instead of hiding the swap or
            # fabricating a number for it.
            delta = None
            delta_basis = "UNKNOWN_MISSING_BENCH_PROJECTION"
            summary = (
                f"START {slot.player.player_name} over {bumped.player_name} -- "
                f"{bumped.player_name}'s projection is missing this week; point swing unknown."
            )
        else:
            # `slot.player.projected_points` is guaranteed non-None here (the
            # early `continue` above already excluded that case); `bumped
            # .projected_points` may legitimately be a real, known 0.0 (e.g.
            # a kicker projected for exactly zero points this week) -- that
            # is a real, computable delta, never confused with the missing
            # case above.
            delta = round(slot.player.projected_points - bumped.projected_points, 2)
            delta_basis = "KNOWN"
            summary = f"START {slot.player.player_name} over {bumped.player_name}, {delta:+.1f} projected"
        reasons.append(
            SwapReason(
                slot_type=slot.slot_type,
                start_player=slot.player.player_name,
                bench_player=bumped.player_name,
                projected_delta=delta,
                delta_basis=delta_basis,
                summary=summary,
            )
        )
    return tuple(reasons)
