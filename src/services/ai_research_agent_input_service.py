"""AI research-agent input contract (directive section 18).

A bounded input artifact for the future AI hypothesis generator
(`ai_hypothesis_challenger_pipeline_service`'s eventual real caller):
only structured evaluation evidence -- metric summaries, failure slices
(from `failure_analysis_service`), feature availability, challenger
metadata, sample sizes, confidence, and known leakage constraints. No
raw historical row data, no player-identifying free text beyond what
the failure slices themselves already carry.

The AI may respond with a hypothesis, suspected mechanism, proposed
feature, proposed challenger, or proposed experiment -- never a
promotion, never a historical-evidence edit, never a response built
only from the favorable slices. `validate_ai_research_agent_response`
enforces the last two structurally: it rejects any response payload
that resembles a promotion action, and it requires the response to
explicitly acknowledge the WORST-performing slice from the input (not
only good news) whenever the input actually has a negative-outcome
slice to acknowledge.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.failure_analysis_service import FailureSliceReport

# Any of these field names appearing in a response payload is treated as a
# forbidden promotion-shaped action -- defense in depth on top of the
# structural fact that this contract has no promote() call to reach at all.
FORBIDDEN_RESPONSE_FIELDS = frozenset({"decided_by", "promotion_status", "champion_replaced"})


class AiResearchAgentInputError(ValueError):
    pass


@dataclass(frozen=True)
class AiResearchAgentInput:
    metric_summaries: Mapping[str, float]
    failure_slices: Mapping[str, FailureSliceReport]
    feature_availability: Mapping[str, str]  # feature_name -> KNOWN/UNKNOWN/BLOCKED/... summary
    challenger_metadata: Mapping[str, Mapping[str, object]]
    sample_sizes: Mapping[str, int]
    confidence: Mapping[str, str]
    known_leakage_constraints: tuple[str, ...]
    generated_at_utc: str


def build_ai_research_agent_input(
    *,
    metric_summaries: Mapping[str, float],
    failure_slices: Mapping[str, FailureSliceReport],
    feature_availability: Mapping[str, str],
    challenger_metadata: Mapping[str, Mapping[str, object]],
    sample_sizes: Mapping[str, int],
    confidence: Mapping[str, str],
    known_leakage_constraints: Sequence[str],
    generated_at_utc: str,
) -> AiResearchAgentInput:
    return AiResearchAgentInput(
        metric_summaries=dict(metric_summaries),
        failure_slices=dict(failure_slices),
        feature_availability=dict(feature_availability),
        challenger_metadata={k: dict(v) for k, v in challenger_metadata.items()},
        sample_sizes=dict(sample_sizes),
        confidence=dict(confidence),
        known_leakage_constraints=tuple(known_leakage_constraints),
        generated_at_utc=generated_at_utc,
    )


@dataclass(frozen=True)
class AiResearchAgentResponse:
    hypothesis: str
    suspected_mechanism: str
    proposed_feature: tuple[str, ...]
    proposed_challenger: str | None
    proposed_experiment: Mapping[str, object] | None
    acknowledged_slice_dimension_values: tuple[object, ...]
    responding_agent: str
    generated_at_utc: str


def validate_ai_research_agent_response(
    response: AiResearchAgentResponse, *, source_input: AiResearchAgentInput
) -> tuple[str, ...]:
    """Returns a tuple of violation descriptions (empty means valid).
    Never raises for a substantive disagreement -- only for the three
    hard rules the directive states: no promotion, no favorable-only
    slicing, and (structurally, by this contract simply never accepting
    one) no historical-evidence mutation."""
    violations: list[str] = []
    if not response.hypothesis.strip():
        violations.append("hypothesis must be non-empty.")
    for field_name in FORBIDDEN_RESPONSE_FIELDS:
        if response.proposed_experiment and field_name in response.proposed_experiment:
            violations.append(
                f"proposed_experiment contains a promotion-shaped field: {field_name!r} -- "
                "AI may not promote; promotion is a separate human-only action."
            )
    worst_values = {
        report.worst_slice.dimension_value
        for report in source_input.failure_slices.values()
        if report.worst_slice is not None
    }
    if worst_values and not (worst_values & set(response.acknowledged_slice_dimension_values)):
        violations.append(
            "response does not acknowledge any worst-performing slice from the input -- "
            "AI may not select only favorable slices."
        )
    return tuple(violations)
