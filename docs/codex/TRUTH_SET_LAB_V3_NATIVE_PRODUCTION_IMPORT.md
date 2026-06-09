# Truth Set Lab v3 Phase 2: Native nflverse Production Import

Generated: 2026-05-15

## Status

Review-only production preview. No active rankings, formulas, model gates, or data packs were changed.

## Purpose

This phase replaces the rejected agent-built production CSV path with structured nflverse player stats. The production file is now sourced from the official nflverse `player_stats.csv` release and filtered to the 40-player truth set.

## Outputs

Reports are stored in:

`local_exports/truth_set_lab/v3/reports/`

Files:

- `truth_set_v3_production_player_week.csv`
- `truth_set_v3_production_player_season.csv`
- `truth_set_v3_production_missing_players.csv`
- `truth_set_v3_production_summary.csv`
- `truth_set_v3_production_summary.json`

Downloaded official source cache:

`local_exports/truth_set_lab/v3/downloads/player_stats.csv`

## Imported Fields

The preview imports:

- player/team/position/season/week identifiers
- passing yards, passing touchdowns, interceptions
- rushing attempts, rushing yards, rushing touchdowns
- targets, receptions, receiving yards, receiving touchdowns
- rushing first downs
- receiving first downs
- total fumbles where available
- fumbles lost where available

All matched production rows are marked:

`source_status = imported_real_data`

## Current Run Summary

The current official nflverse source available to this local run covers through the 2024 season.

Summary:

- Truth-set players: 40
- Matched players: 35
- Missing players: 5
- Player-week rows: 1,183
- Player-season rows: 83
- Requested seasons: 2022, 2023, 2024
- First-down fields present: true
- Rows with rushing or receiving first downs: 1,091

Missing players are listed explicitly rather than imputed:

- Ashton Jeanty
- Jayden Higgins
- Kaleb Johnson
- Luther Burden
- Oronde Gadsden II

These rows remain `source_status = missing` until nflverse includes NFL production rows for them or another structured source is validated.

## Model Safety

This phase does not promote production into active rankings. It only creates v3 preview inputs. Later v3 phases must decide how to merge these validated rows into the preview model and receipts.

## Next Phase

Implement Truth Set Lab v3 Phase 3: Derived Usage From nflverse Play-By-Play.

