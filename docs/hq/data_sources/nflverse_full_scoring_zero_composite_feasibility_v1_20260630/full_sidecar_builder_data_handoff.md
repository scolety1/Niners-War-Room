# Full Sidecar Builder Data Handoff

## Verdict

`YELLOW_ZERO_COMPOSITE_FEASIBILITY_PARTIAL_BLOCKERS`

## What A Future Builder May Do

A future review-only full sidecar builder may:

- read the admitted local-only `player_stats_weekly` source through an approved non-runtime runner;
- validate SHA and row counts before deriving;
- emit observed player-week component rows;
- emit explicit zero component rows for observed rows with numeric zero values;
- derive `fumbles_lost` as `rushing_fumbles_lost + receiving_fumbles_lost + sack_fumbles_lost`;
- derive `return_yards` as `kickoff_return_yards + punt_return_yards`;
- keep every row `label_truth_allowed=false`, `model_use_allowed=false`, `training_allowed=false`, and `source_truth_allowed=false`.

## What A Future Builder Must Keep Blocked

- Missing player-week source rows.
- Identity-review rows.
- `return_touchdowns` and `special_touchdowns` until `special_teams_tds` mapping is approved.
- Any quarantined field.
- Any app behavior, model, training, source truth, ranking, hidden sort, probability, recommendation, trade value, or pick value use.

## Suggested Next Lane

`NFLVerse Full Scoring Component Sidecar Builder V1`

The builder should remain review-only and should clearly separate:

- full observed-row component coverage;
- missing-row censoring;
- special/return touchdown blockers;
- label truth guardrails.
