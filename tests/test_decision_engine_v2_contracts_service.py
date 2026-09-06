import pytest

from src.services.decision_engine_v2_contracts_service import (
    EX_ANTE_MODEL_REGRET,
    PICK_SCORE_DECISION_QUALITY_PERCENTILE,
    TERMINAL_OBJECTIVE_CHAMPIONSHIP_EQUITY,
    TERMINAL_OBJECTIVE_TEAM_SCORE,
    ComparableStateStratum,
    DecisionEngineV2Error,
    FrozenCandidateSet,
    UncertaintyDecomposition,
    compute_decision_confidence,
    compute_decision_quality_percentile_raw_rank,
    compute_raw_action_value,
    compute_regret,
    register_pick_score_calibration_contract_v2,
)

# --- Section 11: Raw Action Value V2 --------------------------------------

def test_raw_action_value_averages_real_rollout_terminal_values() -> None:
    result = compute_raw_action_value(
        state_id="s1", action_candidate_id="p1", terminal_values_by_rollout=[60.0, 70.0, 80.0],
        terminal_objective_name=TERMINAL_OBJECTIVE_TEAM_SCORE, lookahead_depth=2,
        championship_equity_gate_passed=False, provenance={"source": "fixture"},
    )
    assert result.expected_terminal_value == pytest.approx(70.0)
    assert result.rollout_count == 3


def test_raw_action_value_refuses_championship_equity_before_gate_passes() -> None:
    with pytest.raises(DecisionEngineV2Error):
        compute_raw_action_value(
            state_id="s1", action_candidate_id="p1", terminal_values_by_rollout=[1.0],
            terminal_objective_name=TERMINAL_OBJECTIVE_CHAMPIONSHIP_EQUITY, lookahead_depth=1,
            championship_equity_gate_passed=False, provenance={},
        )


def test_raw_action_value_allows_championship_equity_once_gate_passes() -> None:
    result = compute_raw_action_value(
        state_id="s1", action_candidate_id="p1", terminal_values_by_rollout=[0.5, 0.6],
        terminal_objective_name=TERMINAL_OBJECTIVE_CHAMPIONSHIP_EQUITY, lookahead_depth=1,
        championship_equity_gate_passed=True, provenance={},
    )
    assert result.terminal_objective_name == TERMINAL_OBJECTIVE_CHAMPIONSHIP_EQUITY


def test_raw_action_value_refuses_empty_rollouts() -> None:
    with pytest.raises(DecisionEngineV2Error):
        compute_raw_action_value(
            state_id="s1", action_candidate_id="p1", terminal_values_by_rollout=[],
            terminal_objective_name=TERMINAL_OBJECTIVE_TEAM_SCORE, lookahead_depth=1,
            championship_equity_gate_passed=False, provenance={},
        )


# --- Section 12: Regret contract ------------------------------------------

def test_frozen_candidate_set_refuses_construction_after_outcome_unlock() -> None:
    with pytest.raises(DecisionEngineV2Error):
        FrozenCandidateSet(
            state_id="s1", candidate_action_ids=("p1", "p2"), frozen_at_utc="t",
            frozen_before_outcome_unlock=False,
        )


def test_compute_regret_uses_only_the_frozen_set() -> None:
    candidate_set = FrozenCandidateSet(
        state_id="s1", candidate_action_ids=("p1", "p2"), frozen_at_utc="t",
        frozen_before_outcome_unlock=True,
    )
    result = compute_regret(
        action_candidate_id="p2",
        terminal_value_by_candidate={"p1": 80.0, "p2": 60.0, "p3": 999.0},
        regret_kind=EX_ANTE_MODEL_REGRET, candidate_set=candidate_set,
    )
    # p3's 999.0 must NOT influence best_terminal_value -- outside the frozen set.
    assert result.best_terminal_value == pytest.approx(80.0)
    assert result.regret == pytest.approx(20.0)


