# Veteran Decline Reconsideration

## Bottom Line

`VET_008_FALSE_NEGATIVE_PROTECTION_RULE` should not be discarded. It should be preserved as a `CONTEXT_GUARDRAIL_OVERLAY`, not advanced as a primary or secondary scoring overlay.

## Preserved Evidence

- Best rule: `VET_008_FALSE_NEGATIVE_PROTECTION_RULE`
- False-positive reduction: `10`
- Net miss reduction: `20`
- False negatives created: `0`
- Spearman delta: `0.000`
- Prior verdict: mixed/context only
- No veteran rule cleared the promising threshold

## Why VET_008 Did Not Clear Promising Status

The threshold was not merely too strict. VET_008 had one strong full-history row on the best full-history reference, but it was not stable enough across reference formulas and windows:

- PYF full-history: net miss reduction `4`, false-positive reduction `2`, false negatives created `0`.
- Best full-history: net miss reduction `20`, false-positive reduction `10`, false negatives created `0`.
- Best broad-window: net miss reduction `4`, false-positive reduction `2`, false negatives created `2`.
- Best partial-window: net miss reduction `0`, false-positive reduction `0`, false negatives created `1`, classified harmful/no-signal.

That pattern supports context/guardrail preservation, not scoring overlay promotion. It shows a real veteran-decline warning signal, but not a broadly stable scoring overlay.

## Answers

- Was the threshold too strict? No. It correctly blocked promotion from one strong row with mixed window/reference behavior.
- Did it fail by window, position, severity, stability, collateral damage, or another criterion? Primarily by cross-window/reference stability and partial-window behavior; broad-window created false negatives and partial-window was harmful/no-signal.
- Should it remain context only? Yes, but with stronger wording: context/guardrail, not discarded.
- Should it become a `CONTEXT_GUARDRAIL_OVERLAY`? Yes.
- Is a narrow second veteran-decline refinement justified? Not before docs-only push/merge-readiness. It could be user-authorized later if Master HQ wants to invest in a veteran-decline lane.
- Or should veteran decline stop for now? Active veteran-decline testing should stop for now, while VET_008 and the older-player falloff evidence are preserved as context/guardrail.

## Decision

Veteran decline should be preserved as a review-only context/guardrail overlay family. It should not be interpreted as discarded, but it also should not receive scoring-overlay status or ranking simulation eligibility.
