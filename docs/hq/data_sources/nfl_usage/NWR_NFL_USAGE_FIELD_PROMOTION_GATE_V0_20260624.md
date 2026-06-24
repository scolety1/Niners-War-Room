# NFL Usage Field Promotion Gate V0

## Statuses

- `RESEARCH_ONLY`
- `DISPLAY_ONLY_CANDIDATE`
- `CANDIDATE_MODEL_FEATURE_PENDING_BACKTEST`
- `APPROVED_DISPLAY_ONLY`
- `APPROVED_MODEL_CANDIDATE`
- `BLOCKED_LICENSED_GAP`
- `BLOCKED_UNSAFE`

## V0 Rule

All fields remain `RESEARCH_ONLY`, `DISPLAY_ONLY_CANDIDATE`, `CANDIDATE_MODEL_FEATURE_PENDING_BACKTEST`, `BLOCKED_LICENSED_GAP`, or `BLOCKED_UNSAFE`. No field is approved in V0.

## Promotion Requirements

- exact source provenance
- stable schema fingerprint
- sufficient player/season/week coverage
- no leakage
- internal consistency checks
- documented missing-data behavior
- attribution compliance
- no market, projection, rank, ADP, or vendor-opinion contamination
- walk-forward backtest improvement
- rollback plan if non-additive
