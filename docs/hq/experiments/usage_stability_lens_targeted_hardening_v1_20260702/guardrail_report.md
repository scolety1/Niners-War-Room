# Guardrail Report

Verdict: `GREEN_REVIEW_ONLY_GUARDRAILS_PRESERVED`

## Confirmed

- No production formula/config file changed.
- No app, model, rank, source-truth, or runtime path changed.
- No candidate output was wired into NWR.
- No broad formula search was run.
- No holdout threshold tuning was run.
- No market, ADP, vendor, projection, or rank field was used as source truth.
- No routes, TPRR, YPRR, red-zone sidecar, `rz_att`, or unsafe current-only context was used as a formula feature.
- No missing values were forced to zero.
- No raw/shared/cache/local export/secrets files were tracked.
- No player-name hard-coded formula exceptions were created.

## Approval Flags

- production_formula_approved: `false`
- model_training_approved: `false`
- rank_behavior_change_approved: `false`
- app_wiring_approved: `false`
- hidden_sort_approved: `false`
- recommendations_approved: `false`
- source_truth_promotion_approved: `false`
- candidate_output_wired: `false`
