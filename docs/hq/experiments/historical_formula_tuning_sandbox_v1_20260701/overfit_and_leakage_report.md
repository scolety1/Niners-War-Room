# Overfit And Leakage Report

Verdict: `YELLOW_NO_TUNING_READY_CANDIDATE`

## Leakage Checks

- No market, ADP, vendor ranking, projection, current roster/status/injury/depth/schedule, route, TPRR, YPRR, or ambiguous `rz_att` fields are used.
- Candidate features are prior-season factual Backtest V1 fields.
- Candidate calibration uses only prior target seasons for each evaluated season.
- Holdout year `2025` was not used to choose weights.
- Missing values were not converted to zero by this generator. Null candidate scores are excluded from the affected variant.

## Overfit Review

The best validation candidate by aggregate MAE was `prior_ppg_times_games_sqrt`. It improved validation MAE but did not preserve all holdout rank and Top-N metrics.

No candidate passed validation and holdout gates across MAE, Spearman, and Top-N hit rate. This invalidates any tuning-ready claim.
