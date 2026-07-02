# Historical Formula Candidate Targeted Redesign V1

Verdict: `GREEN_TARGETED_REDESIGN_FOR_HUMAN_REVIEW_ONLY_REVIEW_ONLY`

Decision label: `TARGETED_REDESIGN_FOR_HUMAN_REVIEW_ONLY`

Selected redesign: `wr_boundary_breakout_sensitivity_guard`

This lane tested only fixed, interpretable, non-player-specific redesign variants for the held `usage_opportunity_volume` candidate. It did not run unbounded search, train a model, change production formulas, approve shadow review, or wire output into NWR.

## Key Evidence

- Original validation / holdout MAE delta: `-2.036621` / `-1.646492`
- `qb_guard_soft_blend` validation / holdout MAE delta: `-1.820472` / `-1.641657`
- `rb_wr_cutline_safe_blend` validation / holdout MAE delta: `-1.435764` / `-1.18892`
- `wr_boundary_breakout_sensitivity_guard` validation / holdout MAE delta: `-1.424033` / `-1.196383`
- `wr_boundary_breakout_sensitivity_guard` holdout Spearman delta: `0.001089`
- `wr_boundary_breakout_sensitivity_guard` validation / holdout startable precision delta: `0.0` / `0.0`
- Actual cutline hits moved below cutline: original `8`, `qb_guard_soft_blend` `8`, `rb_wr_cutline_safe_blend` `5`, selected redesign `2`
- Elite-QB severe regressions: original `14`, `qb_guard_soft_blend` `1`, selected redesign `1`
- Remaining 5 static-autopsy cases resolved by selected redesign: `3/5`

Conclusion: `wr_boundary_breakout_sensitivity_guard` clears the requested human-review threshold by reducing actual cutline hits from `5` to `2` while preserving a material holdout MAE gain, keeping startable precision flat versus baseline, and keeping elite-QB severe regressions low. It remains review-only and is not production-approved.
