# Small Review-Only Formula Pilot V1 Report

## Verdict

`GREEN_SMALL_FORMULA_PILOT_FOUND_PROMISING_REVIEW_ONLY_CANDIDATES`

## Clear Answer

The small review-only formula pilot tested exactly `15` approved candidates on `5,518` player-season rows. The only candidates that changed rankings were the predeclared two-year and three-year weighted production variants; the role, age/lifecycle, sparse-history, low-games, and confidence-cap candidates were run as PYF-centered diagnostics by contract. `2` candidate(s) beat PYF overall by Spearman, while the context candidates mainly preserved useful guardrail and miss-taxonomy direction rather than producing new formula superiority.

## Benchmark Scope

- Rows tested: `5518`
- Seasons: `2013-2025`
- Position coverage: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Candidates tested: `15`
- Review-only rows: `5518`
- Model-use allowed rows: `0`
- Production-approved rows: `0`
- Age/lifecycle missing rows: `8` (0.1%)

## Best Overall Candidate

Best non-PYF overall candidate by Spearman: `PILOT_003_THREE_YEAR_WEIGHTED_PRODUCTION_60_30_10` with Spearman `0.754` versus comparable PYF `0.741`.

## Best Candidate By Position

- QB: `PILOT_003_THREE_YEAR_WEIGHTED_PRODUCTION_60_30_10` with Spearman `0.735` versus PYF `0.712`.
- RB: `PILOT_003_THREE_YEAR_WEIGHTED_PRODUCTION_60_30_10` with Spearman `0.651` versus PYF `0.633`.
- WR: `PILOT_002_TWO_YEAR_WEIGHTED_PRODUCTION_70_30` with Spearman `0.702` versus PYF `0.691`.
- TE: `PILOT_003_THREE_YEAR_WEIGHTED_PRODUCTION_60_30_10` with Spearman `0.719` versus PYF `0.701`.

## PYF Comparison

- PYF overall Spearman: `0.741`
- PYF startable precision: `52.1%`
- Candidate(s) beating PYF overall: `2`
- Candidate-position results beating PYF: `8`

## Guardrail Findings

- Sparse-history rows: `1453` with startable rate `3.3%`.
- Low-games rows: `1453` with startable rate `3.3%`.
- High-volume role rows contained `469` PYF false positives.
- Low/sparse role rows contained `54` PYF false negatives.
- Older/late lifecycle rows contained `76` PYF false positives.
- Young/early lifecycle rows contained `173` PYF false negatives.

## Interpretation

This pilot does not approve a formula winner. It supports a small next step only if Master HQ wants another review-only lane. Weighted production variants may be considered for cautious review-only refinement because they were predeclared and tested without tuning. Role archetype and age/lifecycle remain useful as slice reporting and guardrail context. Confidence cap remains caution/coverage context only.

## Recommended Next Lane

Recommended next lane: `Medium Review-Only Formula Pilot Contract V1`.

That lane should predeclare a modest expansion around fixed multi-year production variants, position-specific reporting, and guardrail slice reporting. It must not run 100 candidates, tune weights, select winners, change rankings, or approve production/model-use.

## Current Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Gauntlet remains blocked.
- Champion refinement remains blocked.
- No source was promoted.
- No ranking/app/runtime/model behavior changed.
