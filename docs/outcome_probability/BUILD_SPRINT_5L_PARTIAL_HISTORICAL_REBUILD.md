# Build Sprint 5L: Partial Historical Rebuild

Date: 2026-06-11

Verdict: `PARTIAL_HISTORICAL_ROWS_READY_LABELS_ONE_CLASS`

Sprint 5L partially rebuilt historical `all_player_pre_week1` feature snapshots using the Sprint 5K historical availability policy. It did not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, or modify active app/ranking logic.

## Scope

Supported row family:

- `all_player_pre_week1`

Target seasons rebuilt:

- 2023
- 2024

Not emitted:

- 2022 rows still blocked by missing prior completed-season source
- `offseason_carryover`
- `rookie_post_draft`
- pre-draft rows
- in-season rows

## Policy Applied

Sprint 5L used `completed_prior_season_stats_available_feb15_v1` from Sprint 5K:

- completed prior-season factual NWR stat components for season `Y-1` may use derived availability date `Y-02-15`
- only seasons completed before the target season may be used as features
- same-season final stats remain forbidden as preseason features
- label supplement sources remain label-only
- rankings, projections, ADP, market/trade values, prior draft history, RotoWire ranks/projections/outlooks/values, and legacy `private_score` remain blocked

## Rebuild Results

| Target season | Eligible rows attempted | Feature snapshots emitted | Trainable rows | Still blocked |
| --- | ---: | ---: | ---: | ---: |
| 2022 | 0 | 0 | 0 | 20 |
| 2023 | 20 | 20 | 20 | 8 |
| 2024 | 28 | 28 | 28 | 7 |

Totals:

- eligible rows attempted: 48
- historical feature snapshots emitted: 48
- trainable rows: 48
- still blocked rows: 35
- legality issues in emitted rows: 0

## Still-Blocked Rows

All 35 still-blocked rows are `still_blocked_missing_prior_source`.

| Target season | Still blocked count | Reason |
| --- | ---: | --- |
| 2022 | 20 | No 2021 prior completed-season source rows exist locally. |
| 2023 | 8 | Player lacks a 2022 prior completed-season source row in the truth-set universe. |
| 2024 | 7 | Player lacks a 2023 prior completed-season source row in the truth-set universe. |

The derived availability policy cannot invent missing prior-season data.

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

- 2023: 20/20 coverage for every emitted feature
- 2024: 28/28 coverage for every emitted feature

Missing optional fields were preserved where applicable; no zero-filling was used to create false evidence.

## Label Linkage

Same-year labels linked for all 48 emitted rows:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

`next_year_starter` linked only where mature and uncensored:

- 2023 rows: 20 observed
- 2024 rows: censored/unavailable

## Outcome Support

Aggregate support for trainable rows:

| Outcome | 2023 events / non-events | 2024 events / non-events | Readiness note |
| --- | ---: | ---: | --- |
| `same_year_difference_maker` | 19 / 1 | 22 / 6 | Has both classes overall, but support is sparse. |
| `same_year_starter` | 20 / 0 | 28 / 0 | One-class saturated. |
| `same_year_useful` | 20 / 0 | 28 / 0 | One-class saturated. |
| `same_year_replacement_or_bust` | 0 / 20 | 0 / 28 | One-class in the opposite direction. |
| `next_year_starter` | 20 / 0 | 0 / 0 | 2023 observed but one-class; 2024 censored. |

Every position-level slice is sparse. Many position/outcome slices are one-class.

## Legality And Leakage Audit

Emitted rows passed legality checks:

- source availability timestamp `Y-02-15` is before pre-week cutoff `Y-09-01`
- no same-season final stats were used as preseason features
- no same-season target labels were used as features
- no forbidden ranking, projection, market, trade, ADP, prior draft, or legacy private score fields were used
- label supplement sources were not used as prediction features
- row IDs and snapshot hashes are deterministic through the existing feature snapshot service

## Local Exports

Sprint 5L wrote local-only outputs under:

`local_exports/outcome_probability/sprint_5l_partial_historical_rebuild/`

Files:

- `historical_prediction_snapshots.csv`
- `historical_feature_snapshots.csv`
- `historical_snapshot_legality_audit.csv`
- `historical_label_linkage.csv`
- `historical_trainability_report.csv`
- `historical_outcome_support.csv`
- `historical_feature_missingness.csv`
- `still_blocked_historical_rows.csv`
- `README_SPRINT_5L.md`

## Modeling Readiness

Internal modeling feasibility can be reassessed for aggregate/toy diagnostics, but true calibrated modeling remains blocked.

Reasons:

- only 48 trainable rows
- many outcomes are one-class
- all position slices are sparse
- 2024 next-year labels are censored
- truth-set universe remains narrow/enriched
- production/app display gates and final leakage audit are still required

Production/app modeling remains blocked.
