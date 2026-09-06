"""Raw Action Value / Regret / decision-quality Pick Score -- LIVE wiring
of the exact, frozen, historically-validated `decision_engine_v2_contracts_
service.py` pipeline (NWR Final Pre-Draft Product Hardening V1).

Traced from the research branch's final 2025 holdout evaluation
(`run_final_2025_holdout_evaluation_v1.py::evaluate_raw_action_value`),
which is the real, historically-evaluated methodology this module
reproduces live, exactly, with zero formula changes:

1. For each real candidate, run several independent BOUNDED-LOOK-AHEAD
   ROLLOUTS: force the candidate now (`shadow_numeric_authorities_service.
   simulate_pick_now`, the same real function `evaluate_pick_candidates`
   already uses for the live V1 Pick Score), let the rest of the draft
   complete under the real market/CPU continuation policy, then score the
   resulting TERMINAL roster with the real, frozen `team_score()`'s raw
   `roster_value` (NOT its bucketed `.percentile` -- see the real,
   reproduced saturation bug this fixes, documented inline below). This
   is the exact "bounded look-ahead terminal value"
   `compute_raw_action_value()` requires -- never invented here.
2. Feed those real per-trial terminal values straight into
   `decision_engine_v2_contracts_service.compute_raw_action_value()`
   (unmodified) with `terminal_objective_name=TERMINAL_OBJECTIVE_TEAM_SCORE`
   (Championship Equity is gated behind a historical-validation-gate flag
   this program has never opened for it -- see `championship_equity_v2
   _multi_league_service`'s own "ranking_evidence: NOT DECISIVE" finding;
   using it as an RAV terminal objective is refused here by construction).
3. `compute_regret()` (EX_ANTE_MODEL_REGRET, the only kind computable
   live -- no real outcome exists yet to compute EX_POST regret against)
   against a `FrozenCandidateSet` built from exactly the candidates
   evaluated in this one call.
4. `compute_decision_quality_percentile_raw_rank()` against the OTHER
   candidates' regrets in this SAME call as the comparable population --
   mirroring exactly how the live V1 `pick_score()` already treats "the
   candidates evaluated in this call" as its own comparable set, and how
   the historical evaluation script used the batch's own regrets as its
   comparable-regret population.

Cost control (this is real, additional Monte Carlo work on top of the
existing Pick Score rollout, not a replacement): only the top
`max_rav_candidates` of the caller's already-ranked candidate list are
evaluated (an explicit, disclosed "top-N" optimization, never a silent
truncation), and `rav_trials` independent rollouts are run per candidate
(each one a REAL, full draft-completion simulation -- not a shortcut).

Degrades gracefully: any real failure for one candidate (an unavailable
asset mid-rollout, an unresolvable roster) is reported as that
candidate's own `RAW_ACTION_VALUE_UNAVAILABLE` status, never a fabricated
number and never a crash that takes down the rest of the bundle.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from src.services.decision_engine_v2_contracts_service import (
    TERMINAL_OBJECTIVE_TEAM_SCORE,
    ComparableStateStratum,
    DecisionEngineV2Error,
    FrozenCandidateSet,
    RawActionValueResult,
    compute_decision_quality_percentile_raw_rank,
    compute_raw_action_value,
    compute_regret,
    register_pick_score_calibration_contract_v2,
)
from src.services.redraft_draft_room_v1_service import AdpSnapshot
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.shadow_numeric_authorities_service import (
    RosterPlayer,
    simulate_pick_now,
    team_score,
)

RAW_ACTION_VALUE_LIVE_LABEL = "RAW_ACTION_VALUE_LIVE_V1"
MODEL_VERSION = "raw-action-value-live-v1-frozen-decision-engine-v2-contracts"
DEFAULT_MAX_RAV_CANDIDATES = 5
DEFAULT_RAV_TRIALS = 2


class RawActionValueLiveError(ValueError):
    pass


@dataclass(frozen=True)
class CandidateRawActionValue:
    player_id: str
    status: str  # "OK" | "UNAVAILABLE: <reason>"
    raw_action_value: RawActionValueResult | None
    expected_regret: float | None
    decision_quality_percentile: float | None
    rollout_count: int
    terminal_values_by_rollout: tuple[float, ...]


def evaluate_raw_action_value_live(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    owner_slot: int,
    candidate_player_ids: Sequence[str],
    from_state: Mapping[str, Any] | None,
    comparable_leagues: Sequence[dict[int, list[RosterPlayer]]],
    state_id: str,
    max_rav_candidates: int = DEFAULT_MAX_RAV_CANDIDATES,
    rav_trials: int = DEFAULT_RAV_TRIALS,
    base_seed: int = 20260903,
) -> dict[str, CandidateRawActionValue]:
    """Returns one `CandidateRawActionValue` per evaluated candidate,
    keyed by player_id. Candidates beyond `max_rav_candidates` (the
    caller's list is assumed already ranked best-first, e.g. by Pick
    Score) are omitted from the return value entirely -- the caller must
    treat a missing key as `RAW_ACTION_VALUE_LIVE_SKIPPED_TOP_N_ONLY`,
    never as a zero or a failure."""
    evaluated_ids = list(candidate_player_ids)[:max_rav_candidates]
    if not evaluated_ids:
        return {}

    raw_terminal_values: dict[str, list[float]] = {}
    failures: dict[str, str] = {}
    for candidate_id in evaluated_ids:
        trial_values: list[float] = []
        for trial in range(rav_trials):
            trial_seed = base_seed + trial
            try:
                final_state = simulate_pick_now(
                    profile,
                    ranking,
                    manual_assets,
                    adp,
                    owner_slot=owner_slot,
                    candidate_player_id=candidate_id,
                    seed=trial_seed,
                    from_state=from_state,
                )
            except ValueError as exc:
                failures[candidate_id] = str(exc)
                trial_values = []
                break
            owner_player_ids = [
                str(pick["player_id"])
                for pick in final_state["picks"]
                if int(pick["team_slot"]) == owner_slot and pick.get("player_id")
            ]
            result = team_score(
                owner_player_ids,
                profile,
                ranking,
                manual_assets,
                comparable_leagues=comparable_leagues,
            )
            # Real, traced fix (NWR Draft Room Consolidation V1, section 1):
            # `.percentile` is bucketed against the comparable-league
            # population (population_size = trials x team_count -- only 20
            # at the FAST preset), so many genuinely-different real
            # terminal rosters collapse onto the exact same percentile
            # value deep in a real draft, producing a flat, uninformative
            # Raw Action Value/regret for every candidate (reproduced
            # against the real "Fantasy Gamers" league: 8 different real
            # candidates all landed on percentile=90.0). `.roster_value`
            # is the real, continuous, un-bucketed value the percentile is
            # itself computed from -- using it here preserves the exact
            # same real terminal-value semantics (still real Team Score
            # output, still fed unmodified into compute_raw_action_value())
            # while giving genuine, real-number resolution instead of a
            # ~20-bucket ceiling. This does not touch team_score() itself,
            # V1's live pick_score() (deliberately left alone -- it is the
            # explicit real-draft fallback path), or any frozen model.
            trial_values.append(result.roster_value)
        if trial_values:
            raw_terminal_values[candidate_id] = trial_values

    outputs: dict[str, CandidateRawActionValue] = {}
    for candidate_id in evaluated_ids:
        if candidate_id not in raw_terminal_values:
            reason = failures.get(candidate_id, "no rollout completed")
            outputs[candidate_id] = CandidateRawActionValue(
                player_id=candidate_id,
                status=f"UNAVAILABLE: {reason}",
                raw_action_value=None,
                expected_regret=None,
                decision_quality_percentile=None,
                rollout_count=0,
                terminal_values_by_rollout=(),
            )
            continue
        try:
            rav = compute_raw_action_value(
                state_id=state_id,
                action_candidate_id=candidate_id,
                terminal_values_by_rollout=raw_terminal_values[candidate_id],
                terminal_objective_name=TERMINAL_OBJECTIVE_TEAM_SCORE,
                lookahead_depth=max(0, len(evaluated_ids) - 1),
                championship_equity_gate_passed=False,
                provenance={"owner_slot": owner_slot, "rav_trials": rav_trials},
            )
        except DecisionEngineV2Error as exc:
            outputs[candidate_id] = CandidateRawActionValue(
                player_id=candidate_id,
                status=f"UNAVAILABLE: {exc}",
                raw_action_value=None,
                expected_regret=None,
                decision_quality_percentile=None,
                rollout_count=0,
                terminal_values_by_rollout=(),
            )
            continue
        outputs[candidate_id] = CandidateRawActionValue(
            player_id=candidate_id,
            status="OK",
            raw_action_value=rav,
            expected_regret=None,
            decision_quality_percentile=None,
            rollout_count=len(raw_terminal_values[candidate_id]),
            terminal_values_by_rollout=tuple(raw_terminal_values[candidate_id]),
        )

    ok_ids = [cid for cid, out in outputs.items() if out.status == "OK"]
    if len(ok_ids) < 2:
        # Regret needs a real comparison set of at least 2 candidates with
        # a real raw_action_value each -- with fewer, regret and the
        # decision-quality percentile are left None (never fabricated),
        # while raw_action_value itself (computed above) is still real
        # and still returned.
        return outputs

    candidate_set = FrozenCandidateSet(
        state_id=state_id,
        candidate_action_ids=tuple(ok_ids),
        frozen_at_utc="2026-09-06T00:00:00Z",
        frozen_before_outcome_unlock=True,
    )
    terminal_value_by_candidate = {
        cid: outputs[cid].raw_action_value.expected_terminal_value for cid in ok_ids
    }
    stratum = ComparableStateStratum(
        league_format_id=f"LIVE_{profile.team_count}_TEAM_{profile.season}",
        league_size=profile.team_count,
        draft_phase="LIVE_DECISION",
        roster_state_summary=state_id,
    )
    register_pick_score_calibration_contract_v2(stratum)
    regrets: dict[str, float] = {}
    for candidate_id in ok_ids:
        regret_result = compute_regret(
            action_candidate_id=candidate_id,
            terminal_value_by_candidate=terminal_value_by_candidate,
            regret_kind="EX_ANTE_MODEL_REGRET",
            candidate_set=candidate_set,
        )
        regrets[candidate_id] = regret_result.regret
    for candidate_id in ok_ids:
        comparable_regrets = [regrets[other] for other in ok_ids if other != candidate_id]
        percentile = (
            compute_decision_quality_percentile_raw_rank(
                regret_value=regrets[candidate_id],
                comparable_regrets=comparable_regrets,
            )
            if comparable_regrets
            else None
        )
        outputs[candidate_id] = CandidateRawActionValue(
            player_id=candidate_id,
            status="OK",
            raw_action_value=outputs[candidate_id].raw_action_value,
            expected_regret=regrets[candidate_id],
            decision_quality_percentile=percentile,
            rollout_count=outputs[candidate_id].rollout_count,
            terminal_values_by_rollout=outputs[candidate_id].terminal_values_by_rollout,
        )
    return outputs
