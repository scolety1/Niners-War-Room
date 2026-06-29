# Historical NFL Outcome Target Source Gate - 2026-06-30

## Gate Result

`GREEN_REVIEW_ONLY_NFL_OUTCOME_TARGET_SOURCE`

The NFL outcome target source can be used as review-only target truth for
future historical rookie labels. It cannot by itself identify rookie
classes or approve modeling/training use.

## Source Candidate

- Source family: `nflreadpy.load_player_stats(summary_level=reg)`
- Shared generated artifacts: Outcome V2 extended historical labels
- Shared root: `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended`
- Season rows: 7440
- Anchor rows: 7440
- Complete 5Y rows: 1064
- Scoring mode: `exact_verified_first_downs`

## Source Policy

- Uses factual public NFL player-season outcomes.
- Does not use market, ADP, DynastyProcess, projections, vendor/Gmail, or CFBD.
- Rows remain review-only and not model/training/app wiring approved.

## Guardrails

- `model_use_allowed=false` for this rookie lane.
- `training_allowed=false` for this rookie lane.
- CFBD is not used as NFL outcome truth.
