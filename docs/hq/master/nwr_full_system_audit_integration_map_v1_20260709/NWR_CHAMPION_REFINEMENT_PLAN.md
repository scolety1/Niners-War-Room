# NWR Champion Refinement Plan

Champion refinement is not allowed now. This file defines the future process only.

## Future Refinement Flow

1. Run an approved review-only tournament.
2. Select top 5 to 10 candidates only for review, not promotion.
3. Perturb weights around each candidate using predeclared grids.
4. Compare every perturbation to PYF.
5. Require position-level stability.
6. Require sparse-history and low-games guardrail performance.
7. Run leave-one-season-out validation.
8. Run holdout-season checks.
9. Run matched-cohort checks.
10. Run outlier influence checks.
11. Review failure modes before any champion language is allowed.

## Required Metrics

- Spearman rank correlation.
- MAE/RMSE where rank or finish is predicted.
- Top-12, Top-24, Top-36 hit rates where relevant.
- Startable precision for the NWR lineup format.
- Low-games miss deltas.
- Sparse-history miss deltas.
- Prior-production decline false positives.
- Breakout miss rates.
- Position-level coverage and missingness.

## Promotion Wall

Even a refined champion cannot change rankings. Promotion would require:

- Master HQ approval.
- Data Hygiene use-gate clearance.
- Source-gate approval.
- Historical benchmark evidence.
- App/UI label review.
- Rollback plan.
- Separate implementation lane.

## Current Status

Blocked. There is no approved tournament output to refine.
