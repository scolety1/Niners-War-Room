# Model v4 Next Replay Benchmark Contract

## Status

`PARTIAL_REPLAY_BENCHMARK_ALLOWED_EXACT_REPLAY_BLOCKED`

## Eligible Benchmark Type

The next benchmark may be a partial historical replay benchmark using only the review-only historical component receipts created in this lane. It must not be described as exact Model v4 replay.

## Seasons

- Target seasons: `2013-2025`
- Feature seasons: `2012-2024`
- Decision rule: target season `Y` may use only completed feature season `Y-1` factual inputs.

## Positions

- QB
- RB
- WR
- TE

## Eligible Universe

Only rows present in `MODEL_V4_HISTORICAL_COMPONENT_RECEIPTS.csv` and the existing partial replay input panel are eligible. Rookie/no-prior-season rows are not complete in this substrate.

## Allowed Components

Allowed as partial proxy receipts only:

- `air_yard_role`
- `first_down_high_value`
- `first_down_yardage`
- `imported_first_down_points`
- `imported_receiving_first_downs`
- `imported_rushing_first_downs`
- `passing_production`
- `passing_volume_security`
- `receiving_utility`
- `review_scoring_points`
- `role_volume`
- `route_target_role`
- `rushing_separation`
- `target_route_role`
- `vorp_anchor`

## Blocked Components

Blocked for exact replay:

- `nwr_dynasty_score`
- `nwr_rank`
- `checkpoint_review_score`
- `position_specific_review_score`
- `positive_vorp_points`
- `return_scoring_points`
- `lifecycle_modifier_review`
- `confidence_cap`
- `discipline_multiplier`
- `wr_qb_v2_candidate_adjustment`
- `candidate_reason_codes`
- `candidate_evidence_fields_used`
- `old_pocket_qb_horizon_cap`
- exact route/YPRR/TPRR/red-zone normalized components where true denominators are absent

## Labels

Use held-out target-season labels only:

- `next_nwr_points`
- `next_nwr_ppg`
- `next_position_finish`
- `startable_hit`
- `startable_bucket`

## Metrics

Report at minimum:

- MAE
- RMSE
- Spearman
- Top-12 / Top-24 / Top-36 hit rates where position-applicable
- Startable precision and recall
- Coverage by season and position
- Baseline comparisons against prior-year finish and current-formula-family proxy

## Leakage Checks

- Confirm every feature row uses `feature_season = target_season - 1`.
- Confirm every receipt remains `review_only` and `partial_replay_proxy_only`.
- Confirm no current roster, injury, market, ADP, projection, ranking, target-season, or current-board artifact field is used as a historical input.
- Confirm missing/null-fenced source columns are not imputed as exact zero unless source semantics separately prove explicit zero.

## Caveats

- This benchmark cannot claim production accuracy.
- This benchmark cannot promote sources.
- This benchmark cannot tune or activate production rankings.
- Exact Model v4 replay remains blocked until exact historical component receipts exist.
