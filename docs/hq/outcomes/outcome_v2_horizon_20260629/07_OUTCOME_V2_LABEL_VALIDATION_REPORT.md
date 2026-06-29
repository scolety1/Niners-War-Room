# Outcome V2 Historical Label Validation Report

Date: 2026-06-29

## Verdict

`GREEN_REVIEW_ONLY_VALIDATION_PASS`

The review-only historical Outcome V2 label factory built factual season labels and anchor horizon labels from existing local NFL usage target/backtest artifacts. The generated labels preserve censoring and do not convert missing future information into misses.

This validation does not approve current-player probability modeling, calibration, app display, Rankings wiring, or model input promotion.

## Source Validation

All required source files existed and were readable:

| Source | Rows |
| --- | ---: |
| `player_season_core_usage_panel.csv` | 3,701 |
| `player_week_core_usage_panel.csv` | 35,311 |
| `nfl_usage_expanded_target_labels_v0.csv` | 3,578 |
| `nfl_usage_expanded_target_backtest_joined_panel_v0.csv` | 2,848 |

Required keys were present:

- `player_id`
- `season` / `target_season`
- `position`
- player name
- team context

Blocked-source scan: `pass`.

## Output Validation

| Artifact | Rows | SHA256 |
| --- | ---: | --- |
| `outcome_v2_season_outcome_labels.csv` | 3,578 | `5baa0e11273ef7aa7ca374a7bf342434ab272a855bb628a826db89b3d128a1ef` |
| `outcome_v2_anchor_horizon_labels.csv` | 3,569 | `a8ab98e28175de6092f0179710e52f50012c2663898b2e3e401cde9ee5df5d14` |
| `outcome_v2_historical_label_validation_summary.csv` | 83 | `e4bbb12d90b60909e3fe0ef57e47428753b8f28ad8221da8bd2cff5bb701ddde` |

Generated output folder:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels\`

These generated CSVs are local review-only artifacts and must remain untracked.

## Threshold Validation

Position threshold map:

- QB: T6, T12
- RB: T6, T12, T24, T36
- WR: T6, T12, T24, T36
- TE: T6, T12

Non-applicable thresholds are emitted as `not_applicable`, not `0`.

Season hit counts:

| Position | T6 | T12 | T24 | T36 |
| --- | ---: | ---: | ---: | ---: |
| QB | 36 / 476 | 72 / 476 | not applicable | not applicable |
| RB | 36 / 921 | 72 / 921 | 144 / 921 | 217 / 921 |
| WR | 36 / 1,413 | 72 / 1,413 | 144 / 1,413 | 216 / 1,413 |
| TE | 36 / 768 | 72 / 768 | not applicable | not applicable |

## Horizon Validation

Horizon definitions were implemented as:

- `this_year_*` = A+1
- `next_year_*` = A+2
- `within_5y_*` = any hit from A+1 through A+5

Window counts:

- Complete this-year windows: 2,658
- Complete next-year windows: 1,838
- Complete within-five-year windows: 296
- Right-censored rows: 3,273
- Missing-target-data rows: 1,855

Incomplete windows use `Not enough information` for applicable threshold fields. Missing target rows are not treated as `miss`, `0`, or `0%`.

## Scoring Validation

Scoring mode:

- `exact_verified_first_downs`: 3,578

The service was tested against the existing `nfl_usage_target_label_service` scoring expectations. The scoring path includes:

- passing yards
- passing TD
- interception
- rushing yards
- rushing TD
- receiving yards
- receiving TD
- rushing first downs
- receiving first downs
- return yards
- return TD
- two-point conversions
- fumbles lost

No PPR points are added. No generic imported fantasy point field is used as label truth.

## Availability Validation

Availability context is factual and limited to games/usage coverage:

- `available_14_plus_games`: 1,176
- `partial_availability_9_to_13_games`: 872
- `limited_availability_5_to_8_games`: 656
- `limited_availability_1_to_4_games`: 874

No injury-risk score, medical projection, comeback assumption, scraped injury feed, vendor injury data, or manual rumor was used.

## Rookie / Prospect Handling

The generated rows come from NFL factual player-season target labels for QB/RB/WR/TE. College-only rookies/prospects and CFBD-only rows are not used. Future unmatched rookie/prospect rows should be marked `out_of_scope_rookie_or_prospect`, not backfilled from college data, ADP, draft capital, market data, or scouting notes.

## Guardrail Validation

The factory keeps these gates closed:

- `model_input_allowed=no`
- `training_allowed=no`
- `app_wiring_allowed=no`
- no current-player probabilities
- no model training
- no Rankings wiring
- no app-facing Outcome V2 columns
- no latest_candidate update
- no latest_approved update
- no frozen board mutation
- no hidden sort fields
- no market/ADP/DynastyProcess/CFBD/vendor/projection inputs
- no raw shared-cache artifacts committed

## Remaining Gates

Before any next step toward Outcome V2 probability validation/calibration:

1. Review whether the conservative missing-target policy is acceptable, especially retired or absent future-season rows.
2. Decide whether older factual player_stats seasons are needed to expand complete five-year windows.
3. Add calibration/Brier/monotonicity validation only after a separate explicit approval.
4. Keep all current-player probability, model, app, and Rankings work blocked until that approval exists.
