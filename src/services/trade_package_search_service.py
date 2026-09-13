"""Trade Package Search (NWR Post-UI Product V1, P1-3, Worker 6 -- BACKEND
half; a separate worker builds the UI on top of this module).

Trade Finder (`trade_finder_service.py`) only ever generates 1-for-1
packages. Trade Analysis's own `evaluate_trade`
(`redraft_trade_analysis_service.py`) already accepts arbitrary
`gives_ids`/`receives_ids` lists -- it is a real, already-tested
MULTI-PLAYER evaluator, just never driven by a search layer that proposes
multi-player packages. This module is that missing search layer: it
GENERATES 1-for-1, 2-for-1, 1-for-2, and 2-for-2 candidate packages and
scores every one of them by calling `evaluate_trade` TWICE per candidate
(once from the owner's roster perspective, once from the counterparty's) --
the exact same pattern `find_win_win_trades` already uses for 1-for-1, now
extended to bounded multi-player packages. No new scoring formula is
introduced; this module is pure candidate generation + pruning + gating on
top of the existing, unmodified evaluator.

Preregistered quality gates (written BEFORE this file, per this project's
own discipline): see
`docs/codex/post_ui_v1/TRADE_PACKAGE_SEARCH_QUALITY_GATES_P1_3.md`. Every
constant and rule below matches that document exactly.

Three modes:
  * FIND_WIN_WIN -- broad search across every opponent for mutually
    beneficial packages (extends Trade Finder's own 1-for-1-only search).
  * TARGET_PLAYER -- the owner names one specific player they want; search
    is scoped to whichever opponent roster actually holds that player, and
    every receive-combo is forced to include the target.
  * IMPROVE_POSITION -- the owner names a position of need; every
    receive-combo is forced to include a real player at that position,
    drawn from opponents' own rosters at that position (ranked by real ROS
    value, not by "weakest bench piece" -- a deliberately different signal
    than the other two modes, see the gates doc, section 6).

Explicitly NOT included, per the product spec: an acceptance-probability /
"likely to accept" score, in any mode, for any package. `why_it_may_fit_them`
is a structured list of REAL computed deltas from the counterparty's own
`evaluate_trade` result -- never a fabricated likelihood.

Disclosed omission: weekly starting-lineup impact (mentioned as an OPTIONAL
signal in `redraft_trade_analysis_service.py`'s own docstring) is not
computed here. `evaluate_trade` itself does not currently wire
`weekly_lineup_optimizer_service` for any caller (confirmed by reading its
full body -- no such call exists), so there is nothing real for this search
layer to reuse; computing it independently, per candidate, per side, per
opponent, across a bounded-but-still-multi-hundred-candidate search would
require pulling real weekly projections for every roster in the league and
re-running the weekly optimizer per candidate -- a real latency and scope
risk for a first pass. Left as a disclosed, precisely-scoped follow-up
rather than fabricated or bolted on unsafely.

Reuse, not reinvention:
  * `redraft_trade_analysis_service.evaluate_trade` -- the SAME real
    multi-player roster-before/after evaluator (ROS value, marginal
    utility, starting-lineup value, bench contingency, position redundancy,
    status risk flags) used by Trade Analysis, called read-only, never
    duplicated.
  * `waiver_engine_service.rank_drop_candidates` -- the SAME real
    ascending-marginal-utility "weakest roster piece first" ranking used by
    Trade Finder, reused here as the candidate-pool ordering for both
    FIND_WIN_WIN and TARGET_PLAYER filler slots.
  * `shadow_numeric_authorities_service._asset_pool` -- the SAME real ROS
    value pool, reused (read-only) for IMPROVE_POSITION's by-position
    ranking.
  * `redraft_roster_legality_service._normalized_position` -- the SAME
    D/ST-vs-DEF-vs-DST position-name normalization already used by the
    canonical (draft-time) legality authority, reused here for position
    matching so this module never invents a second normalization rule.

Hard boundaries respected (read-only call sites only): `evaluate_trade`'s
own math, `marginal_roster_utility_v2`'s own computation,
`redraft_roster_legality_service.py`'s own draft-time rules, `LeagueProfile`
/ `RankingResult` semantics -- none of these are modified by this file.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from src.services.current_player_status_overrides_service import StatusOverride
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.redraft_roster_legality_service import _normalized_position
from src.services.redraft_trade_analysis_service import TradeAnalysisError, TradeEvaluation, evaluate_trade
from src.services.shadow_numeric_authorities_service import _asset_pool
from src.services.waiver_engine_service import rank_drop_candidates

TradeSearchMode = Literal["TARGET_PLAYER", "FIND_WIN_WIN", "IMPROVE_POSITION"]

# --- Preregistered pruning/gate constants (see the gates doc above) -------
DEFAULT_CANDIDATES_PER_SIDE = 6
MAX_PACKAGE_SIZE = 2
MAX_PACKAGES_EVALUATED_PER_OPPONENT = 120
MAX_TOTAL_PACKAGES_EVALUATED = 900
DEFAULT_LIMIT = 15


@dataclass(frozen=True)
class TradePackageCandidate:
    opponent_roster_id: str
    opponent_team_name: str
    package_shape: str  # "1-for-1" | "2-for-1" | "1-for-2" | "2-for-2"
    you_send: tuple[str, ...]  # canonical player ids, owner's perspective
    you_receive: tuple[str, ...]
    you_send_names: tuple[str, ...]
    you_receive_names: tuple[str, ...]
    owner_evaluation: TradeEvaluation
    opponent_evaluation: TradeEvaluation
    why_it_helps_you: tuple[str, ...]
    why_it_may_fit_them: tuple[str, ...]


@dataclass(frozen=True)
class TradePackageSearchResult:
    mode: TradeSearchMode
    candidates: tuple[TradePackageCandidate, ...]
    packages_evaluated: int
    opponents_searched: int
    truncated: bool  # True if a hard search cap was hit before exhausting the space


def _opp_ids(opponent: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(opponent.get("canonicalIds") or ())


def _opp_names(opponent: Mapping[str, Any]) -> Mapping[str, str]:
    return opponent.get("names") or {}


def _opp_positions(opponent: Mapping[str, Any]) -> Mapping[str, str]:
    return opponent.get("positions") or {}


def _total_roster_slots(profile: LeagueProfile) -> int:
    r = profile.roster
    return r.qb + r.rb + r.wr + r.te + r.flex + r.superflex + r.k + r.dst + r.bench_size


def _roster_size_legal(
    roster_before_ids: Sequence[str], gives_ids: Sequence[str], receives_ids: Sequence[str], profile: LeagueProfile
) -> bool:
    """Post-draft roster-size legality (gate 1). NOT a change to
    `redraft_roster_legality_service.py`'s own draft-time rules -- see the
    gates doc for why position maxima are intentionally not enforced here.
    """

    after_count = len(roster_before_ids) - len(set(gives_ids)) + len(set(receives_ids))
    return 0 <= after_count <= _total_roster_slots(profile)


def _weakest_first_pool_ids(
    *,
    roster_ids: Sequence[str],
    names: Mapping[str, str],
    positions: Mapping[str, str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    top_k: int,
) -> tuple[str, ...]:
    drops = rank_drop_candidates(
        roster_canonical_ids=roster_ids, profile=profile, ranking=ranking, manual_assets=manual_assets,
        player_names=names, player_positions=positions,
    )
    return tuple(candidate.canonical_player_id for candidate in drops[:top_k])


def _by_position_pool_ids(
    *,
    roster_ids: Sequence[str],
    positions: Mapping[str, str],
    position: str,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    top_k: int,
) -> tuple[str, ...]:
    pool = _asset_pool(ranking, manual_assets)
    wanted = _normalized_position(position)
    matches = [
        player_id for player_id in roster_ids if _normalized_position(positions.get(player_id)) == wanted
    ]
    matches.sort(
        key=lambda player_id: -float((pool.get(player_id) or {}).get("replacement_adjusted_value") or 0.0)
    )
    return tuple(matches[:top_k])


def _combos(ids: Sequence[str], max_size: int = MAX_PACKAGE_SIZE) -> list[tuple[str, ...]]:
    combos: list[tuple[str, ...]] = []
    for size in range(1, max_size + 1):
        combos.extend(itertools.combinations(ids, size))
    return combos


def _package_shape(n_give: int, n_receive: int) -> str:
    return f"{n_give}-for-{n_receive}"


def _passes_utility_gates(
    *, mode: TradeSearchMode, owner_eval: TradeEvaluation, opponent_eval: TradeEvaluation, target_player_id: str | None
) -> bool:
    """Gates 2 and 3 from the preregistered doc, applied exactly as
    written -- no tuning after seeing results."""

    if owner_eval.net_marginal_utility is None or opponent_eval.net_marginal_utility is None:
        return False
    if mode == "TARGET_PLAYER":
        target_impact = next(
            (impact for impact in owner_eval.receives if impact.player_id == target_player_id), None
        )
        if target_impact is None or target_impact.marginal_utility is None or target_impact.marginal_utility <= 0.0:
            return False
        return opponent_eval.net_marginal_utility >= 0.0
    if mode == "IMPROVE_POSITION":
        return owner_eval.net_marginal_utility > 0.0 and opponent_eval.net_marginal_utility >= 0.0
    # FIND_WIN_WIN
    return owner_eval.net_marginal_utility > 0.0 and opponent_eval.net_marginal_utility > 0.0


def _explain(evaluation: TradeEvaluation) -> tuple[str, ...]:
    """Structured, real-delta-only explanation -- never a fabricated
    likelihood or fit score (gate 8)."""

    notes: list[str] = []
    if evaluation.net_marginal_utility is not None:
        notes.append(f"Net marginal roster utility {evaluation.net_marginal_utility:+.1f}.")
    if evaluation.ros_value_delta:
        notes.append(f"Real ROS value delta {evaluation.ros_value_delta:+.1f}.")
    if evaluation.starting_lineup_value_delta:
        notes.append(f"Starting lineup value {evaluation.starting_lineup_value_delta:+.1f}.")
    resolved_holes = sorted(set(evaluation.starter_holes_before) - set(evaluation.starter_holes_after))
    if resolved_holes:
        notes.append(f"Fills real starter hole(s): {', '.join(resolved_holes)}.")
    new_holes = sorted(set(evaluation.starter_holes_after) - set(evaluation.starter_holes_before))
    if new_holes:
        notes.append(f"Opens new starter hole(s): {', '.join(new_holes)}.")
    bench_delta = evaluation.bench_contingency_value_after - evaluation.bench_contingency_value_before
    if abs(bench_delta) >= 0.5:
        notes.append(f"Bench contingency value {bench_delta:+.1f}.")
    if evaluation.risk_flags:
        notes.append(f"Risk flag(s): {'; '.join(evaluation.risk_flags)}.")
    if not notes:
        notes.append("No material real change detected on this side's own composition report.")
    return tuple(notes)


def _package_size(candidate: TradePackageCandidate) -> int:
    return len(candidate.you_send) + len(candidate.you_receive)


def _drop_dominated(candidates: Sequence[TradePackageCandidate]) -> list[TradePackageCandidate]:
    """Gate 4: full pairwise Pareto sweep, scoped by caller to one
    opponent at a time."""

    kept: list[TradePackageCandidate] = []
    for candidate in candidates:
        c_owner = candidate.owner_evaluation.net_marginal_utility or 0.0
        c_opp = candidate.opponent_evaluation.net_marginal_utility or 0.0
        c_size = _package_size(candidate)
        dominated = False
        for other in candidates:
            if other is candidate:
                continue
            o_size = _package_size(other)
            if o_size > c_size:
                continue
            o_owner = other.owner_evaluation.net_marginal_utility or 0.0
            o_opp = other.opponent_evaluation.net_marginal_utility or 0.0
            same_values = o_owner == c_owner and o_opp == c_opp
            if o_owner >= c_owner and o_opp >= c_opp and not (same_values and o_size == c_size):
                dominated = True
                break
        if not dominated:
            kept.append(candidate)
    return kept


def _build_receive_combos(
    *,
    mode: TradeSearchMode,
    opponent: Mapping[str, Any],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    candidates_per_side: int,
    target_player_id: str | None,
    improve_position: str | None,
) -> list[tuple[str, ...]]:
    opp_ids = _opp_ids(opponent)
    if not opp_ids:
        return []
    if mode == "TARGET_PLAYER":
        if target_player_id is None or target_player_id not in opp_ids:
            return []
        filler_pool = _weakest_first_pool_ids(
            roster_ids=opp_ids, names=_opp_names(opponent), positions=_opp_positions(opponent),
            profile=profile, ranking=ranking, manual_assets=manual_assets, top_k=candidates_per_side,
        )
        combos: list[tuple[str, ...]] = [(target_player_id,)]
        combos.extend(
            (target_player_id, filler) for filler in filler_pool if filler != target_player_id
        )
        return combos
    if mode == "IMPROVE_POSITION":
        if not improve_position:
            return []
        position_pool = _by_position_pool_ids(
            roster_ids=opp_ids, positions=_opp_positions(opponent), position=improve_position,
            ranking=ranking, manual_assets=manual_assets, top_k=candidates_per_side,
        )
        if not position_pool:
            return []
        # Every combo generated here already contains >=1 player at the
        # requested position by construction (the pre-filter from the
        # gates doc's section 6 is therefore automatically satisfied, not
        # a separate downstream check that could silently no-op).
        combos = [(player_id,) for player_id in position_pool]
        combos.extend(itertools.combinations(position_pool, 2))
        return combos
    # FIND_WIN_WIN: both sides' own weakest-first pool, sizes 1-2.
    opp_pool = _weakest_first_pool_ids(
        roster_ids=opp_ids, names=_opp_names(opponent), positions=_opp_positions(opponent),
        profile=profile, ranking=ranking, manual_assets=manual_assets, top_k=candidates_per_side,
    )
    return _combos(opp_pool)


def _search(
    *,
    my_roster_canonical_ids: Sequence[str],
    my_player_names: Mapping[str, str],
    my_player_positions: Mapping[str, str],
    opponents: Sequence[Mapping[str, Any]],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    status_overrides: Sequence[StatusOverride],
    mode: TradeSearchMode,
    target_player_id: str | None = None,
    improve_position: str | None = None,
    candidates_per_side: int = DEFAULT_CANDIDATES_PER_SIDE,
    limit: int = DEFAULT_LIMIT,
    max_per_opponent: int = MAX_PACKAGES_EVALUATED_PER_OPPONENT,
    max_total: int = MAX_TOTAL_PACKAGES_EVALUATED,
) -> TradePackageSearchResult:
    my_ids = list(my_roster_canonical_ids)
    my_give_pool = _weakest_first_pool_ids(
        roster_ids=my_ids, names=my_player_names, positions=my_player_positions,
        profile=profile, ranking=ranking, manual_assets=manual_assets, top_k=candidates_per_side,
    )
    my_give_combos = _combos(my_give_pool)

    all_candidates: list[TradePackageCandidate] = []
    total_evaluated = 0
    truncated = False
    seen_keys: set[tuple[str, frozenset, frozenset]] = set()
    opponents_searched = 0

    for opponent in opponents:
        if mode == "TARGET_PLAYER" and target_player_id not in _opp_ids(opponent):
            continue  # a real player has exactly one owner; scope to that roster only
        receive_combos = _build_receive_combos(
            mode=mode, opponent=opponent, profile=profile, ranking=ranking, manual_assets=manual_assets,
            candidates_per_side=candidates_per_side, target_player_id=target_player_id,
            improve_position=improve_position,
        )
        if not receive_combos:
            continue
        opponents_searched += 1
        opp_roster_id = str(opponent.get("rosterId") or "")
        opp_ids = _opp_ids(opponent)
        per_opponent_candidates: list[TradePackageCandidate] = []
        per_opponent_evaluated = 0
        stop_opponent = False
        for gives_ids in my_give_combos:
            if stop_opponent or total_evaluated >= max_total:
                break
            for receives_ids in receive_combos:
                if per_opponent_evaluated >= max_per_opponent:
                    stop_opponent = True
                    truncated = True
                    break
                if total_evaluated >= max_total:
                    truncated = True
                    break
                if set(gives_ids) & set(receives_ids):
                    continue
                # Gate 1, checked cheaply BEFORE evaluate_trade (pruning).
                if not _roster_size_legal(my_ids, gives_ids, receives_ids, profile):
                    continue
                if not _roster_size_legal(opp_ids, receives_ids, gives_ids, profile):
                    continue
                key = (opp_roster_id, frozenset(gives_ids), frozenset(receives_ids))
                if key in seen_keys:
                    continue  # gate 5
                seen_keys.add(key)
                per_opponent_evaluated += 1
                total_evaluated += 1
                try:
                    owner_eval = evaluate_trade(
                        roster_before_ids=my_ids, gives_ids=gives_ids, receives_ids=receives_ids,
                        profile=profile, ranking=ranking, manual_assets=manual_assets,
                        status_overrides=status_overrides,
                    )
                    opponent_eval = evaluate_trade(
                        roster_before_ids=opp_ids, gives_ids=receives_ids, receives_ids=gives_ids,
                        profile=profile, ranking=ranking, manual_assets=manual_assets,
                        status_overrides=status_overrides,
                    )
                except TradeAnalysisError:
                    continue
                if not _passes_utility_gates(
                    mode=mode, owner_eval=owner_eval, opponent_eval=opponent_eval,
                    target_player_id=target_player_id,
                ):
                    continue
                per_opponent_candidates.append(
                    TradePackageCandidate(
                        opponent_roster_id=opp_roster_id,
                        opponent_team_name=str(opponent.get("teamName") or ""),
                        package_shape=_package_shape(len(gives_ids), len(receives_ids)),
                        you_send=tuple(gives_ids),
                        you_receive=tuple(receives_ids),
                        you_send_names=tuple(impact.player_name for impact in owner_eval.gives),
                        you_receive_names=tuple(impact.player_name for impact in owner_eval.receives),
                        owner_evaluation=owner_eval,
                        opponent_evaluation=opponent_eval,
                        why_it_helps_you=_explain(owner_eval),
                        why_it_may_fit_them=_explain(opponent_eval),
                    )
                )
        all_candidates.extend(_drop_dominated(per_opponent_candidates))
        if total_evaluated >= max_total:
            break

    all_candidates.sort(key=lambda candidate: -(candidate.owner_evaluation.net_marginal_utility or 0.0))
    return TradePackageSearchResult(
        mode=mode,
        candidates=tuple(all_candidates[:limit]),
        packages_evaluated=total_evaluated,
        opponents_searched=opponents_searched,
        truncated=truncated,
    )


def search_win_win_packages(
    *,
    my_roster_canonical_ids: Sequence[str],
    my_player_names: Mapping[str, str],
    my_player_positions: Mapping[str, str],
    opponents: Sequence[Mapping[str, Any]],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    status_overrides: Sequence[StatusOverride] = (),
    candidates_per_side: int = DEFAULT_CANDIDATES_PER_SIDE,
    limit: int = DEFAULT_LIMIT,
) -> TradePackageSearchResult:
    """FIND_WIN_WIN mode -- extends `trade_finder_service.find_win_win_trades`
    (1-for-1 only) to bounded 1-for-1/2-for-1/1-for-2/2-for-2 packages across
    every opponent."""

    return _search(
        my_roster_canonical_ids=my_roster_canonical_ids, my_player_names=my_player_names,
        my_player_positions=my_player_positions, opponents=opponents, profile=profile, ranking=ranking,
        manual_assets=manual_assets, status_overrides=status_overrides, mode="FIND_WIN_WIN",
        candidates_per_side=candidates_per_side, limit=limit,
    )


def search_target_player_packages(
    *,
    my_roster_canonical_ids: Sequence[str],
    my_player_names: Mapping[str, str],
    my_player_positions: Mapping[str, str],
    opponents: Sequence[Mapping[str, Any]],
    target_player_id: str,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    status_overrides: Sequence[StatusOverride] = (),
    candidates_per_side: int = DEFAULT_CANDIDATES_PER_SIDE,
    limit: int = DEFAULT_LIMIT,
) -> TradePackageSearchResult:
    """TARGET_PLAYER mode -- the owner names a specific player they want;
    search is scoped to whichever real opponent roster holds him."""

    if not target_player_id:
        raise ValueError("target_player_id is required for TARGET_PLAYER search.")
    return _search(
        my_roster_canonical_ids=my_roster_canonical_ids, my_player_names=my_player_names,
        my_player_positions=my_player_positions, opponents=opponents, profile=profile, ranking=ranking,
        manual_assets=manual_assets, status_overrides=status_overrides, mode="TARGET_PLAYER",
        target_player_id=target_player_id, candidates_per_side=candidates_per_side, limit=limit,
    )


def search_improve_position_packages(
    *,
    my_roster_canonical_ids: Sequence[str],
    my_player_names: Mapping[str, str],
    my_player_positions: Mapping[str, str],
    opponents: Sequence[Mapping[str, Any]],
    position: str,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    status_overrides: Sequence[StatusOverride] = (),
    candidates_per_side: int = DEFAULT_CANDIDATES_PER_SIDE,
    limit: int = DEFAULT_LIMIT,
) -> TradePackageSearchResult:
    """IMPROVE_POSITION mode -- the owner names a position of need; every
    returned package's receive side includes a real player at that
    position."""

    if not position:
        raise ValueError("position is required for IMPROVE_POSITION search.")
    return _search(
        my_roster_canonical_ids=my_roster_canonical_ids, my_player_names=my_player_names,
        my_player_positions=my_player_positions, opponents=opponents, profile=profile, ranking=ranking,
        manual_assets=manual_assets, status_overrides=status_overrides, mode="IMPROVE_POSITION",
        improve_position=position, candidates_per_side=candidates_per_side, limit=limit,
    )
