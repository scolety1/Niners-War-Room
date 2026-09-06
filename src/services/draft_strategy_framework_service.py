"""Baseline draft strategy framework (directive section 8).

A common `DraftStrategy` interface so historical replay (and, later,
prospective Draft Room experiments) can compare named strategies under
identical inputs: league rules, pick number, available players, roster,
point-in-time features, and point-in-time market -- never future picks or
outcomes. Every strategy returns the same `StrategyDecision` shape:
selected player, full candidate ranking, decision metadata, runtime, and a
strategy version string, so results are comparable and reproducible.

The three "optimizer" strategies (TEAM_SCORE_OPTIMIZER,
CHAMPIONSHIP_EQUITY_OPTIMIZER, PICK_SCORE_OPTIMIZER) do not reimplement
Team Score / Championship Equity / Pick Score here -- they are thin greedy
wrappers around a caller-supplied `candidate_evaluator` callback, so the
SAME real, unmodified `shadow_numeric_authorities_service` functions this
session already built and tested can be plugged in directly (see
`shadow_numeric_authorities_candidate_evaluator` below), rather than a
second, drifting implementation living in this module.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from src.services.point_in_time_feature_store_service import (
    KNOWN,
    PointInTimeFeatureStore,
)

STRATEGY_PLATFORM_ADP = "PLATFORM_ADP"
STRATEGY_STANDARD_VBD = "STANDARD_VBD"
STRATEGY_GREEDY_NWR = "GREEDY_NWR"
STRATEGY_CURRENT_NWR_DRAFT_HEURISTIC = "CURRENT_NWR_DRAFT_HEURISTIC"
STRATEGY_TEAM_SCORE_OPTIMIZER = "TEAM_SCORE_OPTIMIZER"
STRATEGY_CHAMPIONSHIP_EQUITY_OPTIMIZER = "CHAMPIONSHIP_EQUITY_OPTIMIZER"
STRATEGY_PICK_SCORE_OPTIMIZER = "PICK_SCORE_OPTIMIZER"
STRATEGY_ROSTER_CAPPED_GREEDY_NWR = "ROSTER_CAPPED_GREEDY_NWR"

BASELINE_STRATEGY_NAMES = frozenset(
    {
        STRATEGY_PLATFORM_ADP,
        STRATEGY_STANDARD_VBD,
        STRATEGY_GREEDY_NWR,
        STRATEGY_CURRENT_NWR_DRAFT_HEURISTIC,
        STRATEGY_TEAM_SCORE_OPTIMIZER,
        STRATEGY_CHAMPIONSHIP_EQUITY_OPTIMIZER,
        STRATEGY_PICK_SCORE_OPTIMIZER,
        STRATEGY_ROSTER_CAPPED_GREEDY_NWR,
    }
)


class DraftStrategyError(ValueError):
    pass


@dataclass(frozen=True)
class StrategyDecisionContext:
    """Everything a strategy is allowed to see for one pick. No field here
    may ever be populated with data from a later pick -- callers building
    this for historical replay must derive `as_of` from the real historical
    draft_date of THIS pick, not "now"."""

    league_rules_summary: Mapping[str, Any]  # team_count, roster slots, scoring -- caller's shape
    pick_number: int
    round_number: int
    available_player_ids: tuple[str, ...]
    roster_player_ids: tuple[str, ...]
    feature_store: PointInTimeFeatureStore
    as_of: str
    season: int
    seed: int = 0


@dataclass(frozen=True)
class StrategyDecision:
    strategy_name: str
    strategy_version: str
    selected_player_id: str | None
    candidate_ranking: tuple[str, ...]
    decision_metadata: Mapping[str, Any]
    runtime_seconds: float


DraftStrategy = Callable[[StrategyDecisionContext], StrategyDecision]


def _timed(
    strategy_name: str,
    strategy_version: str,
    context: StrategyDecisionContext,
    rank_fn: Callable[[str], float | None],
    *,
    higher_is_better: bool,
    metadata_extra: Mapping[str, Any] | None = None,
) -> StrategyDecision:
    """Shared scaffolding for every ranking-based strategy below: times the
    ranking call, drops players with no resolvable value (never fabricates
    a rank for an UNKNOWN feature), and orders the rest."""
    start = time.perf_counter()
    scored: list[tuple[str, float]] = []
    unresolved: list[str] = []
    for player_id in context.available_player_ids:
        value = rank_fn(player_id)
        if value is None:
            unresolved.append(player_id)
        else:
            scored.append((player_id, value))
    scored.sort(key=lambda item: item[1], reverse=higher_is_better)
    ranking = tuple(player_id for player_id, _ in scored)
    elapsed = time.perf_counter() - start
    metadata: dict[str, Any] = {"unresolved_player_ids": tuple(unresolved)}
    if metadata_extra:
        metadata.update(metadata_extra)
    return StrategyDecision(
        strategy_name=strategy_name,
        strategy_version=strategy_version,
        selected_player_id=ranking[0] if ranking else None,
        candidate_ranking=ranking,
        decision_metadata=metadata,
        runtime_seconds=round(elapsed, 6),
    )


def platform_adp_strategy(context: StrategyDecisionContext) -> StrategyDecision:
    """Lowest platform ADP available, as-of this pick's decision date."""

    def value_of(player_id: str) -> float | None:
        feature = context.feature_store.lookup_as_of(
            player_id=player_id,
            season=context.season,
            feature_name="market.overall_adp",
            as_of=context.as_of,
        )
        return float(feature.value) if feature.value_status == KNOWN else None

    return _timed(STRATEGY_PLATFORM_ADP, "v1", context, value_of, higher_is_better=False)


