# Refinement Selection Decision

Decision label: `PARTIAL_REFINEMENT_STILL_HOLD`

Validation-only selection logic:

- The selected partial refinement had validation MAE improvement versus baseline.
- It was the fixed refinement that reduced validation cutline misses while preserving the elite-QB guard.
- Holdout was evaluated only after fixed definitions and the validation-only partial selection.

Selected partial refinement: `rb_wr_cutline_safe_blend`.

Why this is not marked `REFINED_CANDIDATE_FOR_HUMAN_REVIEW_ONLY`:

- Holdout MAE still improves versus baseline, but less than `qb_guard_soft_blend`.
- Actual cutline misses improve from `8` to `5`.
- Elite-QB severe regressions stay near the desired level at `1`.
- Startable precision regresses slightly on validation and holdout, so the full success criteria are not met.

Result: `PARTIAL_REFINEMENT_STILL_HOLD`.
