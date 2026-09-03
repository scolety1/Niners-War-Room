import pytest

from src.services.ai_hypothesis_challenger_pipeline_service import (
    Anomaly,
    HypothesisChallengerPipelineError,
    evaluate_promotion_gate,
    propose_challenger_from_anomaly,
    submit_challenger_proposal_for_registration,
)
from src.services.champion_challenger_registry_service import (
    current_status,
    load_registration,
)


def _anomaly() -> Anomaly:
    return Anomaly(
        anomaly_id="anomaly-rookie-underrank-2026",
        description=(
            "Rookies with high market rank and strong draft capital are systematically "
            "under-ranked relative to their real-time ADP."
        ),
        evidence_summary={"sample_size": 12, "mean_gap_rounds": 2.3},
        detected_at_utc="2026-09-03T00:00:00Z",
        detector_version="anomaly-detector-v1",
    )


def test_propose_challenger_from_anomaly_requires_a_specific_hypothesis() -> None:
    with pytest.raises(HypothesisChallengerPipelineError):
        propose_challenger_from_anomaly(
            _anomaly(), proposal_id="p1", hypothesis="  ",
            feature_proposal=["draft_capital"], suggested_parameters={},
            proposed_at_utc="2026-09-03T00:00:00Z",
        )


def test_propose_challenger_from_anomaly_requires_at_least_one_feature() -> None:
    with pytest.raises(HypothesisChallengerPipelineError):
        propose_challenger_from_anomaly(
            _anomaly(), proposal_id="p1", hypothesis="Real hypothesis.",
            feature_proposal=[], suggested_parameters={},
            proposed_at_utc="2026-09-03T00:00:00Z",
        )


def test_propose_challenger_from_anomaly_builds_a_real_proposal() -> None:
    proposal = propose_challenger_from_anomaly(
        _anomaly(), proposal_id="p1",
        hypothesis="Blending market ADP into the rookie prior should reduce this gap.",
        feature_proposal=["draft_capital", "market_rank"],
        suggested_parameters={"blend_weight": 0.3},
        proposed_at_utc="2026-09-03T00:00:00Z",
    )
    assert proposal.anomaly_id == "anomaly-rookie-underrank-2026"
    assert proposal.feature_proposal == ("draft_capital", "market_rank")
    assert proposal.proposed_by == "ai_hypothesis_pipeline_v1"


def test_evaluate_promotion_gate_passes_when_every_metric_is_in_range() -> None:
    result = evaluate_promotion_gate(
        holdout_metrics={"mean_error_improvement": 0.08, "sample_size": 15},
        guardrails={"mean_error_improvement": (0.0, 1.0), "sample_size": (10, 1000)},
    )
    assert result.passed is True
    assert result.failures == ()


def test_evaluate_promotion_gate_fails_and_names_the_out_of_range_metric() -> None:
    result = evaluate_promotion_gate(
        holdout_metrics={"mean_error_improvement": -0.05},
        guardrails={"mean_error_improvement": (0.0, 1.0)},
    )
    assert result.passed is False
    assert "mean_error_improvement" in result.failures[0]


def test_evaluate_promotion_gate_treats_a_missing_metric_as_a_failure_not_a_skip() -> None:
    result = evaluate_promotion_gate(
        holdout_metrics={},
        guardrails={"mean_error_improvement": (0.0, 1.0)},
    )
    assert result.passed is False
    assert "missing" in result.failures[0]


def test_submit_challenger_proposal_for_registration_requires_a_real_human(tmp_path) -> None:
    proposal = propose_challenger_from_anomaly(
        _anomaly(), proposal_id="p1", hypothesis="Real hypothesis.",
        feature_proposal=["draft_capital"], suggested_parameters={},
        proposed_at_utc="2026-09-03T00:00:00Z",
    )
    with pytest.raises(HypothesisChallengerPipelineError):
        submit_challenger_proposal_for_registration(
            tmp_path, proposal, challenger_id="rookie-blend-v4",
            champion_name="champion", challenger_name="rookie-blend-v4",
            challenger_module="src.services.rookie_market_blend_challenger_service",
            replay_evaluation_summary={"mean_error_improvement": 0.08},
            registered_at_utc="2026-09-03T00:00:00Z", registered_by="auto",
        )


def test_submit_challenger_proposal_for_registration_writes_a_real_registration(tmp_path) -> None:
    proposal = propose_challenger_from_anomaly(
        _anomaly(), proposal_id="p1",
        hypothesis="Blending market ADP into the rookie prior should reduce this gap.",
        feature_proposal=["draft_capital", "market_rank"],
        suggested_parameters={"blend_weight": 0.3},
        proposed_at_utc="2026-09-03T00:00:00Z",
    )
    registration = submit_challenger_proposal_for_registration(
        tmp_path, proposal, challenger_id="rookie-blend-v4",
        champion_name="champion", challenger_name="rookie-blend-v4",
        challenger_module="src.services.rookie_market_blend_challenger_service",
        replay_evaluation_summary={"mean_error_improvement": 0.08, "sample_size": 12},
        registered_at_utc="2026-09-03T00:00:00Z", registered_by="owner",
    )
    assert registration.hypothesis == proposal.hypothesis
    assert registration.algorithm_parameters == {"blend_weight": 0.3}
    # Real registry state -- not just an in-memory object.
    assert current_status(tmp_path, "rookie-blend-v4") == "REGISTERED"
    loaded = load_registration(tmp_path, "rookie-blend-v4")
    assert loaded.evaluation_summary == {"mean_error_improvement": 0.08, "sample_size": 12}