def standard_vbd_strategy(context: StrategyDecisionContext) -> StrategyDecision:
    """Highest `replacement_level.value_over_replacement` feature, as-of
    this pick. The feature itself must already be point-in-time computed by
    the caller (VBD needs a full replacement-level calculation, which this
    generic framework does not reimplement -- see
    redraft_engine_v1_service.calculate_replacement_levels for the real
    production formula)."""

    def value_of(player_id: str) -> float | None:
        feature = context.feature_store.lookup_as_of(
            player_id=player_id,
            season=context.season,
            feature_name="replacement_level.value_over_replacement",
            as_of=context.as_of,
        )
        return float(feature.value) if feature.value_status == KNOWN else None

    return _timed(STRATEGY_STANDARD_VBD, "v1", context, value_of, higher_is_better=True)


def greedy_nwr_strategy(context: StrategyDecisionContext) -> StrategyDecision:
    """Best (lowest) `nwr_component_scores.overall_rank` feature available.

    KNOWN LIMITATION (NWR Full Historical Walk-Forward Validation program,
    2026-09-06): this strategy has NO positional-slot gating by design --
    at team_count >= 8 in real historical seasons this has been observed to
    draft a single position exclusively (e.g. 6/6 picks at QB into a
    roster that can only ever start 1), producing a catastrophically weak
    real roster despite the underlying `overall_rank` feature itself being
    real and decisive (see NWR_PLAYER_SCORE_HISTORICAL_VALIDATION_V1_REPORT
    and NWR_HISTORICAL_DRAFT_SIMULATION_V1_REPORT). Prefer
    `make_roster_capped_greedy_nwr_strategy()` for anything resembling a
    real drafting comparison; this function is kept, unmodified, as the
    deliberately-naive baseline it was always documented to be."""

    def value_of(player_id: str) -> float | None:
        feature = context.feature_store.lookup_as_of(
            player_id=player_id,
            season=context.season,
            feature_name="nwr_component_scores.overall_rank",
            as_of=context.as_of,
        )
        return float(feature.value) if feature.value_status == KNOWN else None

    return _timed(STRATEGY_GREEDY_NWR, "v1", context, value_of, higher_is_better=False)


def current_nwr_draft_heuristic_strategy(context: StrategyDecisionContext) -> StrategyDecision:
    """The production Draft Room's own current pick heuristic: best NWR
    rank, tie-broken toward the shallowest starter hole in the roster so
    far -- a deliberately simple, literal mirror of "take the best player
    NWR ranks, prefer a positional need on ties," not a new invention.

    KNOWN LIMITATION (NWR Full Historical Walk-Forward Validation program,
    2026-09-06): the `-0.5` tie-break nudge below is trivially overwhelmed
    whenever the real NWR rank gap between positions exceeds half a rank
    point, which is routine -- this strategy has been observed to produce
    the same catastrophic single-position rosters as `greedy_nwr_strategy`
    in real historical seasons. It also silently no-ops whenever no caller
    populates `league_rules_summary["open_starter_positions"]` (true of
    every corpus-building script in this program to date). Prefer
    `make_roster_capped_greedy_nwr_strategy()` for anything resembling a
    real drafting comparison; kept, unmodified, for historical
    reproducibility of prior reports that reference it by name."""
    need_positions = frozenset(context.league_rules_summary.get("open_starter_positions", ()))

    def value_of(player_id: str) -> float | None:
        rank_feature = context.feature_store.lookup_as_of(
            player_id=player_id,
            season=context.season,
            feature_name="nwr_component_scores.overall_rank",
            as_of=context.as_of,
        )
        if rank_feature.value_status != KNOWN:
            return None
        position_feature = context.feature_store.lookup_as_of(
            player_id=player_id,
            season=context.season,
            feature_name="position",
            as_of=context.as_of,
        )
        needs_bonus = 0.0
        if position_feature.value_status == KNOWN and position_feature.value in need_positions:
            needs_bonus = -0.5  # small tie-break nudge toward roster need, lower rank wins
        return float(rank_feature.value) + needs_bonus

    return _timed(
        STRATEGY_CURRENT_NWR_DRAFT_HEURISTIC, "v1", context, value_of, higher_is_better=False
    )


