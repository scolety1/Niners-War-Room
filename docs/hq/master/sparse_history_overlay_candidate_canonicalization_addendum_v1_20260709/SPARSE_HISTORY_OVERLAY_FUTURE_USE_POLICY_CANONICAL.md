# Sparse-History Overlay Future Use Policy Canonical

Preserved review-only overlay candidates:

- `REFINE_005_A_EARLY_ROLE_015`
- `REFINE_005_B_EARLY_ROLE_025`
- `REFINE_005_C_YEAR2_YEAR3_ONLY_025`
- `REFINE_006_A_DRAFT_ROLE_025`

Allowed uses:

- review-only analysis
- future readiness gates
- miss-taxonomy comparison
- explicitly authorized future overlay simulation

Blocked uses:

- production scores
- production/model-use
- app/runtime behavior
- hidden sort
- recommendation logic
- rankings integration
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

Final preserved decision:

The overlay candidates are preserved as review-only candidates only. They are not approved model logic, ranking logic, production scoring inputs, or hidden sorting/recommendation logic.
