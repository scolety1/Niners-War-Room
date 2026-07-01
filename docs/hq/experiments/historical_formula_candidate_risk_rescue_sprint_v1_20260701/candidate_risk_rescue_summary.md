# Candidate Risk Rescue Sprint V1

Verdict: `YELLOW_RISK_RESCUE_SPRINT_NO_FULL_SAFE_RESCUE_REVIEW_ONLY`

Decision label: `NO_SAFE_RESCUE_HOLD`

Candidate under review: `usage_opportunity_volume`

This sprint tested only the fixed rescue variants listed in `fixed_rescue_variant_definitions.csv`. It did not run unbounded search, train a model, optimize a production formula, or wire any output into NWR.

## Result

No full safe rescue was found.

Best partial rescue by validation evidence: `qb_guard_soft_blend`.

- Original validation MAE delta: `-2.036621`
- Best partial rescue validation MAE delta: `-1.820472`
- Original holdout MAE delta: `-1.646492`
- Best partial rescue holdout MAE delta: `-1.641657`
- Best partial rescue validation/holdout startable precision deltas: `0.0` / `0.0`
- Elite-QB severe regressions, original vs best partial rescue: `14` -> `1`
- Actual cutline hits moved below cutline, original vs best partial rescue: `8` -> `8`

Interpretation: `qb_guard_soft_blend` materially reduces elite-QB severe regressions while preserving most validation/holdout MAE improvement, but it does not reduce actual cutline hits moved below cutline. The conservative 50/50 blend reduces cutline hits to `5` and elite-QB severe regressions to `8`, but gives up more validation signal and introduces a small startable-precision watch item. The candidate should remain on HOLD.