def test_compute_regret_refuses_an_action_outside_the_frozen_set() -> None:
    candidate_set = FrozenCandidateSet(
        state_id="s1", candidate_action_ids=("p1",), frozen_at_utc="t",
        frozen_before_outcome_unlock=True,
    )
    with pytest.raises(DecisionEngineV2Error):
        compute_regret(
            action_candidate_id="p2", terminal_value_by_candidate={"p1": 10.0},
            regret_kind=EX_ANTE_MODEL_REGRET, candidate_set=candidate_set,
        )


def test_compute_regret_refuses_missing_values_for_a_frozen_candidate() -> None:
    candidate_set = FrozenCandidateSet(
        state_id="s1", candidate_action_ids=("p1", "p2"), frozen_at_utc="t",
        frozen_before_outcome_unlock=True,
    )
    with pytest.raises(DecisionEngineV2Error):
        compute_regret(
            action_candidate_id="p1", terminal_value_by_candidate={"p1": 10.0},
            regret_kind=EX_ANTE_MODEL_REGRET, candidate_set=candidate_set,
        )


# --- Section 13: Pick Score calibration contract V2 -----------------------

def test_register_pick_score_v2_never_fits_the_transform() -> None:
    contract = register_pick_score_calibration_contract_v2(
        ComparableStateStratum("12T_PPR", 12, "EARLY_ROUNDS_1_3", "empty")
    )
    assert contract.semantics_name == PICK_SCORE_DECISION_QUALITY_PERCENTILE
    assert contract.transform_fit is False


def test_decision_quality_percentile_raw_rank_favors_lower_regret() -> None:
    percentile = compute_decision_quality_percentile_raw_rank(
        regret_value=2.0, comparable_regrets=[0.0, 1.0, 3.0, 5.0]
    )
    # 2 of 4 comparable regrets are worse (3.0, 5.0) -> 50th percentile
    assert percentile == pytest.approx(50.0)


def test_decision_quality_percentile_refuses_empty_comparable_set() -> None:
    with pytest.raises(DecisionEngineV2Error):
        compute_decision_quality_percentile_raw_rank(regret_value=1.0, comparable_regrets=[])


# --- Section 14: Decision Confidence ---------------------------------------

def test_decision_confidence_within_band_and_rank1_are_computed_correctly() -> None:
    uncertainty = UncertaintyDecomposition(monte_carlo_sampling_error=0.02)
    result = compute_decision_confidence(
        state_id="s1", action_candidate_id="p1",
        terminal_values_by_rollout_per_candidate={
            "p1": [70.0, 69.0, 50.0],
            "p2": [70.0, 70.0, 80.0],
        },
        near_optimal_band_width=1.5, uncertainty=uncertainty,
    )
    # rollout 0: tie (within band, rank1); rollout 1: 69 vs 70, within 1.5 band, not rank1;
    # rollout 2: 50 vs 80, far outside band, not rank1.
    assert result.p_within_near_optimal_band == pytest.approx(2 / 3, abs=1e-4)
    assert result.p_rank_1 == pytest.approx(1 / 3, abs=1e-4)
    assert result.rollout_count == 3


def test_decision_confidence_refuses_unpaired_rollout_counts() -> None:
    uncertainty = UncertaintyDecomposition(monte_carlo_sampling_error=0.01)
    with pytest.raises(DecisionEngineV2Error):
        compute_decision_confidence(
            state_id="s1", action_candidate_id="p1",
            terminal_values_by_rollout_per_candidate={"p1": [1.0, 2.0], "p2": [1.0]},
            near_optimal_band_width=1.0, uncertainty=uncertainty,
        )


def test_uncertainty_decomposition_is_not_fully_characterized_from_mc_se_alone() -> None:
    uncertainty = UncertaintyDecomposition(monte_carlo_sampling_error=0.02)
    assert uncertainty.is_fully_characterized is False


def test_uncertainty_decomposition_is_fully_characterized_when_every_source_is_known() -> None:
    uncertainty = UncertaintyDecomposition(
        monte_carlo_sampling_error=0.02, projection_uncertainty=0.1, market_uncertainty=0.1,
        opponent_randomness=0.1, outcome_uncertainty=0.1, model_uncertainty=0.1,
    )
    assert uncertainty.is_fully_characterized is True
