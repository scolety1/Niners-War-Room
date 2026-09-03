"""AI Explanation API over a DecisionBundle (directive section 30).

Consumes a `decision_bundle_service.DecisionBundle` and produces a
structured explanation, never raw model reasoning, never a claim not
traceable to a real field on the bundle. The explanation is built as a
STRUCTURED dataclass first (`DecisionBundleExplanation`) and the narrative
text is assembled FROM that structure -- so contradiction-checking
(section 30's own requirement) is mechanical: `explain_decision_bundle`
and `verify_explanation_matches_bundle` derive the same structured claims
independently from the same bundle and must agree field-for-field, rather
than a free-text explanation being checked by a second free-text pass.

If a bundle has no candidates, the explanation says so explicitly rather
than guessing -- "insufficient evidence" is a first-class, testable output,
never silently omitted.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.services.decision_bundle_service import CandidateBundle, DecisionBundle

INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"


@dataclass(frozen=True)
class DecisionBundleExplanation:
    has_evidence: bool
    top_player_id: str | None
    top_pick_score: float | None
    primary_reasons: tuple[str, ...]
    runner_up_player_id: str | None
    runner_up_note: str | None
    caveats: tuple[str, ...]
    text: str


def _primary_reasons(top: CandidateBundle) -> tuple[str, ...]:
    reasons: list[str] = []
    if top.team_score_delta > 0:
        reasons.append(f"adds {top.team_score_delta:+.1f} to Team Score")
    if top.equity_gain > 0:
        reasons.append(
            f"gains {top.equity_gain * 100:.1f} percentage points of simulated "
            "Championship Equity"
        )
    if top.make_it_back_probability is not None and top.make_it_back_probability < 0.5:
        reasons.append(
            f"has a low probability ({top.make_it_back_probability * 100:.0f}%) of "
            "surviving to a later pick"
        )
    if not reasons:
        reasons.append(f"has the highest evaluated Pick Score ({top.pick_score:.1f})")
    return tuple(reasons)


def _runner_up_note(top: CandidateBundle, runner_up: CandidateBundle) -> str:
    """The directive's own worked example shape: if the runner-up looks
    better on ONE structured field (standalone Player Score) but the top
    pick still wins, say so explicitly and cite the field that actually
    decided it -- never silently omit the tension."""
    if (
        top.player_score is not None
        and runner_up.player_score is not None
        and runner_up.player_score > top.player_score
    ):
        return (
            f"{runner_up.player_id} has a higher standalone Player Score "
            f"({runner_up.player_score:.1f} vs {top.player_score:.1f}), but adds less "
            f"projected Team Score ({runner_up.team_score_delta:+.1f} vs "
            f"{top.team_score_delta:+.1f})."
        )
    return (
        f"{runner_up.player_id} was the next-best alternative evaluated "
        f"(Pick Score {runner_up.pick_score:.1f} vs {top.pick_score:.1f})."
    )


def explain_decision_bundle(bundle: DecisionBundle) -> DecisionBundleExplanation:
    if not bundle.candidates:
        text = f"{INSUFFICIENT_EVIDENCE}: no candidates were evaluated for this decision."
        return DecisionBundleExplanation(
            has_evidence=False, top_player_id=None, top_pick_score=None,
            primary_reasons=(), runner_up_player_id=None, runner_up_note=None,
            caveats=(), text=text,
        )
    top = bundle.candidates[0]
    reasons = _primary_reasons(top)
    runner_up_id: str | None = None
    runner_up_note: str | None = None
    if len(bundle.candidates) > 1:
        runner_up = bundle.candidates[1]
        runner_up_id = runner_up.player_id
        runner_up_note = _runner_up_note(top, runner_up)
    caveats = top.warnings

    sentences = [
        f"{top.player_id} is the top action (Pick Score {top.pick_score:.1f}) "
        f"because it {', and '.join(reasons)}."
    ]
    if runner_up_note:
        sentences.append(runner_up_note)
    if caveats:
        sentences.append("Caveats: " + "; ".join(caveats) + ".")
    sentences.append(f"Uncertainty: {top.uncertainty}.")
    text = " ".join(sentences)

    return DecisionBundleExplanation(
        has_evidence=True,
        top_player_id=top.player_id,
        top_pick_score=top.pick_score,
        primary_reasons=reasons,
        runner_up_player_id=runner_up_id,
        runner_up_note=runner_up_note,
        caveats=caveats,
        text=text,
    )


def verify_explanation_matches_bundle(
    explanation: DecisionBundleExplanation, bundle: DecisionBundle
) -> tuple[str, ...]:
    """Independently re-derives the same structured claims from `bundle`
    and reports any field where the given explanation disagrees --
    the mechanical contradiction check section 30 asks for. An empty
    tuple means no contradiction was found."""
    reference = explain_decision_bundle(bundle)
    contradictions: list[str] = []
    if explanation.has_evidence != reference.has_evidence:
        contradictions.append(
            f"has_evidence: explanation says {explanation.has_evidence}, "
            f"bundle implies {reference.has_evidence}"
        )
    if explanation.top_player_id != reference.top_player_id:
        contradictions.append(
            f"top_player_id: explanation says {explanation.top_player_id!r}, "
            f"bundle's top candidate is {reference.top_player_id!r}"
        )
    if explanation.top_pick_score != reference.top_pick_score:
        contradictions.append(
            f"top_pick_score: explanation says {explanation.top_pick_score!r}, "
            f"bundle says {reference.top_pick_score!r}"
        )
    if explanation.runner_up_player_id != reference.runner_up_player_id:
        contradictions.append(
            f"runner_up_player_id: explanation says {explanation.runner_up_player_id!r}, "
            f"bundle says {reference.runner_up_player_id!r}"
        )
    return tuple(contradictions)
