"""Decision engine V2 research contracts (Research Addendum V1 sections
11-14 -- HTM-PICK-001, HTM-REGRET-001, HTM-PICK-002, HTM-CONF-001).

Raw Action Value V2, the Regret contract, the Pick Score
decision-quality-percentile semantics registration, and Decision
Confidence all live here together because they compose in one pipeline:
Raw Action Value -> Regret -> Pick Score percentile -> Decision
Confidence. None of the functions below fits a transform, chooses a
terminal objective automatically, or reduces to the pre-calibration
wave's arbitrary weighted-score Pick Score -- every function requires its
real inputs explicitly and raises rather than guessing.
"""

from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

# --- Section 11: Raw Action Value V2 --------------------------------------

TERMINAL_OBJECTIVE_TEAM_SCORE = "TERMINAL_OBJECTIVE_TEAM_SCORE"
TERMINAL_OBJECTIVE_CHAMPIONSHIP_EQUITY = "TERMINAL_OBJECTIVE_CHAMPIONSHIP_EQUITY"
TERMINAL_OBJECTIVES = frozenset(
    {TERMINAL_OBJECTIVE_TEAM_SCORE, TERMINAL_OBJECTIVE_CHAMPIONSHIP_EQUITY}
)


class DecisionEngineV2Error(ValueError):
    pass


@dataclass(frozen=True)
class RawActionValueResult:
    """Q(S,A) = expected terminal objective under bounded look-ahead,
    computed directly from real rollout terminal values -- NEVER a static
    weighted sum of Team Score + Championship Equity + Cost of Waiting
    (that combination lives only in the pre-calibration wave's explicitly
    RESEARCH_ONLY `pick_score()`, not here). Cost of Waiting is a distinct
    opportunity-cost diagnostic evaluated separately, never folded into
    this terminal-value estimate -- avoids double-counting by
    construction rather than by convention."""

    state_id: str
    action_candidate_id: str
    terminal_objective_name: str
    expected_terminal_value: float
    terminal_value_stdev: float
    lookahead_depth: int
    rollout_count: int
    provenance: dict


def compute_raw_action_value(
    *, state_id: str, action_candidate_id: str,
    terminal_values_by_rollout: Sequence[float], terminal_objective_name: str,
    lookahead_depth: int, championship_equity_gate_passed: bool, provenance: dict,
) -> RawActionValueResult:
    """`terminal_values_by_rollout` must already be real bounded-look-ahead
    rollout outcomes under `terminal_objective_name` (e.g. Team Score
    percentile after `lookahead_depth` further picks, averaged over Monte
    Carlo trials) -- this function only aggregates, never simulates.
    Refuses TERMINAL_OBJECTIVE_CHAMPIONSHIP_EQUITY until the caller
    confirms Championship Equity has passed its historical validation
    gate (per the pre-registered methodology's CALIBRATION_GATES), per
    the directive's own explicit ordering."""
    if terminal_objective_name not in TERMINAL_OBJECTIVES:
        raise DecisionEngineV2Error(
            f"Unknown terminal_objective_name {terminal_objective_name!r}. "
            f"Known: {sorted(TERMINAL_OBJECTIVES)}."
        )
    if (
        terminal_objective_name == TERMINAL_OBJECTIVE_CHAMPIONSHIP_EQUITY
        and not championship_equity_gate_passed
    ):
        raise DecisionEngineV2Error(
            "Championship Equity has not passed its historical validation gate -- "
            "Raw Action Value V2 must use TERMINAL_OBJECTIVE_TEAM_SCORE until it does."
        )
    if not terminal_values_by_rollout:
        raise DecisionEngineV2Error("No rollout terminal values supplied.")
    if lookahead_depth < 0:
        raise DecisionEngineV2Error("lookahead_depth must be >= 0.")
    return RawActionValueResult(
        state_id=state_id, action_candidate_id=action_candidate_id,
        terminal_objective_name=terminal_objective_name,
        expected_terminal_value=round(statistics.fmean(terminal_values_by_rollout), 3),
        terminal_value_stdev=(
            round(statistics.pstdev(terminal_values_by_rollout), 3)
            if len(terminal_values_by_rollout) > 1 else 0.0
        ),
        lookahead_depth=lookahead_depth,
        rollout_count=len(terminal_values_by_rollout),
        provenance=dict(provenance),
    )


# --- Section 12: Regret contract ------------------------------------------

EX_ANTE_MODEL_REGRET = "EX_ANTE_MODEL_REGRET"
EX_POST_REALIZED_REGRET = "EX_POST_REALIZED_REGRET"
REGRET_KINDS = frozenset({EX_ANTE_MODEL_REGRET, EX_POST_REALIZED_REGRET})


