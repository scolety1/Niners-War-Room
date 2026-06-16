# Build Sprint 4J: Supplemented Internal V0 Rebuild

Status: local-only supplemented internal benchmark rebuild completed.

Sprint 4J performs an approval-gated rebuild of the limited internal v0 benchmark using rare-component label-layer supplements approved by HQ. This is not calibrated model training, not app-facing probability work, not player-facing probabilities, not rankings, and not deployment work.

## Approval Scope

Approved use is limited to post-event label-layer scoring reconstruction for the internal truth-set v0 benchmark.

This approval does not admit either supplement source as a prediction-time feature source.

This approval does not approve:

- app-facing probabilities
- player-facing probabilities
- calibrated model training
- public rankings
- production deployment
- active app or ranking logic changes

## Component Policy

Supplement policy ID:

`truth_set_v0_component_supplemented_internal_v1`

All Sprint 4J benchmark outputs carry:

- `component_policy_id = truth_set_v0_component_supplemented_internal_v1`
- `scope = limited_truth_set_v0`
- `internal_only = true`

## Sources Merged

Canonical truth-set source:

- `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_week.csv`

Approved label-layer supplement sources:

- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2022.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2023.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2024.csv.gz`

## Player Stats Supplement Contract

Policy:

`allowed_label_supplement_file_timestamp`

Allowed quarantined fields:

- passing 2-point conversions
- rushing 2-point conversions
- receiving 2-point conversions
- special teams TDs

Join key:

`player_id | season | week`

Duplicate handling:

Allowed components are deterministically summed by join key. The known duplicate key from Sprint 4H is outside the truth-set join surface and remains auditable.

Prediction-feature use:

Not allowed.

## Play-By-Play Supplement Contract

Policy:

`allowed_label_supplement_event_date_only`

Allowed strict aggregations:

- return yards by credited primary returner
- return TDs by credited returner
- fumble recovery TDs by credited recovery player

Join key:

`player_id | season | week`

Attribution rules:

- Return yards require exactly one primary punt/kick returner and no lateral ambiguity.
- Return TDs require `return_touchdown = 1` and `td_player_id` matching the sole credited returner.
- Fumble recovery TDs require `touchdown = 1` and `td_player_id` matching exactly one credited fumble recovery player.

Ambiguous attribution is excluded and reported. Event-date-only PBP is not prediction-feature-ready.

## Merge Audit Results

- Canonical truth-set rows: 1,183
- Player stats truth-key matches: 1,183
- Player stats nonzero truth matches: 29
- PBP truth-key matches: 18
- PBP nonzero truth matches: 18
- Forbidden supplement payload fields: 0
- App or ranking changes required: no

Imported fantasy totals, EPA/WP/probability fields, rankings, projections, market fields, and future-looking fields remain blocked from the supplement payload.

## Score Delta Summary

- Affected player-weeks: 47
- Affected player-seasons: 30
- Total NWR score delta from supplements: 86.1667

The observed deltas come only from the approved rare components:

- passing 2-point conversions
- rushing 2-point conversions
- receiving 2-point conversions
- special teams TDs
- return yards
- return TDs
- fumble recovery TDs

## Label Change Summary

- Same-year label-change rows: 0
- Manual-review label changes: 0

No same-year difference-maker, starter, useful, or replacement-or-bust labels changed in the limited truth-set rebuild.

## Collapsed Benchmark Rebuild

Sprint 4J retains the Sprint 4C collapsed benchmark restrictions.

Direct benchmark bucket families kept:

- `position`
- `position_cohort`

Disabled or lineage-only:

- `age_band` remains disabled
- `prior_finish_tier`, `trailing_ppg_tier`, and `games_played_tier` remain collapsed to parent lineage

Outcomes kept:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

Outcomes disabled:

- `next_year_starter`

Supplemented collapsed benchmark rows emitted: 64.

## Local Exports

Sprint 4J writes only to:

`local_exports/outcome_probability/sprint_4j_supplemented_v0_rebuild/`

Export files:

- `supplement_merge_audit.csv`
- `supplemented_score_delta_report.csv`
- `supplemented_label_change_report.csv`
- `supplemented_collapsed_v0_benchmark.csv`
- `supplemented_benchmark_readiness_summary.csv`
- `supplemented_vs_waived_benchmark_comparison.csv`
- `manual_review_label_changes.csv`
- `README_SPRINT_4J.md`

## Readiness Verdict

`SUPPLEMENTED_INTERNAL_BENCHMARK_READY`

The supplement merge passed quarantine and deterministic-join checks, produced no same-year label changes, and rebuilt the collapsed benchmark under the same internal-only restrictions.

## Sprint 5 Status

Sprint 5 calibrated model work remains blocked.

Remaining blockers before Sprint 5:

- HQ needs to approve whether the supplemented internal benchmark should replace the waiver-based internal benchmark as the Sprint 5 benchmark reference.
- Age/DOB and broader data coverage remain outside the Sprint 4J activation scope.
- No app-facing probabilities or calibrated model outputs are approved.
