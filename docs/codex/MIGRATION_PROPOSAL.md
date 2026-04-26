# Migration Proposal

## Summary

V1 uses local SQLite schema creation for the War Room data model. Migrations are local-only and do not touch production systems.

## Reversibility

Generated SQLite databases can be deleted and recreated from CSV data packs. No production migration rollback is needed in V1.

## Data Impact

Only local SQLite files under `data_packs/` are affected. Generated database files are ignored by git.

## Affected Tables Or Collections

- players
- teams
- owners
- rosters
- official_rankings
- future_picks
- pick_values
- market_values
- player_features
- model_outputs
- owner_notes
- metadata_sources
- import_errors

## Local Run Evidence

`scripts/codex-static-check.ps1` initializes a temporary SQLite database and runs tests plus Ruff.

## Rollback Plan

Revert schema code changes and recreate local SQLite databases from source CSV snapshots.