@dataclass(frozen=True)
class FrozenCandidateSet:
    """The exact candidate action set considered at `state_id`, frozen
    BEFORE any realized outcome for this state is unlocked -- Regret can
    only ever be computed against this frozen set, never one silently
    expanded/contracted after seeing what happened."""

    state_id: str
    candidate_action_ids: tuple[str, ...]
    frozen_at_utc: str
    frozen_before_outcome_unlock: bool

    def __post_init__(self) -> None:
        if not self.candidate_action_ids:
            raise DecisionEngineV2Error("candidate_action_ids must be non-empty.")
        if not self.frozen_before_outcome_unlock:
            raise DecisionEngineV2Error(
                "A candidate set not frozen before outcome unlock cannot be used "
                "for a Regret computation -- construct it before opening outcomes."
            )


@dataclass(frozen=True)
class RegretResult:
    state_id: str
    action_candidate_id: str
    regret_kind: str
    best_terminal_value: float
    actual_terminal_value: float
    regret: float


def compute_regret(
    *, action_candidate_id: str, terminal_value_by_candidate: Mapping[str, float],
    regret_kind: str, candidate_set: FrozenCandidateSet,
) -> RegretResult:
    """Regret(S,A) = BestTerminalValue(S) - TerminalValue(S,A), where
    BestTerminalValue is the max over the FROZEN candidate set only --
    never over a value the caller happens to have lying around for an
    action outside that set."""
    if regret_kind not in REGRET_KINDS:
        raise DecisionEngineV2Error(
            f"Unknown regret_kind {regret_kind!r}. Known: {sorted(REGRET_KINDS)}."
        )
    if action_candidate_id not in candidate_set.candidate_action_ids:
        raise DecisionEngineV2Error(
            f"{action_candidate_id!r} is not in the frozen candidate set for "
            f"state {candidate_set.state_id!r}."
        )
    missing = set(candidate_set.candidate_action_ids) - set(terminal_value_by_candidate)
    if missing:
        raise DecisionEngineV2Error(
            "terminal_value_by_candidate is missing values for frozen candidates: "
            f"{sorted(missing)}."
        )
    in_set_values = {
        cid: v for cid, v in terminal_value_by_candidate.items()
        if cid in candidate_set.candidate_action_ids
    }
    best = max(in_set_values.values())
    actual = in_set_values[action_candidate_id]
    return RegretResult(
        state_id=candidate_set.state_id, action_candidate_id=action_candidate_id,
        regret_kind=regret_kind, best_terminal_value=round(best, 3),
        actual_terminal_value=round(actual, 3), regret=round(best - actual, 3),
    )


# --- Section 13: Pick Score calibration contract V2 -----------------------

PICK_SCORE_DECISION_QUALITY_PERCENTILE = "PICK_SCORE_DECISION_QUALITY_PERCENTILE"
_PICK_SCORE_V2_DEFINITION = (
    "Calibrated expected-regret percentile among comparable historical "
    "candidate actions -- NOT '90 = 90% chance correct'. A Pick Score of "
    "90 means this decision's expected regret ranks in roughly the 90th "
    "percentile (i.e. among the lowest-regret decisions) of comparable "
    "historical decisions in the same state stratum."
)


@dataclass(frozen=True)
class ComparableStateStratum:
    league_format_id: str
    league_size: int
    draft_phase: str
    roster_state_summary: str


@dataclass(frozen=True)
class PickScoreCalibrationContractV2:
    semantics_name: str
    definition: str
    comparable_state_stratum: ComparableStateStratum
    transform_fit: bool  # always False from register_...() -- this module never fits it


def register_pick_score_calibration_contract_v2(
    stratum: ComparableStateStratum,
) -> PickScoreCalibrationContractV2:
    """Registers the PROPOSED semantics for a given comparable-state
    stratum. Does NOT fit the calibration transform -- `transform_fit` is
    always False here; fitting is a separate, future, real-data-gated
    step this function deliberately does not perform."""
    return PickScoreCalibrationContractV2(
        semantics_name=PICK_SCORE_DECISION_QUALITY_PERCENTILE,
        definition=_PICK_SCORE_V2_DEFINITION, comparable_state_stratum=stratum,
        transform_fit=False,
    )


