# Model v4.3.5 Historical Replay Judgment Repair

## Goal

Repair the historical rookie replay judge before changing rookie formulas.

The external audit found that the model formula is probably viable, but the replay infrastructure was too easy to misread because it mixed broad offensive draft history, immature outcome windows, and a single loose hit label.

## What Changed

- Added `Fantasy-Relevant Replay Pool` to distinguish likely 10-team rookie-draft candidates from all NFL-drafted offensive players.
- Added `Outcome Maturity` so 2021-2023, 2024, and 2025 are not judged as equally mature.
- Added separate hit labels:
  - `Broad Outcome Hit?`
  - `Strict Starter Hit?`
  - `Difference Maker?`
- Regenerated historical replay exports under `local_exports/model_v4/historical_rookie_tuning/latest`.
- Updated the Model Tuning page to show the new judgment columns.

## Guardrails

- No formula weights were changed.
- No model scores were changed by outcome labels.
- No market, ADP, ranking, projection, mock, or big-board fields were introduced into private value.
- No active rankings, My Team, War Board, readiness gates, or app promotion were changed.

## Why This Matters

The replay should now answer a cleaner question:

> Given the pre-draft rookie formula, how often did the model put future usable, starter, and difference-maker outcomes into the parts of the board a 10-team manager would actually draft?

That is a different question from:

> Did every NFL-drafted offensive player become useful?

The second question is too broad and makes the model look worse than it is.

## Current Reading

The model is not proven perfect, but it is not dead. The next audit should focus on repeated miss patterns inside the fantasy-relevant replay pool, especially mature 2021-2023 classes.
