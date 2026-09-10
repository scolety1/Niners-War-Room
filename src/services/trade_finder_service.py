"""Trade Finder (NWR Overnight V3, Lane 8) -- only built because Lane 7
(Redraft Trade Analysis) shipped and Opponent Rosters is a real, live
capability (Sleeper-backed, already WORKING per this branch's own repo
inventory).

Reuses `redraft_trade_analysis_service.evaluate_trade` -- the SAME real,
non-fabricated roster-before/after evaluator built for Lane 7 -- applied
TWICE per candidate pair: once from my own roster's perspective, once from
the opponent's (same league, same governed ranking/profile, so this is a
real, symmetric application of one governed model to both sides, not two
different formulas). A candidate is only ever surfaced as "win-win" when
BOTH evaluations show a real, positive net marginal-utility gain -- no
acceptance-probability or "likely to accept" figure is fabricated; this app
has no real signal for that, so it is not estimated.

Disclosed, real simplifications:
  * Only searches each side's own weakest real roster pieces (top
    `candidates_per_side` by ascending marginal utility, reusing
    `rank_drop_candidates`) -- not a full combinatorial search of every
    possible multi-player package. A blind automated finder proposing a
    team's best players away is not a realistic trade anyway.
  * 1-for-1 pairings only this pass -- multi-player packages are a real,
    disclosed follow-up, not attempted here.
  * Roster legality is checked at the level `roster_composition_report`
    already provides (starter holes, position redundancy) for BOTH rosters
    post-trade -- this is composition-level plausibility, not the full
    draft-time `evaluate_draft_pick_legality` hard-maxima engine (which has
    no meaning post-draft; roster_limits are draft-time constructs).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.services.current_player_status_overrides_service import StatusOverride
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.redraft_trade_analysis_service import TradeAnalysisError, TradeEvaluation, evaluate_trade
from src.services.waiver_engine_service import rank_drop_candidates


@dataclass(frozen=True)
class TradeFinderCandidate:
    my_give_player_id: str
    my_give_player_name: str
    opponent_give_player_id: str
    opponent_give_player_name: str
    opponent_roster_id: str
    opponent_team_name: str
    my_evaluation: TradeEvaluation
    opponent_evaluation: TradeEvaluation


def find_win_win_trades(
    *,
    my_roster_canonical_ids: Sequence[str],
    my_player_names: Mapping[str, str],
    my_player_positions: Mapping[str, str],
    opponents: Sequence[Mapping[str, Any]],  # {"rosterId","teamName","canonicalIds","names","positions"}
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    status_overrides: Sequence[StatusOverride] = (),
    candidates_per_side: int = 8,
    limit: int = 15,
) -> tuple[TradeFinderCandidate, ...]:
    my_drops = rank_drop_candidates(
        roster_canonical_ids=my_roster_canonical_ids, profile=profile, ranking=ranking,
        manual_assets=manual_assets, player_names=my_player_names, player_positions=my_player_positions,
    )[:candidates_per_side]

    found: list[TradeFinderCandidate] = []
    for opponent in opponents:
        opp_ids = tuple(opponent.get("canonicalIds") or ())
        if not opp_ids:
            continue
        opp_names = opponent.get("names") or {}
        opp_positions = opponent.get("positions") or {}
        opp_drops = rank_drop_candidates(
            roster_canonical_ids=opp_ids, profile=profile, ranking=ranking, manual_assets=manual_assets,
            player_names=opp_names, player_positions=opp_positions,
        )[:candidates_per_side]

        for my_drop in my_drops:
            for their_drop in opp_drops:
                if my_drop.canonical_player_id == their_drop.canonical_player_id:
                    continue
                try:
                    my_eval = evaluate_trade(
                        roster_before_ids=my_roster_canonical_ids,
                        gives_ids=[my_drop.canonical_player_id],
                        receives_ids=[their_drop.canonical_player_id],
                        profile=profile, ranking=ranking, manual_assets=manual_assets,
                        status_overrides=status_overrides,
                    )
                    their_eval = evaluate_trade(
                        roster_before_ids=opp_ids,
                        gives_ids=[their_drop.canonical_player_id],
                        receives_ids=[my_drop.canonical_player_id],
                        profile=profile, ranking=ranking, manual_assets=manual_assets,
                        status_overrides=status_overrides,
                    )
                except TradeAnalysisError:
                    continue  # e.g. a duplicate/overlap edge case -- skip, don't crash the search
                if my_eval.net_marginal_utility is None or their_eval.net_marginal_utility is None:
                    continue
                if my_eval.net_marginal_utility <= 0 or their_eval.net_marginal_utility <= 0:
                    continue  # not a real win-win under the governed model -- discard
                found.append(
                    TradeFinderCandidate(
                        my_give_player_id=my_drop.canonical_player_id,
                        my_give_player_name=my_drop.player_name,
                        opponent_give_player_id=their_drop.canonical_player_id,
                        opponent_give_player_name=their_drop.player_name,
                        opponent_roster_id=str(opponent.get("rosterId") or ""),
                        opponent_team_name=str(opponent.get("teamName") or ""),
                        my_evaluation=my_eval,
                        opponent_evaluation=their_eval,
                    )
                )

    found.sort(
        key=lambda candidate: (
            -(candidate.my_evaluation.net_marginal_utility or 0.0),
            -(candidate.opponent_evaluation.net_marginal_utility or 0.0),
        )
    )
    return tuple(found[:limit])
