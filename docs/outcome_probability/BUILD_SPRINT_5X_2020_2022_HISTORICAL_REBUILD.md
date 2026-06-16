# Build Sprint 5X: 2020-2022 Historical Rebuild

## Scope

Sprint 5X rebuilds additional historical `all_player_pre_week1` snapshots for 2020, 2021, and 2022 using older `player_stats.csv` seasons registered in Sprint 5W.

This sprint did not train models, run promoted model experiments, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, modify active app/ranking logic, or promote/release any model artifact.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5x_2020_2022_historical_rebuild/`

Created files:

- `historical_2020_2022_prediction_snapshots.csv`
- `historical_2020_2022_feature_snapshots.csv`
- `historical_2020_2022_label_linkage.csv`
- `historical_2020_2022_trainability_report.csv`
- `historical_2020_2022_outcome_support.csv`
- `historical_2020_2022_position_support.csv`
- `historical_2020_2022_feature_missingness.csv`
- `historical_2020_2022_legality_audit.csv`
- `expanded_2020_2024_trainable_universe_summary.csv`
- `blocked_historical_2020_2022_rows.csv`
- `README_SPRINT_5X.md`

## Rebuilt Seasons

| Target season | Cutoff | Prior source season | Derived availability | Attempted | Emitted/trainable | Blocked |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| 2020 | `2020-09-01` | 2019 | `2020-02-15` | 578 | 418 | 160 |
| 2021 | `2021-09-01` | 2020 | `2021-02-15` | 589 | 439 | 150 |
| 2022 | `2022-09-01` | 2021 | `2022-02-15` | 575 | 434 | 141 |

Total attempted rows: 1,742

Total emitted/trainable rows: 1,291

Total blocked rows: 451

All blocked rows were `blocked_missing_required_feature`, meaning the player had target-season activity but no completed prior-season feature row in the required prior source season. No rows were blocked for missing labels, identity, position, leakage risk, or no offensive activity.

## Feature Schema

Sprint 5X used the renamed Sprint 5R schema only:

- `age_at_snapshot`
- `position`
- `experience`
- `prior_season_nwr_ppg`
- `prior_season_nwr_finish_rank`
- `prior_completed_season_games`
- `prior_completed_season_games_played`
- `prior_completed_season_games_active`
- `prior_completed_season_rushing_first_downs`
- `prior_completed_season_receiving_first_downs`
- `prior_completed_season_receptions`
- `prior_completed_season_rushing_yards`
- `prior_completed_season_receiving_yards`
- `prior_completed_season_passing_yards`

The rebuild hard-blocked old ambiguous feature names and did not emit any of the old `prior_*` names replaced in Sprint 5R.

## Outcome Support

Aggregate all-position support for the rebuilt seasons:

| Outcome | 2020 | 2021 | 2022 |
| --- | ---: | ---: | ---: |
| `same_year_difference_maker` | 30 / 388 | 31 / 408 | 33 / 401 |
| `same_year_starter` | 56 / 362 | 60 / 379 | 60 / 374 |
| `same_year_useful` | 89 / 329 | 91 / 348 | 92 / 342 |
| `same_year_replacement_or_bust` | 329 / 89 | 348 / 91 | 342 / 92 |
| `next_year_starter` | 47 / 284, 87 missing/censored | 52 / 281, 106 missing/censored | 46 / 267, 121 missing/censored |

Some TE position-level difference-maker buckets remain sparse, but all same-year all-position outcomes have both classes in every rebuilt season.

## Expanded 2020-2024 Universe

Combining Sprint 5X rows with the already-approved Sprint 5N 2023/2024 rows yields:

| Season | Trainable rows |
| --- | ---: |
| 2020 | 418 |
| 2021 | 439 |
| 2022 | 434 |
| 2023 | 412 |
| 2024 | 415 |

Expanded trainable rows: 2,118

Expanded support:

- `same_year_difference_maker`: 150 events / 1,968 non-events
- `same_year_starter`: 293 / 1,825
- `same_year_useful`: 454 / 1,664
- `same_year_replacement_or_bust`: 1,664 / 454
- `next_year_starter`: 194 / 1,102 observed, 822 missing/censored

Position support across 2020-2024:

- QB: 307 rows
- RB: 538 rows
- WR: 817 rows
- TE: 456 rows

This makes a Sprint 5Y calibration-readiness reassessment appropriate. It does not approve calibration, model promotion, or app/player-facing output.

## Missingness

Emitted 2020-2022 snapshots had zero missing values across the emitted feature schema. Missing optional values were not invented; rows without required prior-season features were blocked instead of filled.

## Legality And Leakage Audit

Sprint 5X legality checks passed:

- Derived availability date was before or equal to the prediction cutoff.
- Source season was strictly before target season.
- No same-season final stats were emitted as preseason features.
- No target labels or future-window labels were emitted as features.
- No imported fantasy totals were used as labels.
- No ADP, projection, ranking, market, trade, prior fantasy draft history, legacy `private_score`, or RotoWire projection/ranking/outlook/value fields were emitted.
- No label supplement sources were used as prediction features.
- No old ambiguous feature names were emitted.
- Duplicate row IDs: 0.
- Duplicate snapshot hashes: 0.

## Verdict

`EXPANDED_HISTORICAL_ROWS_READY`

Sprint 5Y calibration-readiness reassessment can start using the expanded 2020-2024 internal historical universe, while preserving the Sprint 5S/5T/5U governance restrictions.

Production/app modeling remains blocked until later validation, calibration, confidence/display gates, final leakage audit, release policy, and explicit HQ approval.

## Confirmed Non-Actions

- No models trained.
- No promoted model experiments run.
- No app percentage values created.
- No public/player-facing probabilities created.
- No rankings created.
- No push or deploy occurred.
- No active app/ranking logic modified.
- No model artifact promoted or released.
