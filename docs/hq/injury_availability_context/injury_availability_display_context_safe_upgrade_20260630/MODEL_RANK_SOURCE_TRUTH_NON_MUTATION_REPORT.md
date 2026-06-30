# Model Rank Source Truth Non Mutation Report

## Verdict

`PASS`

This denominator follow-up does not mutate:

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
- recommendations

## Code Scope

Changed:

- `src/services/injury_availability_context_service.py`
- `tests/test_injury_availability_context_service.py`

No model, rank, source-truth, latest pointer, frozen board, Live Draft, Mock
Draft, Trading Lab valuation, trade-value, pick-value, or recommendation file
is changed by the implementation.

## Service Guardrails

The safe service returns display-only/review-only context and enforces:

- safe identity gate before player context detail
- `denominator_status=SAFE_NOW_DISPLAY_ONLY` before denominator detail
- `games_missed_while_rostered=Not enough information`
- missing injury/status/snap/stat/denominator data remains `Not enough information`
- no raw `C:\NWR_SHARED_DATA` reads from app pages

## Existing Display

Existing Rankings and Player Compare display context remains review-only. The
Player Compare table now includes safe denominator fields but does not promote
them to rank, model, source-truth, hidden sort, recommendation, trade value, or
pick value logic.