FLEX_ELIGIBLE_POSITIONS = frozenset({"RB", "WR", "TE"})
SUPERFLEX_ELIGIBLE_POSITIONS = frozenset({"QB", "RB", "WR", "TE"})
DEDICATED_SLOT_POSITIONS = frozenset({"QB", "RB", "WR", "TE", "K", "DST"})


def compute_position_caps(roster_slots: Mapping[str, int]) -> dict[str, int]:
    """Real, league-config-derived per-position draft caps -- NEVER a
    universal constant. `roster_slots` mirrors `redraft_engine_v1_service.
    RosterSettings`'s own field names (qb, rb, wr, te, flex, superflex, k,
    dst, bench_size) so a caller can pass that dataclass's `__dict__`
    directly. For each dedicated position, the cap is an UPPER BOUND: its
    own starter slots, plus every flex/superflex slot it could legally
    fill, plus the full bench -- generous enough to never make a legal
    roster construction impossible (a 2QB or Superflex league correctly
    gets a higher QB cap; a 0-bench league correctly gets a tighter cap
    everywhere), while still preventing the catastrophic single-position
    hoarding this program found in real historical replays (see
    NWR_HISTORICAL_DRAFT_SIMULATION_V1_REPORT_20260906.md)."""
    bench = int(roster_slots.get("bench_size", 0))
    flex = int(roster_slots.get("flex", 0))
    superflex = int(roster_slots.get("superflex", 0))
    caps: dict[str, int] = {}
    for position in DEDICATED_SLOT_POSITIONS:
        starters = int(roster_slots.get(position.lower(), 0))
        if starters == 0 and position not in {"QB", "RB", "WR", "TE"}:
            continue  # e.g. K/DST not rostered at all in this league -- no cap needed
        cap = starters + bench
        if position in FLEX_ELIGIBLE_POSITIONS:
            cap += flex
        if position in SUPERFLEX_ELIGIBLE_POSITIONS:
            cap += superflex
        caps[position] = max(cap, 1)  # never cap a startable position below 1
    return caps


def make_roster_capped_greedy_nwr_strategy(roster_slots: Mapping[str, int]) -> DraftStrategy:
    """The real fix for `greedy_nwr_strategy`'s discovered defect: the
    SAME real `nwr_component_scores.overall_rank` value function, plus a
    HARD exclusion (never a soft nudge) once a position reaches its real,
    league-config-derived cap from `compute_position_caps()`. Tested at
    team_count=12 across all 9 development seasons: beats the original
    heuristic 9/9 seasons, beats real historical ADP 6/9 seasons (see
    NWR_HISTORICAL_DRAFT_SIMULATION_V1_REPORT_20260906.md)."""
    caps = compute_position_caps(roster_slots)

    def strategy(context: StrategyDecisionContext) -> StrategyDecision:
        position_counts: dict[str, int] = {}
        for player_id in context.roster_player_ids:
            pos_feature = context.feature_store.lookup_as_of(
                player_id=player_id, season=context.season,
                feature_name="position", as_of=context.as_of,
            )
            if pos_feature.value_status == KNOWN:
                pos = str(pos_feature.value)
                position_counts[pos] = position_counts.get(pos, 0) + 1

        def rank_of(player_id: str) -> float | None:
            rank_feature = context.feature_store.lookup_as_of(
                player_id=player_id, season=context.season,
                feature_name="nwr_component_scores.overall_rank", as_of=context.as_of,
            )
            return float(rank_feature.value) if rank_feature.value_status == KNOWN else None

        def position_of(player_id: str) -> str | None:
            position_feature = context.feature_store.lookup_as_of(
                player_id=player_id, season=context.season,
                feature_name="position", as_of=context.as_of,
            )
            return str(position_feature.value) if position_feature.value_status == KNOWN else None

        def value_of(player_id: str) -> float | None:
            position = position_of(player_id)
            if position in caps and position_counts.get(position, 0) >= caps[position]:
                return None  # HARD exclusion -- at real legal cap for this league
            return rank_of(player_id)

        decision = _timed(
            STRATEGY_ROSTER_CAPPED_GREEDY_NWR, "v1", context, value_of,
            higher_is_better=False, metadata_extra={"position_caps": dict(caps)},
        )
        if decision.selected_player_id is not None or not context.available_player_ids:
            return decision
        # Real edge case (e.g. very few real players left in a thin
        # historical pool): every remaining player is at a capped
        # position. Fall back to the uncapped ranking rather than
        # returning no pick at all -- disclosed in metadata, not silent.
        fallback = _timed(
            STRATEGY_ROSTER_CAPPED_GREEDY_NWR, "v1", context, rank_of,
            higher_is_better=False,
            metadata_extra={"position_caps": dict(caps), "cap_fallback_triggered": True},
        )
        return fallback

    return strategy


