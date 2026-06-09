# Model v4.3.4 Historical Rookie Tuning Tab

## Goal

Add a review-only Model Tuning page that replays the rookie formula shape against historical rookie classes before making any further formula changes.

## Scope

The new sidebar page is `Model Tuning` at `/model-tuning`.

The first subsection is `Historical Rookie Replay`, covering draft years:

- 2021
- 2022
- 2023
- 2024
- 2025

## Data Sources

- Historical replay input: `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv`
- Outcome labels: `local_exports/model_v4/historical_rookie_outcomes/latest/historical_rookie_outcome_labels.csv`
- Outcome source: `local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv`

Outcome labels are display-only. They are never used to rank players.

The current outcome label build covers 395 historical rookie rows from 2021-2025 and loads post-draft RotoWire fantasy outcomes for 338 rows. The remaining rows stay visibly unlabeled instead of being treated as misses.

## Table Shape

Each year tab uses the same review columns as the Draft Room prospect board:

- rank
- player
- position
- NFL team
- college
- final score
- production score
- College Team Share
- NFL Draft Pick Signal
- athletic score
- age score
- confidence cap
- evidence available
- Trust Level
- draft round
- overall pick
- model edge/source warning
- fantasy-relevant replay pool
- outcome status
- outcome maturity
- outcome category
- broad outcome hit
- strict starter hit
- difference maker hit
- best LVE PPG
- starter-level seasons
- why this rank

## Replay Judgment Layer

The tab now separates the model score from the backtest judgment:

- `Fantasy-Relevant Replay Pool` filters out players who were NFL-drafted but unlikely to matter in a typical 10-team rookie draft.
- `Broad Outcome Hit?` counts usable, starter, and difference-maker outcomes.
- `Strict Starter Hit?` counts starter and difference-maker outcomes only.
- `Difference Maker?` is the highest outcome bucket.
- `Outcome Maturity` marks 2021-2023 as mature, 2024 as partial, and 2025 as rookie-year-only.

## Guardrails

- No formulas were tuned in this phase.
- No active rankings were changed.
- My Team and War Board were not mutated.
- Outcomes are joined after scoring only.
- Fantasy-relevant replay-pool flags are backtest filters only and do not feed model scoring.
- Missing outcome labels remain visibly missing.

## Known Limitations

Outcome coverage is broad but not complete. Unloaded outcomes are marked as missing labels, not failed players. The tab is useful for spotting formula behavior, especially production/team-share versus draft capital, but formula changes should still be made only after reviewing the labeled misses and the unlabeled rows separately.
