# Overlay Portfolio Challenge / Veteran Decline Reconsideration V1

## Verdict

`GREEN_OVERLAY_PORTFOLIO_REVIEW_CONFIRMS_SPARSE_HISTORY_PRIMARY_WITH_GUARDRAILS`

## Purpose

This packet reviews whether the latest stop packet was being interpreted too narrowly. It confirms that only one overlay deserves primary review-only scoring status, while several other overlay families should be preserved as context, guardrails, warning-only concepts, partial-window concepts, or future user-authorized refinement candidates.

This is review/reconsideration only. It did not run new formula tests, run overlay tests, tune thresholds, run ranking simulation, change production rankings, change app/runtime/model behavior, promote sources, push, merge, write to canonical `local_exports`, approve model-use, or create hidden sort/recommendation logic.

## Verified Inputs

- Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`
- Prior stop packet commit verified: `66d146cda4b8b1e5de4175f809546252b7cd0388`

## Core Clarification

The phrase only one primary overlay means:

- `REFINE_005_A_EARLY_ROLE_015` is the only `PRIMARY_REVIEW_ONLY_SCORING_OVERLAY`.

It does not mean:

- veteran decline is discarded
- older-player falloff is discarded
- injury/availability caveats are discarded
- low snap/depth warnings are discarded
- role-promotion context is discarded

Those families remain valuable as context, guardrails, warning-only overlays, partial-window-only overlays, or future user-authorized refinement candidates.

## Primary Scoring Overlay

- `REFINE_005_A_EARLY_ROLE_015`
- Status: `PRIMARY_REVIEW_ONLY_SCORING_OVERLAY`
- Net miss reduction: `16`
- Misses resolved: `25`
- New misses: `9`
- False-negative reduction: `8`

No overlay batch family beat it on net miss reduction or false-negative reduction.

## Context / Guardrail Overlays

- Availability rebound
- Starter/depth promotion
- Snap-growth role promotion
- Veteran role-loss / prior-production trap
- Older / late lifecycle falloff
- Injury/availability caveat
- Low snap/depth warning

## Future Refinement Candidates

Only if explicitly user-authorized:

- Draft-capital-with-role
- Veteran role-loss / prior-production trap
- Older / late lifecycle falloff
- Availability rebound
- Starter/depth or snap-growth role-promotion
- Expected opportunity / NGS partial-window confirmation

## Stop-Testing Items

- Broad overlay batch testing
- Overlay stacking
- Current position-specific variants
- Current harmful sparse-history variants
- Veteran-decline scoring promotion from current evidence
- Older-player scoring promotion from current evidence

## VET_008 Answer

`VET_008_FALSE_NEGATIVE_PROTECTION_RULE` should be preserved as a `CONTEXT_GUARDRAIL_OVERLAY`.

It had one strong row:

- Best full-history reference
- False-positive reduction: `10`
- Net miss reduction: `20`
- False negatives created: `0`
- Spearman delta: `0.000`

But it did not clear promising status because its behavior was mixed across references/windows:

- PYF full-history net `4`
- Best broad-window net `4` with `2` false negatives created
- Best partial-window net `0` with `1` false negative created and harmful/no-signal classification

The threshold was appropriate. VET_008 is a real guardrail signal, but not stable enough for scoring-overlay status.

## Older-Player Falloff Answer

Older-player falloff is not discarded. It should remain a context/guardrail overlay concept.

It is already partly captured by:

- age/lifecycle
- veteran role-loss / prior-production trap
- low snap/depth warning
- injury/availability caveat

Dedicated older-player scoring overlays were not supported by current evidence because positive rows created too many false negatives or lacked stability.

## Push / Merge Readiness

Recommendation:

`Proceed to docs-only push/merge-readiness`

This recommendation is conditional on preserving the clarified portfolio interpretation: sparse-history is the only primary scoring overlay, while veteran decline and older-player falloff remain preserved as context/guardrail overlays rather than discarded.

## Gates

- Ranking simulation: blocked / not justified.
- Production/model-use: blocked.
- Rankings integration: blocked.
- App/runtime behavior: unchanged.
- Source promotion: blocked.
- Push/merge: not performed.
