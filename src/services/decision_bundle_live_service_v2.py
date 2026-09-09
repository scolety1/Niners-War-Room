"""Live DecisionBundle V2 -- the historically-validated CHALLENGER layer,
bridged into the real live Draft Room state (NWR Big-Draft Readiness
Overnight V1).

Mirrors `decision_bundle_live_service.build_live_decision_bundle()` exactly
(same room-state bridging, same real production candidate-legality and
availability filters), but calls `decision_bundle_service_v2.
build_decision_bundle_v2()` instead of the V1 composer. This file changes
NOTHING about the live V1 path -- `decision_bundle_live_service.py` and
`decision_bundle_service.py` are untouched and remain the default,
unmodified authority. This is purely an additional, explicitly-opt-in
CHALLENGER surface a caller must deliberately choose to use.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from src.services.decision_bundle_live_service import (
    DIVERSITY_POSITIONS,
    LiveDecisionBundleError,
    LiveDecisionBundleUnavailable,
    diversify_candidate_shortlist,
)
from src.services.decision_bundle_service_v2 import DecisionBundleV2, build_decision_bundle_v2
from src.services.redraft_draft_room_v1_service import (
    AdpSnapshot,
    _available_ranked,
    _roster_need_adjustment,
    draft_order,
)
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.redraft_roster_legality_service import evaluate_draft_pick_legality
from src.services.score_provenance_service import ScoreProvenance
from src.services.shadow_numeric_authorities_service import RosterPlayer

LIVE_DECISION_BUNDLE_V2_VERSION = "decision-bundle-live-v2-challenger-v1"
DEFAULT_MAX_CANDIDATES = 12


def build_live_decision_bundle_v2(
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
    include_raw_action_value: bool = True,
    max_rav_candidates: int | None = None,
    rav_trials: int | None = None,
) -> DecisionBundleV2 | LiveDecisionBundleUnavailable:
    """Identical real-state bridging logic to
    `build_live_decision_bundle()` -- deliberately duplicated rather than
    imported-and-wrapped, so this challenger surface can never silently
    drift out of sync with a private helper's signature changing
    underneath it; both call the same real `_available_ranked` /
    `_roster_candidate_allowed` / `draft_order` production functions."""
    if not ranking.ready:
        return LiveDecisionBundleUnavailable(
            "The active Redraft ranking is not ready (blocked/errored) -- no "
            "DecisionBundle can be computed from it."
        )
    owner_slot = room_state.get("owner_slot")
    if not isinstance(owner_slot, int):
        return LiveDecisionBundleUnavailable("Owner slot is not configured for this profile.")

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
        row
        for row in available_rows
        if evaluate_draft_pick_legality(profile, roster, row.position).allowed
    ]
    if not legal_rows:
        return LiveDecisionBundleUnavailable(
            "No roster-legal available candidate exists at this pick (every open "
            "position may already be at its configured maximum, or the player "
            "universe is exhausted)."
        )
    # Reused verbatim from decision_bundle_live_service.py (owner-test
    # follow-up) -- keeps V1 and V2 selecting the SAME real shortlist for
    # the SAME real draft state, including the need-aware coverage fix
    # (a position with no real remaining starter/FLEX need gets no forced
    # quota slot) and the domination cap.
    round_number = (current_pick_number - 1) // max(1, profile.team_count) + 1
    needed_positions = frozenset(
        position for position in DIVERSITY_POSITIONS
        if _roster_need_adjustment(profile, roster, round_number, position) < 0
    )
    candidate_rows = diversify_candidate_shortlist(legal_rows, max_candidates, needed_positions)
    candidate_player_ids = [row.player_id for row in candidate_rows]
    player_scores = {row.player_id: float(row.replacement_adjusted_value) for row in ranking.rows}

    rav_kwargs: dict[str, Any] = {}
    if max_rav_candidates is not None:
        rav_kwargs["max_rav_candidates"] = max_rav_candidates
    if rav_trials is not None:
        rav_kwargs["rav_trials"] = rav_trials
    bundle_v2 = build_decision_bundle_v2(
        profile=profile,
        ranking=ranking,
        manual_assets=manual_assets,
        adp=adp,
        owner_slot=owner_slot,
        current_owner_player_ids=current_owner_player_ids,
        candidate_player_ids=candidate_player_ids,
        comparable_leagues=comparable_leagues,
        provenance=provenance,
        player_scores=player_scores,
        from_state=room_state,
        include_cost_of_waiting=include_cost_of_waiting,
        current_pick_number=current_pick_number,
        trials=trials,
        seasons=seasons,
        base_seed=base_seed,
        include_raw_action_value=include_raw_action_value,
        **rav_kwargs,
    )
    unresolved = [pid for pid in candidate_player_ids if pid in drafted_ids]
    if unresolved:  # defensive -- should be impossible given _available_ranked's own filter
        raise LiveDecisionBundleError(
            f"Candidate player(s) {unresolved} are already drafted; refusing to score them."
        )
    return bundle_v2
