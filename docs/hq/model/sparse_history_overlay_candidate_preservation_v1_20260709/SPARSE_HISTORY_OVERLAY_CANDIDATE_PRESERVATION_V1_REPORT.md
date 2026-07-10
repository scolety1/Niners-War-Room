# Sparse-History Overlay Candidate Preservation V1

## Verdict

`GREEN_SPARSE_HISTORY_OVERLAY_CANDIDATE_PRESERVED`

## Scope

This is a review-only preservation lane. It did not run new rules, run new formulas, tune thresholds, change production rankings, change app/runtime/model behavior, promote sources, push/merge, write to canonical `local_exports`, run review-only ranking simulation, approve production/model-use, or create hidden sort/recommendation logic.

Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`.

Prior readiness gate commit verified: `f1cdceb3a596ed8617287e68a81db710110b56cf`.

## Preserved Overlay Candidates

Primary review-only overlay candidate:

- `REFINE_005_A_EARLY_ROLE_015`

Secondary review-only overlay candidates:

- `REFINE_005_B_EARLY_ROLE_025`
- `REFINE_005_C_YEAR2_YEAR3_ONLY_025`
- `REFINE_006_A_DRAFT_ROLE_025`

Primary evidence preserved:

- `REFINE_005_A_EARLY_ROLE_015` was the best net miss-reduction refined variant.
- Net miss reduction: `16`.
- Misses resolved: `25`.
- New misses created: `9`.
- False-negative reduction: `8`.
- Production/model-use remains blocked.
- Review-only ranking simulation remains not justified.

## Harmful Variants Blocked

- `DIAG_008_B_WR_TE_POSITION_PROFILE_025`
- `REFINE_002_C_LOW_PYF_STARTER_050`
- `REFINE_011_D_COMPOSITE_LOW_PYF_050`

These variants should not advance because they showed unstable churn, severe false-positive spikes, Spearman decline, or excessive collateral damage.

## Future-Use Policy

The preserved overlay candidates may only be used for review-only analysis, future readiness-gate work, future miss-taxonomy comparison, and future overlay simulation only if explicitly authorized.

They may not be used for production ranking scores, model-use, app/runtime behavior, hidden sort, recommendation logic, player ranking integration, source promotion, canonical `local_exports` mutation, push, or merge.

## Decision

Review-only ranking simulation remains not justified.

Recommended next lane:

`Sparse-History Overlay Candidate Canonicalization Addendum V1`
