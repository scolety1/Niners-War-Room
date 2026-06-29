# Outcome V2 Current Player Display Artifact

Date: 2026-06-29

## 1. Executive Decision

`GREEN_PARTIAL_CURRENT_DISPLAY_ARTIFACT_BUILT`

A compact, source-safe, display-only current-player Outcome V2 artifact was built.

Artifact:

`docs/hq/outcomes/outcome_v2_horizon_20260630/outcome_v2_current_player_display.csv`

This artifact does not touch Rankings, app-facing Outcome columns, Dynasty Rank, tiers, model logic, hidden sort, trade value, pick value, `latest_candidate`, or `latest_approved`.

## 2. Inputs Used

Current board identity rows:

`C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`

Approved partial 2025 feature source pointer:

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context\latest_candidate.json`

Resolved 2025 feature source:

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context\20260621_pre_backtest_scoring_aligned_v1\player_season_stats_display_context.csv`

Current identity bridge:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\current_identity_bridge\outcome_v2_current_identity_bridge.csv`

Extended validation results:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended\outcome_v2_probability_validation_results.csv`

Extended model bucket rates:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended\outcome_v2_probability_model_bucket_rates.csv`

## 3. Artifact Shape

| Metric | Value |
| --- | ---: |
| Current board rows included | 240 |
| Rows with validated probability context | 184 |
| Rows with all probabilities as `Not enough information` | 56 |
| Rookie/prospect rows out of scope | 43 |
| Veteran/non-rookie rows missing 2025 feature coverage | 5 |
| Unsupported-position rows out of scope | 8 |
| Probability columns emitted | 34 |

The artifact has no raw passing/rushing/receiving stat columns and no Dynasty Rank, NWR Dynasty Score, market rank, ADP, DynastyProcess, CFBD, trade value, or pick value input columns.

## 4. Eligible Rows

Rows receive display probabilities only when all of these are true:

- player is on the current board
- player is QB/RB/WR/TE
- player is not a rookie/prospect
- player has an approved current-board-to-GSIS identity bridge row
- player has a 2025 regular-season feature row in the approved partial source
- the field passed Outcome V2 validation

Rows that do not satisfy those gates show `Not enough information`.

## 5. Missing Feature Rows

These veteran/non-rookie rows have approved identity bridge rows but no approved 2025 feature row:

| Player | Position | Team | GSIS ID |
| --- | --- | --- | --- |
| Brandon Aiyuk | WR | SF | 00-0036261 |
| Joe Mixon | RB |  | 00-0033897 |
| Tank Dell | WR | HOU | 00-0038977 |
| Jonathon Brooks | RB | CAR | 00-0039344 |
| MarShawn Lloyd | RB | GB | 00-0039811 |

These rows remain `missing_current_feature_coverage` and all probabilities are `Not enough information`.

## 6. Fields Included

Included display probability columns:

- `QB T6 This Year`
- `QB T12 This Year`
- `QB T6 Next Year`
- `QB T12 Next Year`
- `QB T6 Within 5Y`
- `QB T12 Within 5Y`
- `RB T6 This Year`
- `RB T12 This Year`
- `RB T24 This Year`
- `RB T36 This Year`
- `RB T6 Next Year`
- `RB T12 Next Year`
- `RB T24 Next Year`
- `RB T36 Next Year`
- `RB T24 Within 5Y`
- `RB T36 Within 5Y`
- `WR T6 This Year`
- `WR T12 This Year`
- `WR T24 This Year`
- `WR T36 This Year`
- `WR T6 Next Year`
- `WR T12 Next Year`
- `WR T24 Next Year`
- `WR T36 Next Year`
- `WR T6 Within 5Y`
- `WR T12 Within 5Y`
- `WR T24 Within 5Y`
- `WR T36 Within 5Y`
- `TE T6 This Year`
- `TE T12 This Year`
- `TE T6 Next Year`
- `TE T12 Next Year`
- `TE T6 Within 5Y`
- `TE T12 Within 5Y`

## 7. Fields Blocked

Blocked fields not emitted as probability columns:

- `RB_T6_WITHIN_5Y`
- `RB_T12_WITHIN_5Y`

Reason: weak calibration in extended validation.

## 8. Scoring / As-Of Status

Current-board context:

- as-of context: `2026-pre-draft`
- `This Year`: 2026 NFL season
- `Next Year`: 2027 NFL season
- `Within 5Y`: at least once from 2026 through 2030

Feature source:

- 2025 regular-season factual stats
- first-down-aware production fields are present
- `sack_fumbles_lost` is missing

Artifact scoring status for feature-covered rows:

`partial_exact_first_down_scoring_missing_sack_fumbles_lost`

## 9. Availability Caveat

The approved partial 2025 feature source does not include `games`.

Artifact availability status for feature-covered rows:

`partial_availability_context_missing_games`

The caveat explicitly says availability is not clean health. Missing availability is not treated as healthy, zero, false, or a miss.

## 10. Guardrails

The artifact is display-only and review-only.

Every row carries:

- `display_only=true`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`
- `market_used_as_input=false`
- `dynastyprocess_used_as_input=false`
- `adp_used_as_input=false`
- `cfbd_used_as_input=false`

Not allowed from this artifact:

- Dynasty Rank changes
- tier changes
- Final Board Rank changes
- Candidate Rank changes
- hidden sort
- model/rank/source-truth promotion
- model training
- app-facing Outcome V2 columns
- Rankings integration
- draft recommendation
- final draft decision
- trade value
- pick value
- Rookie Outcome probabilities
- CFBD inputs
- market/ADP/DynastyProcess inputs
- vendor/Gmail/projection inputs
- injury-risk or medical projection inputs
- `latest_candidate` mutation
- `latest_approved` creation or mutation

## 11. Validation Summary

Focused display-artifact tests passed.

Artifact audit checks confirmed:

- 240 rows
- 34 validated probability columns
- no `RB T6 Within 5Y` or `RB T12 Within 5Y` probability columns
- 56 rows with all probabilities as `Not enough information`
- 0 missing rows with probability values of `0%` or `false`
- no raw stat columns in the committed artifact
- no generated shared-data CSVs committed

## 12. Next Step

Rankings integration can proceed in a separate task only if the integration keeps Outcome V2 inside the Outcome Lens, keeps Clean Board clean, keeps default sort as Dynasty Rank, and preserves `Not enough information` for missing, blocked, rookie/prospect, and unsupported rows.