CandidateEvaluator = Callable[[str, StrategyDecisionContext], float | None]


def make_optimizer_strategy(
    name: str,
    evaluator: CandidateEvaluator,
    *,
    version: str,
) -> DraftStrategy:
    """Builds a greedy-argmax strategy over any real evaluator callback.
    This is how TEAM_SCORE_OPTIMIZER / CHAMPIONSHIP_EQUITY_OPTIMIZER /
    PICK_SCORE_OPTIMIZER plug in the real
    shadow_numeric_authorities_service functions without this module
    reimplementing them."""
    if name not in BASELINE_STRATEGY_NAMES:
        raise DraftStrategyError(f"Unknown optimizer strategy name: {name!r}")

    def strategy(context: StrategyDecisionContext) -> StrategyDecision:
        def value_of(player_id: str) -> float | None:
            return evaluator(player_id, context)

        return _timed(
            name,
            version,
            context,
            value_of,
            higher_is_better=True,
            metadata_extra={"evaluator": "caller_supplied"},
        )

    return strategy


def baseline_strategy_registry(
    *,
    team_score_evaluator: CandidateEvaluator | None = None,
    championship_equity_evaluator: CandidateEvaluator | None = None,
    pick_score_evaluator: CandidateEvaluator | None = None,
    roster_slots: Mapping[str, int] | None = None,
) -> dict[str, DraftStrategy]:
    """Assembles every named strategy this section requires into one
    registry, ready to hand to a replay runner. The three optimizer slots
    are omitted (not silently stubbed) when no evaluator is supplied --
    a caller inspects the registry's keys rather than getting a strategy
    that would silently no-op. `ROSTER_CAPPED_GREEDY_NWR` is likewise
    omitted unless `roster_slots` (mirroring `RosterSettings`'s own field
    names) is supplied -- it needs a real league shape to derive real,
    league-config-specific caps from, never an arbitrary universal
    constant. Existing callers that never pass `roster_slots` see an
    UNCHANGED registry -- this is purely additive."""
    registry: dict[str, DraftStrategy] = {
        STRATEGY_PLATFORM_ADP: platform_adp_strategy,
        STRATEGY_STANDARD_VBD: standard_vbd_strategy,
        STRATEGY_GREEDY_NWR: greedy_nwr_strategy,
        STRATEGY_CURRENT_NWR_DRAFT_HEURISTIC: current_nwr_draft_heuristic_strategy,
    }
    if roster_slots is not None:
        registry[STRATEGY_ROSTER_CAPPED_GREEDY_NWR] = make_roster_capped_greedy_nwr_strategy(
            roster_slots
        )
    if team_score_evaluator is not None:
        registry[STRATEGY_TEAM_SCORE_OPTIMIZER] = make_optimizer_strategy(
            STRATEGY_TEAM_SCORE_OPTIMIZER, team_score_evaluator, version="v1"
        )
    if championship_equity_evaluator is not None:
        registry[STRATEGY_CHAMPIONSHIP_EQUITY_OPTIMIZER] = make_optimizer_strategy(
            STRATEGY_CHAMPIONSHIP_EQUITY_OPTIMIZER, championship_equity_evaluator, version="v1"
        )
    if pick_score_evaluator is not None:
        registry[STRATEGY_PICK_SCORE_OPTIMIZER] = make_optimizer_strategy(
            STRATEGY_PICK_SCORE_OPTIMIZER, pick_score_evaluator, version="v1"
        )
    return registry
