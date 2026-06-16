# Build Sprint 4G: Supplement Source Registration

Status: `NO_SUPPLEMENT_SOURCE_REGISTERED`

Sprint 4G creates the registration groundwork for rare scoring component supplements. It does not recompute labels, train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, or deploy.

## Inputs

Canonical Sprint 4 source remains:

- `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_week.csv`

Supplement candidates audited:

- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2022.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2023.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2024.csv.gz`

## Outputs

Sprint 4G writes local-only outputs under:

`local_exports/outcome_probability/sprint_4g_supplement_source_registration/`

Created outputs:

- `supplement_timestamp_policy.csv`
- `supplement_field_quarantine.csv`
- `supplement_join_key_audit.csv`
- `pbp_aggregation_allowlist.csv`
- `waiver_reduction_readiness.csv`
- `README_SPRINT_4G.md`

## Timestamp Policy Findings

- `player_stats.csv`: `file_timestamp_only`
- `play_by_play_2022.csv.gz`: `event_date_only`
- `play_by_play_2023.csv.gz`: `event_date_only`
- `play_by_play_2024.csv.gz`: `event_date_only`

No candidate has row-level source timestamps. Event dates are not source-ingestion timestamps and must not be promoted to production-ready point-in-time source timestamps.

## Field Quarantine

Strict allowlist candidates, still gated by timestamp and join validation:

- `passing_2pt_conversions`
- `rushing_2pt_conversions`
- `receiving_2pt_conversions`
- `special_teams_tds`
- `return_yards`
- `return_touchdown`
- returner player IDs
- fumble recovery player IDs/yards
- two-point attribution fields

Explicitly blocked:

- `fantasy_points`
- `fantasy_points_ppr`
- EPA fields
- WPA/WP fields
- win-probability fields
- betting/probability fields
- projection/ranking/market/ADP-style fields
- public fantasy totals as label sources

Quarantine summary:

- allowlist candidates pending timestamp: `103`
- blocked fields: `180`
- manual-review fields: `33`
- excluded by default: `853`

## Join-Key Validation

`player_stats.csv` candidate key:

- `player_id | season | week`

Findings:

- truth-set rows matched: `1183`
- missing player IDs: `0`
- duplicate join keys: `1`
- team mismatches on truth-set matches: `0`
- status: plausible join key, but timestamp-blocked

Play-by-play candidate key after event attribution:

- `player_id | season | week | game_id`

Findings:

- truth-set event matches: `47`
- unmatched supplement events: `5576`
- duplicate candidate event join keys: `1393`
- missing player IDs or uncredited event candidates: `138583`
- status: requires event aggregation allowlist and attribution review

## Play-By-Play Aggregation Allowlist

Sprint 4G defines strict aggregation contracts for:

- return yards by credited returner
- return TDs by credited returner
- fumble recovery TDs by credited recovery player
- fumble recovery yards as audit-only context unless scoring config changes
- two-point plays only when player attribution is clear

Do not infer player credit from ambiguous description text. Lateral returner fields, missing returner IDs, and conflicting `td_player_id` cases require manual review.

## Waiver-Reduction Readiness

Components closest to registration after timestamp policy:

- passing 2-point conversions
- rushing 2-point conversions
- receiving 2-point conversions
- special teams TDs

Components requiring play-by-play aggregation:

- return yards
- return TDs
- fumble recovery TDs

No component can be registered now. `truth_set_v0_component_waiver_v1` remains acceptable for internal-only benchmark use and still blocks calibrated/app-facing probability work.

## Next Step

Register a timestamped `player_stats.csv` supplement source with strict field quarantine for 2-point conversions and special teams TDs. Then build fixture-tested play-by-play aggregation helpers for return yards, return TDs, and fumble recovery TDs before any expanded v0 rebuild.
