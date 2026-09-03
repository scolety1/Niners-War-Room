from src.services.ai_research_agent_input_service import (
    AiResearchAgentResponse,
    build_ai_research_agent_input,
    validate_ai_research_agent_response,
)
from src.services.failure_analysis_service import EvaluationRecord, slice_by_dimension


def _input(**overrides):
    records = [
        EvaluationRecord("r1", {"position": "QB"}, outcome_value=-5.0),
        EvaluationRecord("r2", {"position": "RB"}, outcome_value=8.0),
    ]
    slices = {"position": slice_by_dimension(records, dimension_name="position")}
    defaults = dict(
        metric_summaries={"mean_regret": 3.2}, failure_slices=slices,
        feature_availability={"market.overall_adp": "KNOWN"},
        challenger_metadata={"rookie-blend-v2": {"status": "REGISTERED"}},
        sample_sizes={"position": 2}, confidence={"mean_regret": "LOW"},
        known_leakage_constraints=("source_as_of < draft_date",),
        generated_at_utc="2026-09-03T00:00:00Z",
    )
    defaults.update(overrides)
    return build_ai_research_agent_input(**defaults)


def _response(**overrides):
    defaults = dict(
        hypothesis="QBs underperform due to a stale replacement baseline.",
        suspected_mechanism="Replacement depth uses roster capacity, not starter count.",
        proposed_feature=("replacement_depth_starter_aware",), proposed_challenger=None,
        proposed_experiment=None, acknowledged_slice_dimension_values=("QB",),
        responding_agent="ai_research_agent_v1", generated_at_utc="2026-09-03T00:00:00Z",
    )
    defaults.update(overrides)
    return AiResearchAgentResponse(**defaults)


def test_a_valid_response_acknowledging_the_worst_slice_has_no_violations() -> None:
    result = validate_ai_research_agent_response(_response(), source_input=_input())
    assert result == ()


def test_an_empty_hypothesis_is_a_violation() -> None:
    result = validate_ai_research_agent_response(
        _response(hypothesis="  "), source_input=_input(),
    )
    assert any("hypothesis" in v for v in result)


def test_a_response_that_never_acknowledges_the_worst_slice_is_a_violation() -> None:
    result = validate_ai_research_agent_response(
        _response(acknowledged_slice_dimension_values=("RB",)),  # only the GOOD slice
        source_input=_input(),
    )
    assert any("favorable" in v for v in result)


def test_a_response_smuggling_a_promotion_shaped_field_is_rejected() -> None:
    result = validate_ai_research_agent_response(
        _response(proposed_experiment={"decided_by": "ai_research_agent_v1"}),
        source_input=_input(),
    )
    assert any("promote" in v for v in result)


def test_build_ai_research_agent_input_carries_every_field() -> None:
    payload = _input()
    assert payload.metric_summaries == {"mean_regret": 3.2}
    assert "position" in payload.failure_slices
    assert payload.known_leakage_constraints == ("source_as_of < draft_date",)
