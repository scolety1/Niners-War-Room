# Build Sprint 5C: Data Expansion And Feature Snapshot Plan

Status: data expansion and legal feature snapshot plan created.

Sprint 5C defines the next data layer required before true calibrated outcome modeling can begin. It does not train calibrated models, create app percentage values, create player-facing probabilities, create rankings, push, deploy, or modify active app/ranking logic.

## Context

Sprint 5B verdict:

`AGGREGATE_MECHANICS_PASS_WITH_WARNINGS`

Current blockers:

- same-year starter and useful outcomes are one-class saturated
- replacement/bust is one-class in the opposite direction
- next-year starter is censored/disabled
- current truth-set universe is too narrow and enriched
- legal point-in-time feature snapshots are absent
- out-of-time validation support is weak

## Readiness Verdict

`READY_AFTER_SOURCE_REGISTRATION`

Feature snapshot build work can start after candidate sources are registered and audited. Production/app modeling remains blocked.

## Blocker-To-Solution Matrix

| Blocker | Required Solution |
| --- | --- |
| one-class/saturated outcomes | expand denominator beyond the enriched truth-set universe with broader player-season rows |
| censored next-year starter | use complete future windows or explicitly exclude next-year outcomes |
| limited truth-set universe | register broader nflverse-derived player-week/player-season rows |
| missing legal feature snapshots | materialize point-in-time `FeatureSnapshot` rows with source timestamps, lineage, and missingness masks |
| weak out-of-time split support | register walk-forward train/calibration/test splits with enough seasons |
| missing app display gate | keep app output blocked until a probability package and display policy exist |
| final leakage audit | audit all features, labels, splits, and outputs before model work |

## Broader Row-Source Candidates

Candidate local sources:

- `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_week.csv`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_season.csv`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_usage_player_week.csv`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_usage_player_season.csv`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_snap_share_player_week.csv`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_snap_share_player_season.csv`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2022.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2023.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2024.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/snap_counts_2022.csv`
- `local_exports/truth_set_lab/v3/downloads/snap_counts_2023.csv`
- `local_exports/truth_set_lab/v3/downloads/snap_counts_2024.csv`
- `local_exports/nflverse/preview/*/downloads/dynastyprocess_db_playerids.csv`
- `sample_data/historical_rookie_replay/pre_draft_prospect_inputs.csv`
- `sample_data/historical_rookie_replay/post_draft_outcomes.csv`
- `local_exports/model_v4/audit_packets/*historical_rookie*/*historical_rookie_backtest_feature_matrix.csv`

Source classifications are written to:

`local_exports/outcome_probability/sprint_5c_data_expansion_feature_snapshots/candidate_broader_row_sources.csv`

Blocked or display-only examples:

- historical Yahoo draft history is blocked as a predictive feature
- projection files are blocked
- trade/market/liquidity context is display-only
- label supplement sources remain blocked as prediction-time features

## Legal Feature Snapshot Schema Plan

Future modeling feature snapshots should include only source-safe, timestamped, point-in-time features:

- age/DOB metadata
- position
- team at cutoff
- experience at cutoff
- prior NWR scoring finish tiers
- prior NWR PPG
- prior games played/games active
- trailing target share
- trailing carry share
- trailing snap share
- trailing first-down production
- timestamped draft capital for `rookie_post_draft`
- timestamped injury/status context

Every feature row must include:

- cutoff ID
- input snapshot date
- source family
- source field
- source available timestamp
- source max timestamp
- lineage
- missingness mask
- future-data flag
- target-window overlap check

Explicitly excluded:

- ADP
- FantasyPros
- public rankings
- consensus
- startup rankings
- trade calculators
- projections
- RotoWire projections/rankings/outlooks/values
- market rank
- league rank
- prior fantasy draft history
- legacy private_score
- same-season final stats as preseason features
- hindsight notes

## Cutoff Feature Availability Plan

Supported future row families:

| Row Family | Cutoff Template | Available Feature Families |
| --- | --- | --- |
| `all_player_pre_week1` | `YYYY-09-01` | team, age, position, prior-season scoring, prior usage, prior snap, prior first-down, injury at cutoff |
| `offseason_carryover` | `YYYY-02-15` | age, position, offseason team, prior season finish, prior PPG, prior usage, prior snap, prior injury status |
| `rookie_post_draft` | `YYYY-05-01` | identity, position, school, age, draft capital, landing team, source-safe post-draft facts |

Do not implement pre-draft or in-season rows in this plan.

## Minimum Support Targets

Future support targets before model work:

- position-only baseline: at least 500 observed rows with both classes and at least 50 events/non-events where possible
- position/cohort baseline: at least 100 rows per major position/cohort bucket with both classes
- ridge logistic: at least 1,000 rows preferred and legal feature snapshots present
- Platt calibration: at least 200 holdout rows with both classes and a stable score source
- isotonic calibration: at least 1,000 holdout rows preferred
- discrete-time hazard model: multiple complete future windows and uncensored labels
- gradient boosting challenger: several thousand legal rows, broad features, and robust out-of-time validation

These are planning targets, not model outputs.

## Future Row Expansion Targets

| Outcome | Needed Rows/Support |
| --- | --- |
| `same_year_difference_maker` | more non-events, broader player universe, more seasons |
| `same_year_starter` | more non-events, broader player universe, better labels |
| `same_year_useful` | more non-events, broader player universe, better labels |
| `same_year_replacement_or_bust` | more events, broader lower-end player universe |
| `next_year_starter` | uncensored future windows, more seasons, broader rows, explicit label availability |

## Local Exports

Sprint 5C writes local-only planning exports under:

`local_exports/outcome_probability/sprint_5c_data_expansion_feature_snapshots/`

Files:

- `modeling_blocker_solution_matrix.csv`
- `candidate_broader_row_sources.csv`
- `feature_snapshot_schema_plan.csv`
- `feature_source_allowlist_plan.csv`
- `cutoff_feature_availability_plan.csv`
- `minimum_support_targets.csv`
- `future_row_expansion_targets.csv`
- `README_SPRINT_5C.md`

## Next Safe Build

The next safe sprint is source registration plus legal `FeatureSnapshot` construction for the approved row families. It should not fit models or emit app/player-facing probabilities.

Production/app modeling remains blocked until broader legal rows, materialized feature snapshots, out-of-time splits, confidence gates, app display gates, and final leakage audit are complete.
