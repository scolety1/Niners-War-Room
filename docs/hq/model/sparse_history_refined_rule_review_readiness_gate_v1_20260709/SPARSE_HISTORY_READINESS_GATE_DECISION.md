# Sparse-History Readiness Gate Decision

Readiness status: `READY_FOR_REVIEW_ONLY_OVERLAY_CANDIDATE_PRESERVATION`.

Decision: advance a small set of refined sparse-history rules as review-only overlay candidates for preservation.

Primary candidate:

- `REFINE_005_A_EARLY_ROLE_015`

Secondary candidates:

- `REFINE_005_B_EARLY_ROLE_025`
- `REFINE_005_C_YEAR2_YEAR3_ONLY_025`
- `REFINE_006_A_DRAFT_ROLE_025`

Do not advance harmful variants:

- `DIAG_008_B_WR_TE_POSITION_PROFILE_025`
- `REFINE_002_C_LOW_PYF_STARTER_050`
- `REFINE_011_D_COMPOSITE_LOW_PYF_050`

Rationale:

- At least one full-history variant reached net miss reduction `>= 16`.
- Resolved misses exceeded new misses by a meaningful margin for the preferred candidate.
- False-negative reduction was positive.
- No severe false-positive spike was present for pass-all candidates.
- Spearman did not materially decline.
- The preferred rule is simple enough to preserve as a review-only overlay candidate.
- Production/model-use and rankings integration remain blocked.
