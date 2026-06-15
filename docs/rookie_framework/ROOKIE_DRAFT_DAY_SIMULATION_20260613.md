# Rookie Draft-Day Simulation v0.3 - 2026-06-13

## Status

Stage 7 creates a local-only dry-run simulation export for Tim's known rookie picks:

- `1.03`
- `1.04`
- `2.04`
- `2.08`
- `5.04`

This is not opponent modeling, not ADP logic, not market logic, not probability modeling, not app wiring, and not production ranking promotion.

## Inputs

The simulation reads only the rookie analyzer local export:

`local_exports/model_v4/rookie_framework_v02/rookie_analyzer_v03/rookie_analyzer_v03.csv`

It must not read `data/`, production ranking files, private-score files, app/Streamlit files, outcome files, veteran outcome-head files, probabilities, bands, ADP, public rankings, projections, consensus, market values, trade values, or draft-kit ranks.

## Outputs

The simulation writes local-only exports to:

`local_exports/model_v4/rookie_framework_v02/draft_day_simulation_v03/`

Expected files:

- `rookie_draft_day_simulation_v03.csv`
- `rookie_draft_day_pick_cards_v03.csv`
- `README_ROOKIE_DRAFT_DAY_SIMULATION_V03.md`

Generated local exports must not be committed.

## Row Markers

Every simulation row and pick-card row must keep:

- `simulation_only=yes`
- `app_ready=no`
- `production_score_created=no`
- `probabilities_created=no`

Rows missing any marker fail validation.

## 1.03 Handling

`1.03` remains no-player-cleared.

The simulation creates a single `1.03` row:

- `player=NO_PLAYER_CLEARED`
- `simulation_action=trade_down_or_manual_review`
- `fit_signal=trade_down_or_manual_review_only_no_player_cleared`

No player is forced into `1.03`.

## Pick-Card Logic

The pick cards summarize analyzer-based context only:

- top review options;
- manual-review options;
- emergency-stop count;
- trade-down signal;
- default action.

The pick cards do not rank the whole player pool, create private values, or approve production implementation.

## Guardrails

- No opponent modeling.
- No ADP.
- No public rankings.
- No projections.
- No consensus.
- No market values.
- No trade calculators.
- No probabilities or bands.
- No app or Streamlit wiring.
- No production scores.
- No private-score overwrite.
- No veteran outcome heads.
- Warnings remain visible.
- `data/` remains untouched and uncommitted.
- `local_exports/` remains uncommitted.

## Stage 7 Gate

Stage 7 is GREEN if:

- strict review-board build passes;
- strict shadow-ranking build passes;
- strict production-candidate build passes;
- strict analyzer build passes;
- strict draft-day simulation build passes;
- direct harnesses pass;
- `1.03` remains no-player-cleared;
- only the Stage 7 tracked files are committed.
