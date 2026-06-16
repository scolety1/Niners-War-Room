# Build Sprint 5I: Trainability Label Linkage Audit

Date: 2026-06-11

Verdict: `NOT_READY_LABELS_IMMATURE`

Sprint 5I audits whether the legal feature snapshots emitted in Sprint 5H can link to mature, legally available row-level labels. The answer is no for now. The snapshots are legal and useful as prediction-time artifacts, but they are not training rows because the relevant 2026 outcome labels are not mature or available.

No calibrated models were trained. No app percentages, public/player-facing probabilities, rankings, model artifacts, push, deploy, or active app/ranking changes were created.

## Inputs Inspected

Sprint 5H local exports:

- `local_exports/outcome_probability/sprint_5h_cutoff_approved_snapshot_rebuild/candidate_feature_snapshots.csv`
- `local_exports/outcome_probability/sprint_5h_cutoff_approved_snapshot_rebuild/row_family_snapshot_readiness.csv`
- `local_exports/outcome_probability/sprint_5h_cutoff_approved_snapshot_rebuild/feature_legality_audit.csv`
- `local_exports/outcome_probability/sprint_5h_cutoff_approved_snapshot_rebuild/feature_missingness_report.csv`
- `local_exports/outcome_probability/sprint_5h_cutoff_approved_snapshot_rebuild/rookie_post_draft_manifest_audit.csv`

Reference label/benchmark context:

- `local_exports/outcome_probability/sprint_4j_supplemented_v0_rebuild/supplemented_collapsed_v0_benchmark.csv`
- `local_exports/outcome_probability/sprint_5a_calibration_feasibility/outcome_event_support.csv`
- `local_exports/outcome_probability/sprint_5b_aggregate_baseline_mechanics/aggregate_outcome_support.csv`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_season.csv`

Historical rookie outcome files were observed, but their existing lineage is display/audit context and does not legally turn the 2026 rookie snapshots into trainable rows.

## Snapshot-Label Linkage Summary

| Row family | Emitted snapshots | Trainable now | Prediction-only / future-facing | Blocked |
| --- | ---: | ---: | ---: | ---: |
| `all_player_pre_week1` | 35 | 0 | 35 | 0 |
| `rookie_post_draft` | 257 | 0 | 257 | 0 |
| `offseason_carryover` | 0 | 0 | 0 | 35 |

Total emitted snapshots: 292.

Trainable rows now: 0.

Prediction-only / future-facing rows: 292.

Blocked row-family attempts: 35.

## Why Legal Snapshots Are Not Training Rows

A feature snapshot can become a training row only after the target label window has matured and the label is legally available.

Sprint 5H emitted 2026 target snapshots:

- `all_player_pre_week1` rows need mature 2026 same-year labels, and next-year labels would require later windows.
- `rookie_post_draft` rows are 2026 rookie post-draft snapshots, so their rookie and future windows are not mature.
- `offseason_carryover` emitted no rows because it remains blocked by source-after-cutoff policy.

Therefore, all emitted snapshots are prediction-only at this stage.

## Outcome Support For Trainable Rows

| Outcome | Trainable rows | Event count | Non-event count | Status |
| --- | ---: | ---: | ---: | --- |
| `same_year_difference_maker` | 0 | 0 | 0 | No mature row-level labels linked. |
| `same_year_starter` | 0 | 0 | 0 | No mature row-level labels linked. |
| `same_year_useful` | 0 | 0 | 0 | No mature row-level labels linked. |
| `same_year_replacement_or_bust` | 0 | 0 | 0 | No mature row-level labels linked. |
| `next_year_starter` | 0 | 0 | 0 | Future window unavailable/censored. |

There is no event/non-event modeling support from Sprint 5H rows yet.

## Feature Completeness

For emitted snapshots:

- `all_player_pre_week1`: 35/35 rows have age, experience, prior games, prior first-down production, prior receptions, and prior rushing/receiving/passing yards.
- `rookie_post_draft`: 257/257 rows have draft year, round, pick, and draft day.
- `rookie_post_draft`: 138/257 rows have age; 119/257 keep `age_at_snapshot` missing.

For trainable rows:

- No feature completeness can be assessed for modeling because there are 0 trainable rows.

Missing optional fields remain missing and are not zero-filled.

## Local Exports

Sprint 5I wrote local-only outputs under:

`local_exports/outcome_probability/sprint_5i_trainability_label_linkage/`

Files:

- `snapshot_label_linkage.csv`
- `row_family_trainability.csv`
- `trainable_outcome_support.csv`
- `position_trainability_support.csv`
- `feature_completeness_for_trainable_rows.csv`
- `immature_or_censored_label_report.csv`
- `modeling_feasibility_reassessment.csv`
- `README_SPRINT_5I.md`

## Modeling Feasibility Reassessment

Result: `NOT_READY_LABELS_IMMATURE`

Internal toy modeling should not start from these rows yet because there are zero trainable rows. Aggregate snapshot-quality diagnostics remain allowed, but not model fitting or calibrated probability work.

Production/app modeling remains blocked.

## Remaining Blockers Before True Calibrated Modeling

- Mature row-level labels are absent for the 2026 all-player snapshots.
- 2026 rookie post-draft snapshots are future-facing and not mature.
- `offseason_carryover` remains blocked until an on-or-before `YYYY-02-15` source snapshot or approved availability manifest exists.
- Historical feature snapshots must be built for seasons with mature labels before model training.
- Broader non-enriched rows, out-of-time validation support, confidence/display gates, and a final leakage audit are still required before any production/app modeling.

## Recommended Next Step

Build a historical feature snapshot set for seasons that already have mature legal labels, or hold the 2026 snapshots as prediction-only until their outcome windows mature. For rookie modeling, build historical rookie post-draft snapshots from approved factual draft manifests and legally mature outcome labels.
