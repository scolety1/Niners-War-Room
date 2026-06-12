# Build Sprint 5J: Historical Mature Snapshots

Date: 2026-06-11

Verdict: `BLOCKED_BY_HISTORICAL_SOURCE_TIMESTAMPS`

Sprint 5J attempted to reconstruct historical `all_player_pre_week1` feature snapshots for seasons with mature observed labels. It did not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, or modify active app/ranking logic.

## Scope

Target seasons:

- 2022
- 2023
- 2024

Supported row family:

- `all_player_pre_week1`

Not built in this sprint:

- `offseason_carryover`
- `rookie_post_draft`
- pre-draft rows
- in-season rows

## Source Inspection

The available local truth-set season source is:

`local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_season.csv`

Rows by season:

| Season | Rows |
| --- | ---: |
| 2022 | 20 |
| 2023 | 28 |
| 2024 | 35 |

All rows carry `source_date=2026-05-15`.

For historical `all_player_pre_week1` snapshots, the cutoff is `YYYY-09-01`. A feature source dated `2026-05-15` is after all target cutoffs:

- `2022-09-01`
- `2023-09-01`
- `2024-09-01`

The local data can provide mature label context, but it cannot legally provide point-in-time historical preseason features without an earlier source snapshot or approved source availability manifest.

## Reconstruction Results

| Target season | Attempted target rows | Legal feature snapshots emitted | Trainable rows | Primary blocker |
| --- | ---: | ---: | ---: | --- |
| 2022 | 20 | 0 | 0 | No completed prior-season truth-set feature source exists locally. |
| 2023 | 28 | 0 | 0 | Some rows lack prior-season features; remaining prior-season rows have post-cutoff source timestamps. |
| 2024 | 35 | 0 | 0 | Some rows lack prior-season features; remaining prior-season rows have post-cutoff source timestamps. |

Total attempted rows: 83.

Legal historical feature snapshots emitted: 0.

Trainable rows: 0.

## Blocked Row Reasons

| Blocker | Count | Meaning |
| --- | ---: | --- |
| `missing_prior_completed_season_feature_source` | 35 | No completed prior season exists in the local truth-set for that player before the target cutoff. |
| `post_cutoff_source_timestamp` | 48 | Prior-season values exist, but the source timestamp is after the historical preseason cutoff. |

Rows with post-cutoff historical sources were classified as `blocked_leakage_risk`. Rows with no prior source were classified as `blocked_missing_required_feature`.

## Label Linkage

Same-year labels can be reconstructed as audit context from observed truth-set season rows, and next-year starter context exists for some 2022 and 2023 rows. Those labels were not linked into trainable rows because there are no legal point-in-time historical feature snapshots.

Outcome support for trainable rows:

| Outcome | Trainable rows | Events | Non-events |
| --- | ---: | ---: | ---: |
| `same_year_difference_maker` | 0 | 0 | 0 |
| `same_year_starter` | 0 | 0 | 0 |
| `same_year_useful` | 0 | 0 | 0 |
| `same_year_replacement_or_bust` | 0 | 0 | 0 |
| `next_year_starter` | 0 | 0 | 0 |

The local outputs include observed-label counts as context only, clearly separated from trainable support.

## Feature Missingness

No feature rows were emitted, so model-ready feature missingness cannot be assessed. The export records attempted feature families and their blockers:

- age/DOB metadata
- experience entering season
- prior games played
- prior first-down production
- prior receptions
- prior rushing/receiving/passing yards

Missing optional fields were not zero-filled. Blocked rows were not materialized as legal feature snapshots.

## Local Exports

Sprint 5J wrote local-only outputs under:

`local_exports/outcome_probability/sprint_5j_historical_mature_snapshots/`

Files:

- `historical_prediction_snapshots.csv`
- `historical_feature_snapshots.csv`
- `historical_snapshot_legality_audit.csv`
- `historical_label_linkage.csv`
- `historical_trainability_report.csv`
- `historical_outcome_support.csv`
- `historical_feature_missingness.csv`
- `README_SPRINT_5J.md`

## Readiness

Readiness verdict: `BLOCKED_BY_HISTORICAL_SOURCE_TIMESTAMPS`

Internal modeling feasibility cannot be reassessed from these historical rows yet because there are zero legal emitted feature snapshots and zero trainable rows.

Production/app modeling remains blocked.

## Required Repair Path

Before a future training-row audit can find trainable rows, NWR needs one of:

- historical point-in-time feature snapshots available on or before each `YYYY-09-01` cutoff,
- approved source availability manifests proving prior-season feature values were available by each cutoff, or
- a narrower historical source that carries valid as-of dates for completed prior-season features.

After that, rerun the historical snapshot build and trainability label linkage audit. Do not use current-state overwritten source files as historical prediction-time feature sources without explicit availability proof.
