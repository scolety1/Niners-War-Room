# Model Rank Source Truth Non Mutation Report

## Verdict

`PASS`

This safe upgrade lane does not mutate:

- model inputs
- model outputs
- Dynasty Rank
- Final Board Rank
- tiers
- hidden sort keys
- trade values
- pick values
- source-truth files
- latest approved or pinned model artifacts

## Code Scope

Added:

- `src/services/injury_availability_context_service.py`
- `tests/test_injury_availability_context_service.py`

No app page, model, rank, source-truth, or runtime state file is changed by the
implementation.

## Service Guardrails

The safe service returns:

- `display_only=true`
- `review_only=true`
- `model_input_allowed=false`
- `rank_use_allowed=false`
- `source_truth_allowed=false`

Dataset-backed availability fields return `Not enough information` while the
Refresh Health gate is not green.

## Existing V0 Display

Existing Rankings and Player Compare V0 display context remains review-only. This
lane preserves that display path and does not promote it.
