# Model v4 Confidence Cap Receipt Regeneration Pilot V1

## Verdict

`GREEN_CONFIDENCE_CAP_RECEIPTS_REGENERATED_REVIEW_ONLY`

## Clear Answer

Confidence-cap receipts were regenerated as review-only component-coverage receipts from lagged partial historical component receipts. They are safe for Master HQ review and may support future review-only component signal test planning, but they do not unblock exact Model v4 replay or Formula Gauntlet tournaments.

## Pilot Summary

- Regenerated rows: `5518`
- Season coverage: `2013-2025`
- Position coverage: `QB=754, RB=1429, TE=1211, WR=2124`
- Duplicate keys: `0`
- Leakage/as-of validation: `pass`
- Identity/missingness validation: `pass`
- Maximum allowed use: `REVIEW_ONLY_COMPONENT_SIGNAL_TESTS` after separate Master HQ execution approval.

## Confidence Status Counts

- `review_only_full_component_coverage`: `5490`
- `review_only_high_component_coverage`: `28`

## Guardrails

- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- Production/model-use remains blocked.
- No source was promoted.
