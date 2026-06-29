# Outcome V2 Historical Label Factory

Date: 2026-06-29

## Status

`GREEN_REVIEW_ONLY_LABEL_FACTORY_BUILT`

The Outcome V2 lane now has a review-only historical label factory. It builds factual historical outcome labels from already-local NFL usage target/backtest artifacts. It does not create current-player probabilities, does not train a model, does not wire Rankings, and does not create app-facing Outcome V2 columns.

## Files Added

- `src/services/outcome_v2_historical_label_factory.py`
- `scripts/build_outcome_v2_historical_labels.py`
- `tests/test_outcome_v2_historical_label_factory.py`

## Source Inputs

The factory reads only approved review-only local NFL usage cache files:

- `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\panels\player_season_core_usage_panel.csv`
- `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\panels\player_week_core_usage_panel.csv`
- `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\nfl_usage_expanded_target_labels_v0.csv`
- `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\nfl_usage_expanded_target_backtest_joined_panel_v0.csv`

The service uses the existing NWR/LVE scoring semantics from `src/services/nfl_usage_target_label_service.py` through the existing target-label outputs. Generic imported fantasy point fields, market/ADP, DynastyProcess, CFBD, vendor projections, analyst ranks, trade values, true routes, TPRR, YPRR, lane-exchange display candidates, and injury projections are not used.

## Generated Review-Only Outputs

Generated artifacts are written to ignored shared data and must not be committed:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels\`

Files:

- `outcome_v2_season_outcome_labels.csv`
- `outcome_v2_anchor_horizon_labels.csv`
- `outcome_v2_historical_label_manifest.csv`
- `outcome_v2_historical_label_validation_summary.csv`

## Layer 1: Factual Season Outcome Labels

Rows: 3,578.

Season coverage: 2019-2024.

Positions:

- QB: 476 rows
- RB: 921 rows
- WR: 1,413 rows
- TE: 768 rows

Fields include:

- `player_id`
- `player_name`
- `position`
- `season`
- `team`
- `scoring_mode`
- `fantasy_points`
- `position_finish`
- `games_played`
- `availability_context`
- `top_6_hit`
- `top_12_hit`
- `top_24_hit`
- `top_36_hit`
- `data_quality_status`

Threshold values are text labels, not hidden numeric sort fields:

- `hit`
- `miss`
- `not_applicable`
- `Not enough information`

For thresholds outside a position's map, the output uses `not_applicable`, not `0`.

## Layer 2: Anchor Horizon Labels

Rows: 3,569.

Anchor season coverage: 2018-2023.

The horizon semantics are locked as:

- `this_year_*`: season A+1
- `next_year_*`: season A+2
- `within_5y_*`: at least one hit in seasons A+1 through A+5

Incomplete or missing windows are marked as `Not enough information` and censored. They are not treated as misses.

Window completeness:

- Complete this-year windows: 2,658
- Complete next-year windows: 1,838
- Complete within-five-year windows: 296
- Right-censored rows: 3,273
- Missing-target-data rows: 1,855

## Scoring

Scoring mode count:

- `exact_verified_first_downs`: 3,578 rows

The source path has verified rushing and receiving first-down fields. Passing first downs are not used for scoring because the league rules award first-down points only for rushing and receiving first downs.

## Availability

Availability context is factual only:

- `available_14_plus_games`: 1,176
- `partial_availability_9_to_13_games`: 872
- `limited_availability_5_to_8_games`: 656
- `limited_availability_1_to_4_games`: 874

The factory does not infer medical cause, injury risk, recovery, or future availability.

## Guardrails

All generated artifacts are marked:

- `approval_status=review_only_historical_labels`
- `model_input_allowed=no`
- `training_allowed=no`
- `app_wiring_allowed=no`

This is ready for review-only historical validation work. It is not yet approved for Outcome V2 current-player probability calibration, model training, Rankings display, app wiring, or any draft-day decision surface.
