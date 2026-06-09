# Model v4 RotoWire Intake Build Kickoff

Status: started

## Purpose

Build a licensed-data intake spine from the manually exported RotoWire files before changing
Model v4 scoring or app promotion.

## Raw Source Roots

- RotoWire manual exports:
  `local_exports/model_v4/raw_user_exports/rotowire_manual`
- Rookie manual upload drop zone:
  `local_exports/model_v4/raw_user_exports/rookie_manual/incoming`

## First Intake Output

- Source index:
  `local_exports/model_v4/rotowire_intake/latest/rotowire_source_index.csv`
- Source index summary:
  `local_exports/model_v4/rotowire_intake/latest/rotowire_source_index_summary.csv`

## Current Source Index Result

- CSV files indexed: 128
- Clean files: 128
- Review files: 0
- Active canonical files: 103
- Inactive duplicate/sample files: 25
- Stable active schema groups: 37

## Guardrails

- Raw RotoWire exports remain local and immutable.
- RotoWire data may be used for the local model, but raw licensed exports should not be
  redistributed in public audit packets.
- Market, ADP, and external rankings are context/sanity only.
- Injuries are sourced risk context only; absence from an injury file is not healthy evidence.
- Team context and offensive-line rankings are environment context only.
- Projections are comparison/review context until LVE scoring is recomputed locally.
- Rookie uploads stay separate until validated and mapped.
- Duplicate raw exports are preserved but excluded from canonical intake reads.

## Next Build Steps

1. Add RotoWire schema validators and canonical header maps.
2. Build player identity normalization for RotoWire names, teams, status suffixes, and duplicate
   stat headers.
3. Build normalized evidence tables for historical player stats, snaps, targets, alignment,
   TE routes, depth charts, injuries, projections, rankings/ADP, combine/workout, and team context.
4. Generate a RotoWire-powered stats-first Model v4 preview.
5. Run sanity fixtures and named-player audits before any app promotion.