def compute_decision_quality_percentile_raw_rank(
    *, regret_value: float, comparable_regrets: Sequence[float],
) -> float:
    """MECHANICS ONLY: an empirical percentile rank of `regret_value`
    among `comparable_regrets` from the SAME stratum -- lower regret is
    better, so the percentile counts how many comparable regrets were
    WORSE (higher). This is the raw ordinal mechanism the eventual fitted
    calibration transform would replace -- not itself a claimed
    calibration."""
    if not comparable_regrets:
        raise DecisionEngineV2Error(
            "No comparable_regrets supplied -- cannot compute a percentile rank "
            "against zero comparable historical decisions."
        )
    worse = sum(1 for r in comparable_regrets if r > regret_value)
    return round(100.0 * worse / len(comparable_regrets), 1)


# --- Section 14: Decision Confidence ---------------------------------------

PROJECTION_UNCERTAINTY = "PROJECTION_UNCERTAINTY"
MARKET_UNCERTAINTY = "MARKET_UNCERTAINTY"
OPPONENT_RANDOMNESS = "OPPONENT_RANDOMNESS"
OUTCOME_UNCERTAINTY = "OUTCOME_UNCERTAINTY"
MODEL_UNCERTAINTY = "MODEL_UNCERTAINTY"
MONTE_CARLO_SAMPLING_ERROR = "MONTE_CARLO_SAMPLING_ERROR"
UNCERTAINTY_SOURCES = (
    PROJECTION_UNCERTAINTY, MARKET_UNCERTAINTY, OPPONENT_RANDOMNESS,
    OUTCOME_UNCERTAINTY, MODEL_UNCERTAINTY, MONTE_CARLO_SAMPLING_ERROR,
)


@dataclass(frozen=True)
class UncertaintyDecomposition:
    """Every source tracked SEPARATELY. `monte_carlo_sampling_error` is
    the only one this codebase can currently compute for free (it falls
    out of the replay's own rollout count); the other five stay None
    until real evidence exists for them -- `is_fully_characterized`
    returns False whenever any of them is still None, so a caller cannot
    mistake "we only measured MC noise" for "we measured all uncertainty.\""""

    monte_carlo_sampling_error: float
    projection_uncertainty: float | None = None
    market_uncertainty: float | None = None
    opponent_randomness: float | None = None
    outcome_uncertainty: float | None = None
    model_uncertainty: float | None = None

    @property
    def is_fully_characterized(self) -> bool:
        return all(
            getattr(self, source.lower()) is not None
            for source in UNCERTAINTY_SOURCES
            if source != MONTE_CARLO_SAMPLING_ERROR
        )


@dataclass(frozen=True)
class DecisionConfidenceResult:
    state_id: str
    action_candidate_id: str
    p_within_near_optimal_band: float
    p_rank_1: float | None
    near_optimal_band_width: float
    uncertainty: UncertaintyDecomposition
    rollout_count: int


def compute_decision_confidence(
    *, state_id: str, action_candidate_id: str,
    terminal_values_by_rollout_per_candidate: Mapping[str, Sequence[float]],
    near_optimal_band_width: float, uncertainty: UncertaintyDecomposition,
    include_rank_1: bool = True,
) -> DecisionConfidenceResult:
    """Every candidate's rollout list must be PAIRED (index i is the same
    common-random-number draw across every candidate) -- raises if the
    candidates don't share one rollout count, since an unpaired comparison
    would silently mix independent randomness into what should be a
    common-random-number diagnostic."""
    if action_candidate_id not in terminal_values_by_rollout_per_candidate:
        raise DecisionEngineV2Error(
            f"{action_candidate_id!r} has no rollout values supplied."
        )
    rollout_counts = {len(v) for v in terminal_values_by_rollout_per_candidate.values()}
    if len(rollout_counts) != 1:
        raise DecisionEngineV2Error(
            "Every candidate must share the same (paired, common-random-number) "
            f"rollout count -- got {rollout_counts}."
        )
    n_rollouts = rollout_counts.pop()
    if n_rollouts == 0:
        raise DecisionEngineV2Error("No rollouts supplied.")
    within_band = 0
    rank1 = 0
    for i in range(n_rollouts):
        values_this_rollout = {
            cid: vals[i] for cid, vals in terminal_values_by_rollout_per_candidate.items()
        }
        best = max(values_this_rollout.values())
        this_value = values_this_rollout[action_candidate_id]
        if best - this_value <= near_optimal_band_width:
            within_band += 1
        if this_value >= best:
            rank1 += 1
    return DecisionConfidenceResult(
        state_id=state_id, action_candidate_id=action_candidate_id,
        p_within_near_optimal_band=round(within_band / n_rollouts, 4),
        p_rank_1=round(rank1 / n_rollouts, 4) if include_rank_1 else None,
        near_optimal_band_width=near_optimal_band_width, uncertainty=uncertainty,
        rollout_count=n_rollouts,
    )
