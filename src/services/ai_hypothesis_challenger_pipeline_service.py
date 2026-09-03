"""AI hypothesis -> challenger pipeline (directive section 22).

The future self-improving loop, scoped exactly as the directive draws it:

    anomaly -> hypothesis -> feature/challenger proposal -> registered
    challenger -> replay evaluation -> holdout evaluation -> gate ->
    human/restricted promotion mechanism

This module owns everything UP TO registration and the mechanical gate
check. It deliberately does NOT wrap, call, or shortcut
`champion_challenger_registry_service.record_promotion_decision` --
promotion stays exactly where section 23 already put it: a human calling
that function directly, with a full receipt and a real identity. AI may
detect an anomaly, propose a hypothesis, propose a feature/challenger
spec, and register the resulting challenger (an ordinary, auditable
registration, not a promotion); AI may never promote itself.

`submit_challenger_proposal_for_registration` is the ONLY function here
that touches the registry, and it does so only through
`champion_challenger_registry_service.register_challenger` -- the same
public write path every other registration in this repo uses.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.champion_challenger_registry_service import (
    ChallengerRegistration,
    register_challenger,
)

PIPELINE_VERSION = "ai-hypothesis-challenger-pipeline-v1"


class HypothesisChallengerPipelineError(ValueError):
    pass


@dataclass(frozen=True)
class Anomaly:
    anomaly_id: str
    description: str  # e.g. "rookies with high market rank and strong draft capital are
    # systematically under-ranked"
    evidence_summary: Mapping[str, object]  # real numbers backing the anomaly claim
    detected_at_utc: str
    detector_version: str


@dataclass(frozen=True)
class ChallengerProposal:
    proposal_id: str
    anomaly_id: str
    hypothesis: str
    feature_proposal: tuple[str, ...]  # named features the challenger would add/change
    suggested_parameters: Mapping[str, object]
    proposed_by: str  # always an AI actor identity, e.g. "ai_hypothesis_pipeline_v1"
    proposed_at_utc: str


def propose_challenger_from_anomaly(
    anomaly: Anomaly,
    *,
    proposal_id: str,
    hypothesis: str,
    feature_proposal: Sequence[str],
    suggested_parameters: Mapping[str, object],
    proposed_at_utc: str,
    proposed_by: str = "ai_hypothesis_pipeline_v1",
) -> ChallengerProposal:
    if not hypothesis.strip():
        raise HypothesisChallengerPipelineError(
            "hypothesis must be a specific, non-empty claim, not a vague 'improve accuracy'."
        )
    if not feature_proposal:
        raise HypothesisChallengerPipelineError(
            "feature_proposal must name at least one concrete feature."
        )
    return ChallengerProposal(
        proposal_id=proposal_id,
        anomaly_id=anomaly.anomaly_id,
        hypothesis=hypothesis,
        feature_proposal=tuple(feature_proposal),
        suggested_parameters=dict(suggested_parameters),
        proposed_by=proposed_by,
        proposed_at_utc=proposed_at_utc,
    )


@dataclass(frozen=True)
class GateResult:
    passed: bool
    failures: tuple[str, ...]
    checked_metrics: Mapping[str, float]


def evaluate_promotion_gate(
    *,
    holdout_metrics: Mapping[str, float],
    guardrails: Mapping[str, tuple[float, float]],
) -> GateResult:
    """A purely mechanical pre-check -- NOT a promotion decision. Each
    guardrail is (min_inclusive, max_inclusive) for a named holdout
    metric. A metric named in `guardrails` but missing from
    `holdout_metrics` is treated as a failure (never silently skipped --
    a caller must actually compute the holdout metric, not just declare
    a guardrail for it). Passing this gate is a prerequisite a human
    should consult before calling `record_promotion_decision` themselves
    -- this function has no power to promote anything."""
    failures: list[str] = []
    checked: dict[str, float] = {}
    for metric_name, (low, high) in guardrails.items():
        if metric_name not in holdout_metrics:
            failures.append(f"{metric_name}: missing from holdout_metrics")
            continue
        value = holdout_metrics[metric_name]
        checked[metric_name] = value
        if not (low <= value <= high):
            failures.append(f"{metric_name}={value} outside guardrail [{low}, {high}]")
    return GateResult(passed=not failures, failures=tuple(failures), checked_metrics=checked)


def submit_challenger_proposal_for_registration(
    root,
    proposal: ChallengerProposal,
    *,
    challenger_id: str,
    champion_name: str,
    challenger_name: str,
    challenger_module: str,
    replay_evaluation_summary: Mapping[str, object],
    registered_at_utc: str,
    registered_by: str,
    parent: str | None = None,
) -> ChallengerRegistration:
    """The one and only registry write path in this module -- a real
    registration via the existing public `register_challenger`, never a
    promotion. `replay_evaluation_summary` becomes the registration's
    `evaluation_summary` (the same real-evidence requirement
    `register_challenger` already enforces: it must not be empty)."""
    if registered_by.strip().lower() in {"system", "auto", "automatic", ""}:
        raise HypothesisChallengerPipelineError(
            "registered_by must name a real human identity/role -- an AI-proposed "
            "challenger still requires a human to submit its registration."
        )
    registration = ChallengerRegistration(
        challenger_id=challenger_id,
        champion_name=champion_name,
        challenger_name=challenger_name,
        challenger_module=challenger_module,
        hypothesis=proposal.hypothesis,
        evaluation_summary=dict(replay_evaluation_summary),
        registered_at_utc=registered_at_utc,
        registered_by=registered_by,
        parent=parent,
        algorithm_parameters=dict(proposal.suggested_parameters),
    )
    register_challenger(root, registration)
    return registration
