# Build Sprint 5N: Broader Historical Rebuild

Date: 2026-06-11

Verdict: `BROADER_HISTORICAL_TRAINING_ROWS_READY`

Sprint 5N rebuilt broader historical `all_player_pre_week1` feature snapshots and linked mature labels for rows marked `ready_for_5n` in Sprint 5M. It did not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, or modify active app/ranking logic.

## Scope

Supported row family:

- `all_player_pre_week1`

Target seasons:

- 2023
- 2024

Not built:

- `offseason_carryover`
- `rookie_post_draft`
- pre-draft rows
- in-season rows

## Sources

Primary broader source:

- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`

Identity/DOB source:

- `local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads/dynastyprocess_db_playerids.csv`

Truth-set v3 production season rows remain comparison/enriched-context only and did not restrict the universe.

`player_stats.csv` contains fields that remain quarantined and unused for labels/features:

- `fantasy_points`
- `fantasy_points_ppr`
- `passing_epa`
- `rushing_epa`
- `receiving_epa`
- `pacr`
- `racr`
- `dakota`
- `wopr`

No public ranking, ADP, projection, market, trade, prior fantasy draft history, or legacy `private_score` inputs were used.

## Feature Policy Applied

Sprint 5N used the approved historical availability policy:

- completed prior-season factual stat components use derived availability date `Y-02-15`
- pre-week cutoff is `Y-09-01`
- only seasons completed before the target season are feature sources
- same-season final stats are labels only and never preseason features
- label supplement sources remain blocked from prediction-time features

## Snapshot Results

| Target season | Ready rows attempted | Feature snapshots emitted | Trainable rows | Blocked rows |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 412 | 412 | 412 | 134 |
| 2024 | 415 | 415 | 415 | 147 |

Totals:

- broader snapshots emitted: 827
- trainable rows: 827
- blocked rows preserved: 281
- duplicate row IDs: 0
- invalid emitted candidates: 0

Blocked reasons:

| Reason | 2023 | 2024 | Total |
| --- | ---: | ---: | ---: |
| `blocked_missing_prior_source` | 133 | 144 | 277 |
| `no_offensive_activity` | 1 | 3 | 4 |

## Feature Families Emitted

Each emitted snapshot includes:

- `age_at_snapshot`
- `position`
- `experience_at_snapshot`
- `prior_nwr_finish_rank`
- `prior_nwr_ppg`
- `prior_games_played`
- `prior_rushing_first_downs`
- `prior_receiving_first_downs`
- `prior_receptions`
- `prior_rushing_yards`
- `prior_receiving_yards`
- `prior_passing_yards`

Feature missingness:

- 2023: 0 missing across emitted features
- 2024: 0 missing across emitted features

## Outcome Support

Aggregate support:

| Outcome | 2023 events / non-events | 2024 events / non-events | Status |
| --- | ---: | ---: | --- |
| `same_year_difference_maker` | 29 / 383 | 27 / 388 | Both classes present. |
| `same_year_starter` | 59 / 353 | 58 / 357 | Both classes present. |
| `same_year_useful` | 91 / 321 | 91 / 324 | Both classes present. |
| `same_year_replacement_or_bust` | 321 / 91 | 324 / 91 | Both classes present. |
| `next_year_starter` | 49 / 270 | 0 / 0 | 2023 mature; 2024 censored/unavailable. |

Position-level support for `same_year_starter` and `same_year_useful` now has both classes for QB, RB, WR, and TE in both 2023 and 2024.

## Legality And Leakage Audit

Emitted rows passed legality checks:

- 827 valid rows
- 0 legality issues
- 0 duplicate row IDs
- source max timestamp uses derived availability `Y-02-15`, before `Y-09-01`
- no same-season final stats were used as preseason features
- no same-season labels were used as features
- no forbidden public/market/rank/projection fields were used
- no label supplement sources were used as prediction features
- snapshot hashes are deterministic through the existing snapshot service

## Local Exports

Sprint 5N wrote local-only outputs under:

`local_exports/outcome_probability/sprint_5n_broader_historical_rebuild/`

Files:

- `broader_historical_prediction_snapshots.csv`
- `broader_historical_feature_snapshots.csv`
- `broader_historical_snapshot_legality_audit.csv`
- `broader_historical_label_linkage.csv`
- `broader_historical_trainability_report.csv`
- `broader_historical_outcome_support.csv`
- `broader_historical_position_support.csv`
- `broader_historical_feature_missingness.csv`
- `blocked_broader_historical_rows.csv`
- `README_SPRINT_5N.md`

## Readiness

Internal modeling feasibility can now be reassessed with aggregate/toy diagnostics because broader historical training rows exist and same-year outcomes have both classes.

Production/app modeling remains blocked until model validation, out-of-time testing, confidence/display gates, and final leakage audits pass. The 2024 `next_year_starter` window remains censored.
