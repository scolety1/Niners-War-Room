# Build Sprint 3C - Data Readiness Dry Run

Status: `NOT_READY_NEEDS_DATA`

Sprint 3C ran the committed Sprint 1, Sprint 2, Sprint 3, and Sprint 3B scaffolds against real local candidate sources and fixture/template sources. This sprint did not build v0 base rates, train models, create player probabilities, create app percentage values, create rankings, push, or deploy.

## Output Folder

Dry-run outputs were written only under:

`local_exports/outcome_probability/sprint_3c_data_readiness/`

Created outputs:

- `source_inventory.csv`
- `row_family_manifest.csv`
- `raw_stat_mapping_report.csv`
- `leakage_audit_report.csv`
- `missingness_report.csv`
- `candidate_prediction_snapshots.csv`
- `candidate_feature_snapshots.csv`
- `README_SPRINT_3C.md`

## Sources Inspected

Sprint 3C inspected 28 candidate local sources across:

- truth-set / NFLVERSE raw data downloads
- truth-set production, usage, and snap-share reports
- sleeper / NFLVERSE identity bridge files
- Model v4 historical rookie outcome and tuning files
- Model v4 RotoWire evidence intake files
- sample historical rookie replay files
- template real-data input contracts

Important real local source candidates:

- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2022.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2023.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2024.csv.gz`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_week.csv`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_usage_player_week.csv`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_snap_share_player_week.csv`
- `local_exports/truth_set_lab/v3_2/promoted_review_models/truth_set_v3_2_promoted_review_20260515T212700Z/sleeper_nflverse_identity_bridge.csv`
- `local_exports/truth_set_lab/v3_2/promoted_review_models/truth_set_v3_2_promoted_review_20260515T212700Z/stats_first_normalized_features.csv`
- `local_exports/model_v4/historical_rookie_outcomes/latest/historical_rookie_outcome_labels.csv`
- `local_exports/model_v4/historical_rookie_tuning/latest/historical_rookie_tuning_board_rows.csv`

## Source Classification Summary

Readiness counts:

- `ready`: 1
- `needs_data`: 10
- `manual_review_required`: 15
- `display_only`: 1
- `blocked`: 1

The only `ready` source in this dry run is a fixture/sample rookie input with timestamped rows. It is not enough to claim real-data readiness.

Real truth-set/NFLVERSE candidate files contain useful historical data, but most are currently blocked from production row emission because they lack row-level source timestamps, are not yet explicitly registered as allowed source families, or require manual review.

## Row-Family Readiness

All supported row families remain blocked:

- `rookie_post_draft`: blocked
- `all_player_pre_week1`: blocked
- `offseason_carryover`: blocked

Common blockers:

- required source families are missing or not ready in the manifests
- source-family classification is still unknown/manual-review for several real local exports
- source timestamps are missing on otherwise useful raw files
- cutoff templates still need concrete historical-season dates

No candidate training rows were emitted. `candidate_prediction_snapshots.csv` records the blocked/not-emitted status; `candidate_feature_snapshots.csv` is intentionally empty except for headers.

## Raw-Stat Mapping Readiness

The dry run confirms that local files contain many Sprint 1 raw scoring components.

Available in at least one real/template source:

- passing yards
- passing touchdowns
- interceptions
- carries
- rushing yards
- rushing touchdowns
- rushing first downs
- receptions
- receiving yards
- receiving touchdowns
- receiving first downs
- fumbles lost
- return yards
- return touchdowns

Still incomplete or needs explicit handling:

- passing two-point conversions
- rushing two-point conversions
- receiving two-point conversions
- sacks suffered
- special touchdowns
- fumble recovery touchdowns
- miscellaneous yards
- consistent return-yard / return-touchdown coverage across real production rows

Imported fantasy totals are rejected as label sources. Sprint 4 labels must be reconstructed from raw stat components, not imported fantasy point totals.

## First-Down Field Coverage

First-down coverage exists but is not yet production-ready:

- `player_stats.csv` includes `passing_first_downs`, `rushing_first_downs`, and `receiving_first_downs`, but lacks row-level source timestamps.
- `truth_set_v3_production_player_week.csv` includes `rushing_first_downs` and `receiving_first_downs` plus `source_date`, but the source family is still manual-review/unknown to the generic manifest classifier.
- Template NFLVERSE contracts include first-down columns but contain no real rows.

## Leakage Audit Results

Sample row-level leakage audit rows:

- total sampled leakage rows: 100
- blocked rows: 75
- manual-review rows: 25

Issue breakdown:

- `missing_source_timestamp`: 25
- `forbidden_source_or_field`: 50
- `unknown_source`: 25

The forbidden rows came from blocked projection/import contexts. Those remain excluded from predictive inputs.

## Missingness Results

`missingness_report.csv` contains 96 readiness issues across:

- missing required row-family source families
- missing raw stat scoring components
- imported fantasy total rejection
- specific first-down / fumble / return coverage gaps by file

Missing optional features are not zero-filled; they are carried as missingness/readiness issues.

## Data-Readiness Verdict

Verdict: `NOT_READY_NEEDS_DATA`

Sprint 4 v0 base rates should not start yet.

Before Sprint 4, NWR needs:

1. explicit source-family registration for the selected real local source files
2. row-level `source_max_timestamp`, `source_date`, or equivalent timestamp coverage on real raw stat / identity / label files
3. concrete cutoff dates by historical season
4. a decision on canonical raw stat source: direct `player_stats.csv` / play-by-play, or the reconstructed `truth_set_v3_production_player_week.csv`
5. a policy for missing two-point, sack, special touchdown, fumble recovery touchdown, misc yard, and return scoring components
6. full-file row-level leakage audits after sources are registered
7. confirmation that fixture/sample files are not mistaken for real production training data

## Guardrails

No base rates, probabilities, rankings, app percentages, push, or deploy occurred.

Forbidden/public/market/projection/rank/trade-calculator/legacy private-score fields remain blocked or manual-review-only. RotoWire factual/raw evidence still requires source-family review unless already explicitly allowed.

