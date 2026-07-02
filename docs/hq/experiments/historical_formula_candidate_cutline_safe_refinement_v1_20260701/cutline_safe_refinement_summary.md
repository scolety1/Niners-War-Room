# Historical Formula Candidate Cutline-Safe Refinement V1

Verdict: `YELLOW_CUTLINE_SAFE_REFINEMENT_PARTIAL_HOLD_REVIEW_ONLY`

Decision label: `PARTIAL_REFINEMENT_STILL_HOLD`

Selected partial refinement: `rb_wr_cutline_safe_blend`

This lane tested only fixed, interpretable cutline-safe variants of the existing `usage_opportunity_volume` candidate. It did not run unbounded search, train a model, change production formulas, approve shadow review, or wire output into NWR.

## Key Evidence

- Original validation MAE delta: `-2.036621`
- Original holdout MAE delta: `-1.646492`
- `qb_guard_soft_blend` validation MAE delta: `-1.820472`
- `qb_guard_soft_blend` holdout MAE delta: `-1.641657`
- `rb_wr_cutline_safe_blend` validation MAE delta: `-1.435764`
- `rb_wr_cutline_safe_blend` holdout MAE delta: `-1.18892`
- `rb_wr_cutline_safe_blend` holdout Spearman delta: `0.001057`
- `rb_wr_cutline_safe_blend` validation/holdout startable precision delta: `-0.005952` / `-0.005953`
- Actual cutline hits moved below cutline: original `8`, `qb_guard_soft_blend` `8`, selected partial `5`
- Elite-QB severe regressions: original `14`, `qb_guard_soft_blend` `1`, selected partial `1`

Conclusion: the selected partial refinement improves cutline safety toward the preferred target and keeps elite-QB regressions low, but it introduces a small startable-precision regression and weaker holdout MAE than `qb_guard_soft_blend`. The candidate remains HOLD.
