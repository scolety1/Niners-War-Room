import pytest

from src.services.metric_status_contract_service import (
    MetricStatus,
    championship_equity_status,
    cost_of_waiting_status,
    make_it_back_status,
    pick_score_status,
    player_score_status,
    raw_action_value_status,
    team_score_status,
)


def test_metric_status_rejects_an_unknown_computation_state() -> None:
    with pytest.raises(ValueError):
        MetricStatus(
            computation_state="NOT_A_REAL_STATE",
            genuine_zero=False,
            tied_no_spread=None,
            validation_domain="x",
            source_freshness="x",
        )


def test_player_score_missing_is_missing_input_not_a_coerced_zero() -> None:
    status = player_score_status(None, source_as_of="2026-08-08")
    assert status.computation_state == "MISSING_INPUT"
    assert status.genuine_zero is False


def test_player_score_present_and_genuinely_zero_is_evaluated_and_flagged() -> None:
    status = player_score_status(0.0, source_as_of="2026-08-08")
    assert status.computation_state == "EVALUATED"
    assert status.genuine_zero is True


def test_player_score_present_and_nonzero() -> None:
    status = player_score_status(42.0, source_as_of="2026-08-08")
    assert status.computation_state == "EVALUATED"
    assert status.genuine_zero is False


def test_team_score_and_equity_are_always_evaluated_when_a_candidate_exists() -> None:
    # Candidates without a legal pick_score are excluded upstream before a
    # CandidateBundle is ever built -- so for any candidate that IS present,
    # Team Score / Equity really did run; this is not a fabricated "always
    # evaluated" claim, it reflects how build_decision_bundle actually works.
    team = team_score_status(55.0, source_as_of="2026-08-08")
    equity = championship_equity_status(0.12, standard_error=0.02, source_as_of="2026-08-08")
    assert team.computation_state == "EVALUATED"
    assert equity.computation_state == "EVALUATED"
    assert "standard error" in (equity.data_coverage or "")


def test_make_it_back_pending_when_no_probability_yet() -> None:
    status = make_it_back_status(None, None, source_as_of="2026-08-08")
    assert status.computation_state == "PENDING"


def test_make_it_back_evaluated_discloses_real_trial_count() -> None:
    status = make_it_back_status(0.73, 200, source_as_of="2026-08-08")
    assert status.computation_state == "EVALUATED"
    assert status.data_coverage == "200 simulated continuations"


def test_cost_of_waiting_flags_the_fallback_estimate_distinctly() -> None:
    full = cost_of_waiting_status(3.0, from_v2_evaluation=True, source_as_of="2026-08-08")
    fallback = cost_of_waiting_status(3.0, from_v2_evaluation=False, source_as_of="2026-08-08")
    assert full.data_coverage != fallback.data_coverage
    assert full.computation_state == fallback.computation_state == "EVALUATED"


def test_pick_score_status_carries_the_tied_flag_through_unmodified() -> None:
    tied = pick_score_status(50.0, tied_no_spread=True, source_as_of="2026-08-08")
    not_tied = pick_score_status(90.0, tied_no_spread=False, source_as_of="2026-08-08")
    assert tied.tied_no_spread is True
    assert not_tied.tied_no_spread is False


def test_raw_action_value_ok_maps_to_evaluated() -> None:
    status = raw_action_value_status("OK", 4.2, source_as_of="2026-08-08")
    assert status.computation_state == "EVALUATED"


def test_raw_action_value_unavailable_maps_to_a_real_non_evaluated_state() -> None:
    status = raw_action_value_status(
        "UNAVAILABLE: outside top max_rav_candidates", None, source_as_of="2026-08-08"
    )
    assert status.computation_state == "BUDGET_LIMITED"
    assert status.data_coverage == "outside top max_rav_candidates"


def test_source_freshness_reports_unknown_rather_than_a_blank_string() -> None:
    status = team_score_status(10.0, source_as_of="")
    assert status.source_freshness == "UNKNOWN"
