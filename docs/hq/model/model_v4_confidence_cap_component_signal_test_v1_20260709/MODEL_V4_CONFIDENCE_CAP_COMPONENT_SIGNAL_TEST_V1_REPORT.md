# Model v4 Confidence Cap Component Signal Test V1 Report

## Verdict

`YELLOW_CONFIDENCE_CAP_COMPONENT_SIGNAL_MIXED_WITH_CAVEATS`

## Clear Answer

The regenerated confidence-cap receipts show limited review-only guardrail value, but they do not add useful predictive signal beyond PYF. They should be interpreted as coverage/missingness context only, not as a formula score, rank adjustment, exact Model v4 replay evidence, or production accuracy evidence.

## Scope

- Rows tested: `5518`
- Seasons: `2013-2025`
- Position coverage: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Input signal tested: `confidence_cap_value` from regenerated `confidence_cap_receipts` only
- Baseline: PYF / `prior_nwr_points` from the existing partial replay panel

## Main Findings

- Low-confidence rows: `28` with distribution `{'WR': 28}`.
- QB/RB/TE have no confidence-cap variation, so direct component signal is not measurable there.
- WR confidence-cap Spearman vs next-season finish: `0.085` versus PYF `0.685`.
- PYF false positives explained by low-confidence rows: `0.0%`.
- PYF false negatives flagged by low-confidence rows: `0.3%`.
- The low-confidence rows are mostly non-startable, but they are too few and too concentrated to justify broader use.

## PYF Comparison

Confidence cap does not beat PYF in any position. It also does not meaningfully explain PYF misses. The strongest safe conclusion is that confidence cap can remain as a review-only caution/coverage field for future component tests.

## Production Status

- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Formula Gauntlet remains blocked.
- Champion refinement remains blocked.
- Rankings integration remains blocked.
- Production/model-use remains blocked.
- No source was promoted.

## Recommendation

Recommended next lane: `Model v4 Role Archetype Receipt Regeneration Pilot V1`, still one-family, review-only, and contract-bound. Confidence cap does not resolve the major miss patterns by itself.