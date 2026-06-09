# Truth Set Lab v3 Phase 3: Derived Usage From nflverse Play-By-Play

Generated: 2026-05-15

## Status

Review-only usage preview. No active rankings, formulas, model gates, or data packs were changed.

## Purpose

This phase replaces the rejected role/usage CSV path with usage signals derived from structured nflverse play-by-play. It does **not** estimate route-based metrics.

## Outputs

Reports are stored in:

`local_exports/truth_set_lab/v3/reports/`

Files:

- `truth_set_v3_usage_player_week.csv`
- `truth_set_v3_usage_player_season.csv`
- `truth_set_v3_usage_missing_players.csv`
- `truth_set_v3_usage_summary.csv`
- `truth_set_v3_usage_summary.json`

Downloaded official source cache:

- `local_exports/truth_set_lab/v3/downloads/play_by_play_2022.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2023.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2024.csv.gz`

## Derived Fields

The preview derives:

- targets
- team targets
- target share
- RB target share
- rushing attempts
- team rushing attempts
- RB carry share
- weighted opportunities
- red-zone carries
- red-zone targets
- goal-line carries
- goal-line targets
- short-yardage carries

All derived rows are marked:

`source_status = derived_real_data`

## Explicit Non-Estimates

This phase does **not** estimate:

- routes run
- route participation
- targets per route run
- yards per route run

Those remain unavailable from free/public structured data and must stay visible as a source gap unless a legal structured source is added later.

## Current Run Summary

The current official nflverse play-by-play source available to this local run covers the same useful range as the v3 production preview: 2022, 2023, and 2024.

Summary:

- Truth-set players: 40
- Players with matched player IDs: 35
- Missing players: 5
- Play-by-play rows read: 148,591
- Player-week usage rows: 1,255
- Player-season usage rows: 83
- Requested seasons: 2022, 2023, 2024

Missing players are listed explicitly rather than imputed:

- Ashton Jeanty
- Jayden Higgins
- Kaleb Johnson
- Luther Burden
- Oronde Gadsden II

## Method Notes

- Target share is derived from player targets divided by team targets for the player team-week or season.
- RB carry share is derived from player rush attempts divided by team rush attempts.
- RB target share currently uses the same team-target denominator as target share, keeping the denominator explicit.
- Weighted opportunities use `carries + (1.15 * targets)` for preview purposes.
- Red-zone usage uses `yardline_100 <= 20`.
- Goal-line usage uses `yardline_100 <= 5`.
- Short-yardage carries use `ydstogo <= 2`.
- Active player-weeks from nflverse production rows seed the usage table so zero-usage active weeks are retained rather than silently omitted.

## Model Safety

This phase does not promote usage into active rankings. It only creates v3 preview inputs. Later v3 phases must decide how to merge these validated rows into source coverage, receipts, and model previews.

## Next Phase

Implement Truth Set Lab v3 Phase 4: Snap Share Import.

