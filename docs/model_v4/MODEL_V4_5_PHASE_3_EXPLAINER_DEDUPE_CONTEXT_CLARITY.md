# Model v4.5 Phase 3 - Explainer De-Dupe And Context Clarity

## Purpose

Phase 3 resolves the audit concern that some players appeared multiple times in the Player Rank Explainer because the same name existed in multiple review contexts.

This phase changes only the explanation layer and its CSV outputs. It does not change formulas, player scores, active rankings, My Team, War Board, readiness gates, app promotion, or final recommendations.

## De-Dupe Strategy

The default explainer table now uses one primary row per player.

When a player exists as both:

- `rookie_prospect`
- `current_player`

the explainer keeps the rookie row as the primary human-facing row and collapses the current-player context into component receipts.

This keeps the table readable while preserving auditability.

## Context Preservation

Collapsed current-player contexts are preserved in:

`local_exports/model_v4/explainers/latest/player_rank_explainer_component_rows.csv`

They use:

- `entity_type`: `alternate_context`
- `component_name`: `current_player_context_preserved`
- `receipt_pointer`: `current_value_context_collapsed_from_default_view`

Current-player component rows are also retained with:

- `entity_type`: `alternate_context_current_player`

Collapsed current-player warnings are preserved in:

`local_exports/model_v4/explainers/latest/player_rank_explainer_warnings.csv`

They use:

- `entity_type`: `alternate_context`
- `warning_plain_english`: begins with `Alternate current-player context:`

## Regenerated Outputs

- `local_exports/model_v4/explainers/latest/player_rank_explainer_rows.csv`
- `local_exports/model_v4/explainers/latest/player_rank_explainer_component_rows.csv`
- `local_exports/model_v4/explainers/latest/player_rank_explainer_warnings.csv`
- `docs/model_v4/PLAYER_RANK_EXPLAINER.md`

## Output Check

After regeneration:

- default explainer rows: 285
- component receipt rows: 2320
- warning rows: 2460
- alternate context receipts: 5
- alternate context warnings: 69
- duplicate player rows in default explainer: 0

Named-player sanity:

- Jeremiyah Love: 1 default row, `rookie_prospect`
- Carnell Tate: 1 default row, `rookie_prospect`
- Skyler Bell: 1 default row, `rookie_prospect`
- Makai Lemon: 1 default row, `rookie_prospect`

## Tests

Focused tests prove:

- top-50 rookie default rows have no confusing duplicate player rows
- collapsed duplicate contexts are preserved in component receipts
- collapsed duplicate warnings are preserved in warning drilldowns
- every explanation remains review-only
- top-50 rookies still have explanations and manual review notes
- component receipts remain present
- blocked market/projection/consensus language does not enter explainer value text

## Verdict

Explainer de-dupe is implemented. The default human-facing explainer is clearer, and alternate context remains available for audit/review.
