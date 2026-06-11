# Build Sprint 4F: Rare Component Supplements

Status: `WAIVER_REMAINS_INTERNAL_ONLY_ACCEPTABLE`

Sprint 4F audits local candidate sources for rare scoring components currently covered by `truth_set_v0_component_waiver_v1`. It does not merge supplemental data into labels, train calibrated models, create player-facing probabilities, create app percentage values, create rankings, push, or deploy.

## Sources Audited

Canonical Sprint 4 source remains:

- `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_week.csv`

Supplement candidates audited:

- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2022.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2023.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2024.csv.gz`

## Source Findings

`player_stats.csv` has structured supplement fields:

- `passing_2pt_conversions`
- `rushing_2pt_conversions`
- `receiving_2pt_conversions`
- `special_teams_tds`

It also contains fields that must remain quarantined:

- `fantasy_points`
- `fantasy_points_ppr`
- EPA/derived efficiency fields

The play-by-play files have event-level candidates:

- `return_yards`
- `return_touchdown`
- punt/kick returner IDs
- fumble recovery player IDs and yards
- two-point attempt/result fields

They also contain many fields requiring strict quarantine:

- EPA/WP/probability fields
- fantasy player ID/name helper fields
- betting/probability context fields

## Timestamp Legality

No supplement source is registered for production supplement use in Sprint 4F.

- `player_stats.csv` lacks row-level `source_date`; it can only move forward after a source manifest timestamp/quarantine policy.
- Play-by-play files have `game_date`, but not a source-ingestion timestamp suitable by itself for point-in-time supplement registration.
- File-level timestamps were recorded as audit context only.

Missing source timestamps block waiver reduction in this sprint.

## Mapping Contract

Sprint 4F writes a dry-run mapping contract:

- `raw_passing_2pt_conversions` from `player_stats.csv:passing_2pt_conversions`
- `raw_rushing_2pt_conversions` from `player_stats.csv:rushing_2pt_conversions`
- `raw_receiving_2pt_conversions` from `player_stats.csv:receiving_2pt_conversions`
- `raw_return_yards` from play-by-play `return_yards` plus returner ID attribution
- `raw_return_tds` from play-by-play `return_touchdown` plus returner/TD attribution
- `raw_special_teams_tds` from `player_stats.csv:special_teams_tds`
- `raw_fumble_recovery_tds` from play-by-play fumble recovery plus TD attribution

No mapping is applied to labels in Sprint 4F.

## Join Safety

Dry-run join keys:

- `player_stats.csv`: `player_id | season | week`
- play-by-play: `player_id | season | week | game_id`

Join risks:

- `player_stats.csv` needs source timestamp and fantasy-total quarantine before registration.
- play-by-play requires event aggregation rules before duplicate and ambiguity checks can be final.
- team/week/game mismatch checks remain future work for the supplement registration pass.

## Nonzero Impact

Dry-run truth-set joins found nonzero rare components:

- passing 2-point conversions: 9 player-weeks, max swing 2.0 points
- rushing 2-point conversions: 6 player-weeks, max swing 2.0 points
- receiving 2-point conversions: 14 player-weeks, max swing 2.0 points
- return yards: 17 player-weeks, max swing 1.5667 points
- fumble recovery TDs: 1 player-week, max swing 4.0 points
- return TDs: 0 player-weeks in this dry run
- special teams TDs: 0 player-weeks in this dry run

These results show the waiver is not purely theoretical, but the current impact appears rare/small in the limited truth-set universe. Labels were not changed.

## Waiver Decision

`WAIVER_REMAINS_INTERNAL_ONLY_ACCEPTABLE`

The waiver cannot be reduced now because candidate supplement fields exist but are blocked by missing source timestamps and play-by-play mapping/quarantine gaps.

The waiver still blocks calibrated/app-facing probability work.

## Outputs

Sprint 4F writes local-only outputs under:

`local_exports/outcome_probability/sprint_4f_rare_component_supplements/`

Created outputs:

- `rare_component_source_audit.csv`
- `rare_component_mapping_contract.csv`
- `rare_component_join_key_audit.csv`
- `rare_component_nonzero_impact.csv`
- `component_waiver_decision.csv`
- `blocked_fields_audit.csv`
- `rare_component_component_decisions.csv`
- `README_SPRINT_4F.md`

## Next Step

Register a timestamped, quarantined `player_stats.csv` supplement source for 2-point conversions and special teams TDs. Then build a strict play-by-play aggregation allowlist for return yards, return TDs, and fumble recovery TDs before any expanded v0 rebuild.
