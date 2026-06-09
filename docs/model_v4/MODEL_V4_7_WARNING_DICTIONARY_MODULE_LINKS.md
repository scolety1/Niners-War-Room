# Model v4.7 Warning Dictionary Module Links

## Goal

Patch the non-blocking v4.6 audit concern that warning codes could still require cross-reference to understand which module or evidence surface to inspect.

## Changes

Added these fields to `warning_code_dictionary.csv`:

- `primary_module`
- `primary_export`
- `receipt_or_drilldown_to_open`
- `example_review_question`

## Module Inference

The dictionary infers modules conservatively from source file paths:

- `source_risk_heatmap`
- `model_edge_queue`
- `player_rank_explainer`
- `rookie_draft_review`
- `roster_opportunity_cost`
- `rookie_pick_decision_lab`
- `multiple_modules`
- `unknown`

## Safety

Raw warning codes and source file paths remain preserved. This patch only improves traceability from a warning code to the right app surface or CSV. It does not change formulas, scores, rankings, My Team, War Board, readiness gates, app promotion, or recommendations.
