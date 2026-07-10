# Age / Lifecycle Formula Pilot Decision

## Decision

Age/lifecycle may be included in the next small review-only formula pilot.

## Allowed Pilot Role

- Formula-family context
- Diagnostic slice
- Guarded candidate variant
- Decline-risk slice
- Breakout-window slice
- Position-specific age/lifecycle reporting

## Pilot Boundaries

The pilot may not:

- tune optimized weights
- select formula winners
- run Formula Gauntlet tournaments
- run 100 candidates
- change rankings
- change app/runtime/model behavior
- write to canonical `local_exports`
- promote sources
- claim production accuracy

## Required Interpretation

Age/lifecycle is useful context, not a direct ranking signal. The evidence supports slice reporting and guarded formula-family design because age/lifecycle helps explain PYF false positives and false negatives. It does not prove formula superiority.

## Recommended Next Lane

`Small Review-Only Formula Pilot Contract V1`

The contract should define a narrow pilot before any execution. It should include PYF as mandatory anchor, role archetype as review-only guardrail/miss taxonomy, and age/lifecycle as review-only formula-family context.
