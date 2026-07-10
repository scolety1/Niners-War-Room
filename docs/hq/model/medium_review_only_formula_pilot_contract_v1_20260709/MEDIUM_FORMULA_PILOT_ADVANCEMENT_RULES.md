# Medium Formula Pilot Advancement Rules

No candidate can become a winner, champion, production-ready formula, ranking-ready formula, approved model, source promotion, or production/model-use input.

## Promising Review-Only

A candidate may be called `PROMISING_REVIEW_ONLY` only if it:

- beats or clearly contextualizes PYF overall.
- beats or clearly contextualizes PYF by at least one position.
- reports position-level performance.
- does not materially worsen sparse-history or low-games slices.
- improves or explains PYF false positives or false negatives.
- uses only allowed review-safe inputs.
- stays review-only.
- passes leakage/as-of checks.
- documents source/use-gate status.
- has no hidden production effect.

## Held Or Rejected

A candidate must be held or rejected if it:

- improves pooled metrics while harming sparse-history or low-games rows.
- wins only through a tiny or unstable slice.
- fails source/use-gate or leakage/as-of checks.
- needs blocked inputs.
- changes after results are seen.
- implies direct role, age, PFR, injury, market, or current-context production logic.

## Review Boundary

Advancement from this pilot can only recommend a later Master HQ review lane. It cannot approve rankings integration, production/model-use, exact Model v4 replay, Formula Gauntlet, 100-candidate Gauntlet, or champion refinement.
