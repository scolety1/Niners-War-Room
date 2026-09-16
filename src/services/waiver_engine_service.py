"""Waiver-wire ranking, Add/Drop pairing, and FAAB bid ranges (NWR Overnight
V3, Lanes 4/5/6).

Two honest modes, per the governing directive:
  * REST_OF_SEASON -- buildable regardless of Lane 1/2's weekly-source find,
    since ROS player value already exists via NWR's own governed ranking.
  * THIS_WEEK -- only enabled when a real weekly projection was resolved for
    the candidate (Lane 1/2). Never fabricated when unavailable; the caller
    (facade) is expected to disable this mode outright when no weekly
    context is passed in, per the directive's "disable that mode honestly
    rather than fake it."

Reuses, does not duplicate:
  * `marginal_roster_utility_v2` (`shadow_numeric_authorities_service.py`) --
    the SAME promoted, closed, read-only bench-value signal used live in the
    draft room. MODEL STATUS IS CLOSED: this module calls it, never retunes
    or reimplements it. Used for BOTH add-ranking (marginal value of adding
    a free agent to the current roster) and drop-ranking (marginal value of
    a currently rostered bench player, computed the same way against the
    roster with that player removed -- "how much is he actually worth to
    THIS roster right now" is the same function, just pointed at an
    already-rostered player instead of a free agent).
  * `sleeper_free_agent_pool`'s own free-agent rows (`playerId` /
    `replacementAdjustedValue` / `overallRank`) for ROS value -- no second
    ranking read.

What is deliberately NOT estimated, per the directive's own anti-fabrication
rule: schedule/strength-of-schedule for general waiver ranking (a real,
disclosed omission -- the DST/K streamer lane is pure FantasyPros ECR
passthrough plus live Sleeper roster-ownership matching, it has no real
schedule/matchup signal either; general skill-position waiver ranking does
not get a schedule boost invented here), and any "likely competition for
this FAAB bid" acceptance probability (no real signal in this app
estimates that).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from src.services.fantasypros_kdst_consensus_service import (
    SLEEPER_FANTASY_POSITIONS,
    _identity,
    _sleeper_position,
)
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.shadow_numeric_authorities_service import (
    MarginalRosterUtility,
    marginal_roster_utility_v2,
)
from src.services.weekly_projection_service import WeeklyProjectionRow

WaiverMode = Literal["THIS_WEEK", "REST_OF_SEASON"]


@dataclass(frozen=True)
class ResolvedRoster:
    canonical_player_ids: tuple[str, ...]
    player_names_by_canonical_id: dict[str, str]
    player_positions_by_canonical_id: dict[str, str]
    unmatched_sleeper_player_ids: tuple[str, ...]
    canonical_id_by_sleeper_id: dict[str, str]


def resolve_roster_canonical_ids(
    *,
    roster_sleeper_player_ids: Sequence[str],
    players_catalog: Mapping[str, Mapping[str, Any]],
    ranking_rows: Sequence[Mapping[str, Any]],
) -> ResolvedRoster:
    """Joins a Sleeper roster to NWR's canonical ranking id space via the
    SAME name/position/team identity matcher `sleeper_free_agent_pool`
    already uses -- no new identity system, and never silently drops an
    unmatched roster player (reported separately, not just omitted)."""

    ranking_by_identity: dict[tuple[str, str, str], str] = {}
    for row in ranking_rows:
        key = _identity(
            row.get("playerName"), row.get("position"), row.get("team"),
            allowed_positions=SLEEPER_FANTASY_POSITIONS,
        )
        if key != ("", "", ""):
            ranking_by_identity.setdefault(key, str(row.get("playerId") or ""))

    canonical_ids: list[str] = []
    names: dict[str, str] = {}
    positions: dict[str, str] = {}
    unmatched: list[str] = []
    by_sleeper_id: dict[str, str] = {}
    for raw_id in roster_sleeper_player_ids:
        sleeper_id = str(raw_id)
        catalog_entry = players_catalog.get(sleeper_id)
        if not isinstance(catalog_entry, Mapping):
            unmatched.append(sleeper_id)
            continue
        position = _sleeper_position(catalog_entry.get("position"))
        team = str(catalog_entry.get("team") or "").upper().strip()
        name = str(catalog_entry.get("full_name") or catalog_entry.get("search_full_name") or "").strip()
        if position == "DST" and not name and team:
            name = f"{team} D/ST"
        key = _identity(name, position, team, allowed_positions=SLEEPER_FANTASY_POSITIONS)
        canonical_id = ranking_by_identity.get(key, "")
        if not canonical_id:
            unmatched.append(sleeper_id)
            continue
        canonical_ids.append(canonical_id)
        names[canonical_id] = name
        positions[canonical_id] = position
        by_sleeper_id[sleeper_id] = canonical_id
    return ResolvedRoster(
        canonical_player_ids=tuple(canonical_ids),
        player_names_by_canonical_id=names,
        player_positions_by_canonical_id=positions,
        unmatched_sleeper_player_ids=tuple(unmatched),
        canonical_id_by_sleeper_id=by_sleeper_id,
    )


# Positions that structurally have zero rows in NWR's governed ranking, by
# design (see docs/codex/waiver_night_v1/LEDGER.md, "K/DST are never
# evaluated by this waiver-ranking path at all, by design, not a bug this
# pass introduced"). A K/DST roster slot will therefore ALWAYS show up in
# `ResolvedRoster.unmatched_sleeper_player_ids`, even when its real Sleeper
# identity resolves cleanly -- this is a scope boundary, not an identity
# gap.
_OUT_OF_RANKED_MODEL_SCOPE_POSITIONS = frozenset({"K", "DST"})


@dataclass(frozen=True)
class UnmatchedRosterPlayer:
    """A human-readable description of one entry in
    `ResolvedRoster.unmatched_sleeper_player_ids`, distinguishing two
    genuinely different situations that a flat raw-Sleeper-id list conflates:
      * `OUT_OF_RANKED_MODEL_SCOPE` -- the real Sleeper catalog resolves a
        real player/team-defense name, but the position (K/DST) simply has
        no rows in NWR's governed ranking by design. Not a bug.
      * `UNKNOWN_TO_CATALOG` -- the id has no entry in the Sleeper player
        catalog at all, a genuinely unresolved identity worth investigating.
    Purely additive/display: never changes which ids are matched/unmatched
    (that remains `resolve_roster_canonical_ids`'s own, unmodified job) and
    never affects any ranking, score, or roster-legality computation.
    """

    sleeper_id: str
    label: str
    reason: str
    category: Literal["OUT_OF_RANKED_MODEL_SCOPE", "UNKNOWN_TO_CATALOG"]


def describe_unmatched_roster_players(
    unmatched_sleeper_ids: Sequence[str],
    players_catalog: Mapping[str, Mapping[str, Any]],
) -> tuple[UnmatchedRosterPlayer, ...]:
    """Builds a readable label/reason for each already-computed unmatched
    Sleeper roster id, using the SAME Sleeper player catalog
    `resolve_roster_canonical_ids` was given -- no new identity system, no
    re-matching, no change to which ids are considered unmatched."""

    out: list[UnmatchedRosterPlayer] = []
    for raw_id in unmatched_sleeper_ids:
        sleeper_id = str(raw_id)
        entry = players_catalog.get(sleeper_id)
        if isinstance(entry, Mapping):
            position = _sleeper_position(entry.get("position"))
            team = str(entry.get("team") or "").upper().strip()
            name = str(entry.get("full_name") or entry.get("search_full_name") or "").strip()
            if not name and team:
                name = f"{team} D/ST" if position == "DST" else team
            if not name:
                name = sleeper_id
            label = f"{name} ({position})" if position else name
            if position in _OUT_OF_RANKED_MODEL_SCOPE_POSITIONS:
                out.append(
                    UnmatchedRosterPlayer(
                        sleeper_id=sleeper_id, label=label,
                        reason="Outside NWR's ranked model -- K/DST are not part of the governed ranking.",
                        category="OUT_OF_RANKED_MODEL_SCOPE",
                    )
                )
            else:
                out.append(
                    UnmatchedRosterPlayer(
                        sleeper_id=sleeper_id, label=label,
                        reason="Identity could not be matched to NWR's governed ranking.",
                        category="UNKNOWN_TO_CATALOG",
                    )
                )
        else:
            out.append(
                UnmatchedRosterPlayer(
                    sleeper_id=sleeper_id, label=sleeper_id,
                    reason="Unknown Sleeper id -- no entry in the Sleeper player catalog.",
                    category="UNKNOWN_TO_CATALOG",
                )
            )
    return tuple(out)


@dataclass(frozen=True)
class WaiverCandidate:
    sleeper_player_id: str
    canonical_player_id: str
    player_name: str
    position: str
    team: str
    ros_replacement_value: float | None
    ros_overall_rank: int | None
    weekly_projected_points: float | None
    marginal_utility: float | None
    becomes_starter: bool
    marginal_utility_explanation: str
    identity_status: str  # MATCHED | UNMATCHED_IDENTITY


@dataclass(frozen=True)
class DropCandidate:
    canonical_player_id: str
    player_name: str
    position: str
    marginal_utility: float | None
    explanation: str


@dataclass(frozen=True)
class AddDropPairing:
    add: WaiverCandidate
    drop: DropCandidate | None
    # Waiver Night V1 (Section 4, add/drop context repair): whether a drop
    # is genuinely required for this add to be legal. `False` only when a
    # real, verified open non-reserve roster slot exists (see
    # `redraft_waivers`'s `roster_positions`-based check) -- never inferred
    # from anything else.
    drop_required: bool
    # The add's own marginal value against the roster exactly as it stands
    # today (unchanged from `WaiverCandidate.marginal_utility` -- kept here
    # too so a consumer never has to reach back into a different list to
    # see both reference points side by side).
    add_utility_vs_original_roster: float | None
    # The add's own marginal value recomputed against the SAME roster the
    # drop's own value was computed against (the roster with `drop` already
    # removed) -- `None` when `drop` is `None` (nothing to compare against)
    # or when either side's value could not be computed at all.
    add_utility_vs_post_drop_roster: float | None
    # The drop's own marginal value -- already computed by
    # `rank_drop_candidates` against this same post-drop roster (dropping a
    # player is, by definition, evaluated against the roster without him),
    # so no recomputation is needed on this side. Equal to
    # `drop.marginal_utility` when `drop` is not `None`.
    drop_utility_vs_post_drop_roster: float | None
    # A real, same-context marginal comparison
    # (`add_utility_vs_post_drop_roster - drop_utility_vs_post_drop_roster`,
    # both measured against the identical post-drop roster) when a drop is
    # paired; the add's own unchanged-roster value when no drop is needed.
    # This is NOT an authoritative "total-roster" or "completed-transaction"
    # utility -- no such objective is defined anywhere else in this
    # codebase, so none is claimed here.
    net_marginal_utility: float | None
    # "SAME_CONTEXT_MARGINAL_COMPARISON" (a drop was paired and both sides
    # were measured against the same post-drop roster),
    # "OPEN_ROSTER_SLOT_ADD_ONLY" (a real open roster slot means no drop is
    # needed), or "NO_DROP_CANDIDATE_AVAILABLE" (the roster has no drop
    # candidates at all, e.g. an empty roster).
    context_label: str


def rank_waiver_candidates(
    *,
    free_agents: Sequence[Mapping[str, Any]],
    owner_roster_canonical_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    mode: WaiverMode,
    weekly_projections_by_sleeper_id: Mapping[str, WeeklyProjectionRow] | None = None,
    limit: int = 25,
) -> tuple[WaiverCandidate, ...]:
    if mode == "THIS_WEEK" and weekly_projections_by_sleeper_id is None:
        raise ValueError(
            "THIS_WEEK mode requires real weekly projections; the caller must disable this "
            "mode honestly rather than call it with no data."
        )
    candidates: list[WaiverCandidate] = []
    for row in free_agents:
        sleeper_id = str(row.get("sleeperPlayerId") or "")
        canonical_id = str(row.get("playerId") or "")
        position = str(row.get("position") or "")
        weekly_row = (
            weekly_projections_by_sleeper_id.get(sleeper_id) if weekly_projections_by_sleeper_id else None
        )
        if canonical_id:
            utility_result: MarginalRosterUtility | None = marginal_roster_utility_v2(
                canonical_id, owner_roster_canonical_ids, profile, ranking, manual_assets
            )
            identity_status = "MATCHED"
        else:
            utility_result = None
            identity_status = "UNMATCHED_IDENTITY"
        candidates.append(
            WaiverCandidate(
                sleeper_player_id=sleeper_id,
                canonical_player_id=canonical_id,
                player_name=str(row.get("playerName") or ""),
                position=position,
                team=str(row.get("team") or ""),
                ros_replacement_value=row.get("replacementAdjustedValue"),
                ros_overall_rank=row.get("overallRank"),
                weekly_projected_points=weekly_row.projected_points if weekly_row else None,
                marginal_utility=utility_result.utility if utility_result else None,
                becomes_starter=utility_result.becomes_starter if utility_result else False,
                marginal_utility_explanation=(
                    utility_result.explanation if utility_result else "MARGINAL_UTILITY_UNAVAILABLE_UNMATCHED_IDENTITY"
                ),
                identity_status=identity_status,
            )
        )

    def sort_key(candidate: WaiverCandidate) -> tuple:
        # Primary: real marginal roster utility (the same promoted, closed
        # signal live drafting already uses) -- never fabricated when
        # unmatched, which sorts last. THIS_WEEK mode breaks ties with real
        # weekly points when two candidates have equal/near-equal utility.
        primary = candidate.marginal_utility
        secondary = candidate.weekly_projected_points if mode == "THIS_WEEK" else candidate.ros_replacement_value
        return (
            primary is None,
            -(primary or 0.0),
            secondary is None,
            -(secondary or 0.0),
        )

    candidates.sort(key=sort_key)
    return tuple(candidates[:limit])


def rank_drop_candidates(
    *,
    roster_canonical_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    player_names: Mapping[str, str],
    player_positions: Mapping[str, str],
) -> tuple[DropCandidate, ...]:
    """Rank the CURRENT roster's own players by how little marginal value
    they contribute right now -- weakest first, the honest drop-candidate
    order. Computed with the SAME `marginal_roster_utility_v2` call used for
    adds, just pointed at a rostered player against the rest of his own
    roster (never against the closed model's own promoted formula)."""

    drops: list[DropCandidate] = []
    roster_set = list(roster_canonical_ids)
    for player_id in roster_set:
        rest_of_roster = [value for value in roster_set if value != player_id]
        result = marginal_roster_utility_v2(player_id, rest_of_roster, profile, ranking, manual_assets)
        drops.append(
            DropCandidate(
                canonical_player_id=player_id,
                player_name=player_names.get(player_id, player_id),
                position=player_positions.get(player_id, ""),
                marginal_utility=result.utility,
                explanation=result.explanation,
            )
        )
    drops.sort(key=lambda candidate: (candidate.marginal_utility is None, candidate.marginal_utility or 0.0))
    return tuple(drops)


def pair_add_drop(
    *,
    add_candidates: Sequence[WaiverCandidate],
    drop_candidates: Sequence[DropCandidate],
    owner_roster_canonical_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    open_slot_available: bool | None = None,
    top_n: int = 10,
) -> tuple[AddDropPairing, ...]:
    """Pairs each top ADD with the single weakest real roster piece
    (`drop_candidates[0]`, already ranked ascending by real marginal
    utility). A genuine, disclosed simplification: this does not solve a
    joint multi-add/multi-drop assignment across several simultaneous
    moves, only the single best drop for one add at a time.

    Same-context repair (Waiver Night V1, Section 4): the reported "net"
    value must compare the add and the drop against the SAME roster, or the
    difference is meaningless. Before this fix, the add's own value came
    from `rank_waiver_candidates` (computed against the owner's ORIGINAL
    roster, drop candidate still on it) while the drop's own value came
    from `rank_drop_candidates` (computed against the roster with the drop
    candidate already removed) -- two different reference rosters
    subtracted from each other. Fixed here: this function constructs the
    roster AFTER removing the weakest real drop and evaluates the add
    candidate against THAT roster too (`add_utility_vs_post_drop_roster`),
    through the SAME unmodified `marginal_roster_utility_v2` authority
    `rank_drop_candidates` already used for the drop's own value -- no
    retuning, no reimplementation, just a second, same-context call. The
    drop's own value was already computed against this exact post-drop
    roster, so it needs no recomputation. The result is a real, same-context
    marginal comparison -- explicitly NOT an authoritative "total-roster" or
    "completed-transaction" utility, since this codebase defines no such
    objective anywhere else.

    Open-slot handling: `open_slot_available=True` (a real, verified open
    non-reserve roster slot -- never inferred from how many roster ids
    happened to resolve to a canonical identity) means the add is legal on
    its own; every pairing then carries `drop=None`/`drop_required=False`
    and `net_marginal_utility` is simply the add's own value against the
    roster as it stands today (there is no drop, so no second context to
    compare against). `None` (unverifiable) is treated the same as `False`
    here -- the conservative default is to keep showing the real weakest
    drop as a suggestion, never to silently assume an open slot exists.
    """

    weakest_drop = drop_candidates[0] if drop_candidates else None
    roster_after_weakest_drop: list[str] | None = None
    if weakest_drop is not None:
        roster_after_weakest_drop = [
            player_id for player_id in owner_roster_canonical_ids if player_id != weakest_drop.canonical_player_id
        ]

    pairings: list[AddDropPairing] = []
    for add in add_candidates[:top_n]:
        if open_slot_available is True:
            pairings.append(
                AddDropPairing(
                    add=add,
                    drop=None,
                    drop_required=False,
                    add_utility_vs_original_roster=add.marginal_utility,
                    add_utility_vs_post_drop_roster=None,
                    drop_utility_vs_post_drop_roster=None,
                    net_marginal_utility=add.marginal_utility,
                    context_label="OPEN_ROSTER_SLOT_ADD_ONLY",
                )
            )
            continue

        if weakest_drop is None:
            pairings.append(
                AddDropPairing(
                    add=add,
                    drop=None,
                    drop_required=False,
                    add_utility_vs_original_roster=add.marginal_utility,
                    add_utility_vs_post_drop_roster=None,
                    drop_utility_vs_post_drop_roster=None,
                    net_marginal_utility=None,
                    context_label="NO_DROP_CANDIDATE_AVAILABLE",
                )
            )
            continue

        add_utility_after_drop: float | None = None
        net: float | None = None
        if (
            add.canonical_player_id
            and add.marginal_utility is not None
            and weakest_drop.marginal_utility is not None
            and roster_after_weakest_drop is not None
        ):
            after_drop_result = marginal_roster_utility_v2(
                add.canonical_player_id, roster_after_weakest_drop, profile, ranking, manual_assets
            )
            add_utility_after_drop = after_drop_result.utility
            net = round(add_utility_after_drop - weakest_drop.marginal_utility, 2)

        pairings.append(
            AddDropPairing(
                add=add,
                drop=weakest_drop,
                drop_required=True,
                add_utility_vs_original_roster=add.marginal_utility,
                add_utility_vs_post_drop_roster=add_utility_after_drop,
                drop_utility_vs_post_drop_roster=weakest_drop.marginal_utility,
                net_marginal_utility=net,
                context_label="SAME_CONTEXT_MARGINAL_COMPARISON",
            )
        )
    return tuple(pairings)


# NWR Post-Closure Fix V1: the contract-facing 3-tier urgency scale
# (`weekly-shared.tsx`'s `FAAB_URGENCY_TONE`, `improve-team.tsx`'s
# `FAAB_URGENCY_RANK`, and `contracts/src/index.ts`'s `faabUrgency` type) has
# always promised HIGH/MEDIUM/LOW. This module's own real, more descriptive
# internal reasoning (a starter-upgrade opportunity vs. bench depth vs. low
# real value) maps onto that scale one-to-one and is still fully preserved
# in the separate `rationale` string every caller already renders --
# nothing informative is lost by exposing the tier here, not the reason.
FAAB_URGENCY_TIER: dict[str, str] = {
    "STARTER_UPGRADE": "HIGH",
    "BENCH_DEPTH": "MEDIUM",
    "LOW_VALUE": "LOW",
}


@dataclass(frozen=True)
class FaabBidSuggestion:
    canonical_player_id: str
    player_name: str
    bid_low_pct: float
    bid_high_pct: float
    bid_low_dollars: int
    bid_high_dollars: int
    urgency: str  # HIGH | MEDIUM | LOW -- the shared contract's 3-tier scale (see FAAB_URGENCY_TIER)
    percentile_in_pool: float | None
    rationale: str


def suggest_faab_bids(
    *,
    candidates: Sequence[WaiverCandidate],
    remaining_budget_dollars: int,
    weeks_remaining: int,
    total_budget_dollars: int = 100,
) -> tuple[FaabBidSuggestion, ...]:
    """Contextual bid range, not a static universal percentage table --
    every candidate's range is computed from the REAL, live utility
    distribution of the candidates passed in this call plus real roster
    urgency and weeks-remaining context. No acceptance-probability /
    likely-competition figure is fabricated -- this app has no real signal
    for that.

    Two floors/gates, applied BEFORE the positive-utility pricing formula
    below (which is itself unchanged): an unmatched identity (no real
    signal at all) and a zero-or-negative real `marginal_roster_utility_v2`
    value (a real signal that says "not worth paying for") both produce a
    non-positive ($0) result, never a fabricated positive bid -- see the
    two distinctly-worded `rationale` strings below for why they are
    different reasons, not the same "no bid" state.

    KNOWN LIMITATION, surfaced to the owner (see `FaabTab`'s caption in
    `improve-team.tsx`, not just this comment): the POSITIVE dollar amounts
    this function produces are a real, contextual, percentile-of-pool
    heuristic -- they are NOT calibrated against real FAAB auction/market
    outcomes (no historical "what did this bid actually cost to win"
    dataset feeds this formula). Treat the positive ranges as a relative
    ordering signal (who is worth more than whom, and roughly how much
    more), not a guaranteed market-clearing price.
    """

    if remaining_budget_dollars < 0 or total_budget_dollars <= 0 or weeks_remaining < 0:
        raise ValueError("Invalid FAAB context.")
    utilities = sorted(
        (candidate.marginal_utility for candidate in candidates if candidate.marginal_utility is not None),
        reverse=True,
    )
    suggestions: list[FaabBidSuggestion] = []
    for candidate in candidates:
        if candidate.marginal_utility is None:
            suggestions.append(
                FaabBidSuggestion(
                    canonical_player_id=candidate.canonical_player_id,
                    player_name=candidate.player_name,
                    bid_low_pct=0.0, bid_high_pct=0.0, bid_low_dollars=0, bid_high_dollars=0,
                    urgency=FAAB_URGENCY_TIER["LOW_VALUE"], percentile_in_pool=None,
                    rationale=(
                        "Unknown identity -- this player could not be matched to NWR's own ranking, so no "
                        "real marginal-utility signal exists to price a bid from. No positive bid is "
                        "suggested. A $0 result here does NOT mean the player has no value -- only that "
                        "NWR has no real signal to price a claim on him."
                    ),
                )
            )
            continue
        rank = utilities.index(candidate.marginal_utility)
        percentile = 1.0 - (rank / max(1, len(utilities) - 1)) if len(utilities) > 1 else 1.0
        # NWR Waiver Night V1 (Worker 2, FAAB nonpositive-bid fix): a zero or
        # negative real `marginal_roster_utility_v2` value means NWR's own
        # (closed, unmodified) valuation model has already judged this add
        # is not worth paying for -- never a positive paid recommendation,
        # regardless of where it happens to rank within THIS pool's
        # percentile. This is a floor/gate on top of the existing pricing
        # formula, not a change to it: the positive-utility branch below
        # (percentile -> base_low/base_high -> urgency multiplier -> season
        # taper -> dollars) is completely unreached and unmodified for any
        # candidate that gets here. The rationale below is deliberately
        # worded differently from the UNMATCHED_IDENTITY $0 case above: that
        # case means "no real signal was computed at all"; this case means
        # "a real signal WAS computed, and it says not to pay" -- the two
        # are different reasons for a non-positive result and must read
        # differently to the owner, per the directive.
        if candidate.marginal_utility <= 0:
            suggestions.append(
                FaabBidSuggestion(
                    canonical_player_id=candidate.canonical_player_id,
                    player_name=candidate.player_name,
                    bid_low_pct=0.0, bid_high_pct=0.0, bid_low_dollars=0, bid_high_dollars=0,
                    urgency=FAAB_URGENCY_TIER["LOW_VALUE"], percentile_in_pool=round(percentile, 3),
                    rationale=(
                        "Modeled nonpositive value -- NWR's own marginal-roster-utility model rates this "
                        f"add at {candidate.marginal_utility:.1f} for your current roster (not a missing "
                        "signal, a real computed judgment). No positive bid is suggested. A $0 result here "
                        "does NOT mean the player has no future value -- only that no paid claim is "
                        "justified against your roster right now."
                    ),
                )
            )
            continue
        urgency_reason = "STARTER_UPGRADE" if candidate.becomes_starter else "BENCH_DEPTH"
        # Base range scales with real percentile standing in THIS pool, not
        # a fixed lookup table. Starter upgrades get a real, disclosed
        # urgency multiplier; bench depth does not. Season-lateness tapers
        # the range down (fewer real weeks left to realize the value).
        base_low = 0.02 + 0.28 * percentile
        base_high = 0.05 + 0.45 * percentile
        urgency_multiplier = 1.4 if urgency_reason == "STARTER_UPGRADE" else 1.0
        season_taper = min(1.0, max(0.35, weeks_remaining / 14.0))
        low_pct = min(0.95, base_low * urgency_multiplier * season_taper)
        high_pct = min(0.98, base_high * urgency_multiplier * season_taper)
        low_dollars = round(remaining_budget_dollars * low_pct)
        high_dollars = round(remaining_budget_dollars * high_pct)
        suggestions.append(
            FaabBidSuggestion(
                canonical_player_id=candidate.canonical_player_id,
                player_name=candidate.player_name,
                bid_low_pct=round(low_pct, 3), bid_high_pct=round(high_pct, 3),
                bid_low_dollars=low_dollars, bid_high_dollars=high_dollars,
                urgency=FAAB_URGENCY_TIER[urgency_reason], percentile_in_pool=round(percentile, 3),
                rationale=(
                    f"{'Real starter upgrade' if urgency_reason == 'STARTER_UPGRADE' else 'Bench depth' if urgency_reason == 'BENCH_DEPTH' else 'Low real value'}; "
                    f"marginal utility {candidate.marginal_utility:.1f} ranks at the {percentile:.0%} "
                    # Waiver Night V1 (Section 5, THIS_WEEK honesty): this
                    # rationale used to say "this week's real free-agent
                    # pool" regardless of mode -- but `candidate.marginal_
                    # utility` (what this percentile is actually computed
                    # from, both here and in `rank_waiver_candidates`' own
                    # sort key) is always the real REST_OF_SEASON-oriented
                    # marginal-roster-utility signal, never a weekly value,
                    # in EITHER mode. "this week's" was never accurate; it
                    # is horizon-neutral now, and the season-taper input is
                    # labeled for what it actually is (season weeks left).
                    f"percentile of this real free-agent pool, {weeks_remaining} season weeks remaining."
                ),
            )
        )
    return tuple(suggestions)
