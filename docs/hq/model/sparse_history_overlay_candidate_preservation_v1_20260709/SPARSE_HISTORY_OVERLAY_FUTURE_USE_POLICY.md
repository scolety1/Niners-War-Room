# Sparse-History Overlay Future Use Policy

The preserved sparse-history overlay candidates may only be used for:

- review-only analysis
- future readiness-gate work
- future miss-taxonomy comparison
- future overlay simulation only if explicitly authorized

The preserved sparse-history overlay candidates may not be used for:

- production ranking scores
- model-use
- app/runtime behavior
- hidden sort
- recommendation logic
- player ranking integration
- source promotion
- canonical `local_exports` mutation
- push/merge

Input and leakage policy:

- Same-season and future leakage remain blocked.
- Current-only ADP remains blocked for historical use.
- SportsDataIO, paid/API/free-trial/API-key work, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain blocked.
- CFBD/prospect data remains blocked as model input unless separately source-gated and identity-gated.
- UDFA truth must not be inferred without source evidence.
- Draft-capital variants may only be reviewed where source and identity gates are satisfied.

Preservation status:

- `REFINE_005_A_EARLY_ROLE_015`: primary review-only overlay candidate.
- `REFINE_005_B_EARLY_ROLE_025`: secondary review-only overlay candidate with churn caution.
- `REFINE_005_C_YEAR2_YEAR3_ONLY_025`: secondary narrow early-career overlay candidate.
- `REFINE_006_A_DRAFT_ROLE_025`: secondary draft-role overlay candidate with draft source/identity caveat.
