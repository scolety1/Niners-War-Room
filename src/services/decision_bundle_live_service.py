"""Live DecisionBundle composition for the current draft state (Owner Test
Candidate V1, section 2).

Bridges the real, already-loaded live Draft Room state (the exact
`ranking`/`manual_assets`/`adp`/room `state` `redraft_bootstrap()` and
`build_draft_room_payload()` already produce) into a real
`decision_bundle_service.DecisionBundle` -- backend computes, frontend
renders. Reuses the real production candidate-legality rule
(`_roster_candidate_allowed`) and availability filter (`_available_ranked`)
from `redraft_draft_room_v1_service` directly, rather than re-deriving
"roster-legal available candidates" a second time -- the exact same
precedent `shadow_numeric_authorities_service.evaluate_pick_candidates`
already established for reusing internal draft-room mechanics from a
research/decision-support module.

Never fabricates a value: if the owner slot isn't configured, or no
roster-legal candidate exists, this returns an explicit
`LiveDecisionBundleUnavailable` with a real reason -- never a
DecisionBundle with placeholder numbers.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from src.services.decision_bundle_service import DecisionBundle, build_decision_bundle
from src.services.redraft_draft_room_v1_service import (
    AdpSnapshot,
    _available_ranked,
    _roster_candidate_allowed,
    draft_order,
)
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.score_provenance_service import ScoreProvenance
from src.services.shadow_numeric_authorities_service import RosterPlayer

LIVE_DECISION_BUNDLE_VERSION = "decision-bundle-live-v1"
DEFAULT_MAX_CANDIDATES = 12


class LiveDecisionBundleError(ValueError):
    pass


@dataclass(frozen=True)
class LiveDecisionBundleUnavailable:
    reason: str


def build_live_decision_bundle(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    room_state: Mapping[str, Any],
    *,
    comparable_leagues: Sequence[dict[int, list[RosterPlayer]]],
    provenance: ScoreProvenance,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
    include_cost_of_waiting: bool = True,
    trials: int = 200,
    seasons: int = 200,
    base_seed: int = 20260903,
) -> DecisionBundle | LiveDecisionBundleUnavailable:
    """`comparable_leagues` and `provenance` are caller-supplied (not
    built here) so the expensive Monte Carlo reference population can be
    cached at the facade layer, keyed by real provenance (profile,
    ranking/ADP hashes, trial count, seed) -- never reused across a
    changed universe/market/model version."""
    if not ranking.ready:
        return LiveDecisionBundleUnavailable(
            "The active Redraft ranking is not ready (blocked/errored) -- no "
            "DecisionBundle can be computed from it."
        )
    owner_slot = room_state.get("owner_slot")
    if not isinstance(owner_slot, int):
        return LiveDecisionBundleUnavailable("Owner slot is not configured for this profile.")

    # The look-ahead simulation this composes (evaluate_pick_candidates ->
    # simulate_pick_now) forces a candidate as the owner's VERY NEXT actual
    # turn, then completes the draft from there. That is only a meaningful
    # "if I pick X now" answer when it genuinely IS the owner's turn right
    # now -- otherwise the intervening CPU picks (deterministic, same
    # best-available logic driving this function's own candidate selection)
    # can legitimately draft one of these candidates before the owner's
    # real next turn arrives, which is a real state to report, not a crash
    # to hide.
    order = draft_order(profile)
    picks_so_far = len(room_state.get("picks", []))
    current_pick_number = picks_so_far + 1
    current_team_slot = order[picks_so_far] if picks_so_far < len(order) else None
    if current_team_slot != owner_slot:
        return LiveDecisionBundleUnavailable(
            f"It is not currently the owner's turn (pick {current_pick_number} belongs to "
            f"team {current_team_slot}) -- DecisionBundle recommendations are only computed "
            "for the immediate next owner pick, never a hypothetical future turn."
        )

    drafted_ids = {str(value) for value in room_state.get("drafted", [])}
    current_owner_player_ids = tuple(
        str(pick["player_id"])
        for pick in room_state.get("picks", [])
        if pick.get("team_slot") == owner_slot and pick.get("player_id")
    )
    roster = Counter(
        str(pick["position"])
        for pick in room_state.get("picks", [])
        if pick.get("team_slot") == owner_slot
    )
    available_rows = _available_ranked(ranking, room_state)
    legal_rows = [
        row for row in available_rows
        if _roster_candidate_allowed(profile, roster, {"position": row.position})
    ]
    if not legal_rows:
        return LiveDecisionBundleUnavailable(
            "No roster-legal available candidate exists at this pick (every open "
            "position may already be at its configured maximum, or the player "
            "universe is exhausted)."
        )
    candidate_rows = legal_rows[:max_candidates]
    candidate_player_ids = [row.player_id for row in candidate_rows]
    player_scores = {
        row.player_id: float(row.replacement_adjusted_value) for row in ranking.rows
    }

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=owner_slot, current_owner_player_ids=current_owner_player_ids,
        candidate_player_ids=candidate_player_ids, comparable_leagues=comparable_leagues,
        provenance=provenance, player_scores=player_scores,
        # The CURRENT real draft-room state -- without this, the look-ahead
        # simulation (evaluate_pick_candidates -> simulate_pick_now) starts
        # from an EMPTY draft instead of continuing the real one, and can
        # collide with players the real room has already drafted.
        from_state=room_state,
        include_cost_of_waiting=include_cost_of_waiting,
        current_pick_number=current_pick_number, trials=trials, seasons=seasons,
        base_seed=base_seed,
    )
    unresolved = [pid for pid in candidate_player_ids if pid in drafted_ids]
    if unresolved:  # defensive -- should be impossible given _available_ranked's own filter
        raise LiveDecisionBundleError(
            f"Candidate player(s) {unresolved} are already drafted; refusing to score them."
        )
    return bundle
